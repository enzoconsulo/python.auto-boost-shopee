"""Testes de `catalogo.py` com um cliente fake (sem rede) e do script que o consome."""

from __future__ import annotations

import importlib.util
import tomllib
from pathlib import Path
from unittest.mock import patch

import pytest

from shopee_rodizio.catalogo import (
    PATH_INFO_ITENS,
    PATH_LISTA_ITENS,
    PATH_MODELOS,
    ErroCatalogo,
    ItemCatalogo,
    buscar_detalhes,
    buscar_item_ids_ativos,
    extrair_item,
)
from shopee_rodizio.cliente_shopee import Resultado


class _ClienteFake:
    """Responde por path; registra as chamadas feitas."""

    def __init__(self, respostas: dict[str, list[Resultado]]):
        self._respostas = {path: list(lista) for path, lista in respostas.items()}
        self.chamadas: list[tuple[str, dict]] = []

    def chamar(self, path: str, params: dict, *, metodo: str = "POST") -> Resultado:
        assert metodo == "GET"
        self.chamadas.append((path, params))
        return self._respostas[path].pop(0)


def _ok(response: dict) -> Resultado:
    return Resultado(sucesso=True, dados={"error": "", "response": response})


ITEM_SIMPLES = {
    "item_id": 1,
    "item_name": "Filamento  PETG\n1kg",
    "item_status": "NORMAL",
    "has_model": False,
    "image": {"image_url_list": ["https://cf.shopee.com.br/file/a", "https://x/b"]},
    "price_info": [{"current_price": 89.9, "original_price": 99.9}],
    "stock_info_v2": {"summary_info": {"total_reserved_stock": 0, "total_available_stock": 7}},
}
ITEM_COM_VARIACAO = {
    "item_id": 2,
    "item_name": "Ursinho",
    "item_status": "NORMAL",
    "has_model": True,
    "image": {"image_url_list": []},
}


def test_lista_ids_ativos_paginando_ate_o_fim():
    cliente = _ClienteFake(
        {
            PATH_LISTA_ITENS: [
                _ok({"item": [{"item_id": 1}, {"item_id": 2}], "has_next_page": True}),
                _ok({"item": [{"item_id": 3}], "has_next_page": False}),
            ]
        }
    )

    assert buscar_item_ids_ativos(cliente) == [1, 2, 3]
    assert [params["offset"] for _, params in cliente.chamadas] == [0, 50]


def test_falha_em_qualquer_pagina_da_listagem_lanca_erro_catalogo():
    cliente = _ClienteFake(
        {
            PATH_LISTA_ITENS: [
                _ok({"item": [{"item_id": 1}], "has_next_page": True}),
                Resultado(sucesso=False, erro="error_auth"),
            ]
        }
    )

    with pytest.raises(ErroCatalogo, match="error_auth"):
        buscar_item_ids_ativos(cliente)


def test_extrai_nome_imagem_preco_estoque_e_status():
    item = extrair_item(ITEM_SIMPLES)

    assert item == ItemCatalogo(
        id=1,
        nome="Filamento PETG 1kg",
        imagem_url="https://cf.shopee.com.br/file/a",
        preco_min=89.9,
        preco_max=89.9,
        estoque=7,
        status="NORMAL",
        tem_variacoes=False,
    )


def test_estoque_no_formato_legado_stock_info_tambem_e_lido():
    bruto = {**ITEM_SIMPLES, "stock_info_v2": None, "stock_info": [{"normal_stock": 12}]}

    assert extrair_item(bruto).estoque == 12


def test_item_sem_preco_nem_estoque_vira_none_sem_erro():
    item = extrair_item({"item_id": 9, "item_name": "x"})

    assert (item.preco_min, item.estoque, item.imagem_url) == (None, None, None)


def test_variacoes_so_sao_buscadas_quando_pedido_e_agregam_preco_e_estoque():
    modelos = _ok(
        {
            "model": [
                {"price_info": [{"current_price": 30.0}], "stock_info": [{"normal_stock": 2}]},
                {"price_info": [{"current_price": 45.5}], "stock_info": [{"normal_stock": 3}]},
            ]
        }
    )
    info = _ok({"item_list": [ITEM_SIMPLES, ITEM_COM_VARIACAO]})

    sem = buscar_detalhes(_ClienteFake({PATH_INFO_ITENS: [info]}), [1, 2])
    cliente = _ClienteFake({PATH_INFO_ITENS: [info], PATH_MODELOS: [modelos]})
    com = buscar_detalhes(cliente, [1, 2], buscar_variacoes=True)

    assert sem[2].preco_min is None
    assert (com[2].preco_min, com[2].preco_max, com[2].estoque) == (30.0, 45.5, 5)
    assert [path for path, _ in cliente.chamadas].count(PATH_MODELOS) == 1  # só o item 2


def test_lote_de_detalhes_que_falha_e_pulado_sem_lancar():
    cliente = _ClienteFake({PATH_INFO_ITENS: [Resultado(sucesso=False, erro="timeout")]})

    assert buscar_detalhes(cliente, [1, 2]) == {}


def test_detalhes_em_lotes_de_50():
    ids = list(range(1, 121))
    cliente = _ClienteFake({PATH_INFO_ITENS: [_ok({"item_list": []})] * 3})

    buscar_detalhes(cliente, ids)

    assert [len(p["item_id_list"].split(",")) for _, p in cliente.chamadas] == [50, 50, 20]


# --- scripts/sincronizar_itens.py consome o módulo ------------------------------------------


def _script_sincronizar():
    caminho = Path(__file__).resolve().parent.parent / "scripts" / "sincronizar_itens.py"
    spec = importlib.util.spec_from_file_location("sincronizar_itens", caminho)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def test_sincronizar_preserva_pesos_e_secao_rede_depois_dos_itens(tmp_path):
    config = tmp_path / "config.toml"
    config.write_text(
        f"""[shopee]
partner_id = 1
partner_key = "k"
shop_id = 9
access_token = "a"
refresh_token = "r"

[ciclo]
intervalo_horas = 4
limite_slots = 5
endpoint_boost = "/api/v2/product/boost_item"

[caminhos]
log = "{(tmp_path / 'l.log').as_posix()}"
estado = "{(tmp_path / 'estado.json').as_posix()}"

[[itens]]
id = 1
peso = 40

[[itens]]
id = 99
peso = 5

[rede]
proxy_https = "socks5h://127.0.0.1:1080"
""",
        encoding="utf-8",
    )
    cliente = _ClienteFake(
        {
            PATH_LISTA_ITENS: [_ok({"item": [{"item_id": 1}, {"item_id": 2}]})],
            PATH_INFO_ITENS: [_ok({"item_list": [ITEM_SIMPLES, ITEM_COM_VARIACAO]})],
        }
    )
    script = _script_sincronizar()

    with patch.object(script, "cliente_da_config", return_value=cliente):
        assert script.main([str(config), "--peso-padrao", "3"]) == 0

    dados = tomllib.loads(config.read_text(encoding="utf-8"))
    assert dados["itens"] == [{"id": 1, "peso": 40}, {"id": 2, "peso": 3}]
    assert dados["rede"] == {"proxy_https": "socks5h://127.0.0.1:1080"}
    assert "id = 1  # Filamento PETG 1kg" in config.read_text(encoding="utf-8")


# --- cache em disco -------------------------------------------------------------------------


def test_cache_roundtrip_e_vencimento(tmp_path):
    from datetime import UTC, datetime, timedelta

    from shopee_rodizio.catalogo import CacheCatalogo, carregar_cache, gravar_cache

    agora = datetime(2026, 10, 19, 12, tzinfo=UTC)
    cache = CacheCatalogo(atualizado_em=agora, itens=(extrair_item(ITEM_SIMPLES),))

    gravar_cache(tmp_path / "catalogo.json", cache)
    relido = carregar_cache(tmp_path / "catalogo.json")

    assert relido == cache
    assert not relido.vencido(24, agora + timedelta(hours=23))
    assert relido.vencido(24, agora + timedelta(hours=24))


def test_cache_ausente_ou_corrompido_vira_vazio_e_vencido(tmp_path):
    from shopee_rodizio.catalogo import carregar_cache

    (tmp_path / "corrompido.json").write_text("{nao é json", encoding="utf-8")

    for caminho in (tmp_path / "nao-existe.json", tmp_path / "corrompido.json"):
        cache = carregar_cache(caminho)
        assert cache.itens == ()
        assert cache.vencido(24)


def test_baixar_catalogo_mantem_item_ativo_sem_detalhe():
    from shopee_rodizio.catalogo import baixar_catalogo

    cliente = _ClienteFake(
        {
            PATH_LISTA_ITENS: [_ok({"item": [{"item_id": 1}, {"item_id": 5}]})],
            PATH_INFO_ITENS: [_ok({"item_list": [ITEM_SIMPLES]})],
        }
    )

    cache = baixar_catalogo(cliente, buscar_variacoes=False, pausa=0)

    assert [item.id for item in cache.itens] == [1, 5]
    assert cache.itens[1].nome == ""
