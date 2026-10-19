"""Painel web local para ver o catálogo real da loja e ajustar os pesos do rodízio.

Uso: `python -m shopee_rodizio.painel [caminho/para/config.toml]` — escuta em
`[painel].endereco:[painel].porta` (padrão `0.0.0.0:8790`) e é acessado da LAN por
`http://<ip-do-pi>:8790`. Serviço SEPARADO do rodízio (`systemd/shopee-painel.service`):
cair aqui não afeta o rodízio, que só lê o `config.toml` gravado por este processo.

Peso no hardware (o CB1 divide CPU com o Klipper): `http.server` da stdlib, uma thread só,
sem dependência nova. Ocioso, o processo fica bloqueado em `select()` — 0% de CPU, sem
timer nem polling. A página é estática (HTML/JS/CSS deste pacote) e as imagens dos produtos
o navegador baixa direto do CDN da Shopee, não passam pelo Pi. A API da Shopee só é chamada
quando o cache do catálogo vence ou o usuário pede (`catalogo.py`).

Segurança (mexer em pesos é mexer em dinheiro, mesmo na LAN):
- só atende IPs de `[painel].redes_permitidas` (padrão: faixas privadas RFC 1918 +
  loopback); bind só IPv4, então um IPv6 global do Pi nunca expõe o painel; a interface do
  Tailscale (100.64.0.0/10) também fica de fora por padrão;
- HTTP Basic com a senha guardada como hash PBKDF2 em `[painel].senha_hash` (config.toml,
  nunca versionado); sem hash configurado, o painel não atende nada;
- escrita só via POST com `Content-Type: application/json` + header `X-Painel: 1` (força
  preflight CORS, que nunca é respondido — barra CSRF de outra aba do navegador que já
  tenha a senha em cache) e `Host` precisa ser IP literal ou o nome da máquina (barra DNS
  rebinding);
- nenhuma resposta, página ou linha de log carrega partner_key, access_token ou
  refresh_token: o JSON é montado campo a campo, nunca a partir de `Config`.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import ipaddress
import json
import logging
import os
import secrets
import socket
import sys
import time
from datetime import UTC, datetime, timedelta
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs

from . import armazem_token, catalogo, relatorio
from .config import (
    Config,
    ConfigError,
    ConflitoConfig,
    atualizar_itens,
    carregar_config,
    nomes_nos_comentarios,
    versao_config,
)
from .estado import ancora_do_intervalo, carregar_estado, segundos_ate_proximo_ciclo

_logger = logging.getLogger("shopee_rodizio.painel")

_CAMINHO_CONFIG_PADRAO = "config.toml"
_DIR_ESTATICO = Path(__file__).with_name("painel_web")
_ESTATICOS = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/painel.js": ("painel.js", "text/javascript; charset=utf-8"),
    "/painel.css": ("painel.css", "text/css; charset=utf-8"),
}
_CSP = (
    "default-src 'self'; img-src 'self' https: data:; connect-src 'self'; "
    "style-src 'self'; script-src 'self'; frame-ancestors 'none'; base-uri 'none'; "
    "form-action 'none'"
)
PESO_MAXIMO = 1000
DIAS_RELATORIO = (1, 7, 30, 90)
_TAMANHO_MAXIMO_CORPO = 64 * 1024
_PAUSA_SENHA_ERRADA = 1.0
ITERACOES_PBKDF2 = 200_000


# --- Senha -----------------------------------------------------------------------------------


def gerar_hash_senha(senha: str, iteracoes: int = ITERACOES_PBKDF2) -> str:
    """`pbkdf2_sha256$<iteracoes>$<sal hex>$<hash hex>` — stdlib, sem dependência."""
    sal = secrets.token_bytes(16)
    derivado = hashlib.pbkdf2_hmac("sha256", senha.encode("utf-8"), sal, iteracoes)
    return f"pbkdf2_sha256${iteracoes}${sal.hex()}${derivado.hex()}"


def verificar_senha(senha: str, senha_hash: str) -> bool:
    try:
        algoritmo, iteracoes, sal, esperado = senha_hash.split("$")
        if algoritmo != "pbkdf2_sha256":
            return False
        derivado = hashlib.pbkdf2_hmac(
            "sha256", senha.encode("utf-8"), bytes.fromhex(sal), int(iteracoes)
        )
    except ValueError:
        return False
    return hmac.compare_digest(derivado.hex(), esperado)


# --- Regras de acesso ------------------------------------------------------------------------


def cliente_permitido(ip: str, redes: tuple[str, ...]) -> bool:
    try:
        endereco = ipaddress.ip_address(ip)
    except ValueError:
        return False
    if isinstance(endereco, ipaddress.IPv6Address) and endereco.ipv4_mapped:
        endereco = endereco.ipv4_mapped
    return any(endereco in ipaddress.ip_network(rede, strict=False) for rede in redes)


def host_permitido(host: str | None, nomes_maquina: tuple[str, ...]) -> bool:
    """`Host` tem de ser IP literal ou um nome desta máquina — barra DNS rebinding."""
    if not host:
        return False
    nome = host.rsplit(":", 1)[0] if host.count(":") == 1 else host
    nome = nome.strip("[]").lower()
    try:
        ipaddress.ip_address(nome)
        return True
    except ValueError:
        return nome in nomes_maquina


def _nomes_desta_maquina() -> tuple[str, ...]:
    nome = socket.gethostname().lower()
    return (nome, f"{nome}.local", "localhost")


# --- Montagem das respostas ------------------------------------------------------------------


def montar_estado(
    config: Config,
    texto_config: str,
    cache: catalogo.CacheCatalogo,
    *,
    agora: datetime | None = None,
    erro_catalogo: str | None = None,
) -> dict:
    """JSON da página. Montado campo a campo: nenhuma credencial entra aqui."""
    agora = agora or datetime.now(UTC)
    estado = carregar_estado(config.caminhos.estado)
    nomes_config = nomes_nos_comentarios(texto_config)

    desde = agora - timedelta(days=7)
    historico: dict[int, dict] = {}
    for registro in estado.historico:
        try:
            momento = datetime.fromisoformat(registro.timestamp)
        except ValueError:
            continue
        if momento.tzinfo is None:
            momento = momento.replace(tzinfo=UTC)
        info = historico.setdefault(
            registro.item_id, {"ultimo_sucesso_em": None, "sucessos_7d": 0, "tentativas_7d": 0}
        )
        if momento >= desde:
            info["tentativas_7d"] += 1
            info["sucessos_7d"] += int(registro.sucesso)
        if registro.sucesso:
            info["ultimo_sucesso_em"] = registro.timestamp

    ultimo = ancora_do_intervalo(estado)
    espera = segundos_ate_proximo_ciclo(estado, config.ciclo.intervalo_horas, agora)
    return {
        "versao": versao_config(texto_config),
        "ciclo": {
            "intervalo_horas": config.ciclo.intervalo_horas,
            "limite_slots": config.ciclo.limite_slots,
            "ultimo_ciclo_em": ultimo.isoformat() if ultimo else None,
            "proximo_ciclo_em": (agora + timedelta(seconds=espera)).isoformat(),
        },
        "rodizio": [{"id": item.id, "peso": item.peso} for item in config.itens],
        "nomes_config": {str(k): v for k, v in nomes_config.items()},
        "catalogo": {
            "atualizado_em": cache.atualizado_em.isoformat() if cache.atualizado_em else None,
            "vencido": cache.vencido(config.painel.cache_horas, agora),
            "erro": erro_catalogo,
            "itens": [
                {
                    "id": item.id,
                    "nome": item.nome,
                    "imagem_url": item.imagem_url,
                    "preco_min": item.preco_min,
                    "preco_max": item.preco_max,
                    "estoque": item.estoque,
                    "status": item.status,
                    "tem_variacoes": item.tem_variacoes,
                }
                for item in cache.itens
            ],
        },
        "historico": {str(k): v for k, v in historico.items()},
    }


def montar_relatorio(
    config: Config,
    texto_config: str,
    cache: catalogo.CacheCatalogo,
    dias: int,
    *,
    agora: datetime | None = None,
) -> dict:
    """JSON das abas "No ar agora" e "Relatório" — só agregados do `estado.json`."""
    estado = carregar_estado(config.caminhos.estado)
    nomes = {str(k): v for k, v in nomes_nos_comentarios(texto_config).items()}
    nomes.update({str(i.id): i.nome for i in cache.itens if i.nome})
    imagens = {str(i.id): i.imagem_url for i in cache.itens if i.imagem_url}
    return {
        "agora": relatorio.no_ar_agora(estado, agora),
        "relatorio": relatorio.relatorio(
            estado, dias, {i.id: i.peso for i in config.itens}, agora
        ),
        "nomes": nomes,
        "imagens": imagens,
    }


def dias_do_pedido(query: str) -> int:
    """`?dias=N` com N em `DIAS_RELATORIO`; qualquer outra coisa vira 7."""
    valor = parse_qs(query).get("dias", ["7"])[0]
    return int(valor) if valor.isdigit() and int(valor) in DIAS_RELATORIO else 7


class PedidoInvalido(Exception):
    """Pedido de gravação de pesos recusado; a mensagem é mostrada ao usuário."""


def validar_pesos(corpo: object, ids_conhecidos: set[int]) -> list[tuple[int, int]]:
    """Valida o pedido de gravação; lança `PedidoInvalido` com mensagem para o usuário."""
    if not isinstance(corpo, dict) or not isinstance(corpo.get("itens"), list):
        raise PedidoInvalido("corpo inválido: esperado {versao, itens: [{id, peso}]}")
    itens: list[tuple[int, int]] = []
    vistos: set[int] = set()
    for bruto in corpo["itens"]:
        if not isinstance(bruto, dict):
            raise PedidoInvalido("item inválido")
        item_id, peso = bruto.get("id"), bruto.get("peso")
        if type(item_id) is not int or type(peso) is not int:
            raise PedidoInvalido("id e peso precisam ser inteiros")
        if not 1 <= peso <= PESO_MAXIMO:
            raise PedidoInvalido(f"peso do item {item_id} fora de 1..{PESO_MAXIMO}")
        if item_id in vistos:
            raise PedidoInvalido(f"item {item_id} repetido")
        if item_id not in ids_conhecidos:
            raise PedidoInvalido(f"item {item_id} não está no catálogo nem no rodízio atual")
        vistos.add(item_id)
        itens.append((item_id, peso))
    if not itens:
        raise PedidoInvalido("o rodízio precisa de pelo menos um item")
    return itens


# --- Servidor --------------------------------------------------------------------------------


class Painel:
    """Estado do processo: caminho do config, cache de autenticação, última atualização."""

    def __init__(self, caminho_config: str | Path) -> None:
        self.caminho_config = Path(caminho_config)
        self.nomes_maquina = _nomes_desta_maquina()
        # PBKDF2 custa ~0,5 s no CB1: verificar a cada requisição queimaria a CPU que o
        # Klipper usa. Guarda o digest do header já validado (e do hash que o validou).
        self._autorizados: set[str] = set()
        self._ultima_tentativa_catalogo: datetime | None = None
        self._erro_catalogo: str | None = None

    def ler_config(self) -> tuple[Config, str]:
        texto = self.caminho_config.read_text(encoding="utf-8")
        return carregar_config(self.caminho_config), texto

    def autorizado(self, cabecalho: str | None, senha_hash: str) -> bool:
        if not cabecalho or not cabecalho.startswith("Basic "):
            return False
        chave = hashlib.sha256(f"{senha_hash}\n{cabecalho}".encode()).hexdigest()
        if chave in self._autorizados:
            return True
        try:
            _usuario, _, senha = base64.b64decode(cabecalho[6:], validate=True).decode(
                "utf-8"
            ).partition(":")
        except ValueError:  # base64 inválido (binascii.Error) ou não-UTF-8
            return False
        if not verificar_senha(senha, senha_hash):
            return False
        self._autorizados = {chave}  # uma senha válida por vez; trocar a senha invalida
        return True

    def cache(self, config: Config, *, forcar: bool = False) -> catalogo.CacheCatalogo:
        caminho = catalogo.caminho_cache(config.caminhos.estado)
        atual = catalogo.carregar_cache(caminho)
        if not forcar and not atual.vencido(config.painel.cache_horas):
            return atual
        agora = datetime.now(UTC)
        if (
            self._ultima_tentativa_catalogo is not None
            and agora - self._ultima_tentativa_catalogo < catalogo.INTERVALO_MINIMO_ATUALIZACAO
        ):
            return atual
        self._ultima_tentativa_catalogo = agora
        try:
            # sempre o cliente ligado ao token.json do serviço: renovar com o token do
            # config.toml quebraria a cadeia de refresh_token (uso único)
            cliente = armazem_token.cliente_da_config(config)
            novo = catalogo.baixar_catalogo(
                cliente, buscar_variacoes=config.painel.buscar_variacoes
            )
        except catalogo.ErroCatalogo as exc:
            self._erro_catalogo = f"não foi possível atualizar o catálogo: {exc}"
            _logger.warning(self._erro_catalogo)
            return atual
        catalogo.gravar_cache(caminho, novo)
        self._erro_catalogo = None
        _logger.info("catálogo atualizado: %d anúncio(s) ativo(s)", len(novo.itens))
        return novo

    @property
    def erro_catalogo(self) -> str | None:
        return self._erro_catalogo


def criar_handler(painel: Painel) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        server_version = "shopee-painel"
        sys_version = ""
        timeout = 15  # cliente lento/parado não segura a única thread

        def log_message(self, formato: str, *args) -> None:
            # só método, path sem query e status — nunca headers (Authorization)
            _logger.info(
                "%s %s %s %s",
                self.client_address[0],
                self.command,
                self.path.split("?", 1)[0],
                args[1] if len(args) > 1 else "",
            )

        # -- portaria ----------------------------------------------------------------------

        def _barrado(self) -> bool:
            try:
                config, _ = painel.ler_config()
                redes = config.painel.redes_permitidas
                senha_hash = config.painel.senha_hash
            except (ConfigError, OSError, ValueError, TypeError) as exc:
                self._texto(HTTPStatus.SERVICE_UNAVAILABLE, f"config.toml inválido: {exc}")
                return True
            if not cliente_permitido(self.client_address[0], redes):
                self._texto(HTTPStatus.FORBIDDEN, "fora da rede local")
                return True
            if not host_permitido(self.headers.get("Host"), painel.nomes_maquina):
                self._texto(HTTPStatus.FORBIDDEN, "host não permitido")
                return True
            if not senha_hash:
                self._texto(
                    HTTPStatus.SERVICE_UNAVAILABLE,
                    "senha do painel não definida: rode scripts/atalhos/definir_senha_painel.sh",
                )
                return True
            if not painel.autorizado(self.headers.get("Authorization"), senha_hash):
                if self.headers.get("Authorization"):
                    time.sleep(_PAUSA_SENHA_ERRADA)
                self.send_response(HTTPStatus.UNAUTHORIZED)
                self.send_header("WWW-Authenticate", 'Basic realm="shopee-rodizio", charset="UTF-8"')
                self._cabecalhos_comuns("text/plain; charset=utf-8", 0)
                self.end_headers()
                return True
            return False

        # -- rotas -------------------------------------------------------------------------

        def do_GET(self) -> None:
            if self._barrado():
                return
            path = self.path.split("?", 1)[0]
            if path in _ESTATICOS:
                nome, tipo = _ESTATICOS[path]
                self._enviar(HTTPStatus.OK, (_DIR_ESTATICO / nome).read_bytes(), tipo)
            elif path == "/api/estado":
                config, texto = painel.ler_config()
                cache = painel.cache(config)
                self._json(
                    HTTPStatus.OK,
                    montar_estado(config, texto, cache, erro_catalogo=painel.erro_catalogo),
                )
            elif path == "/api/relatorio":
                config, texto = painel.ler_config()
                cache = catalogo.carregar_cache(catalogo.caminho_cache(config.caminhos.estado))
                query = self.path.partition("?")[2]
                self._json(
                    HTTPStatus.OK, montar_relatorio(config, texto, cache, dias_do_pedido(query))
                )
            else:
                self._texto(HTTPStatus.NOT_FOUND, "não encontrado")

        def do_POST(self) -> None:
            if self._barrado():
                return
            if (
                self.headers.get("X-Painel") != "1"
                or self.headers.get_content_type() != "application/json"
            ):
                self._texto(HTTPStatus.FORBIDDEN, "requisição recusada")
                return
            path = self.path.split("?", 1)[0]
            if path == "/api/catalogo/atualizar":
                config, texto = painel.ler_config()
                cache = painel.cache(config, forcar=True)
                self._json(
                    HTTPStatus.OK,
                    montar_estado(config, texto, cache, erro_catalogo=painel.erro_catalogo),
                )
            elif path == "/api/pesos":
                self._gravar_pesos()
            else:
                self._texto(HTTPStatus.NOT_FOUND, "não encontrado")

        def _gravar_pesos(self) -> None:
            try:
                tamanho = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                tamanho = -1
            if not 0 < tamanho <= _TAMANHO_MAXIMO_CORPO:
                self._json(HTTPStatus.BAD_REQUEST, {"erro": "corpo ausente ou grande demais"})
                return
            try:
                corpo = json.loads(self.rfile.read(tamanho))
            except ValueError:
                self._json(HTTPStatus.BAD_REQUEST, {"erro": "JSON inválido"})
                return

            config, _ = painel.ler_config()
            cache = catalogo.carregar_cache(catalogo.caminho_cache(config.caminhos.estado))
            conhecidos = {i.id for i in cache.itens} | {i.id for i in config.itens}
            try:
                itens = validar_pesos(corpo, conhecidos)
            except PedidoInvalido as exc:
                self._json(HTTPStatus.BAD_REQUEST, {"erro": str(exc)})
                return
            nomes = {i.id: i.nome for i in cache.itens if i.nome}
            try:
                atualizar_itens(
                    painel.caminho_config, itens, nomes, versao_esperada=corpo.get("versao")
                )
            except ConflitoConfig as exc:
                self._json(HTTPStatus.CONFLICT, {"erro": str(exc)})
                return
            except (ConfigError, OSError) as exc:
                self._json(HTTPStatus.BAD_REQUEST, {"erro": f"não gravado: {exc}"})
                return
            _logger.info("pesos gravados: %d item(ns) no rodízio", len(itens))
            config, texto = painel.ler_config()
            self._json(
                HTTPStatus.OK,
                montar_estado(config, texto, cache, erro_catalogo=painel.erro_catalogo),
            )

        # -- respostas ---------------------------------------------------------------------

        def _cabecalhos_comuns(self, tipo: str, tamanho: int) -> None:
            self.send_header("Content-Type", tipo)
            self.send_header("Content-Length", str(tamanho))
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Security-Policy", _CSP)
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("X-Frame-Options", "DENY")
            self.send_header("Referrer-Policy", "no-referrer")

        def _enviar(self, status: HTTPStatus, corpo: bytes, tipo: str) -> None:
            self.send_response(status)
            self._cabecalhos_comuns(tipo, len(corpo))
            self.end_headers()
            self.wfile.write(corpo)

        def _json(self, status: HTTPStatus, dados: dict) -> None:
            corpo = json.dumps(dados, ensure_ascii=False).encode("utf-8")
            self._enviar(status, corpo, "application/json; charset=utf-8")

        def _texto(self, status: HTTPStatus, texto: str) -> None:
            self._enviar(status, texto.encode("utf-8"), "text/plain; charset=utf-8")

    return Handler


def criar_servidor(caminho_config: str | Path, endereco: str, porta: int) -> HTTPServer:
    """Servidor single-thread (as gravações ficam serializadas por construção)."""
    return HTTPServer((endereco, porta), criar_handler(Painel(caminho_config)))


def _analisar_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="python -m shopee_rodizio.painel",
        description="Painel web local (LAN) para ajustar os pesos do rodízio.",
    )
    parser.add_argument("config", nargs="?", default=_CAMINHO_CONFIG_PADRAO)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = _analisar_args(sys.argv[1:] if argv is None else argv)
    logging.basicConfig(
        level=logging.INFO, format="%(levelname)s %(message)s", stream=sys.stderr
    )
    config = carregar_config(args.config)
    servidor = criar_servidor(args.config, config.painel.endereco, config.painel.porta)
    _logger.info(
        "painel escutando em http://%s:%d (pid %d)",
        config.painel.endereco,
        config.painel.porta,
        os.getpid(),
    )
    if not config.painel.senha_hash:
        _logger.warning("senha do painel não definida — nada será atendido até definir")
    try:
        servidor.serve_forever(poll_interval=3600)
    except KeyboardInterrupt:
        pass
    finally:
        servidor.server_close()


if __name__ == "__main__":
    main()
