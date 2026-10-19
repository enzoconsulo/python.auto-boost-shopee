"""Puxa a lista real de anúncios ativos da loja e gera o bloco `[[itens]]` do
`config.toml` sozinho — sem digitar item por item.

A busca do catálogo (`get_item_list` para os IDs ativos, `get_item_base_info` para os
nomes) vive em `shopee_rodizio.catalogo`, compartilhada com o painel web. O nome de cada
item entra como comentário ao lado do `id` no `config.toml`, só para leitura humana — não
afeta o funcionamento do rodízio.

Uso:
    uv run python scripts/sincronizar_itens.py config.toml [--peso-padrao N]

Pesos de itens que já existem em `[[itens]]` são preservados; itens novos entram com
`--peso-padrao` (default 1). Itens que estavam em `[[itens]]` mas não estão mais ativos
na loja são removidos da rotação (impulsionar um anúncio fora do ar só falharia todo
ciclo) — a lista de removidos é impressa, nada é apagado silenciosamente.
"""

from __future__ import annotations

import argparse
import sys

from shopee_rodizio.armazem_token import cliente_da_config
from shopee_rodizio.catalogo import ErroCatalogo, buscar_detalhes, buscar_item_ids_ativos
from shopee_rodizio.config import ConfigError, atualizar_itens, carregar_config

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


def main(argv: list[str] | None = None) -> int:
    args = _analisar_args(sys.argv[1:] if argv is None else argv)

    try:
        config = carregar_config(args.config)
    except (ConfigError, OSError) as exc:
        print(f"não foi possível carregar '{args.config}': {exc}", file=sys.stderr)
        return 1

    # token.json compartilhado com o serviço: renovar com o refresh_token do config.toml
    # (já consumido pelo serviço) falharia ou quebraria a cadeia dele
    cliente = cliente_da_config(config)
    print("buscando anúncios ativos na Shopee...")
    try:
        ids_ativos = buscar_item_ids_ativos(cliente)
    except ErroCatalogo as exc:
        print(f"falha ao listar itens: {exc}", file=sys.stderr)
        return 1

    if not ids_ativos:
        print("nenhum anúncio ativo (status NORMAL) encontrado nesta loja.", file=sys.stderr)
        return 1

    print("buscando nomes dos itens...")
    detalhes = buscar_detalhes(cliente, ids_ativos)
    nomes = {item_id: item.nome for item_id, item in detalhes.items() if item.nome}

    pesos_atuais = {item.id: item.peso for item in config.itens}
    itens_novos = [
        (item_id, pesos_atuais.get(item_id, args.peso_padrao)) for item_id in ids_ativos
    ]
    removidos = [item_id for item_id in pesos_atuais if item_id not in ids_ativos]

    # escrita atômica, sob o lock do config.toml (o painel web também grava nele) e só do
    # bloco [[itens]] — o resto do arquivo, inclusive seções depois dos itens, fica intacto
    try:
        atualizar_itens(args.config, itens_novos, nomes)
    except (ConfigError, OSError) as exc:
        print(f"config.toml NÃO foi alterado: {exc}", file=sys.stderr)
        return 1

    print(f"{len(itens_novos)} item(ns) gravado(s) em {args.config}.")
    if removidos:
        print(f"removido(s) da rotação por não estarem mais ativos na loja: {removidos}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
