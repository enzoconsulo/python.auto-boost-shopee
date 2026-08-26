"""Entrypoint do serviço: carrega a config, configura o log e entra no loop de rodízio.

Uso: `python -m shopee_rodizio [caminho/para/config.toml]` (padrão: `config.toml` no
diretório atual). A cada volta do loop, executa um ciclo (`ciclo.py`) e dorme
`ciclo.intervalo_horas` antes da próxima.

Persistência do token (RF-02): a renovação do `access_token` acontece dentro de
`cliente_shopee.py`, que muta o token in-place — `cliente.token` reflete o valor renovado
depois de um ciclo. Este módulo grava esse token num `token.json` (irmão do `estado.json`)
sempre que ele muda e o recarrega na subida, para que um restart do systemd
(`Restart=on-failure`) reconstrua o cliente com o `refresh_token` fresco, e não com o valor
possivelmente já invalidado que ainda está no `config.toml`.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path

from .ciclo import executar_ciclo
from .cliente_shopee import ClienteShopee, Token
from .config import Config, carregar_config
from .estado import carregar_estado
from .logging_config import configurar as configurar_logging

_logger = logging.getLogger("shopee_rodizio")

_CAMINHO_CONFIG_PADRAO = "config.toml"
_NOME_ARQUIVO_TOKEN = "token.json"


def _caminho_token(config: Config) -> Path:
    """Caminho do token persistido: irmão do `estado.json` (runtime, não config do usuário)."""
    return Path(config.caminhos.estado).with_name(_NOME_ARQUIVO_TOKEN)


def _carregar_token(caminho: Path) -> Token | None:
    """Lê o token renovado de `caminho`; `None` se o arquivo ainda não existe."""
    if not caminho.exists():
        return None
    dados = json.loads(caminho.read_text(encoding="utf-8"))
    expira_em = dados.get("expira_em")
    return Token(
        access_token=dados["access_token"],
        refresh_token=dados["refresh_token"],
        expira_em=datetime.fromisoformat(expira_em) if expira_em else None,
    )


def _persistir_token(caminho: Path, token: Token) -> None:
    """Grava `token` em `caminho` atomicamente (via arquivo temporário + os.replace)."""
    caminho.parent.mkdir(parents=True, exist_ok=True)
    dados = {
        "access_token": token.access_token,
        "refresh_token": token.refresh_token,
        "expira_em": token.expira_em.isoformat() if token.expira_em else None,
    }
    tmp = caminho.with_name(caminho.name + ".tmp")
    tmp.write_text(json.dumps(dados, indent=2, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, caminho)


def _analisar_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="python -m shopee_rodizio",
        description="Rodízio automático de impulsionamento de anúncios na Shopee.",
    )
    parser.add_argument(
        "config",
        nargs="?",
        default=_CAMINHO_CONFIG_PADRAO,
        help=f"caminho do arquivo de configuração TOML (padrão: {_CAMINHO_CONFIG_PADRAO})",
    )
    return parser.parse_args(argv)


def _cliente_de(config: Config, token: Token | None = None) -> ClienteShopee:
    """Constrói o cliente. Se houver um token persistido (renovação de execução anterior),
    usa-o em vez do token do `config.toml`, que pode já ter sido invalidado (RF-02)."""
    if token is None:
        token = Token(config.shopee.access_token, config.shopee.refresh_token, expira_em=None)
    return ClienteShopee(
        partner_id=config.shopee.partner_id,
        partner_key=config.shopee.partner_key,
        shop_id=config.shopee.shop_id,
        access_token=token.access_token,
        refresh_token=token.refresh_token,
        expira_em=token.expira_em,
        proxy_https=config.rede.proxy_https,
    )


def executar_loop(caminho_config: str, *, max_iteracoes: int | None = None) -> None:
    """Carrega a config, configura o log e roda o loop de rodízio.

    `max_iteracoes` limita o número de voltas (usado só em teste); em produção o loop
    roda para sempre. Erro inesperado dentro de um ciclo é logado e o loop segue para a
    próxima volta (RF-06: nenhum erro de ciclo pode terminar o processo).
    """
    config = carregar_config(caminho_config)
    configurar_logging(config.caminhos.log)
    _logger.info("shopee-rodizio iniciado (config: %s)", caminho_config)

    caminho_token = _caminho_token(config)
    cliente = _cliente_de(config, _carregar_token(caminho_token))
    # `token_anterior` reflete o token com que o cliente REALMENTE subiu (persistido ou,
    # na falta dele, o do config com `expira_em=None`) — não o resultado cru de
    # `_carregar_token`. Assim a primeira subida sem `token.json` não grava um token.json
    # redundante ao fim do primeiro ciclo: só gravamos quando há renovação de fato.
    token_anterior = cliente.token
    estado = carregar_estado(config.caminhos.estado)

    iteracao = 0
    while max_iteracoes is None or iteracao < max_iteracoes:
        try:
            estado = executar_ciclo(cliente, config, estado)
            if cliente.token != token_anterior:
                # o cliente renovou o access_token neste ciclo (RF-02): grava o token novo
                # para não perdê-lo num restart.
                _persistir_token(caminho_token, cliente.token)
                token_anterior = cliente.token
        except Exception:
            _logger.exception("erro inesperado no ciclo — o loop continua")
        iteracao += 1
        time.sleep(config.ciclo.intervalo_horas * 3600)


def main(argv: list[str] | None = None) -> None:
    args = _analisar_args(sys.argv[1:] if argv is None else argv)
    executar_loop(args.config)


if __name__ == "__main__":
    main()
