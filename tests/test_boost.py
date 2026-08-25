from unittest.mock import Mock

from shopee_rodizio.boost import impulsionar
from shopee_rodizio.cliente_shopee import Resultado
from shopee_rodizio.config import (
    CaminhosConfig,
    CicloConfig,
    Config,
    Item,
    ShopeeCredenciais,
)

SHOP_ID = 789
ENDPOINT_BOOST = "/api/v2/product/boost_item"


def _config(**overrides_ciclo) -> Config:
    ciclo_kwargs = {
        "intervalo_horas": 4,
        "limite_slots": 5,
        "endpoint_boost": ENDPOINT_BOOST,
    }
    ciclo_kwargs.update(overrides_ciclo)
    return Config(
        shopee=ShopeeCredenciais(
            partner_id=123456,
            partner_key="chave-secreta-de-teste",
            shop_id=SHOP_ID,
            access_token="access-tok",
            refresh_token="refresh-tok",
        ),
        ciclo=CicloConfig(**ciclo_kwargs),
        caminhos=CaminhosConfig(log="log.jsonl", estado="estado.json"),
        itens=[Item(id=1, peso=1)],
    )


def test_impulsionar_com_sucesso_devolve_resultado_positivo():
    cliente = Mock()
    cliente.chamar.return_value = Resultado(sucesso=True, dados={"error": "", "response": {}})

    resultado = impulsionar(cliente, _config(), item_id=42)

    assert resultado.sucesso is True
    assert resultado.mensagem

    cliente.chamar.assert_called_once_with(
        ENDPOINT_BOOST, {"item_id": 42, "shop_id": SHOP_ID}
    )


def test_impulsionar_usa_endpoint_e_shop_id_da_config():
    cliente = Mock()
    cliente.chamar.return_value = Resultado(sucesso=True, dados={})

    outro_endpoint = "/api/v2/product/outro_caminho"
    config = _config(endpoint_boost=outro_endpoint)

    impulsionar(cliente, config, item_id=7)

    cliente.chamar.assert_called_once_with(
        outro_endpoint, {"item_id": 7, "shop_id": SHOP_ID}
    )


def test_impulsionar_erro_da_api_devolve_resultado_negativo_sem_lancar():
    cliente = Mock()
    cliente.chamar.return_value = Resultado(
        sucesso=False, erro="item_limit_exceeded: limite atingido"
    )

    resultado = impulsionar(cliente, _config(), item_id=42)

    assert resultado.sucesso is False
    assert "limite atingido" in resultado.mensagem


def test_impulsionar_erro_sem_mensagem_devolve_mensagem_generica():
    cliente = Mock()
    cliente.chamar.return_value = Resultado(sucesso=False, erro=None)

    resultado = impulsionar(cliente, _config(), item_id=42)

    assert resultado.sucesso is False
    assert resultado.mensagem
