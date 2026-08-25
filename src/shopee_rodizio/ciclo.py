"""Orquestração de um ciclo de rodízio: seleciona itens, impulsiona cada um via
`boost.py` e grava o resultado em `estado.py`.

Defesa em profundidade (RF-06): erro ao impulsionar um item é logado e registrado como
falha no histórico, mas nunca propaga — mesmo que `boost.impulsionar` já não devesse
lançar, um bug futuro em qualquer módulo abaixo não pode derrubar o serviço 24/7.
"""

from __future__ import annotations

import logging

from . import boost
from .cliente_shopee import ClienteShopee
from .config import Config
from .estado import Estado, registrar_boost
from .selecao import selecionar

_logger = logging.getLogger("shopee_rodizio")


def executar_ciclo(cliente: ClienteShopee, config: Config, estado: Estado) -> Estado:
    """Executa um ciclo: seleciona itens, impulsiona cada um, grava o histórico.

    Devolve o `Estado` atualizado (já persistido em disco). Nunca lança.
    """
    selecionados = selecionar(config.itens, config.ciclo.limite_slots)
    for item in selecionados:
        try:
            resultado = boost.impulsionar(cliente, config, item.id)
            sucesso, mensagem = resultado.sucesso, resultado.mensagem
        except Exception as exc:  # última rede de segurança, ver docstring do módulo
            sucesso, mensagem = False, f"erro inesperado: {exc}"
            _logger.exception("erro inesperado ao impulsionar item %s", item.id)

        estado = registrar_boost(estado, item.id, sucesso, mensagem)
        nivel = logging.INFO if sucesso else logging.WARNING
        _logger.log(nivel, "item %s: %s", item.id, mensagem)

    return estado
