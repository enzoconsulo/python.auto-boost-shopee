import logging

from shopee_rodizio.logging_config import configurar


def _limpar_handlers(logger):
    for handler in list(logger.handlers):
        handler.close()
        logger.removeHandler(handler)


def test_configurar_cria_arquivo_de_log_com_mensagem(tmp_path):
    caminho_log = tmp_path / "shopee-rodizio.log"
    logger = logging.getLogger("shopee_rodizio")
    _limpar_handlers(logger)

    configurar(str(caminho_log))
    try:
        logger.info("mensagem de teste")
        for handler in logger.handlers:
            handler.flush()

        assert caminho_log.exists()
        conteudo = caminho_log.read_text(encoding="utf-8")
        assert "mensagem de teste" in conteudo
        assert "INFO" in conteudo
    finally:
        _limpar_handlers(logger)


def test_configurar_formato_de_linha_inclui_timestamp_nivel_e_mensagem(tmp_path):
    caminho_log = tmp_path / "shopee-rodizio.log"
    logger = logging.getLogger("shopee_rodizio")
    _limpar_handlers(logger)

    configurar(str(caminho_log))
    try:
        logger.warning("algo estranho aconteceu")
        for handler in logger.handlers:
            handler.flush()

        linha = caminho_log.read_text(encoding="utf-8").strip().splitlines()[-1]
        partes = linha.split(" ", 2)
        assert len(partes[0]) == 10 and partes[0].count("-") == 2  # data AAAA-MM-DD
        assert "WARNING" in linha
        assert "algo estranho aconteceu" in linha
    finally:
        _limpar_handlers(logger)


def test_configurar_rotaciona_quando_arquivo_excede_max_bytes(tmp_path):
    caminho_log = tmp_path / "shopee-rodizio.log"
    logger = logging.getLogger("shopee_rodizio")
    _limpar_handlers(logger)

    configurar(str(caminho_log), max_bytes=200, backup_count=2)
    try:
        for i in range(100):
            logger.info("linha de log número %d para forçar rotação por tamanho", i)

        backup = caminho_log.with_name(caminho_log.name + ".1")
        assert backup.exists()
    finally:
        _limpar_handlers(logger)


def test_configurar_cria_diretorio_pai_do_log_se_nao_existir(tmp_path):
    caminho_log = tmp_path / "subdir" / "shopee-rodizio.log"
    logger = logging.getLogger("shopee_rodizio")
    _limpar_handlers(logger)

    configurar(str(caminho_log))
    try:
        logger.info("cria diretorio")
        for handler in logger.handlers:
            handler.flush()

        assert caminho_log.exists()
    finally:
        _limpar_handlers(logger)


def test_configurar_chamado_duas_vezes_nao_duplica_handlers(tmp_path):
    caminho_log = tmp_path / "shopee-rodizio.log"
    logger = logging.getLogger("shopee_rodizio")
    _limpar_handlers(logger)

    configurar(str(caminho_log))
    configurar(str(caminho_log))
    try:
        assert len(logger.handlers) == 1
    finally:
        _limpar_handlers(logger)
