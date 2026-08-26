from pathlib import Path

import pytest

from shopee_rodizio.config import ConfigError, carregar_config

TOML_VALIDO = """
[shopee]
partner_id = 123
partner_key = "chave-secreta"
shop_id = 456
access_token = "tok"
refresh_token = "reftok"

[ciclo]
intervalo_horas = 4
limite_slots = 5
endpoint_boost = "/api/v2/product/boost_item"

[caminhos]
log = "shopee-rodizio.log"
estado = "estado.json"

[[itens]]
id = 111
peso = 3

[[itens]]
id = 222
peso = 1
"""


def _escrever(tmp_path: Path, conteudo: str) -> Path:
    caminho = tmp_path / "config.toml"
    caminho.write_text(conteudo, encoding="utf-8")
    return caminho


def test_config_valida_carrega_estrutura_tipada(tmp_path):
    config = carregar_config(_escrever(tmp_path, TOML_VALIDO))

    assert config.shopee.partner_id == 123
    assert config.shopee.partner_key == "chave-secreta"
    assert config.ciclo.intervalo_horas == 4
    assert config.ciclo.limite_slots == 5
    assert config.ciclo.endpoint_boost == "/api/v2/product/boost_item"
    assert config.caminhos.log == "shopee-rodizio.log"
    assert config.caminhos.estado == "estado.json"
    assert len(config.itens) == 2
    assert config.itens[0].id == 111
    assert config.itens[0].peso == 3
    assert config.itens[1].peso == 1


def test_config_exemplo_do_projeto_e_valida():
    caminho = Path(__file__).resolve().parent.parent / "config.example.toml"
    config = carregar_config(caminho)
    assert len(config.itens) >= 1


def test_item_com_peso_negativo_levanta_erro_identificando_o_campo(tmp_path):
    invalido = TOML_VALIDO.replace("peso = 3", "peso = -1")
    with pytest.raises(ConfigError, match="peso"):
        carregar_config(_escrever(tmp_path, invalido))


def test_secao_shopee_incompleta_levanta_erro_identificando_o_campo(tmp_path):
    invalido = TOML_VALIDO.replace('partner_key = "chave-secreta"\n', "")
    with pytest.raises(ConfigError, match="shopee.partner_key"):
        carregar_config(_escrever(tmp_path, invalido))


def test_item_sem_peso_levanta_erro(tmp_path):
    invalido = TOML_VALIDO.replace("peso = 3\n", "")
    with pytest.raises(ConfigError, match="peso"):
        carregar_config(_escrever(tmp_path, invalido))


def test_item_sem_id_levanta_erro(tmp_path):
    invalido = TOML_VALIDO.replace("id = 111\n", "")
    with pytest.raises(ConfigError, match="id"):
        carregar_config(_escrever(tmp_path, invalido))


def test_intervalo_horas_invalido_levanta_erro(tmp_path):
    invalido = TOML_VALIDO.replace("intervalo_horas = 4", "intervalo_horas = 0")
    with pytest.raises(ConfigError, match="intervalo_horas"):
        carregar_config(_escrever(tmp_path, invalido))


def test_limite_slots_invalido_levanta_erro(tmp_path):
    invalido = TOML_VALIDO.replace("limite_slots = 5", "limite_slots = 0")
    with pytest.raises(ConfigError, match="limite_slots"):
        carregar_config(_escrever(tmp_path, invalido))


def test_config_sem_secao_rede_tem_proxy_https_none(tmp_path):
    config = carregar_config(_escrever(tmp_path, TOML_VALIDO))
    assert config.rede.proxy_https is None


def test_config_com_secao_rede_carrega_proxy_https(tmp_path):
    com_proxy = TOML_VALIDO + '\n[rede]\nproxy_https = "socks5h://127.0.0.1:1080"\n'
    config = carregar_config(_escrever(tmp_path, com_proxy))
    assert config.rede.proxy_https == "socks5h://127.0.0.1:1080"
