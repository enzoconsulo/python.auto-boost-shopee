"""Testes da regravação do `[[itens]]` do config.toml (`config.py`) e de `arquivo.py`."""

from __future__ import annotations

import os
import tomllib

import pytest

from shopee_rodizio.arquivo import gravar_atomico
from shopee_rodizio.config import (
    ConfigError,
    ConflitoConfig,
    atualizar_itens,
    carregar_config,
    gravar_config,
    nomes_nos_comentarios,
    regenerar_bloco_itens,
    versao_config,
)

# Mesma forma do config.toml de produção: [rede] DEPOIS dos [[itens]], com comentário.
TOML_PRODUCAO = """# cabeçalho do usuário
[shopee]
partner_id = 1
partner_key = "chave"
shop_id = 99
access_token = "tok"
refresh_token = "ref"

[ciclo]
intervalo_horas = 4
limite_slots = 5
endpoint_boost = "/api/v2/product/boost_item"

[caminhos]
log = "shopee-rodizio.log"
estado = "estado.json"

# Um bloco [[itens]] por anúncio participante do rodízio.

[[itens]]
id = 111  # Filamento PETG
peso = 40

[[itens]]
id = 222  # Ursinho Decorativo
peso = 30

# Seção opcional — túnel SSH
[rede]
proxy_https = "socks5h://127.0.0.1:1080"
"""


def test_regenerar_preserva_secao_depois_dos_itens_e_seu_comentario():
    novo = regenerar_bloco_itens(TOML_PRODUCAO, [(111, 5), (333, 1)], {111: "Filamento PETG"})

    dados = tomllib.loads(novo)
    assert dados["rede"] == {"proxy_https": "socks5h://127.0.0.1:1080"}
    assert dados["itens"] == [{"id": 111, "peso": 5}, {"id": 333, "peso": 1}]
    assert "# Seção opcional — túnel SSH\n[rede]" in novo
    assert "# Um bloco [[itens]] por anúncio participante do rodízio." in novo
    assert "id = 111  # Filamento PETG" in novo


def test_regenerar_sem_itens_anexa_no_fim():
    sem_itens = TOML_PRODUCAO.split("[[itens]]")[0]

    novo = regenerar_bloco_itens(sem_itens, [(7, 2)])

    assert tomllib.loads(novo)["itens"] == [{"id": 7, "peso": 2}]


def test_regenerar_junta_blocos_de_itens_separados_por_outra_secao():
    texto = TOML_PRODUCAO + "\n[[itens]]\nid = 444\npeso = 1\n"

    novo = regenerar_bloco_itens(texto, [(1, 1)])

    dados = tomllib.loads(novo)
    assert dados["itens"] == [{"id": 1, "peso": 1}]
    assert dados["rede"]["proxy_https"] == "socks5h://127.0.0.1:1080"


def test_regenerar_nome_com_quebra_de_linha_nao_quebra_o_toml():
    novo = regenerar_bloco_itens(TOML_PRODUCAO, [(111, 1)], {111: "linha 1\nlinha 2"})

    assert tomllib.loads(novo)["itens"] == [{"id": 111, "peso": 1}]


def test_nomes_nos_comentarios_le_o_que_a_regeneracao_escreve():
    assert nomes_nos_comentarios(TOML_PRODUCAO) == {111: "Filamento PETG", 222: "Ursinho Decorativo"}


def test_atualizar_itens_grava_e_preserva_nomes_existentes(tmp_path):
    caminho = tmp_path / "config.toml"
    caminho.write_text(TOML_PRODUCAO, encoding="utf-8")

    versao = atualizar_itens(caminho, [(222, 7)])

    texto = caminho.read_text(encoding="utf-8")
    assert versao == versao_config(texto)
    assert "id = 222  # Ursinho Decorativo\npeso = 7" in texto
    assert carregar_config(caminho).rede.proxy_https == "socks5h://127.0.0.1:1080"


def test_atualizar_itens_com_versao_desatualizada_lanca_conflito_e_nao_grava(tmp_path):
    caminho = tmp_path / "config.toml"
    caminho.write_text(TOML_PRODUCAO, encoding="utf-8")
    versao_lida = versao_config(TOML_PRODUCAO)
    caminho.write_text(TOML_PRODUCAO.replace("peso = 40", "peso = 41"), encoding="utf-8")

    with pytest.raises(ConflitoConfig):
        atualizar_itens(caminho, [(111, 1)], versao_esperada=versao_lida)

    assert "peso = 41" in caminho.read_text(encoding="utf-8")


def test_atualizar_itens_sem_nenhum_item_e_recusado_sem_tocar_no_arquivo(tmp_path):
    caminho = tmp_path / "config.toml"
    caminho.write_text(TOML_PRODUCAO, encoding="utf-8")

    with pytest.raises(ConfigError):
        atualizar_itens(caminho, [])

    assert caminho.read_text(encoding="utf-8") == TOML_PRODUCAO


def test_gravar_config_recusa_texto_que_muda_outra_secao(tmp_path):
    caminho = tmp_path / "config.toml"
    caminho.write_text(TOML_PRODUCAO, encoding="utf-8")

    with pytest.raises(ConfigError):
        gravar_config(caminho, TOML_PRODUCAO.replace('"chave"', '"outra"'))

    assert caminho.read_text(encoding="utf-8") == TOML_PRODUCAO


def test_gravar_atomico_nao_deixa_temporario_e_preserva_modo(tmp_path):
    caminho = tmp_path / "arquivo.txt"
    caminho.write_text("antigo", encoding="utf-8")
    os.chmod(caminho, 0o640)
    modo_antes = caminho.stat().st_mode

    gravar_atomico(caminho, "novo")

    assert caminho.read_text(encoding="utf-8") == "novo"
    assert caminho.stat().st_mode == modo_antes
    assert [p.name for p in tmp_path.iterdir()] == ["arquivo.txt"]


def test_config_sem_secao_painel_usa_padroes(tmp_path):
    caminho = tmp_path / "config.toml"
    caminho.write_text(TOML_PRODUCAO, encoding="utf-8")

    painel = carregar_config(caminho).painel

    assert painel.porta == 8790
    assert painel.senha_hash is None
    assert "192.168.0.0/16" in painel.redes_permitidas


def test_config_com_porta_do_painel_invalida_e_recusada(tmp_path):
    caminho = tmp_path / "config.toml"
    caminho.write_text(TOML_PRODUCAO + "\n[painel]\nporta = 70000\n", encoding="utf-8")

    with pytest.raises(ConfigError, match="painel.porta"):
        carregar_config(caminho)
