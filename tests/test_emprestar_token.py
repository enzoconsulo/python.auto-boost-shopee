"""Testes de `scripts/emprestar_token.py`, sem rede real."""

from __future__ import annotations

import importlib.util
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from shopee_rodizio.armazem_token import ArmazemToken
from shopee_rodizio.cliente_shopee import Token

_SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "emprestar_token.py"


@pytest.fixture
def emprestar():
    spec = importlib.util.spec_from_file_location("emprestar_token", _SCRIPT)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


@pytest.fixture
def config_toml(tmp_path):
    caminho = tmp_path / "config.toml"
    caminho.write_text(
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
endpoint_boost = "/api/v2/product/boost_item"

[caminhos]
log = "{(tmp_path / "log.log").as_posix()}"
estado = "{(tmp_path / "estado.json").as_posix()}"

[[itens]]
id = 1
peso = 1
""",
        encoding="utf-8",
    )
    return caminho


def _gravar_token(tmp_path, validade: timedelta) -> None:
    ArmazemToken(tmp_path / "token.json").gravar(
        Token("at-atual", "rt-atual", datetime.now(UTC) + validade)
    )


def _resposta(json_dados: dict) -> Mock:
    resposta = Mock()
    resposta.json.return_value = json_dados
    resposta.raise_for_status.return_value = None
    return resposta


@patch("shopee_rodizio.cliente_shopee.requests.post")
def test_token_valido_pelo_tempo_pedido_e_emprestado_sem_renovar(
    post_mock, emprestar, config_toml, tmp_path, capsys
):
    _gravar_token(tmp_path, timedelta(hours=2))

    assert emprestar.main([str(config_toml), "--minutos", "60"]) == 0

    post_mock.assert_not_called()
    saida = json.loads(capsys.readouterr().out)
    assert saida["access_token"] == "at-atual"
    assert saida["shop_id"] == 99
    assert saida["partner_id"] == 1
    assert "refresh_token" not in saida  # o refresh_token nunca sai do Pi


@patch("shopee_rodizio.cliente_shopee.requests.post")
def test_token_perto_de_vencer_e_renovado_e_gravado_antes_de_emprestar(
    post_mock, emprestar, config_toml, tmp_path, capsys
):
    _gravar_token(tmp_path, timedelta(minutes=30))
    post_mock.return_value = _resposta(
        {"access_token": "at-novo", "refresh_token": "rt-novo", "expire_in": 14400}
    )

    assert emprestar.main([str(config_toml), "--minutos", "60"]) == 0

    assert json.loads(capsys.readouterr().out)["access_token"] == "at-novo"
    assert ArmazemToken(tmp_path / "token.json").carregar().refresh_token == "rt-novo"


@patch("shopee_rodizio.cliente_shopee.requests.post")
def test_falha_ao_renovar_sai_com_erro_sem_imprimir_token(
    post_mock, emprestar, config_toml, tmp_path, capsys
):
    _gravar_token(tmp_path, timedelta(minutes=5))
    post_mock.return_value = _resposta(
        {"error": "error_auth", "message": "Your refresh_token expired."}
    )

    assert emprestar.main([str(config_toml)]) == 1

    capturado = capsys.readouterr()
    assert capturado.out == ""
    assert "refresh_token expired" in capturado.err


def test_minutos_perto_da_validade_do_token_e_recusado(emprestar, config_toml, capsys):
    assert emprestar.main([str(config_toml), "--minutos", "240"]) == 1
    assert "--minutos" in capsys.readouterr().err
