"""Catálogo real da loja via Shopee Open Platform: anúncios ativos e seus detalhes.

Consumido por `scripts/sincronizar_itens.py` (gera o `[[itens]]`) e pelo painel web
(`painel.py`, mostra os produtos para ajustar os pesos).

Endpoints, todos GET:
- `get_item_list` (IDs ativos) e `get_item_base_info` (nome, imagem, preço, estoque,
  status) — confirmados contra conta real via `analista_dados_shopee/workers/
  sync_catalogo.py`, implementação irmã já validada em produção.
- `get_model_list` (preço/estoque de anúncio COM variações, que o `get_item_base_info` não
  traz) — usado pela mesma implementação irmã, mas não exercitado por este projeto antes;
  opcional (`buscar_variacoes`) e registrado em `_gestao/DECISOES.md` (2026-10-19).

Formato do estoque: a API tem `stock_info_v2.summary_info.total_available_stock` (atual) e
`stock_info[0].normal_stock` (legado, o que a implementação irmã lê). Não sabemos qual a
conta devolve, então a extração aceita os dois; ausência vira `None`, nunca erro.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

from .cliente_shopee import ClienteShopee

PATH_LISTA_ITENS = "/api/v2/product/get_item_list"
PATH_INFO_ITENS = "/api/v2/product/get_item_base_info"
PATH_MODELOS = "/api/v2/product/get_model_list"
PAGE_SIZE = 50
LOTE_INFO = 50


class ErroCatalogo(RuntimeError):
    """Falha ao listar o catálogo — uma listagem parcial não pode ser usada."""


@dataclass(frozen=True)
class ItemCatalogo:
    id: int
    nome: str
    imagem_url: str | None = None
    preco_min: float | None = None
    preco_max: float | None = None
    estoque: int | None = None
    status: str | None = None
    tem_variacoes: bool = False


def buscar_item_ids_ativos(cliente: ClienteShopee, *, pausa: float = 0.0) -> list[int]:
    """Pagina `get_item_list` (status NORMAL) até o fim. Lança `ErroCatalogo` se alguma
    página falhar — uma listagem parcial removeria itens ativos do rodízio por engano."""
    item_ids: list[int] = []
    offset = 0
    while True:
        resultado = cliente.chamar(
            PATH_LISTA_ITENS,
            {"offset": offset, "page_size": PAGE_SIZE, "item_status": "NORMAL"},
            metodo="GET",
        )
        if not resultado.sucesso:
            raise ErroCatalogo(resultado.erro or "erro desconhecido ao listar itens")

        pagina = _resposta(resultado.dados)
        item_ids.extend(item["item_id"] for item in pagina.get("item") or [])
        if not pagina.get("has_next_page"):
            return item_ids
        offset += PAGE_SIZE
        time.sleep(pausa)


def buscar_detalhes(
    cliente: ClienteShopee,
    item_ids: list[int],
    *,
    buscar_variacoes: bool = False,
    pausa: float = 0.0,
) -> dict[int, ItemCatalogo]:
    """Detalhes de cada item, em lotes de `get_item_base_info`. Lote que falha é pulado
    (detalhe é cosmético: os itens ficam sem nome/imagem, não somem). Com
    `buscar_variacoes`, cada item com variações custa mais uma chamada (`get_model_list`)."""
    detalhes: dict[int, ItemCatalogo] = {}
    for inicio in range(0, len(item_ids), LOTE_INFO):
        if inicio:
            time.sleep(pausa)
        lote = item_ids[inicio : inicio + LOTE_INFO]
        resultado = cliente.chamar(
            PATH_INFO_ITENS,
            {"item_id_list": ",".join(str(i) for i in lote)},
            metodo="GET",
        )
        if not resultado.sucesso:
            continue
        for bruto in _resposta(resultado.dados).get("item_list") or []:
            item = extrair_item(bruto)
            if item.tem_variacoes and buscar_variacoes:
                time.sleep(pausa)
                item = _com_variacoes(cliente, item)
            detalhes[item.id] = item
    return detalhes


def extrair_item(bruto: dict) -> ItemCatalogo:
    """Converte um elemento de `item_list` do `get_item_base_info` em `ItemCatalogo`."""
    imagens = (bruto.get("image") or {}).get("image_url_list") or []
    preco = _preco(bruto)
    return ItemCatalogo(
        id=int(bruto["item_id"]),
        nome=" ".join(str(bruto.get("item_name", "")).split()),
        imagem_url=imagens[0] if imagens else None,
        preco_min=preco,
        preco_max=preco,
        estoque=_estoque(bruto),
        status=bruto.get("item_status"),
        tem_variacoes=bool(bruto.get("has_model")),
    )


def _com_variacoes(cliente: ClienteShopee, item: ItemCatalogo) -> ItemCatalogo:
    resultado = cliente.chamar(PATH_MODELOS, {"item_id": item.id}, metodo="GET")
    if not resultado.sucesso:
        return item
    modelos = _resposta(resultado.dados).get("model") or []
    precos = [p for p in (_preco(m) for m in modelos) if p is not None]
    estoques = [e for e in (_estoque(m) for m in modelos) if e is not None]
    return ItemCatalogo(
        id=item.id,
        nome=item.nome,
        imagem_url=item.imagem_url,
        preco_min=min(precos) if precos else item.preco_min,
        preco_max=max(precos) if precos else item.preco_max,
        estoque=sum(estoques) if estoques else item.estoque,
        status=item.status,
        tem_variacoes=True,
    )


def _resposta(dados: dict | None) -> dict:
    return (dados or {}).get("response") or {}


def _preco(bruto: dict) -> float | None:
    for info in bruto.get("price_info") or []:
        valor = info.get("current_price")
        if isinstance(valor, int | float):
            return float(valor)
    return None


def _estoque(bruto: dict) -> int | None:
    resumo = (bruto.get("stock_info_v2") or {}).get("summary_info") or {}
    total = resumo.get("total_available_stock")
    if isinstance(total, int):
        return total
    legado = [
        info.get("normal_stock")
        for info in bruto.get("stock_info") or []
        if isinstance(info.get("normal_stock"), int)
    ]
    return legado[0] if legado else None
