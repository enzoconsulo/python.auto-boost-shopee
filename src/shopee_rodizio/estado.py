"""Persistência do histórico de impulsionamentos em JSON, com escrita atômica."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from .arquivo import gravar_atomico


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


def ultimo_ciclo_em(estado: Estado, *, so_sucesso: bool = False) -> datetime | None:
    """Momento do registro mais recente do histórico (só dos com sucesso, se `so_sucesso`);
    `None` se não houver.

    Registro com timestamp ilegível é ignorado — um `estado.json` editado à mão não pode
    impedir o serviço de subir.
    """
    momentos = []
    for registro in estado.historico:
        if so_sucesso and not registro.sucesso:
            continue
        try:
            momento = datetime.fromisoformat(registro.timestamp)
        except (TypeError, ValueError):
            continue
        momentos.append(momento if momento.tzinfo else momento.replace(tzinfo=UTC))
    return max(momentos, default=None)


def ancora_do_intervalo(estado: Estado) -> datetime | None:
    """De onde se conta o intervalo até o próximo ciclo: o último boost COM SUCESSO, que é o
    que ocupa slot na Shopee. Tentativa que falhou (ex.: "reached shop's bump slot limit")
    não ocupa nada e não pode empurrar o próximo ciclo — em 19/10/2026 as falhas das 18:57
    adiaram o ciclo para 22:57 e deixaram a loja sem boost das 20:36 às 22:57. Sem nenhum
    sucesso no histórico, vale o último registro (evita martelar a API num loop de falha).
    """
    return ultimo_ciclo_em(estado, so_sucesso=True) or ultimo_ciclo_em(estado)


def segundos_ate_proximo_ciclo(
    estado: Estado, intervalo_horas: float, agora: datetime | None = None
) -> float:
    """Quanto falta, a partir de `agora`, para completar `intervalo_horas` desde a
    `ancora_do_intervalo` (último boost com sucesso). Sem histórico, 0 (roda já).

    O CB1 não tem RTC: no boot, antes do NTP, o relógio volta para o horário salvo pelo
    fake-hwclock (no passado). Se QUALQUER registro parecer estar no futuro, espera o
    intervalo cheio — na dúvida, errar para o lado de não queimar slots de boost.
    """
    intervalo = intervalo_horas * 3600
    agora = agora or datetime.now(UTC)
    ultimo_registro = ultimo_ciclo_em(estado)
    if ultimo_registro is None:
        return 0.0
    if ultimo_registro > agora:
        return float(intervalo)
    decorrido = (agora - ancora_do_intervalo(estado)).total_seconds()
    return max(0.0, intervalo - decorrido)


def _gravar(estado: Estado) -> None:
    dados = {"historico": [asdict(registro) for registro in estado.historico]}
    gravar_atomico(estado.caminho, json.dumps(dados, indent=2, ensure_ascii=False))
