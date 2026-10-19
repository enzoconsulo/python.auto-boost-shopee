"""Define (ou troca) a senha do painel web: grava só o hash PBKDF2 em `[painel].senha_hash`
do `config.toml` — a senha em si não vai para disco nem para log.

Uso:
    uv run python scripts/definir_senha_painel.py config.toml

Pede a senha duas vezes no terminal (sem eco). O painel lê o config a cada requisição, então
a senha nova vale na hora, sem reiniciar.
"""

from __future__ import annotations

import argparse
import getpass
import sys

from shopee_rodizio.config import ConfigError, definir_senha_painel
from shopee_rodizio.painel import gerar_hash_senha

TAMANHO_MINIMO = 8


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="definir_senha_painel.py",
        description="Grava o hash da senha do painel web em [painel].senha_hash.",
    )
    parser.add_argument("config", help="caminho do config.toml")
    args = parser.parse_args(sys.argv[1:] if argv is None else argv)

    senha = getpass.getpass("senha nova do painel: ")
    if len(senha) < TAMANHO_MINIMO:
        print(f"use pelo menos {TAMANHO_MINIMO} caracteres.", file=sys.stderr)
        return 1
    if getpass.getpass("repita a senha: ") != senha:
        print("as senhas não conferem; nada foi alterado.", file=sys.stderr)
        return 1

    try:
        definir_senha_painel(args.config, gerar_hash_senha(senha))
    except (ConfigError, OSError) as exc:
        print(f"config.toml NÃO foi alterado: {exc}", file=sys.stderr)
        return 1
    print("senha do painel definida (só o hash foi gravado no config.toml).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
