"""Leitura, validação e regravação (só do bloco `[[itens]]`) da configuração TOML."""

from __future__ import annotations

import hashlib
import re
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from .arquivo import gravar_atomico, travado


class ConfigError(Exception):
    """Configuração inválida; a mensagem identifica o campo problemático."""


class ConflitoConfig(Exception):
    """O `config.toml` mudou desde que foi lido (outro escritor gravou no meio)."""


@dataclass(frozen=True)
class ShopeeCredenciais:
    partner_id: int
    partner_key: str
    shop_id: int
    access_token: str
    refresh_token: str


@dataclass(frozen=True)
class CicloConfig:
    intervalo_horas: int
    limite_slots: int
    endpoint_boost: str


@dataclass(frozen=True)
class CaminhosConfig:
    log: str
    estado: str


@dataclass(frozen=True)
class RedeConfig:
    """Seção opcional: ausente em config.toml existente = sem proxy, comportamento igual
    a antes desta seção existir."""

    proxy_https: str | None = None


# faixas privadas IPv4 (RFC 1918) + loopback — o painel só atende clientes da rede local
REDES_LAN_PADRAO = ("10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16", "127.0.0.0/8")


@dataclass(frozen=True)
class PainelConfig:
    """Seção opcional `[painel]` — só o painel web (`painel.py`) a lê; o serviço ignora."""

    endereco: str = "0.0.0.0"
    porta: int = 8790
    senha_hash: str | None = None
    redes_permitidas: tuple[str, ...] = REDES_LAN_PADRAO
    cache_horas: int = 24
    buscar_variacoes: bool = True


@dataclass(frozen=True)
class Item:
    id: int
    peso: int


@dataclass(frozen=True)
class Config:
    shopee: ShopeeCredenciais
    ciclo: CicloConfig
    caminhos: CaminhosConfig
    itens: list[Item]
    rede: RedeConfig = field(default_factory=RedeConfig)
    painel: PainelConfig = field(default_factory=PainelConfig)


_CAMPOS_SHOPEE = ("partner_id", "partner_key", "shop_id", "access_token", "refresh_token")
_CAMPOS_CICLO = ("intervalo_horas", "limite_slots", "endpoint_boost")
_CAMPOS_CAMINHOS = ("log", "estado")


def carregar_config(caminho: str | Path) -> Config:
    """Lê o arquivo TOML em `caminho`, valida e devolve uma `Config` tipada."""
    dados = tomllib.loads(Path(caminho).read_text(encoding="utf-8"))
    return _validar(dados)


def _validar(dados: dict) -> Config:
    shopee = _validar_secao(dados, "shopee", _CAMPOS_SHOPEE)
    ciclo = _validar_secao(dados, "ciclo", _CAMPOS_CICLO)
    caminhos = _validar_secao(dados, "caminhos", _CAMPOS_CAMINHOS)

    if ciclo["intervalo_horas"] <= 0:
        raise ConfigError("ciclo.intervalo_horas deve ser > 0")
    if ciclo["limite_slots"] <= 0:
        raise ConfigError("ciclo.limite_slots deve ser > 0")

    itens_brutos = dados.get("itens")
    if not itens_brutos:
        raise ConfigError("campo ausente: itens (é preciso ao menos um [[itens]])")

    itens = [_validar_item(item, i) for i, item in enumerate(itens_brutos)]
    rede = RedeConfig(proxy_https=dados.get("rede", {}).get("proxy_https"))

    return Config(
        shopee=ShopeeCredenciais(**shopee),
        ciclo=CicloConfig(**ciclo),
        caminhos=CaminhosConfig(**caminhos),
        itens=itens,
        rede=rede,
        painel=_validar_painel(dados.get("painel", {})),
    )


def _validar_painel(secao: dict) -> PainelConfig:
    padrao = PainelConfig()
    porta = secao.get("porta", padrao.porta)
    if not isinstance(porta, int) or not 1 <= porta <= 65535:
        raise ConfigError("painel.porta deve ser um inteiro entre 1 e 65535")
    cache_horas = secao.get("cache_horas", padrao.cache_horas)
    if not isinstance(cache_horas, int) or cache_horas <= 0:
        raise ConfigError("painel.cache_horas deve ser > 0")
    return PainelConfig(
        endereco=secao.get("endereco", padrao.endereco),
        porta=porta,
        senha_hash=secao.get("senha_hash") or None,
        redes_permitidas=tuple(secao.get("redes_permitidas", padrao.redes_permitidas)),
        cache_horas=cache_horas,
        buscar_variacoes=bool(secao.get("buscar_variacoes", padrao.buscar_variacoes)),
    )


def _validar_secao(dados: dict, nome: str, campos: tuple[str, ...]) -> dict:
    secao = dados.get(nome)
    if secao is None:
        raise ConfigError(f"campo ausente: seção [{nome}]")
    for campo in campos:
        if campo not in secao:
            raise ConfigError(f"campo ausente: {nome}.{campo}")
    return {campo: secao[campo] for campo in campos}


def _validar_item(item: dict, indice: int) -> Item:
    if "id" not in item:
        raise ConfigError(f"campo ausente: itens[{indice}].id")
    if "peso" not in item:
        raise ConfigError(f"campo ausente: itens[{indice}].peso")
    if item["peso"] <= 0:
        raise ConfigError(f"itens[{indice}].peso deve ser > 0 (item id={item['id']})")
    return Item(id=item["id"], peso=item["peso"])


# --- Regravação do bloco [[itens]] ---------------------------------------------------------
#
# Escritores do config.toml: `scripts/sincronizar_itens.py` e o painel web. Ambos só trocam
# os blocos `[[itens]]`; todo o resto do arquivo (credenciais, comentários, seções depois dos
# itens — em produção o `[rede]` fica DEPOIS deles) tem de sair igual. O serviço só lê o
# arquivo, e `gravar_atomico` garante que ele nunca veja uma versão pela metade.

_RE_CABECALHO = re.compile(r"^\s*\[")
_RE_CABECALHO_ITENS = re.compile(r"^\s*\[\[\s*itens\s*\]\]")
_RE_ID_COM_NOME = re.compile(r"(?m)^\s*id\s*=\s*(\d+)[ \t]*#[ \t]*(.+?)[ \t]*$")


def versao_config(texto: str) -> str:
    """Identificador da versão do texto do config (para detectar escrita concorrente)."""
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


def nomes_nos_comentarios(texto: str) -> dict[int, str]:
    """Nomes que `regenerar_bloco_itens` deixou como comentário ao lado de cada `id`."""
    return {int(item_id): nome for item_id, nome in _RE_ID_COM_NOME.findall(texto)}


def regenerar_bloco_itens(
    texto: str, itens: list[tuple[int, int]], nomes: dict[int, str] | None = None
) -> str:
    """Troca todos os blocos `[[itens]]` de `texto` por `itens` (id, peso), no lugar do
    primeiro; o resto do arquivo é preservado. Nome vira comentário ao lado do `id`."""
    nomes = nomes or {}
    blocos = "".join(
        f"[[itens]]\nid = {item_id}"
        + (f"  # {_nome_de_comentario(nomes[item_id])}" if nomes.get(item_id) else "")
        + f"\npeso = {peso}\n\n"
        for item_id, peso in itens
    ).rstrip("\n") + "\n"

    linhas = texto.splitlines(keepends=True)
    inicio_primeiro: int | None = None
    mantidas: list[str] = []
    i = 0
    while i < len(linhas):
        if not _RE_CABECALHO_ITENS.match(linhas[i]):
            mantidas.append(linhas[i])
            i += 1
            continue
        if inicio_primeiro is None:
            inicio_primeiro = len(mantidas)
        fim = i + 1
        while fim < len(linhas) and not _RE_CABECALHO.match(linhas[fim]):
            fim += 1
        if fim < len(linhas) and not _RE_CABECALHO_ITENS.match(linhas[fim]):
            # comentários/linhas em branco logo antes da próxima seção pertencem a ela
            while fim > i + 1 and _linha_solta(linhas[fim - 1]):
                fim -= 1
        i = fim

    if inicio_primeiro is None:
        return texto.rstrip("\n") + "\n\n" + blocos
    antes = "".join(mantidas[:inicio_primeiro]).rstrip("\n")
    depois = "".join(mantidas[inicio_primeiro:]).strip("\n")
    resultado = (antes + "\n\n" if antes else "") + blocos
    if depois:
        resultado += "\n" + depois + "\n"
    return resultado


def _linha_solta(linha: str) -> bool:
    conteudo = linha.strip()
    return not conteudo or conteudo.startswith("#")


def _nome_de_comentario(nome: str) -> str:
    return " ".join(str(nome).split())


def gravar_config(
    caminho: str | Path,
    texto_novo: str,
    *,
    alteravel: tuple[tuple[str, ...], ...] = (("itens",),),
) -> None:
    """Grava `texto_novo` atomicamente, só se ele for uma config válida e mudar apenas as
    chaves em `alteravel` (padrão: os `[[itens]]`) em relação ao arquivo atual — nunca deixa
    um config.toml quebrado no disco nem mexe em credenciais por engano."""
    caminho = Path(caminho)
    try:
        dados_novos = tomllib.loads(texto_novo)
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(f"o texto gerado não é TOML válido: {exc}") from exc
    _validar(dados_novos)
    if caminho.exists():
        dados_atuais = tomllib.loads(caminho.read_text(encoding="utf-8"))
        if _sem_chaves(dados_novos, alteravel) != _sem_chaves(dados_atuais, alteravel):
            raise ConfigError("a regravação alteraria partes protegidas do config; abortada")
    gravar_atomico(caminho, texto_novo)


def _sem_chaves(dados: dict, caminhos: tuple[tuple[str, ...], ...]) -> dict:
    copia = {k: (dict(v) if isinstance(v, dict) else v) for k, v in dados.items()}
    for caminho in caminhos:
        alvo = copia
        for chave in caminho[:-1]:
            alvo = alvo.get(chave) if isinstance(alvo.get(chave), dict) else {}
        alvo.pop(caminho[-1], None)
    return {k: v for k, v in copia.items() if v != {}}


_RE_CABECALHO_PAINEL = re.compile(r"^\s*\[\s*painel\s*\]\s*(#.*)?$")
_RE_SENHA_HASH = re.compile(r"^\s*senha_hash\s*=")


def definir_senha_painel(caminho: str | Path, senha_hash: str) -> None:
    """Grava `[painel].senha_hash` no config.toml (cria a seção se faltar), atomicamente e
    sob o mesmo lock do `[[itens]]`; nada além dessa chave pode mudar."""
    caminho = Path(caminho)
    linha_nova = f'senha_hash = "{senha_hash}"\n'
    with travado(caminho.with_name(caminho.name + ".lock")):
        linhas = caminho.read_text(encoding="utf-8").splitlines(keepends=True)
        inicio = next((i for i, linha in enumerate(linhas) if _RE_CABECALHO_PAINEL.match(linha)), None)
        if inicio is None:
            texto = "".join(linhas).rstrip("\n") + (
                "\n\n# Painel web dos pesos (ver README). Hash da senha: "
                "scripts/atalhos/definir_senha_painel.sh\n[painel]\n" + linha_nova
            )
        else:
            fim = inicio + 1
            while fim < len(linhas) and not _RE_CABECALHO.match(linhas[fim]):
                fim += 1
            existente = next(
                (i for i in range(inicio + 1, fim) if _RE_SENHA_HASH.match(linhas[i])), None
            )
            if existente is None:
                linhas.insert(inicio + 1, linha_nova)
            else:
                linhas[existente] = linha_nova
            texto = "".join(linhas)
        gravar_config(caminho, texto, alteravel=(("painel", "senha_hash"),))


def atualizar_itens(
    caminho: str | Path,
    itens: list[tuple[int, int]],
    nomes: dict[int, str] | None = None,
    versao_esperada: str | None = None,
) -> str:
    """Regrava os `[[itens]]` de `caminho` sob o lock `config.toml.lock` e devolve a versão
    nova. Com `versao_esperada`, lança `ConflitoConfig` se o arquivo mudou desde a leitura
    (cobre também quem não usa o lock, como uma edição no nano)."""
    caminho = Path(caminho)
    with travado(caminho.with_name(caminho.name + ".lock")):
        texto = caminho.read_text(encoding="utf-8")
        if versao_esperada is not None and versao_config(texto) != versao_esperada:
            raise ConflitoConfig("o config.toml mudou desde que foi lido; recarregue")
        todos_nomes = {**nomes_nos_comentarios(texto), **(nomes or {})}
        texto_novo = regenerar_bloco_itens(texto, itens, todos_nomes)
        if texto_novo != texto:
            gravar_config(caminho, texto_novo)
        return versao_config(texto_novo)
