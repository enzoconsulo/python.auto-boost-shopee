---
id: T-017
titulo: Extrair a busca do catálogo para src/shopee_rodizio/catalogo.py (imagem, preço, estoque, status)
projeto: shopee-rodizio
status: concluida
prioridade: alta
dependencias: [T-012]
areas: [src/shopee_rodizio/catalogo.py, scripts/sincronizar_itens.py, tests/test_catalogo.py]
tentativas: 1
agente: integracao-shopee
criada: 2026-10-19
atualizada: 2026-10-19
---

## Objetivo
A busca do catálogo real vivia em funções privadas de `scripts/sincronizar_itens.py`,
inacessíveis ao painel web. Extrair para um módulo e fazer script e painel consumirem o
mesmo código, estendendo a extração do `get_item_base_info` (antes só `item_name`).

## Critérios de aceite
- [x] `catalogo.buscar_item_ids_ativos` (pagina `get_item_list`; falha em qualquer página
      → `ErroCatalogo`, nunca listagem parcial) e `catalogo.buscar_detalhes` (lotes de 50 de
      `get_item_base_info`; lote com falha é pulado).
- [x] `ItemCatalogo` (frozen): id, nome, imagem_url, preco_min/max, estoque, status,
      tem_variacoes. Estoque lido de `stock_info_v2.summary_info.total_available_stock` ou,
      na falta, do legado `stock_info[0].normal_stock`; ausência vira `None`.
- [x] `get_model_list` só com `buscar_variacoes=True` e só para itens com `has_model`
      (agrega preço mín/máx e soma de estoque) — incerteza em DECISOES 2026-10-19.
- [x] `sincronizar_itens.py` consome o módulo; saída e comportamento iguais (o teste do
      script cobre pesos preservados + `[rede]` depois dos itens intacto).
- [x] `uv run pytest -q` e `uv run ruff check .` passam.
      `verificar: uv run pytest -q`

**Reproduzir:** `.venv\Scripts\python.exe -m pytest tests/test_catalogo.py -q`
