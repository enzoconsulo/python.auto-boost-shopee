from pathlib import Path

from shopee_rodizio.estado import carregar_estado, historico_recente, registrar_boost


def test_primeira_execucao_sem_arquivo_previo_nao_lanca_erro(tmp_path):
    estado = carregar_estado(tmp_path / "estado.json")

    assert estado.historico == []


def test_registrar_boost_grava_e_carregar_estado_relê_o_historico(tmp_path):
    caminho = tmp_path / "estado.json"
    estado = carregar_estado(caminho)

    estado = registrar_boost(estado, item_id=123, sucesso=True, mensagem="ok")

    relido = carregar_estado(caminho)
    assert len(relido.historico) == 1
    registro = relido.historico[0]
    assert registro.item_id == 123
    assert registro.sucesso is True
    assert registro.mensagem == "ok"
    assert registro.timestamp


def test_registrar_boost_acumula_multiplos_registros(tmp_path):
    caminho = tmp_path / "estado.json"
    estado = carregar_estado(caminho)

    estado = registrar_boost(estado, item_id=1, sucesso=True, mensagem="ok")
    estado = registrar_boost(estado, item_id=2, sucesso=False, mensagem="erro de rede")

    relido = carregar_estado(caminho)
    assert len(relido.historico) == 2
    assert relido.historico[0].item_id == 1
    assert relido.historico[1].item_id == 2
    assert relido.historico[1].sucesso is False


def test_escrita_usa_arquivo_temporario_e_nao_sobra_tmp_orfao(tmp_path):
    caminho = tmp_path / "estado.json"
    estado = carregar_estado(caminho)

    registrar_boost(estado, item_id=1, sucesso=True, mensagem="ok")

    assert caminho.exists()
    tmps = list(tmp_path.glob("*.tmp"))
    assert tmps == []


def test_historico_recente_filtra_por_item_id(tmp_path):
    caminho = tmp_path / "estado.json"
    estado = carregar_estado(caminho)

    estado = registrar_boost(estado, item_id=1, sucesso=True, mensagem="ok")
    estado = registrar_boost(estado, item_id=2, sucesso=True, mensagem="ok")
    estado = registrar_boost(estado, item_id=1, sucesso=False, mensagem="falhou")

    recentes = historico_recente(estado, 1)

    assert len(recentes) == 2
    assert all(r.item_id == 1 for r in recentes)


def test_historico_recente_sem_registros_devolve_lista_vazia(tmp_path):
    estado = carregar_estado(tmp_path / "estado.json")

    assert historico_recente(estado, 999) == []
