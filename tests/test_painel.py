"""Testes do painel web (`painel.py`): servidor real numa thread, sem rede externa."""

from __future__ import annotations

import base64
import http.client
import json
import threading
import tomllib
from datetime import UTC, datetime
from unittest.mock import patch

import pytest

from shopee_rodizio import catalogo, painel
from shopee_rodizio.catalogo import CacheCatalogo, ItemCatalogo, gravar_cache
from shopee_rodizio.config import definir_senha_painel

SENHA = "segredo-do-painel"
PARTNER_KEY = "pk-super-secreta"
ACCESS_TOKEN = "at-super-secreto"
REFRESH_TOKEN = "rt-super-secreto"


def _toml(tmp_path, senha_hash: str | None) -> str:
    painel_secao = f'\n[painel]\nsenha_hash = "{senha_hash}"\n' if senha_hash else ""
    return f"""[shopee]
partner_id = 1
partner_key = "{PARTNER_KEY}"
shop_id = 99
access_token = "{ACCESS_TOKEN}"
refresh_token = "{REFRESH_TOKEN}"

[ciclo]
intervalo_horas = 4
limite_slots = 2
endpoint_boost = "/api/v2/product/boost_item"

[caminhos]
log = "{(tmp_path / 'r.log').as_posix()}"
estado = "{(tmp_path / 'estado.json').as_posix()}"

[[itens]]
id = 1  # Filamento
peso = 40

[[itens]]
id = 2
peso = 30

[rede]
proxy_https = "socks5h://127.0.0.1:1080"
{painel_secao}"""


@pytest.fixture
def ambiente(tmp_path):
    config = tmp_path / "config.toml"
    # iterações baixas só para o teste ser rápido; o hash carrega o número de iterações
    config.write_text(_toml(tmp_path, painel.gerar_hash_senha(SENHA, 1000)), encoding="utf-8")
    gravar_cache(
        tmp_path / "catalogo.json",
        CacheCatalogo(
            atualizado_em=datetime.now(UTC),
            itens=(
                ItemCatalogo(id=1, nome="Filamento PETG", estoque=3, status="NORMAL"),
                ItemCatalogo(id=3, nome="Gancho", preco_min=19.9, preco_max=19.9),
            ),
        ),
    )
    servidor = painel.criar_servidor(config, "127.0.0.1", 0)
    thread = threading.Thread(target=servidor.serve_forever, kwargs={"poll_interval": 0.05})
    thread.start()
    yield config, servidor.server_address[1]
    servidor.shutdown()
    servidor.server_close()
    thread.join()


def _pedir(porta, metodo, caminho, *, senha=SENHA, corpo=None, cabecalhos=None, host=None):
    conexao = http.client.HTTPConnection("127.0.0.1", porta, timeout=10)
    h = {"Host": host or f"127.0.0.1:{porta}"}
    if senha is not None:
        h["Authorization"] = "Basic " + base64.b64encode(f"eu:{senha}".encode()).decode()
    h.update(cabecalhos or {})
    dados = json.dumps(corpo).encode() if corpo is not None else None
    conexao.request(metodo, caminho, body=dados, headers=h)
    resposta = conexao.getresponse()
    return resposta.status, resposta.read().decode("utf-8"), resposta


_POST = {"Content-Type": "application/json", "X-Painel": "1"}


def test_senha_hash_roundtrip_e_senha_errada():
    senha_hash = painel.gerar_hash_senha("abc", 1000)

    assert painel.verificar_senha("abc", senha_hash)
    assert not painel.verificar_senha("abd", senha_hash)
    assert not painel.verificar_senha("abc", "lixo")


@pytest.mark.parametrize(
    ("ip", "permitido"),
    [
        ("192.168.2.50", True),
        ("10.1.2.3", True),
        ("172.20.0.9", True),
        ("127.0.0.1", True),
        ("100.72.137.10", False),  # Tailscale (CGNAT) fica de fora
        ("8.8.8.8", False),
        ("::ffff:192.168.2.50", True),
        ("2804:14c::1", False),
    ],
)
def test_so_clientes_da_rede_local_sao_atendidos(ip, permitido):
    from shopee_rodizio.config import REDES_LAN_PADRAO

    assert painel.cliente_permitido(ip, REDES_LAN_PADRAO) is permitido


def test_host_precisa_ser_ip_ou_nome_da_maquina_contra_dns_rebinding():
    nomes = ("bigtreetech-cb1", "bigtreetech-cb1.local", "localhost")

    assert painel.host_permitido("192.168.2.112:8790", nomes)
    assert painel.host_permitido("bigtreetech-cb1.local:8790", nomes)
    assert not painel.host_permitido("evil.example.com:8790", nomes)
    assert not painel.host_permitido(None, nomes)


def test_sem_senha_responde_401_e_nao_entrega_nada(ambiente):
    _, porta = ambiente

    status, corpo, resposta = _pedir(porta, "GET", "/api/estado", senha=None)

    assert status == 401
    assert "Basic" in resposta.getheader("WWW-Authenticate")
    assert "Filamento" not in corpo


def test_senha_errada_responde_401(ambiente):
    _, porta = ambiente

    status, _, _ = _pedir(porta, "GET", "/", senha="errada")

    assert status == 401


def test_host_estranho_e_recusado(ambiente):
    _, porta = ambiente

    status, _, _ = _pedir(porta, "GET", "/", host="evil.example.com")

    assert status == 403


def test_pagina_e_estado_sem_nenhuma_credencial(ambiente):
    _, porta = ambiente

    status_pagina, pagina, resposta = _pedir(porta, "GET", "/")
    status, corpo, _ = _pedir(porta, "GET", "/api/estado")

    assert status_pagina == 200
    assert "frame-ancestors 'none'" in resposta.getheader("Content-Security-Policy")
    assert status == 200
    for segredo in (PARTNER_KEY, ACCESS_TOKEN, REFRESH_TOKEN, "pbkdf2"):
        assert segredo not in corpo
        assert segredo not in pagina
    dados = json.loads(corpo)
    assert dados["rodizio"] == [{"id": 1, "peso": 40}, {"id": 2, "peso": 30}]
    assert [i["nome"] for i in dados["catalogo"]["itens"]] == ["Filamento PETG", "Gancho"]
    assert dados["nomes_config"] == {"1": "Filamento"}


def test_post_sem_header_do_painel_e_recusado_contra_csrf(ambiente):
    config, porta = ambiente
    antes = config.read_text(encoding="utf-8")

    status, _, _ = _pedir(
        porta, "POST", "/api/pesos", corpo={"itens": []},
        cabecalhos={"Content-Type": "application/json"},
    )

    assert status == 403
    assert config.read_text(encoding="utf-8") == antes


def test_gravar_pesos_atualiza_config_e_preserva_o_resto(ambiente):
    config, porta = ambiente
    _, corpo, _ = _pedir(porta, "GET", "/api/estado")
    versao = json.loads(corpo)["versao"]

    status, corpo, _ = _pedir(
        porta, "POST", "/api/pesos", cabecalhos=_POST,
        corpo={"versao": versao, "itens": [{"id": 1, "peso": 5}, {"id": 3, "peso": 2}]},
    )

    assert status == 200, corpo
    dados = tomllib.loads(config.read_text(encoding="utf-8"))
    assert dados["itens"] == [{"id": 1, "peso": 5}, {"id": 3, "peso": 2}]
    assert dados["shopee"]["partner_key"] == PARTNER_KEY
    assert dados["rede"]["proxy_https"] == "socks5h://127.0.0.1:1080"
    assert "id = 3  # Gancho" in config.read_text(encoding="utf-8")
    assert json.loads(corpo)["rodizio"] == [{"id": 1, "peso": 5}, {"id": 3, "peso": 2}]


def test_gravar_com_versao_antiga_responde_409_e_nao_grava(ambiente):
    config, porta = ambiente
    config.write_text(
        config.read_text(encoding="utf-8").replace("peso = 30", "peso = 31"), encoding="utf-8"
    )
    antes = config.read_text(encoding="utf-8")

    status, _, _ = _pedir(
        porta, "POST", "/api/pesos", cabecalhos=_POST,
        corpo={"versao": "versao-velha", "itens": [{"id": 1, "peso": 5}]},
    )

    assert status == 409
    assert config.read_text(encoding="utf-8") == antes


@pytest.mark.parametrize(
    "itens",
    [
        [],
        [{"id": 1, "peso": 0}],
        [{"id": 1, "peso": 1001}],
        [{"id": 1, "peso": "5"}],
        [{"id": 1, "peso": 5}, {"id": 1, "peso": 6}],
        [{"id": 777, "peso": 5}],  # fora do catálogo e do rodízio
    ],
)
def test_pedido_invalido_responde_400_sem_tocar_no_config(ambiente, itens):
    config, porta = ambiente
    antes = config.read_text(encoding="utf-8")

    status, _, _ = _pedir(porta, "POST", "/api/pesos", cabecalhos=_POST, corpo={"itens": itens})

    assert status == 400
    assert config.read_text(encoding="utf-8") == antes


def test_atualizar_catalogo_usa_cliente_do_token_json_e_respeita_intervalo_minimo(ambiente):
    _, porta = ambiente
    novo = CacheCatalogo(atualizado_em=datetime.now(UTC), itens=(ItemCatalogo(id=9, nome="Novo"),))

    with (
        patch.object(painel.armazem_token, "cliente_da_config") as fabrica,
        patch.object(catalogo, "baixar_catalogo", return_value=novo) as baixar,
    ):
        status, corpo, _ = _pedir(porta, "POST", "/api/catalogo/atualizar", cabecalhos=_POST)
        _pedir(porta, "POST", "/api/catalogo/atualizar", cabecalhos=_POST)

    assert status == 200
    assert [i["id"] for i in json.loads(corpo)["catalogo"]["itens"]] == [9]
    assert fabrica.call_count == 1
    assert baixar.call_count == 1  # segundo pedido dentro de 60 s não bate na API


def test_falha_ao_atualizar_catalogo_mantem_cache_e_mostra_erro(ambiente):
    _, porta = ambiente

    with (
        patch.object(painel.armazem_token, "cliente_da_config"),
        patch.object(catalogo, "baixar_catalogo", side_effect=catalogo.ErroCatalogo("403")),
    ):
        status, corpo, _ = _pedir(porta, "POST", "/api/catalogo/atualizar", cabecalhos=_POST)

    dados = json.loads(corpo)
    assert status == 200
    assert "403" in dados["catalogo"]["erro"]
    assert len(dados["catalogo"]["itens"]) == 2


def test_sem_senha_configurada_o_painel_nao_atende(tmp_path):
    config = tmp_path / "config.toml"
    config.write_text(_toml(tmp_path, None), encoding="utf-8")
    servidor = painel.criar_servidor(config, "127.0.0.1", 0)
    thread = threading.Thread(target=servidor.serve_forever, kwargs={"poll_interval": 0.05})
    thread.start()
    try:
        status, corpo, _ = _pedir(servidor.server_address[1], "GET", "/api/estado")
    finally:
        servidor.shutdown()
        servidor.server_close()
        thread.join()

    assert status == 503
    assert "definir_senha_painel" in corpo


def test_definir_senha_cria_secao_painel_sem_mexer_no_resto(tmp_path):
    config = tmp_path / "config.toml"
    config.write_text(_toml(tmp_path, None), encoding="utf-8")

    definir_senha_painel(config, "pbkdf2_sha256$1$aa$bb")
    definir_senha_painel(config, "pbkdf2_sha256$1$cc$dd")

    dados = tomllib.loads(config.read_text(encoding="utf-8"))
    assert dados["painel"] == {"senha_hash": "pbkdf2_sha256$1$cc$dd"}
    assert dados["rede"]["proxy_https"] == "socks5h://127.0.0.1:1080"
    assert dados["itens"] == [{"id": 1, "peso": 40}, {"id": 2, "peso": 30}]


def test_relatorio_responde_agregados_com_nomes_e_sem_credenciais(ambiente):
    config, porta = ambiente
    (config.parent / "estado.json").write_text(
        json.dumps(
            {
                "historico": [
                    {"item_id": 1, "timestamp": datetime.now(UTC).isoformat(), "sucesso": True,
                     "mensagem": "impulsionado com sucesso"}
                ]
            }
        ),
        encoding="utf-8",
    )

    status, corpo, _ = _pedir(porta, "GET", "/api/relatorio?dias=30")

    dados = json.loads(corpo)
    assert status == 200
    assert dados["relatorio"]["dias"] == 30
    assert [i["id"] for i in dados["agora"]["no_ar"]] == [1]
    assert dados["nomes"]["1"] == "Filamento PETG"
    for segredo in (PARTNER_KEY, ACCESS_TOKEN, REFRESH_TOKEN, "pbkdf2"):
        assert segredo not in corpo


def test_relatorio_exige_senha(ambiente):
    _, porta = ambiente

    status, _, _ = _pedir(porta, "GET", "/api/relatorio", senha=None)

    assert status == 401
