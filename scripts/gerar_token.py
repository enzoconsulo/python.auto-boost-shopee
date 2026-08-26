"""Troca o código de autorização da Shopee Open Platform pelo par definitivo de
`access_token`/`refresh_token`, descobre o `shop_id` e grava os três direto no
config.toml.

Esse é o único passo que a Shopee não deixa automatizar: exige o dono da loja
logado no navegador clicando em "Autorizar" — é o mecanismo de consentimento do
OAuth, não uma limitação deste script. Depois de rodado uma vez, o serviço nunca
mais precisa de intervenção manual: `cliente_shopee.py` renova o access_token
sozinho a cada ciclo e persiste o refresh_token rotacionado em `token.json`
(ver `__main__.py`).

Uso:
    uv run python scripts/gerar_token.py caminho/para/config.toml [--redirect URL]

`config.toml` precisa ter `partner_id`/`partner_key` já preenchidos antes de rodar
(`shop_id`/`access_token`/`refresh_token` podem ficar com os valores de exemplo —
este script os sobrescreve). `--redirect` deve bater com a URL cadastrada no app
na Open Platform (padrão: https://google.com, a mesma usada em analista_dados_shopee).
"""

from __future__ import annotations

import argparse
import re
import sys
import time
from pathlib import Path

import requests

from shopee_rodizio.cliente_shopee import BASE_URL, assinatura, base_publica
from shopee_rodizio.config import ConfigError, carregar_config

PATH_AUTORIZACAO = "/api/v2/shop/auth_partner"
PATH_TROCA_CODIGO = "/api/v2/auth/token/get"
REDIRECT_PADRAO = "https://google.com"


def _analisar_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="gerar_token.py",
        description=(
            "Gera o link de autorização da Shopee, troca o código pelo access_token/"
            "refresh_token definitivos e grava tudo direto no config.toml."
        ),
    )
    parser.add_argument("config", help="caminho do config.toml (partner_id/partner_key já preenchidos)")
    parser.add_argument(
        "--redirect",
        default=REDIRECT_PADRAO,
        help=f"URL de redirect cadastrada no app da Open Platform (padrão: {REDIRECT_PADRAO})",
    )
    return parser.parse_args(argv)


def _link_autorizacao(partner_id: int, partner_key: str, redirect: str) -> str:
    timestamp = int(time.time())
    base = base_publica(partner_id, PATH_AUTORIZACAO, timestamp)
    sign = assinatura(partner_key, base)
    return (
        f"{BASE_URL}{PATH_AUTORIZACAO}?partner_id={partner_id}&timestamp={timestamp}"
        f"&sign={sign}&redirect={redirect}"
    )


def _extrair_code_e_shop_id(url_colada: str) -> tuple[str, int]:
    code = re.search(r"[?&]code=([^&]+)", url_colada)
    shop_id = re.search(r"[?&]shop_id=([^&]+)", url_colada)
    if not code or not shop_id:
        raise ValueError("não encontrei 'code' e 'shop_id' na URL colada")
    return code.group(1), int(shop_id.group(1))


def _trocar_code_por_tokens(
    partner_id: int, partner_key: str, code: str, shop_id: int, proxy_https: str | None = None
) -> dict:
    timestamp = int(time.time())
    base = base_publica(partner_id, PATH_TROCA_CODIGO, timestamp)
    sign = assinatura(partner_key, base)
    url = f"{BASE_URL}{PATH_TROCA_CODIGO}?partner_id={partner_id}&timestamp={timestamp}&sign={sign}"
    payload = {"code": code, "shop_id": shop_id, "partner_id": partner_id}
    proxies = {"http": proxy_https, "https": proxy_https} if proxy_https else None
    resposta = requests.post(url, json=payload, timeout=30, proxies=proxies)
    resposta.raise_for_status()
    return resposta.json()


def _gravar_no_config(caminho: str, shop_id: int, access_token: str, refresh_token: str) -> None:
    arquivo = Path(caminho)
    texto = arquivo.read_text(encoding="utf-8")
    texto = re.sub(r"(?m)^shop_id\s*=.*$", f"shop_id = {shop_id}", texto)
    texto = re.sub(r"(?m)^access_token\s*=.*$", f'access_token = "{access_token}"', texto)
    texto = re.sub(r"(?m)^refresh_token\s*=.*$", f'refresh_token = "{refresh_token}"', texto)
    arquivo.write_text(texto, encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    args = _analisar_args(sys.argv[1:] if argv is None else argv)

    try:
        config = carregar_config(args.config)
    except (ConfigError, OSError) as exc:
        print(f"não foi possível carregar '{args.config}': {exc}", file=sys.stderr)
        return 1

    if not config.shopee.partner_id or not config.shopee.partner_key:
        print(
            "preencha partner_id e partner_key em config.toml antes de rodar este script",
            file=sys.stderr,
        )
        return 1

    link = _link_autorizacao(config.shopee.partner_id, config.shopee.partner_key, args.redirect)
    print("1. Abra este link e faça login como a conta VENDEDORA da loja:")
    print(link)
    print()
    print(
        f"2. Depois de clicar em 'Autorizar', você cai em {args.redirect} com "
        "'code' e 'shop_id' colados na URL — copie a barra de endereço inteira."
    )

    url_colada = input("\nCole a URL redirecionada aqui: ").strip()

    try:
        code, shop_id = _extrair_code_e_shop_id(url_colada)
    except ValueError as exc:
        print(f"erro: {exc}", file=sys.stderr)
        return 1

    print(f"\nshop_id encontrado: {shop_id}")
    print("trocando o código pelos tokens definitivos...")

    try:
        dados = _trocar_code_por_tokens(
            config.shopee.partner_id,
            config.shopee.partner_key,
            code,
            shop_id,
            config.rede.proxy_https,
        )
    except requests.exceptions.RequestException as exc:
        print(f"falha de rede ao chamar a Shopee: {exc}", file=sys.stderr)
        return 1

    if dados.get("error"):
        print(f"a Shopee recusou: {dados.get('error')}: {dados.get('message')}", file=sys.stderr)
        return 1

    _gravar_no_config(args.config, shop_id, dados["access_token"], dados["refresh_token"])
    print(f"\n{args.config} atualizado com shop_id, access_token e refresh_token.")
    print("a partir de agora o serviço renova o token sozinho — não precisa rodar este script de novo.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
