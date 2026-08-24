"""Persistência do histórico de impulsionamentos em JSON, com escrita atômica."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path


@dataclass(frozen=True)
class RegistroBoost:
    item_id: int
    timestamp: str
    sucesso: bool
    mensagem: str


@dataclass(frozen=True)
class Estado:
    caminho: Path
    historico: list[RegistroBoost] = field(default_factory=list)


def carregar_estado(caminho: str | Path) -> Estado:
    """Lê o histórico em `caminho`. Arquivo ausente é tratado como histórico vazio."""
    caminho = Path(caminho)
    if not caminho.exists():
        return Estado(caminho=caminho, historico=[])
    dados = json.loads(caminho.read_text(encoding="utf-8"))
    historico = [RegistroBoost(**registro) for registro in dados.get("historico", [])]
    return Estado(caminho=caminho, historico=historico)


def registrar_boost(estado: Estado, item_id: int, sucesso: bool, mensagem: str) -> Estado:
    """Acrescenta um registro ao histórico e grava o resultado em disco atomicamente."""
    registro = RegistroBoost(
        item_id=item_id,
        timestamp=datetime.now(UTC).isoformat(),
        sucesso=sucesso,
        mensagem=mensagem,
    )
    novo_estado = Estado(caminho=estado.caminho, historico=[*estado.historico, registro])
    _gravar(novo_estado)
    return novo_estado


def historico_recente(estado: Estado, item_id: int) -> list[RegistroBoost]:
    """Devolve, em ordem cronológica, os registros do histórico para `item_id`."""
    return [registro for registro in estado.historico if registro.item_id == item_id]


def _gravar(estado: Estado) -> None:
    caminho = estado.caminho
    caminho.parent.mkdir(parents=True, exist_ok=True)
    dados = {"historico": [asdict(registro) for registro in estado.historico]}
    tmp = caminho.with_name(caminho.name + ".tmp")
    tmp.write_text(json.dumps(dados, indent=2, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, caminho)
