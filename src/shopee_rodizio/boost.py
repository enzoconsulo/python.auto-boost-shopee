"""Chamada do endpoint de impulsionamento de UM item, via `cliente_shopee.py`.

O caminho do endpoint vem de `config.ciclo.endpoint_boost` (RF-04) — não é fixo aqui,
porque a documentação pública não confirma esse caminho sem login (ver
`_gestao/DECISOES.md`, 2026-08-24). O payload (`item_id_list`) foi confirmado contra conta
real em 2026-08-25 (ver `_gestao/DECISOES.md`): `v2.product.boost_item` espera uma LISTA de
itens, não um `item_id` singular — `shop_id` não entra no corpo, já vai assinado na query.
"""

from __future__ import annotations

from dataclasses import dataclass

from .cliente_shopee import ClienteShopee
from .config import Config


@dataclass(frozen=True)
class ResultadoBoost:
    sucesso: bool
    mensagem: str


def impulsionar(cliente: ClienteShopee, config: Config, item_id: int) -> ResultadoBoost:
    """Chama o endpoint de impulsionamento configurado para `item_id`.

    Nunca lança: erro do cliente (rede, HTTP, corpo de erro da API) vira
    `ResultadoBoost(sucesso=False, ...)`.
    """
    resultado = cliente.chamar(
        config.ciclo.endpoint_boost,
        {"item_id_list": [item_id]},
    )
    if not resultado.sucesso:
        return ResultadoBoost(sucesso=False, mensagem=resultado.erro or "erro desconhecido")
    return ResultadoBoost(sucesso=True, mensagem="impulsionado com sucesso")
