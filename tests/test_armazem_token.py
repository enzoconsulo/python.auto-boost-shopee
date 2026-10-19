"""Testes de `armazem_token.py`: token.json compartilhado entre processos."""

from __future__ import annotations

import threading
import time
from datetime import UTC, datetime

from shopee_rodizio.armazem_token import ArmazemToken, caminho_token, cliente_da_config
from shopee_rodizio.cliente_shopee import Token
from shopee_rodizio.config import CaminhosConfig, CicloConfig, Config, Item, ShopeeCredenciais


def _config(tmp_path) -> Config:
    return Config(
        shopee=ShopeeCredenciais(
            partner_id=1,
            partner_key="chave",
            shop_id=99,
            access_token="tok",
            refresh_token="ref",
        ),
        ciclo=CicloConfig(
            intervalo_horas=4, limite_slots=1, endpoint_boost="/api/v2/product/boost_item"
        ),
        caminhos=CaminhosConfig(
            log=str(tmp_path / "log.log"), estado=str(tmp_path / "estado.json")
        ),
        itens=[Item(id=1, peso=1)],
    )


def test_gravar_e_carregar_faz_roundtrip_sem_deixar_temporario(tmp_path):
    armazem = ArmazemToken(tmp_path / "token.json")
    token = Token("at-novo", "rt-novo", datetime(2030, 1, 1, tzinfo=UTC))

    armazem.gravar(token)

    assert armazem.carregar() == token
    assert list(tmp_path.glob("*.tmp")) == []


def test_carregar_sem_arquivo_devolve_none(tmp_path):
    assert ArmazemToken(tmp_path / "nao-existe.json").carregar() is None


def test_travado_so_libera_outro_interessado_depois_de_solto(tmp_path):
    eventos: list[str] = []

    def _outro_processo():
        with ArmazemToken(tmp_path / "token.json").travado():
            eventos.append("outro entrou")

    with ArmazemToken(tmp_path / "token.json").travado():
        concorrente = threading.Thread(target=_outro_processo)
        concorrente.start()
        time.sleep(0.3)
        eventos.append("primeiro saiu")
    concorrente.join(timeout=15)

    assert eventos == ["primeiro saiu", "outro entrou"]


def test_caminho_token_fica_ao_lado_do_estado(tmp_path):
    assert caminho_token(_config(tmp_path)) == tmp_path / "token.json"


def test_cliente_da_config_usa_token_json_em_vez_do_config_apos_restart(tmp_path):
    persistido = Token("at-renovado", "rt-renovado", datetime(2030, 1, 1, tzinfo=UTC))
    ArmazemToken(tmp_path / "token.json").gravar(persistido)

    cliente = cliente_da_config(_config(tmp_path))

    assert cliente.token == persistido  # não o "tok"/"ref" do config.toml


def test_cliente_da_config_sem_token_json_usa_config(tmp_path):
    cliente = cliente_da_config(_config(tmp_path))

    assert cliente.token == Token("tok", "ref", None)
