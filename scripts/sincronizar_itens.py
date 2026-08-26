"""Puxa a lista real de anúncios ativos da loja e gera o bloco `[[itens]]` do
`config.toml` sozinho — sem digitar item por item.

Endpoint (`/api/v2/product/get_item_list`, GET, paginado por `offset`/`page_size`,
filtrado por `item_status`) confirmado contra conta real via
`analista_dados_shopee/workers/sync_catalogo.py` (implementação irmã do mesmo usuário,
já validada em produção).

Uso:
    uv run python scripts/sincronizar_itens.py config.toml [--peso-padrao N]

Pesos de itens que já existem em `[[itens]]` são preservados; itens novos entram com
`--peso-padrao` (default 1). Itens que estavam em `[[itens]]` mas não estão mais ativos
na loja são removidos da rotação (impulsionar um anúncio fora do ar só falharia todo
ciclo) — a lista de removidos é impressa, nada é apagado silenciosamente.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from shopee_rodizio.cliente_shopee import ClienteShopee
from shopee_rodizio.config import Config, ConfigError, carregar_config

PATH_LISTA_ITENS = "/api/v2/product/get_item_list"
PAGE_SIZE = 50
PESO_PADRAO = 1


def _analisar_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="sincronizar_itens.py",
        description=(
            "Busca os anúncios ativos da loja na Shopee e regenera o [[itens]] do "
            "config.toml automaticamente, preservando pesos já definidos."
        ),
    )
    parser.add_argument("config", help="caminho do config.toml (já com tokens válidos)")
    parser.add_argument(
        "--peso-padrao",
        type=int,
        default=PESO_PADRAO,
        help=f"peso atribuído a itens novos, sem peso definido ainda (padrão: {PESO_PADRAO})",
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


def _buscar_item_ids_ativos(cliente: ClienteShopee) -> list[int]:
    """Pagina `get_item_list` até o fim. Lança RuntimeError se alguma página falhar —
    uma listagem parcial não pode virar `[[itens]]` (removeria itens ativos por engano)."""
    item_ids: list[int] = []
    offset = 0
    while True:
        resultado = cliente.chamar(
            PATH_LISTA_ITENS,
            {"offset": offset, "page_size": PAGE_SIZE, "item_status": "NORMAL"},
            metodo="GET",
        )
        if not resultado.sucesso:
            raise RuntimeError(resultado.erro or "erro desconhecido ao listar itens")

        pagina = resultado.dados.get("response", {})
        item_ids.extend(item["item_id"] for item in pagina.get("item", []))
        if not pagina.get("has_next_page"):
            return item_ids
        offset += PAGE_SIZE


def _regenerar_bloco_itens(texto: str, itens: list[tuple[int, int]]) -> str:
    blocos = "".join(f"[[itens]]\nid = {item_id}\npeso = {peso}\n\n" for item_id, peso in itens)
    marcador = re.search(r"(?m)^\[\[itens\]\]", texto)
    inicio = marcador.start() if marcador else len(texto.rstrip("\n")) + 2
    return texto[:inicio].rstrip("\n") + "\n\n" + blocos.rstrip("\n") + "\n"


def main(argv: list[str] | None = None) -> int:
    args = _analisar_args(sys.argv[1:] if argv is None else argv)

    try:
        config = carregar_config(args.config)
    except (ConfigError, OSError) as exc:
        print(f"não foi possível carregar '{args.config}': {exc}", file=sys.stderr)
        return 1

    cliente = _cliente_de(config)
    print("buscando anúncios ativos na Shopee...")
    try:
        ids_ativos = _buscar_item_ids_ativos(cliente)
    except RuntimeError as exc:
        print(f"falha ao listar itens: {exc}", file=sys.stderr)
        return 1

    if not ids_ativos:
        print("nenhum anúncio ativo (status NORMAL) encontrado nesta loja.", file=sys.stderr)
        return 1

    pesos_atuais = {item.id: item.peso for item in config.itens}
    itens_novos = [
        (item_id, pesos_atuais.get(item_id, args.peso_padrao)) for item_id in ids_ativos
    ]
    removidos = [item_id for item_id in pesos_atuais if item_id not in ids_ativos]

    texto_atualizado = _regenerar_bloco_itens(Path(args.config).read_text(encoding="utf-8"), itens_novos)
    Path(args.config).write_text(texto_atualizado, encoding="utf-8")

    print(f"{len(itens_novos)} item(ns) gravado(s) em {args.config}.")
    if removidos:
        print(f"removido(s) da rotação por não estarem mais ativos na loja: {removidos}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
