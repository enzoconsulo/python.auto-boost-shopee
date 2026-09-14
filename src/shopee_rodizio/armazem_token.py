"""Token da Shopee persistido em disco e compartilhado entre processos.

O refresh_token da Shopee é de uso único, e mais de um processo usa a mesma loja: o serviço
24/7, os scripts (`sincronizar_itens.py`, `smoke_test.py`, `gerar_token.py`) e o
`scripts/emprestar_token.py`, que o analista_dados_shopee do PC chama por SSH. Se cada um
renovasse com a própria cópia em memória, o primeiro a renovar invalidaria a cópia dos
outros e a cadeia inteira morreria. Por isso `token.json` é a única fonte da verdade:

- antes de usar o token, o cliente relê o arquivo (outro processo pode ter renovado);
- a renovação acontece sob lock exclusivo de arquivo (`token.json.lock`), relendo o
  arquivo já dentro do lock e gravando o token novo antes de soltá-lo.
"""

from __future__ import annotations

import contextlib
import json
import os
from collections.abc import Iterator
from datetime import datetime
from pathlib import Path

from .cliente_shopee import ClienteShopee, Token
from .config import Config

NOME_ARQUIVO_TOKEN = "token.json"

if os.name == "nt":  # desenvolvimento e testes no Windows

    import msvcrt

    def _travar(handle) -> None:
        handle.seek(0)
        msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1)

    def _destravar(handle) -> None:
        handle.seek(0)
        msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)

else:

    import fcntl

    def _travar(handle) -> None:
        fcntl.flock(handle, fcntl.LOCK_EX)

    def _destravar(handle) -> None:
        fcntl.flock(handle, fcntl.LOCK_UN)


class ArmazemToken:
    def __init__(self, caminho: str | Path) -> None:
        self.caminho = Path(caminho)
        self._caminho_lock = self.caminho.with_name(self.caminho.name + ".lock")

    def carregar(self) -> Token | None:
        """Lê o token gravado; `None` se o arquivo ainda não existe."""
        if not self.caminho.exists():
            return None
        dados = json.loads(self.caminho.read_text(encoding="utf-8"))
        expira_em = dados.get("expira_em")
        return Token(
            access_token=dados["access_token"],
            refresh_token=dados["refresh_token"],
            expira_em=datetime.fromisoformat(expira_em) if expira_em else None,
        )

    def gravar(self, token: Token) -> None:
        """Grava `token` atomicamente (arquivo temporário + `os.replace`)."""
        self.caminho.parent.mkdir(parents=True, exist_ok=True)
        dados = {
            "access_token": token.access_token,
            "refresh_token": token.refresh_token,
            "expira_em": token.expira_em.isoformat() if token.expira_em else None,
        }
        tmp = self.caminho.with_name(self.caminho.name + ".tmp")
        tmp.write_text(json.dumps(dados, indent=2, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, self.caminho)

    @contextlib.contextmanager
    def travado(self) -> Iterator[None]:
        """Lock exclusivo entre processos para a janela reler → renovar → gravar."""
        self._caminho_lock.parent.mkdir(parents=True, exist_ok=True)
        with open(self._caminho_lock, "a+") as handle:
            _travar(handle)
            try:
                yield
            finally:
                _destravar(handle)


def caminho_token(config: Config) -> Path:
    """`token.json` fica ao lado do `estado.json` (runtime, não config do usuário)."""
    return Path(config.caminhos.estado).with_name(NOME_ARQUIVO_TOKEN)


def cliente_da_config(config: Config) -> ClienteShopee:
    """Cliente ligado ao `token.json` compartilhado. Sem `token.json` ainda, parte do token
    do `config.toml`, e a primeira renovação cria o arquivo."""
    armazem = ArmazemToken(caminho_token(config))
    token = armazem.carregar() or Token(
        config.shopee.access_token, config.shopee.refresh_token, expira_em=None
    )
    return ClienteShopee(
        partner_id=config.shopee.partner_id,
        partner_key=config.shopee.partner_key,
        shop_id=config.shopee.shop_id,
        access_token=token.access_token,
        refresh_token=token.refresh_token,
        expira_em=token.expira_em,
        proxy_https=config.rede.proxy_https,
        armazem=armazem,
    )
