"""Primitivas de disco compartilhadas: escrita atômica durável e lock entre processos.

O serviço roda num SBC com cartão SD (corrupção de arquivo já observada em produção) e
mais de um processo escreve nos mesmos arquivos (serviço, painel, scripts). Por isso:

- `gravar_atomico` escreve num temporário de nome ÚNICO no mesmo diretório (dois
  escritores simultâneos nunca disputam o mesmo `.tmp`), faz `fsync`, preserva o modo do
  arquivo original e só então troca via `os.replace` — quem lê vê o arquivo antigo inteiro
  ou o novo inteiro, nunca pela metade, nem depois de queda de energia;
- `travado` é um lock exclusivo de arquivo para janelas ler → modificar → gravar.
"""

from __future__ import annotations

import contextlib
import os
import stat
import tempfile
from collections.abc import Iterator
from pathlib import Path

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


def gravar_atomico(caminho: str | Path, texto: str) -> None:
    """Grava `texto` (UTF-8) em `caminho` atomicamente e de forma durável."""
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    fd, nome_tmp = tempfile.mkstemp(dir=caminho.parent, prefix=f".{caminho.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            handle.write(texto)
            handle.flush()
            os.fsync(handle.fileno())
        if caminho.exists():
            # mkstemp cria com 0600; manter o modo do original evita mudar quem pode ler o
            # arquivo (ex.: o grupo do usuário do serviço) a cada gravação
            os.chmod(nome_tmp, stat.S_IMODE(caminho.stat().st_mode))
        os.replace(nome_tmp, caminho)
    except BaseException:
        with contextlib.suppress(OSError):
            os.unlink(nome_tmp)
        raise
    _fsync_diretorio(caminho.parent)


def _fsync_diretorio(diretorio: Path) -> None:
    """Persiste a entrada de diretório do `os.replace` (no Windows não há como; ignora)."""
    if os.name == "nt":
        return
    fd = os.open(diretorio, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


@contextlib.contextmanager
def travado(caminho_lock: str | Path) -> Iterator[None]:
    """Lock exclusivo entre processos, mantido enquanto o bloco `with` executa."""
    caminho_lock = Path(caminho_lock)
    caminho_lock.parent.mkdir(parents=True, exist_ok=True)
    with open(caminho_lock, "a+") as handle:
        _travar(handle)
        try:
            yield
        finally:
            _destravar(handle)
