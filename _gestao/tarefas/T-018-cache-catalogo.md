---
id: T-018
titulo: Cache do catálogo em disco (catalogo.json) com TTL e intervalo mínimo de atualização
projeto: shopee-rodizio
status: concluida
prioridade: media
dependencias: [T-017]
areas: [src/shopee_rodizio/catalogo.py, tests/test_catalogo.py]
tentativas: 1
agente: integracao-shopee
criada: 2026-10-19
atualizada: 2026-10-19
---

## Objetivo
O painel não pode bater na API da Shopee a cada carregamento de página.

## Critérios de aceite
- [x] `CacheCatalogo` (frozen) + `carregar_cache`/`gravar_cache` em `catalogo.json`, ao
      lado do `estado.json`, gravado com `arquivo.gravar_atomico`. Ausente/corrompido →
      cache vazio e vencido, nunca erro.
- [x] `CacheCatalogo.vencido(horas)` com o TTL de `[painel].cache_horas` (padrão 24h).
- [x] `baixar_catalogo` busca tudo com pausa de 0,2 s entre chamadas; falha na listagem
      lança `ErroCatalogo` e o cache antigo NÃO é sobrescrito (o painel mostra o erro e
      segue com o cache).
- [x] Intervalo mínimo de 60 s entre tentativas de atualização (no painel, T-019),
      também quando a atualização automática por TTL falha.
- [x] `uv run pytest -q` e `uv run ruff check .` passam.

**Reproduzir:** `.venv\Scripts\python.exe -m pytest tests/test_catalogo.py -q`
