"""Smoke-test manual contra a API real da Shopee.

Script standalone para o USUÁRIO rodar com credenciais reais, fora do CI da fábrica, para
confirmar (ou revelar que precisa ajustar) `ciclo.endpoint_boost` e os nomes de parâmetro
de `boost.py` antes do primeiro deploy contínuo — a documentação pública da Shopee Open
Platform não confirma esse endpoint sem login (ver `_gestao/DECISOES.md`, 2026-08-24).

Faz UMA única chamada de impulsionamento (o item é consumido do limite da conta real),
então não roda em teste automatizado nem repete a chamada.

Uso:
    uv run python scripts/smoke_test.py caminho/para/config.toml [--item-id ID]
"""

from __future__ import annotations

import argparse
import sys

from shopee_rodizio.boost import impulsionar
from shopee_rodizio.cliente_shopee import ClienteShopee
from shopee_rodizio.config import Config, ConfigError, carregar_config


def _analisar_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="smoke_test.py",
        description=(
            "Tenta impulsionar UM item de teste contra a API real da Shopee, para "
            "confirmar o endpoint e os parâmetros de boost antes do primeiro deploy."
        ),
    )
    parser.add_argument("config", help="caminho do config.toml com credenciais reais")
    parser.add_argument(
        "--item-id",
        type=int,
        default=None,
        help="item a impulsionar (padrão: o primeiro em [[itens]] do config.toml)",
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


def main(argv: list[str] | None = None) -> int:
    args = _analisar_args(sys.argv[1:] if argv is None else argv)

    try:
        config = carregar_config(args.config)
    except (ConfigError, OSError) as exc:
        print(f"não foi possível carregar '{args.config}': {exc}", file=sys.stderr)
        return 1

    item_id = args.item_id if args.item_id is not None else config.itens[0].id
    cliente = _cliente_de(config)

    print(f"endpoint: {config.ciclo.endpoint_boost}")
    print(f"shop_id: {config.shopee.shop_id}")
    print(f"item_id: {item_id}")
    print("chamando a API da Shopee...")

    resultado = impulsionar(cliente, config, item_id)

    print()
    if resultado.sucesso:
        print(f"SUCESSO: {resultado.mensagem}")
    else:
        print(f"FALHA: {resultado.mensagem}")
        print(
            "Se a mensagem indicar path/parâmetro inválido, ajuste "
            "`ciclo.endpoint_boost` no config.toml e os nomes de parâmetro em "
            "`boost.py`, depois rode este script de novo."
        )

    if cliente.token.access_token != config.shopee.access_token:
        print()
        print(
            "aviso: o access_token foi renovado durante esta chamada — atualize "
            "config.toml (ou deixe o serviço persistir em token.json na próxima subida)."
        )

    return 0 if resultado.sucesso else 1


if __name__ == "__main__":
    sys.exit(main())
