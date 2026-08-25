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


def test_ciclo_com_falha_ao_gravar_historico_nao_escapa(tmp_path):
    # Se gravar o histórico falhar (I/O de SD card instável) DEPOIS de um boost ter renovado
    # o token in-place, a exceção não pode escapar de `executar_ciclo` — senão o loop pularia
    # a persistência do token novo (RF-02). `executar_ciclo` promete "Nunca lança".
    config = _config(_itens(1, 2), limite_slots=2)
    estado = _estado(tmp_path)

    with (
        patch.object(
            boost, "impulsionar", return_value=boost.ResultadoBoost(sucesso=True, mensagem="ok")
        ),
        patch("shopee_rodizio.ciclo.registrar_boost", side_effect=OSError("disco cheio")),
    ):
        resultado = executar_ciclo(cliente=object(), config=config, estado=estado)

    # não lançou; devolveu o Estado (inalterado, pois nenhuma gravação vingou)
    assert resultado is estado


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


# --- Persistência do token renovado (RF-02) ---------------------------------------------


class _ClienteFake:
    """Cliente mínimo para o loop: só precisa de um atributo `token` mutável, que o mock de
    `boost.impulsionar` troca para simular a renovação in-place feita por `cliente.chamar`."""

    def __init__(self, token):
        self.token = token


def test_persistir_e_carregar_token_faz_roundtrip(tmp_path):
    from datetime import UTC, datetime

    from shopee_rodizio.__main__ import _carregar_token, _persistir_token
    from shopee_rodizio.cliente_shopee import Token

    caminho = tmp_path / "token.json"
    token = Token(
        access_token="at-novo",
        refresh_token="rt-novo",
        expira_em=datetime(2030, 1, 1, tzinfo=UTC),
    )
    _persistir_token(caminho, token)

    assert _carregar_token(caminho) == token


def test_carregar_token_inexistente_devolve_none(tmp_path):
    from shopee_rodizio.__main__ import _carregar_token

    assert _carregar_token(tmp_path / "nao-existe.json") is None


def test_cliente_de_usa_token_persistido_em_vez_do_config_apos_restart():
    from datetime import UTC, datetime

    from shopee_rodizio.__main__ import _cliente_de
    from shopee_rodizio.cliente_shopee import Token

    config = _config(_itens(1))  # config traz access_token="tok", refresh_token="ref"
    token_persistido = Token(
        access_token="at-renovado",
        refresh_token="rt-renovado",
        expira_em=datetime(2030, 1, 1, tzinfo=UTC),
    )

    cliente = _cliente_de(config, token_persistido)

    assert cliente.token == token_persistido  # não o "tok"/"ref" do config.toml


def test_cliente_de_sem_token_persistido_usa_config():
    from shopee_rodizio.__main__ import _cliente_de

    config = _config(_itens(1))
    cliente = _cliente_de(config, None)

    assert cliente.token.access_token == "tok"
    assert cliente.token.refresh_token == "ref"
    assert cliente.token.expira_em is None


def test_loop_persiste_token_renovado_apos_ciclo(tmp_path, _config_arquivo):
    from datetime import UTC, datetime

    from shopee_rodizio.__main__ import _carregar_token, executar_loop
    from shopee_rodizio.cliente_shopee import Token

    token_novo = Token(
        access_token="at-renovado",
        refresh_token="rt-renovado",
        expira_em=datetime(2030, 1, 1, tzinfo=UTC),
    )
    fake = _ClienteFake(Token("tok", "ref", None))

    def _impulsionar(cliente, config, item_id):
        cliente.token = token_novo  # simula a renovação in-place feita por cliente.chamar
        return boost.ResultadoBoost(sucesso=True, mensagem="ok")

    with (
        patch("shopee_rodizio.__main__.time.sleep"),
        patch("shopee_rodizio.__main__._cliente_de", return_value=fake),
        patch.object(boost, "impulsionar", side_effect=_impulsionar),
    ):
        executar_loop(str(_config_arquivo), max_iteracoes=1)

    caminho_token = _config_arquivo.parent / "token.json"
    assert _carregar_token(caminho_token) == token_novo


def test_loop_nao_grava_token_quando_nao_ha_renovacao(tmp_path, _config_arquivo):
    from shopee_rodizio.__main__ import executar_loop

    fake = _ClienteFake(None)  # token nunca muda: nenhuma renovação ocorre

    with (
        patch("shopee_rodizio.__main__.time.sleep"),
        patch("shopee_rodizio.__main__._cliente_de", return_value=fake),
        patch.object(
            boost, "impulsionar", return_value=boost.ResultadoBoost(sucesso=True, mensagem="ok")
        ),
    ):
        executar_loop(str(_config_arquivo), max_iteracoes=2)

    assert not (_config_arquivo.parent / "token.json").exists()


def test_loop_primeira_subida_sem_renovacao_nao_grava_token_com_cliente_real(
    tmp_path, _config_arquivo
):
    # Regressão do achado [menor]: com o `_cliente_de` REAL (não mockado) e sem `token.json`
    # prévio, o cliente sobe com o token do config; se nenhum ciclo renova, o loop não pode
    # gravar um `token.json` redundante ao fim da primeira volta.
    from shopee_rodizio.__main__ import executar_loop

    with (
        patch("shopee_rodizio.__main__.time.sleep"),
        patch.object(
            boost, "impulsionar", return_value=boost.ResultadoBoost(sucesso=True, mensagem="ok")
        ),
    ):
        executar_loop(str(_config_arquivo), max_iteracoes=1)

    assert not (_config_arquivo.parent / "token.json").exists()
