"""Empresta o access_token da loja para outro app sem criar uma segunda cadeia de token.

O serviço 24/7 do BTT Pi é o único dono da autorização da loja: renova o token sozinho e
grava em `token.json`. Outro app que chama a API da mesma loja — o analista_dados_shopee,
que roda de vez em quando no PC — executa este script por SSH e recebe um access_token
válido por pelo menos `--minutos`. Se faltar menos que isso, o script renova antes, sob o
mesmo lock do serviço (ver `armazem_token.py`). O refresh_token nunca sai do Pi.

Uso (no Pi, na raiz do projeto):
    .venv/bin/python scripts/emprestar_token.py config.toml [--minutos 60]

Saída: uma linha JSON no stdout — {"access_token", "expira_em", "shop_id", "partner_id"}.
Erro: mensagem no stderr e código de saída 1.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import timedelta

from shopee_rodizio.armazem_token import cliente_da_config
from shopee_rodizio.config import ConfigError, carregar_config

MINUTOS_PADRAO = 60
# o access_token da Shopee dura 4h: pedir perto disso forçaria renovar a cada empréstimo
MINUTOS_MAXIMO = 180


def _analisar_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="emprestar_token.py",
        description=(
            "Devolve (JSON no stdout) um access_token válido da loja, renovando antes, sob o "
            "lock do serviço, se faltar menos que --minutos."
        ),
    )
    parser.add_argument("config", help="caminho do config.toml do serviço")
    parser.add_argument(
        "--minutos",
        type=int,
        default=MINUTOS_PADRAO,
        help=(
            f"validade mínima do token devolvido (padrão: {MINUTOS_PADRAO}, "
            f"máximo: {MINUTOS_MAXIMO})"
        ),
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _analisar_args(sys.argv[1:] if argv is None else argv)
    if not 1 <= args.minutos <= MINUTOS_MAXIMO:
        print(f"--minutos precisa estar entre 1 e {MINUTOS_MAXIMO}", file=sys.stderr)
        return 1

    try:
        config = carregar_config(args.config)
    except (ConfigError, OSError) as exc:
        print(f"não foi possível carregar '{args.config}': {exc}", file=sys.stderr)
        return 1

    cliente = cliente_da_config(config)
    resultado = cliente.garantir_token(margem=timedelta(minutes=args.minutos))
    if not resultado.sucesso:
        print(f"não consegui um token válido: {resultado.erro}", file=sys.stderr)
        return 1

    token = cliente.token
    print(
        json.dumps(
            {
                "access_token": token.access_token,
                "expira_em": token.expira_em.isoformat(),
                "shop_id": config.shopee.shop_id,
                "partner_id": config.shopee.partner_id,
            }
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
