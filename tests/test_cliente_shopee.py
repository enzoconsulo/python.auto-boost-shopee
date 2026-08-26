import hashlib
import hmac
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from unittest.mock import Mock, patch

import requests

from shopee_rodizio.cliente_shopee import (
    ClienteShopee,
    assinatura,
    base_loja,
    base_publica,
)

PARTNER_ID = 123456
PARTNER_KEY = "chave-secreta-de-teste"
SHOP_ID = 789
ACCESS_TOKEN = "access-tok-atual"
REFRESH_TOKEN = "refresh-tok-atual"


def _cliente(**overrides) -> ClienteShopee:
    kwargs = {
        "partner_id": PARTNER_ID,
        "partner_key": PARTNER_KEY,
        "shop_id": SHOP_ID,
        "access_token": ACCESS_TOKEN,
        "refresh_token": REFRESH_TOKEN,
        "expira_em": datetime.now(UTC) + timedelta(hours=2),
    }
    kwargs.update(overrides)
    return ClienteShopee(**kwargs)


def _resposta(json_dados: dict, status_ok: bool = True) -> Mock:
    resposta = Mock()
    resposta.json.return_value = json_dados
    if status_ok:
        resposta.raise_for_status.return_value = None
    else:
        resposta.raise_for_status.side_effect = requests.HTTPError("erro http")
    return resposta


def test_assinatura_publica_bate_com_vetor_conhecido():
    path = "/api/v2/auth/access_token/get"
    timestamp = 1700000000

    base = f"{PARTNER_ID}{path}{timestamp}"
    esperado = hmac.new(PARTNER_KEY.encode("utf-8"), base.encode("utf-8"), hashlib.sha256).hexdigest()

    assert assinatura(PARTNER_KEY, base_publica(PARTNER_ID, path, timestamp)) == esperado


def test_assinatura_loja_bate_com_vetor_conhecido_e_inclui_token_e_shop():
    path = "/api/v2/product/boost_item"
    timestamp = 1700000000

    base = f"{PARTNER_ID}{path}{timestamp}{ACCESS_TOKEN}{SHOP_ID}"
    esperado = hmac.new(PARTNER_KEY.encode("utf-8"), base.encode("utf-8"), hashlib.sha256).hexdigest()

    calculada = assinatura(
        PARTNER_KEY, base_loja(PARTNER_ID, path, timestamp, ACCESS_TOKEN, SHOP_ID)
    )
    assert calculada == esperado
    # muda se qualquer componente da base mudar (prova que shop_id/access_token entram na base)
    assert calculada != assinatura(PARTNER_KEY, base_publica(PARTNER_ID, path, timestamp))


@patch("shopee_rodizio.cliente_shopee.requests.post")
def test_chamar_com_token_valido_nao_renova_e_devolve_sucesso(post_mock):
    post_mock.return_value = _resposta({"error": "", "response": {"ok": True}})
    cliente = _cliente()

    resultado = cliente.chamar("/api/v2/product/boost_item", {"item_id": 1})

    assert resultado.sucesso is True
    assert resultado.dados == {"error": "", "response": {"ok": True}}
    assert resultado.token_renovado is None
    assert post_mock.call_count == 1


@patch("shopee_rodizio.cliente_shopee.requests.post")
def test_chamar_com_token_expirado_renova_antes_e_persiste_novo_token(post_mock):
    resposta_renovacao = _resposta(
        {
            "access_token": "access-tok-novo",
            "refresh_token": "refresh-tok-novo",
            "expire_in": 14400,
        }
    )
    resposta_chamada = _resposta({"error": "", "response": {"ok": True}})
    post_mock.side_effect = [resposta_renovacao, resposta_chamada]

    cliente = _cliente(expira_em=None)
    resultado = cliente.chamar("/api/v2/product/boost_item", {"item_id": 1})

    assert post_mock.call_count == 2
    assert resultado.sucesso is True
    assert resultado.token_renovado is not None
    assert resultado.token_renovado.access_token == "access-tok-novo"
    assert resultado.token_renovado.refresh_token == "refresh-tok-novo"
    # a chamada seguinte já usa o token renovado
    assert cliente.token.access_token == "access-tok-novo"


@patch("shopee_rodizio.cliente_shopee.requests.post")
def test_chamar_renova_mas_alvo_falha_ainda_devolve_token_renovado_para_persistir(post_mock):
    # renovação OK invalida o refresh_token antigo; se a chamada-alvo falha e o token novo
    # não voltar ao chamador, um reinício do processo perde o refresh_token válido.
    resposta_renovacao = _resposta(
        {
            "access_token": "access-tok-novo",
            "refresh_token": "refresh-tok-novo",
            "expire_in": 14400,
        }
    )
    resposta_erro = _resposta({"error": "item_limit_exceeded", "message": "limite atingido"})
    post_mock.side_effect = [resposta_renovacao, resposta_erro]

    cliente = _cliente(expira_em=None)
    resultado = cliente.chamar("/api/v2/product/boost_item", {"item_id": 1})

    assert resultado.sucesso is False
    assert resultado.token_renovado is not None
    assert resultado.token_renovado.refresh_token == "refresh-tok-novo"


@patch("shopee_rodizio.cliente_shopee.requests.post")
def test_chamar_renova_mas_timeout_no_alvo_ainda_devolve_token_renovado(post_mock):
    resposta_renovacao = _resposta(
        {
            "access_token": "access-tok-novo",
            "refresh_token": "refresh-tok-novo",
            "expire_in": 14400,
        }
    )
    post_mock.side_effect = [resposta_renovacao, requests.exceptions.Timeout("estourou")]

    cliente = _cliente(expira_em=None)
    resultado = cliente.chamar("/api/v2/product/boost_item", {"item_id": 1})

    assert resultado.sucesso is False
    assert resultado.token_renovado is not None
    assert resultado.token_renovado.refresh_token == "refresh-tok-novo"


@patch("shopee_rodizio.cliente_shopee.requests.post")
def test_chamar_timeout_devolve_resultado_de_erro_sem_lancar(post_mock):
    post_mock.side_effect = requests.exceptions.Timeout("tempo esgotado")
    cliente = _cliente()

    resultado = cliente.chamar("/api/v2/product/boost_item", {"item_id": 1})

    assert resultado.sucesso is False
    assert resultado.dados is None
    assert "tempo esgotado" in resultado.erro or "Timeout" in resultado.erro


@patch("shopee_rodizio.cliente_shopee.requests.post")
def test_chamar_erro_conexao_devolve_resultado_de_erro_sem_lancar(post_mock):
    post_mock.side_effect = requests.exceptions.ConnectionError("sem rede")
    cliente = _cliente()

    resultado = cliente.chamar("/api/v2/product/boost_item", {"item_id": 1})

    assert resultado.sucesso is False
    assert resultado.erro is not None


@patch("shopee_rodizio.cliente_shopee.requests.post")
def test_chamar_erro_http_devolve_resultado_de_erro_sem_lancar(post_mock):
    post_mock.return_value = _resposta({"error": "some_error"}, status_ok=False)
    cliente = _cliente()

    resultado = cliente.chamar("/api/v2/product/boost_item", {"item_id": 1})

    assert resultado.sucesso is False
    assert resultado.erro is not None


@patch("shopee_rodizio.cliente_shopee.requests.post")
def test_chamar_corpo_de_erro_da_api_devolve_resultado_de_erro_sem_lancar(post_mock):
    post_mock.return_value = _resposta({"error": "item_limit_exceeded", "message": "limite atingido"})
    cliente = _cliente()

    resultado = cliente.chamar("/api/v2/product/boost_item", {"item_id": 1})

    assert resultado.sucesso is False
    assert "limite atingido" in resultado.erro


@patch("shopee_rodizio.cliente_shopee.requests.post")
def test_chamar_falha_ao_renovar_token_devolve_erro_sem_chamar_endpoint_alvo(post_mock):
    post_mock.return_value = _resposta({"error": "invalid_refresh_token"})
    cliente = _cliente(expira_em=None)

    resultado = cliente.chamar("/api/v2/product/boost_item", {"item_id": 1})

    assert resultado.sucesso is False
    assert post_mock.call_count == 1


@patch("shopee_rodizio.cliente_shopee.requests.get")
def test_chamar_com_metodo_get_manda_params_na_query_sem_corpo(get_mock):
    get_mock.return_value = _resposta({"error": "", "response": {"item": []}})
    cliente = _cliente()

    resultado = cliente.chamar(
        "/api/v2/product/get_item_list",
        {"offset": 0, "page_size": 50, "item_status": "NORMAL"},
        metodo="GET",
    )

    assert resultado.sucesso is True
    get_mock.assert_called_once()
    _, kwargs = get_mock.call_args
    assert kwargs["params"]["offset"] == 0
    assert kwargs["params"]["page_size"] == 50
    assert kwargs["params"]["item_status"] == "NORMAL"
    assert kwargs["params"]["access_token"] == ACCESS_TOKEN


@patch("shopee_rodizio.cliente_shopee.requests.post")
def test_chamar_com_proxy_configurado_manda_proxies_na_chamada(post_mock):
    post_mock.return_value = _resposta({"error": "", "response": {"ok": True}})
    cliente = _cliente(proxy_https="socks5h://127.0.0.1:1080")

    cliente.chamar("/api/v2/product/boost_item", {"item_id": 1})

    _, kwargs = post_mock.call_args
    assert kwargs["proxies"] == {
        "http": "socks5h://127.0.0.1:1080",
        "https": "socks5h://127.0.0.1:1080",
    }


@patch("shopee_rodizio.cliente_shopee.requests.post")
def test_chamar_sem_proxy_configurado_nao_manda_proxies(post_mock):
    post_mock.return_value = _resposta({"error": "", "response": {"ok": True}})
    cliente = _cliente()

    cliente.chamar("/api/v2/product/boost_item", {"item_id": 1})

    _, kwargs = post_mock.call_args
    assert kwargs["proxies"] is None


def test_token_property_reflete_estado_atual_do_cliente():
    cliente = _cliente()
    token = cliente.token
    assert token.access_token == ACCESS_TOKEN
    assert token.refresh_token == REFRESH_TOKEN
    assert replace(token, access_token="x").access_token == "x"
