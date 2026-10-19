"""Testes de `relatorio.py`: agregados do histórico para as abas do painel."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from shopee_rodizio import painel
from shopee_rodizio.estado import Estado, RegistroBoost
from shopee_rodizio.relatorio import no_ar_agora, relatorio

AGORA = datetime(2026, 10, 19, 20, 0, tzinfo=UTC)  # 17:00 em UTC-3


def _r(item_id: int, atras: timedelta, sucesso: bool = True, mensagem: str = "ok"):
    return RegistroBoost(item_id, (AGORA - atras).isoformat(), sucesso, mensagem)


def _estado(*registros: RegistroBoost) -> Estado:
    return Estado(caminho=None, historico=list(registros))


H = timedelta(hours=1)
M = timedelta(minutes=1)


def test_no_ar_agora_lista_so_sucessos_dentro_das_4h_ordenados_por_expiracao():
    estado = _estado(
        _r(1, 5 * H),  # já expirou
        _r(2, 3 * H),
        _r(3, 3 * H - M, sucesso=False, mensagem="slot limit"),  # falha não está no ar
        _r(4, 1 * H),
    )

    resultado = no_ar_agora(estado, AGORA)

    assert [i["id"] for i in resultado["no_ar"]] == [2, 4]
    assert resultado["no_ar"][0]["minutos_restantes"] == 60
    assert resultado["no_ar"][1]["minutos_restantes"] == 180


def test_ultimo_ciclo_agrupa_registros_proximos_e_ignora_ciclos_anteriores():
    estado = _estado(
        _r(1, 4 * H),
        _r(2, 2 * H + 30 * M),
        _r(3, 2 * H + 29 * M, sucesso=False, mensagem="product.error_busi: slot limit"),
        _r(4, 2 * H + 28 * M),
    )

    ultimo = no_ar_agora(estado, AGORA)["ultimo_ciclo"]

    assert [i["id"] for i in ultimo["itens"]] == [2, 3, 4]
    assert ultimo["itens"][1] == {
        "id": 3, "sucesso": False, "mensagem": "product.error_busi: slot limit"
    }


def test_sem_historico_nada_no_ar_e_sem_ultimo_ciclo():
    resultado = no_ar_agora(_estado(), AGORA)

    assert resultado["no_ar"] == []
    assert resultado["ultimo_ciclo"] == {"em": None, "itens": []}


def test_relatorio_resume_periodo_e_ignora_o_que_e_mais_antigo():
    estado = _estado(
        _r(1, timedelta(days=10)),  # fora dos 7 dias
        _r(1, 30 * H),
        _r(2, 30 * H - M, sucesso=False, mensagem="reached shop's bump slot limit"),
        _r(1, 2 * H),
        _r(2, 2 * H - M),
    )

    rel = relatorio(estado, 7, {1: 30, 2: 10}, AGORA)

    assert rel["resumo"] == {
        "ciclos": 2,
        "ciclos_com_sucesso": 2,
        "tentativas": 4,
        "sucessos": 3,
        "falhas": 1,
        "itens_impulsionados": 2,
    }
    assert rel["erros"] == [{"mensagem": "reached shop's bump slot limit", "vezes": 1}]


def test_relatorio_por_dia_usa_fuso_de_brasilia_e_tem_um_ponto_por_dia():
    # 01:00 UTC de 19/10 = 22:00 de 18/10 em Brasília
    estado = _estado(_r(1, 19 * H))

    rel = relatorio(estado, 7, {1: 1}, AGORA)

    assert len(rel["por_dia"]) == 7
    assert rel["por_dia"][-1]["dia"] == "2026-10-19"
    assert {d["dia"]: d["sucessos"] for d in rel["por_dia"]}["2026-10-18"] == 1


def test_relatorio_por_item_compara_parte_dos_boosts_com_parte_do_peso():
    estado = _estado(_r(1, 2 * H), _r(1, 6 * H), _r(1, 10 * H), _r(9, 3 * H))

    por_item = {i["id"]: i for i in relatorio(estado, 7, {1: 75, 2: 25}, AGORA)["por_item"]}

    assert por_item[1]["parte_dos_boosts"] == 0.75
    assert por_item[1]["parte_do_peso"] == 0.75
    assert por_item[2]["sucessos"] == 0  # no rodízio, nunca sorteado: aparece com zero
    assert por_item[9]["peso"] is None  # impulsionado no período, mas fora do rodízio hoje


def test_erro_http_e_resumido_sem_url():
    estado = _estado(_r(1, H, sucesso=False, mensagem="403 Client Error: Forbidden for url: https://x?<omitido>"))

    assert relatorio(estado, 7, {1: 1}, AGORA)["erros"][0]["mensagem"] == "403 Client Error: Forbidden"


def test_dias_do_pedido_aceita_so_periodos_conhecidos():
    assert painel.dias_do_pedido("dias=30") == 30
    assert painel.dias_do_pedido("dias=1") == 1
    assert painel.dias_do_pedido("dias=9999") == 7
    assert painel.dias_do_pedido("dias=abc") == 7
    assert painel.dias_do_pedido("") == 7
