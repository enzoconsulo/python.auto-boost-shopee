"""Testes de `ciclo.py`: orquestração de um ciclo de rodízio, sem depender de rede real."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from shopee_rodizio import boost
from shopee_rodizio.ciclo import executar_ciclo
from shopee_rodizio.config import CaminhosConfig, CicloConfig, Config, Item, ShopeeCredenciais
from shopee_rodizio.estado import Estado


def _config(itens: list[Item], limite_slots: int = 2) -> Config:
    return Config(
        shopee=ShopeeCredenciais(
            partner_id=1,
            partner_key="chave",
            shop_id=99,
            access_token="tok",
            refresh_token="ref",
        ),
        ciclo=CicloConfig(
            intervalo_horas=4, limite_slots=limite_slots, endpoint_boost="/api/v2/product/boost"
        ),
        caminhos=CaminhosConfig(log="log.log", estado="estado.json"),
        itens=itens,
    )


def _estado(tmp_path) -> Estado:
    return Estado(caminho=tmp_path / "estado.json", historico=[])


def _itens(*ids: int) -> list[Item]:
    return [Item(id=item_id, peso=1) for item_id in ids]


def test_ciclo_com_todos_os_boosts_com_sucesso_grava_historico(tmp_path):
    config = _config(_itens(1, 2), limite_slots=2)
    estado = _estado(tmp_path)

    with patch.object(
        boost, "impulsionar", return_value=boost.ResultadoBoost(sucesso=True, mensagem="ok")
    ) as mock_impulsionar:
        resultado = executar_ciclo(cliente=object(), config=config, estado=estado)

    assert mock_impulsionar.call_count == 2
    assert len(resultado.historico) == 2
    assert all(registro.sucesso for registro in resultado.historico)
    assert resultado.caminho.exists()


def test_ciclo_com_boost_falhando_por_erro_de_api_nao_lanca_e_grava_falha(tmp_path):
    config = _config(_itens(1, 2), limite_slots=2)
    estado = _estado(tmp_path)

    def _impulsionar(cliente, config, item_id):
        if item_id == 1:
            return boost.ResultadoBoost(sucesso=False, mensagem="erro da API: item bloqueado")
        return boost.ResultadoBoost(sucesso=True, mensagem="ok")

    with patch.object(boost, "impulsionar", side_effect=_impulsionar):
        resultado = executar_ciclo(cliente=object(), config=config, estado=estado)

    assert len(resultado.historico) == 2
    falhou = next(r for r in resultado.historico if r.item_id == 1)
    sucedeu = next(r for r in resultado.historico if r.item_id == 2)
    assert falhou.sucesso is False
    assert sucedeu.sucesso is True
    assert resultado.caminho.exists()


def test_ciclo_com_excecao_inesperada_de_rede_nao_escapa_e_grava_falha(tmp_path):
    config = _config(_itens(1, 2), limite_slots=2)
    estado = _estado(tmp_path)

    def _impulsionar(cliente, config, item_id):
        if item_id == 1:
            raise ConnectionError("timeout de rede")
        return boost.ResultadoBoost(sucesso=True, mensagem="ok")

    with patch.object(boost, "impulsionar", side_effect=_impulsionar):
        resultado = executar_ciclo(cliente=object(), config=config, estado=estado)

    assert len(resultado.historico) == 2
    falhou = next(r for r in resultado.historico if r.item_id == 1)
    assert falhou.sucesso is False
    assert "timeout de rede" in falhou.mensagem


def test_ciclo_respeita_limite_de_slots_e_seleciona_via_selecao(tmp_path):
    config = _config(_itens(1, 2, 3), limite_slots=1)
    estado = _estado(tmp_path)

    with patch.object(
        boost, "impulsionar", return_value=boost.ResultadoBoost(sucesso=True, mensagem="ok")
    ) as mock_impulsionar:
        resultado = executar_ciclo(cliente=object(), config=config, estado=estado)

    assert mock_impulsionar.call_count == 1
    assert len(resultado.historico) == 1


def test_ciclo_sem_itens_selecionados_nao_grava_nada(tmp_path):
    config = _config([], limite_slots=2)
    estado = _estado(tmp_path)

    with patch.object(boost, "impulsionar") as mock_impulsionar:
        resultado = executar_ciclo(cliente=object(), config=config, estado=estado)

    mock_impulsionar.assert_not_called()
    assert resultado.historico == []


@pytest.fixture
def _config_arquivo(tmp_path):
    caminho_log = (tmp_path / "shopee-rodizio.log").as_posix()
    caminho_estado = (tmp_path / "estado.json").as_posix()
    config_path = tmp_path / "config.toml"
    config_path.write_text(
        f"""
[shopee]
partner_id = 1
partner_key = "chave"
shop_id = 99
access_token = "tok"
refresh_token = "ref"

[ciclo]
intervalo_horas = 4
limite_slots = 1
endpoint_boost = "/api/v2/product/boost"

[caminhos]
log = "{caminho_log}"
estado = "{caminho_estado}"

[[itens]]
id = 1
peso = 10
""",
        encoding="utf-8",
    )
    return config_path


def test_loop_principal_roda_numero_limitado_de_iteracoes_sem_quebrar(tmp_path, _config_arquivo):
    from shopee_rodizio.__main__ import executar_loop

    with (
        patch("shopee_rodizio.__main__.time.sleep") as mock_sleep,
        patch.object(
            boost, "impulsionar", return_value=boost.ResultadoBoost(sucesso=True, mensagem="ok")
        ) as mock_impulsionar,
    ):
        executar_loop(str(_config_arquivo), max_iteracoes=2)

    assert mock_sleep.call_count == 2
    assert mock_impulsionar.call_count == 2


def test_loop_principal_continua_apos_ciclo_lancar_excecao_inesperada(tmp_path, _config_arquivo):
    from shopee_rodizio.__main__ import executar_loop

    with (
        patch("shopee_rodizio.__main__.time.sleep"),
        patch("shopee_rodizio.__main__.executar_ciclo", side_effect=RuntimeError("bug")) as mock_ciclo,
    ):
        executar_loop(str(_config_arquivo), max_iteracoes=2)

    assert mock_ciclo.call_count == 2
