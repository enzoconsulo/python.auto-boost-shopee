"""Leitura do histórico (`estado.json`) para as abas "No ar agora" e "Relatório" do painel.

Só agrega — não escreve nada e não chama a Shopee. Funções puras sobre `Estado`, com
`agora` injetável para teste. Custo: uma passada no histórico (alguns milhares de
registros), feita só quando a aba é aberta no navegador.

Duas convenções, ambas sem confirmação na documentação pública da Shopee:
- um boost dura `DURACAO_BOOST` (4 h, o comportamento observado do "Impulsionar" do
  vendedor) — é isso que define o que está "no ar agora";
- registros separados por menos de `JANELA_CICLO` pertencem ao mesmo ciclo (o ciclo
  impulsiona os itens em sequência, segundos um do outro).
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta, timezone

from .estado import Estado

DURACAO_BOOST = timedelta(hours=4)
JANELA_CICLO = timedelta(minutes=10)
# Brasil sem horário de verão desde 2019: os dias do relatório são em UTC-3 fixo, sem
# depender de tzdata instalado no SBC
FUSO_RELATORIO = timezone(timedelta(hours=-3))
MAX_ERROS = 5


@dataclass(frozen=True)
class _Registro:
    item_id: int
    momento: datetime
    sucesso: bool
    mensagem: str


def _registros(estado: Estado) -> list[_Registro]:
    """Histórico com timestamp legível, em ordem cronológica."""
    saida = []
    for r in estado.historico:
        try:
            momento = datetime.fromisoformat(r.timestamp)
        except (TypeError, ValueError):
            continue
        if momento.tzinfo is None:
            momento = momento.replace(tzinfo=UTC)
        saida.append(_Registro(r.item_id, momento, r.sucesso, r.mensagem))
    saida.sort(key=lambda r: r.momento)
    return saida


def _ciclos(registros: list[_Registro]) -> list[list[_Registro]]:
    ciclos: list[list[_Registro]] = []
    for r in registros:
        if ciclos and r.momento - ciclos[-1][-1].momento < JANELA_CICLO:
            ciclos[-1].append(r)
        else:
            ciclos.append([r])
    return ciclos


def no_ar_agora(estado: Estado, agora: datetime | None = None) -> dict:
    """Itens impulsionados com sucesso nas últimas `DURACAO_BOOST` horas (com quanto falta
    para expirar) e o resultado do último ciclo, item a item."""
    agora = agora or datetime.now(UTC)
    registros = _registros(estado)

    ativos: dict[int, _Registro] = {}
    for r in registros:
        if r.sucesso and agora - r.momento < DURACAO_BOOST:
            ativos[r.item_id] = r  # o mais recente vence
    no_ar = [
        {
            "id": r.item_id,
            "desde": r.momento.isoformat(),
            "expira_em": (r.momento + DURACAO_BOOST).isoformat(),
            "minutos_restantes": int((r.momento + DURACAO_BOOST - agora).total_seconds() // 60),
        }
        for r in sorted(ativos.values(), key=lambda r: r.momento + DURACAO_BOOST)
    ]

    ciclos = _ciclos(registros)
    ultimo = ciclos[-1] if ciclos else []
    return {
        "duracao_boost_horas": DURACAO_BOOST.total_seconds() / 3600,
        "no_ar": no_ar,
        "ultimo_ciclo": {
            "em": ultimo[0].momento.isoformat() if ultimo else None,
            "itens": [
                {"id": r.item_id, "sucesso": r.sucesso, "mensagem": r.mensagem}
                for r in ultimo
            ],
        },
    }


def relatorio(
    estado: Estado,
    dias: int,
    pesos_atuais: dict[int, int],
    agora: datetime | None = None,
) -> dict:
    """Agregados dos últimos `dias`: resumo, boosts por dia, por item e erros frequentes."""
    agora = agora or datetime.now(UTC)
    inicio = agora - timedelta(days=dias)
    registros = [r for r in _registros(estado) if r.momento >= inicio]
    sucessos = [r for r in registros if r.sucesso]

    hoje = agora.astimezone(FUSO_RELATORIO).date()
    por_dia = {hoje - timedelta(days=i): [0, 0] for i in range(dias - 1, -1, -1)}
    for r in registros:
        dia = r.momento.astimezone(FUSO_RELATORIO).date()
        if dia in por_dia:
            por_dia[dia][0 if r.sucesso else 1] += 1

    total_peso = sum(pesos_atuais.values()) or 1
    total_sucessos = len(sucessos) or 1
    por_item: dict[int, dict] = {}
    for item_id, peso in pesos_atuais.items():
        por_item[item_id] = _linha_item(item_id, peso)
    for r in registros:
        linha = por_item.setdefault(r.item_id, _linha_item(r.item_id, None))
        if r.sucesso:
            linha["sucessos"] += 1
            linha["ultimo_sucesso_em"] = r.momento.isoformat()
        else:
            linha["falhas"] += 1
    for linha in por_item.values():
        linha["parte_dos_boosts"] = linha["sucessos"] / total_sucessos
        linha["parte_do_peso"] = (linha["peso"] or 0) / total_peso

    erros = Counter(_erro_resumido(r.mensagem) for r in registros if not r.sucesso)
    ciclos = _ciclos(registros)
    return {
        "dias": dias,
        "desde": inicio.isoformat(),
        "resumo": {
            "ciclos": len(ciclos),
            "ciclos_com_sucesso": sum(1 for c in ciclos if any(r.sucesso for r in c)),
            "tentativas": len(registros),
            "sucessos": len(sucessos),
            "falhas": len(registros) - len(sucessos),
            "itens_impulsionados": len({r.item_id for r in sucessos}),
        },
        "por_dia": [
            {"dia": dia.isoformat(), "sucessos": ok, "falhas": falha}
            for dia, (ok, falha) in por_dia.items()
        ],
        "por_item": sorted(
            por_item.values(), key=lambda linha: (-linha["sucessos"], -(linha["peso"] or 0))
        ),
        "erros": [{"mensagem": m, "vezes": n} for m, n in erros.most_common(MAX_ERROS)],
    }


def _linha_item(item_id: int, peso: int | None) -> dict:
    return {"id": item_id, "peso": peso, "sucessos": 0, "falhas": 0, "ultimo_sucesso_em": None}


def _erro_resumido(mensagem: str) -> str:
    """Agrupa variações da mesma falha (ex.: mensagens com horário ou id embutido)."""
    return mensagem.split(" for url:")[0].strip()[:160] or "erro sem mensagem"

