"""Testes do loop de `__main__.py`: espera na subida (sem queimar ciclo a cada restart) e
releitura do `config.toml` a cada ciclo."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import pytest

from shopee_rodizio import boost
from shopee_rodizio.__main__ import executar_loop
from shopee_rodizio.estado import (
    Estado,
    RegistroBoost,
    segundos_ate_proximo_ciclo,
    ultimo_ciclo_em,
)

AGORA = datetime(2026, 10, 19, 18, 56, tzinfo=UTC)


def _estado_com(*momentos: datetime) -> Estado:
    return Estado(
        caminho=None,
        historico=[RegistroBoost(1, m.isoformat(), False, "x") for m in momentos],
    )


def test_sem_historico_o_primeiro_ciclo_roda_na_hora():
    assert segundos_ate_proximo_ciclo(_estado_com(), 4, AGORA) == 0


def test_restart_2h20_depois_do_ultimo_ciclo_espera_1h40():
    # o caso de produção de 19/10: ciclo às 16:36, restart às 18:56
    estado = _estado_com(AGORA - timedelta(hours=6), AGORA - timedelta(hours=2, minutes=20))

    assert segundos_ate_proximo_ciclo(estado, 4, AGORA) == pytest.approx(100 * 60)


def test_ultimo_ciclo_ha_mais_de_um_intervalo_roda_na_hora():
    assert segundos_ate_proximo_ciclo(_estado_com(AGORA - timedelta(hours=9)), 4, AGORA) == 0


def test_relogio_atrasado_sem_rtc_espera_o_intervalo_cheio():
    # boot antes do NTP: fake-hwclock devolve um horário anterior ao último ciclo gravado
    estado = _estado_com(AGORA + timedelta(days=3))

    assert segundos_ate_proximo_ciclo(estado, 4, AGORA) == 4 * 3600


def _r(atras: timedelta, sucesso: bool) -> RegistroBoost:
    return RegistroBoost(1, (AGORA - atras).isoformat(), sucesso, "x")


def test_falhas_depois_do_ultimo_sucesso_nao_empurram_o_proximo_ciclo():
    # caso de 19/10: boosts ok às 16:36, restarts às 18:56 falharam por slot cheio; o
    # próximo ciclo tem de ser 20:36 (quando os slots liberam), não 22:56
    estado = Estado(
        caminho=None,
        historico=[
            _r(timedelta(hours=2, minutes=20), True),
            _r(timedelta(minutes=0), False),
        ],
    )

    assert segundos_ate_proximo_ciclo(estado, 4, AGORA) == pytest.approx(100 * 60)


def test_sucesso_ha_mais_de_um_intervalo_e_falha_recente_roda_na_hora():
    estado = Estado(
        caminho=None,
        historico=[_r(timedelta(hours=6), True), _r(timedelta(hours=2), False)],
    )

    assert segundos_ate_proximo_ciclo(estado, 4, AGORA) == 0


def test_relogio_atrasado_vale_mesmo_quando_o_registro_futuro_e_uma_falha():
    estado = Estado(
        caminho=None,
        historico=[_r(timedelta(hours=6), True), _r(-timedelta(days=2), False)],
    )

    assert segundos_ate_proximo_ciclo(estado, 4, AGORA) == 4 * 3600


def test_timestamp_ilegivel_e_ignorado():
    estado = Estado(
        caminho=None,
        historico=[
            RegistroBoost(1, "lixo", True, "ok"),
            RegistroBoost(2, (AGORA - timedelta(hours=1)).isoformat(), True, "ok"),
        ],
    )

    assert ultimo_ciclo_em(estado) == AGORA - timedelta(hours=1)


# --- loop ----------------------------------------------------------------------------------


def _toml(tmp_path, pesos: dict[int, int]) -> str:
    itens = "".join(f"\n[[itens]]\nid = {i}\npeso = {p}\n" for i, p in pesos.items())
    return f"""
[shopee]
partner_id = 1
partner_key = "chave"
shop_id = 99
access_token = "tok"
refresh_token = "ref"

[ciclo]
intervalo_horas = 4
limite_slots = 1
endpoint_boost = "/api/v2/product/boost_item"

[caminhos]
log = "{(tmp_path / 'rodizio.log').as_posix()}"
estado = "{(tmp_path / 'estado.json').as_posix()}"
{itens}"""


@pytest.fixture
def config_arquivo(tmp_path):
    caminho = tmp_path / "config.toml"
    caminho.write_text(_toml(tmp_path, {1: 10}), encoding="utf-8")
    return caminho


def _ok(*_args, **_kwargs):
    return boost.ResultadoBoost(sucesso=True, mensagem="ok")


def test_loop_com_ciclo_recente_no_historico_dorme_o_restante_antes_do_primeiro_ciclo(
    tmp_path, config_arquivo
):
    ha_uma_hora = datetime.now(UTC) - timedelta(hours=1)
    (tmp_path / "estado.json").write_text(
        json.dumps(
            {
                "historico": [
                    {"item_id": 1, "timestamp": ha_uma_hora.isoformat(), "sucesso": True,
                     "mensagem": "ok"}
                ]
            }
        ),
        encoding="utf-8",
    )
    ordem: list[str] = []

    with (
        patch("shopee_rodizio.__main__.time.sleep", side_effect=lambda s: ordem.append(s)),
        patch.object(boost, "impulsionar", side_effect=lambda *a: ordem.append("boost") or _ok()),
    ):
        executar_loop(str(config_arquivo), max_iteracoes=1)

    assert ordem[0] == pytest.approx(3 * 3600, abs=5)  # dormiu antes de impulsionar
    assert ordem[1] == "boost"
    assert "aguardando" in (tmp_path / "rodizio.log").read_text(encoding="utf-8")


def test_loop_rele_config_a_cada_ciclo_e_usa_itens_novos_sem_reiniciar(tmp_path, config_arquivo):
    impulsionados: list[int] = []

    def _sleep(_segundos):
        # entre um ciclo e outro, o painel troca o item do rodízio
        config_arquivo.write_text(_toml(tmp_path, {2: 5}), encoding="utf-8")

    with (
        patch("shopee_rodizio.__main__.time.sleep", side_effect=_sleep),
        patch.object(
            boost, "impulsionar", side_effect=lambda c, cfg, item_id: impulsionados.append(item_id) or _ok()
        ),
    ):
        executar_loop(str(config_arquivo), max_iteracoes=2)

    assert impulsionados == [1, 2]


def test_loop_com_config_invalido_no_meio_segue_com_a_ultima_config_valida(
    tmp_path, config_arquivo
):
    impulsionados: list[int] = []

    with (
        patch(
            "shopee_rodizio.__main__.time.sleep",
            side_effect=lambda _s: config_arquivo.write_text("[[itens]\nquebrado", encoding="utf-8"),
        ),
        patch.object(
            boost, "impulsionar", side_effect=lambda c, cfg, item_id: impulsionados.append(item_id) or _ok()
        ),
    ):
        executar_loop(str(config_arquivo), max_iteracoes=2)

    assert impulsionados == [1, 1]
    assert "config.toml inválido" in (tmp_path / "rodizio.log").read_text(encoding="utf-8")


def test_loop_so_recria_cliente_quando_credenciais_mudam(tmp_path, config_arquivo):
    with (
        patch("shopee_rodizio.__main__.time.sleep"),
        patch.object(boost, "impulsionar", side_effect=_ok),
        patch(
            "shopee_rodizio.__main__.cliente_da_config", wraps=__import__(
                "shopee_rodizio.armazem_token", fromlist=["cliente_da_config"]
            ).cliente_da_config
        ) as fabrica,
    ):
        executar_loop(str(config_arquivo), max_iteracoes=3)

    assert fabrica.call_count == 1
