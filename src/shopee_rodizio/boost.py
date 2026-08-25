"""Chamada do endpoint de impulsionamento de UM item, via `cliente_shopee.py`.

O caminho do endpoint vem de `config.ciclo.endpoint_boost` (RF-04) — não é fixo aqui,
porque a documentação pública não confirma esse caminho sem login (ver
`_gestao/DECISOES.md`, 2026-08-24). Os nomes de parâmetro do payload (`item_id`,
`shop_id`) são um palpite plausível para um endpoint `v2.product.boost_item`-like; podem
precisar de ajuste contra a conta real — é o que a T-010 (smoke-test) confirma.
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
        {"item_id": item_id, "shop_id": config.shopee.shop_id},
    )
    if not resultado.sucesso:
        return ResultadoBoost(sucesso=False, mensagem=resultado.erro or "erro desconhecido")
    return ResultadoBoost(sucesso=True, mensagem="impulsionado com sucesso")
