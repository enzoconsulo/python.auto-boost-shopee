"""Entrypoint do serviço: carrega a config, configura o log e entra no loop de rodízio.

Uso: `python -m shopee_rodizio [caminho/para/config.toml]` (padrão: `config.toml` no
diretório atual). A cada volta do loop, executa um ciclo (`ciclo.py`) e dorme
`ciclo.intervalo_horas` antes da próxima.
"""

from __future__ import annotations

import argparse
import logging
import sys
import time

from .ciclo import executar_ciclo
from .cliente_shopee import ClienteShopee
from .config import Config, carregar_config
from .estado import carregar_estado
from .logging_config import configurar as configurar_logging

_logger = logging.getLogger("shopee_rodizio")

_CAMINHO_CONFIG_PADRAO = "config.toml"


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


def _cliente_de(config: Config) -> ClienteShopee:
    return ClienteShopee(
        partner_id=config.shopee.partner_id,
        partner_key=config.shopee.partner_key,
        shop_id=config.shopee.shop_id,
        access_token=config.shopee.access_token,
        refresh_token=config.shopee.refresh_token,
        expira_em=None,
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

    cliente = _cliente_de(config)
    estado = carregar_estado(config.caminhos.estado)

    iteracao = 0
    while max_iteracoes is None or iteracao < max_iteracoes:
        try:
            estado = executar_ciclo(cliente, config, estado)
        except Exception:
            _logger.exception("erro inesperado no ciclo — o loop continua")
        iteracao += 1
        time.sleep(config.ciclo.intervalo_horas * 3600)


def main(argv: list[str] | None = None) -> None:
    args = _analisar_args(sys.argv[1:] if argv is None else argv)
    executar_loop(args.config)


if __name__ == "__main__":
    main()
