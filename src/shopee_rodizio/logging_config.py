"""Configuração do logging do projeto: arquivo com rotação por tamanho (stdlib)."""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

_FORMATO = "%(asctime)s %(levelname)s %(message)s"
_FORMATO_DATA = "%Y-%m-%d %H:%M:%S"

_MAX_BYTES_PADRAO = 2 * 1024 * 1024  # 2 MiB — SBC com pouco espaço em disco
_BACKUP_COUNT_PADRAO = 3

_NOME_LOGGER = "shopee_rodizio"


def configurar(
    caminho_log: str,
    max_bytes: int = _MAX_BYTES_PADRAO,
    backup_count: int = _BACKUP_COUNT_PADRAO,
) -> None:
    """Configura o logger `shopee_rodizio` para escrever em `caminho_log` com rotação.

    Idempotente: chamadas repetidas não duplicam handlers. Cria o diretório pai de
    `caminho_log` se ainda não existir.
    """
    caminho = Path(caminho_log)
    caminho.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(_NOME_LOGGER)
    logger.setLevel(logging.INFO)

    for handler in list(logger.handlers):
        handler.close()
        logger.removeHandler(handler)

    handler = RotatingFileHandler(
        caminho, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8"
    )
    handler.setFormatter(logging.Formatter(_FORMATO, datefmt=_FORMATO_DATA))
    logger.addHandler(handler)
