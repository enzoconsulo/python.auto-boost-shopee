---
id: T-013
titulo: Mensagens de erro do cliente Shopee sem credenciais (access_token vazando no log)
projeto: shopee-rodizio
status: concluida
prioridade: alta
dependencias: []
areas: [src/shopee_rodizio/cliente_shopee.py, tests/test_cliente_shopee.py]
tentativas: 1
agente: integracao-shopee
criada: 2026-10-19
atualizada: 2026-10-19
---

## Objetivo
Nenhum `Resultado.erro` pode carregar `access_token`, `refresh_token`, `sign` ou
`partner_key` — esse texto vai para o log (`ciclo.py`), para o `estado.json` e, a partir
de T-018, para o painel web.

## Contexto
Achado na leitura do código para a auditoria de 2026-10-19 e **confirmado no Pi**: o
`shopee-rodizio.log` de produção tem 5 linhas com `access_token=eyJh…` em claro. Causa:
`raise_for_status()` do `requests` gera `HTTPError("403 … for url: <URL completa>")`, e a
URL assinada leva `access_token` e `sign` na query; o cliente devolvia `str(exc)` direto.

## Critérios de aceite
- [x] `cliente_shopee.mensagem_segura(exc)` remove a query string de qualquer URL e o valor
      de parâmetros secretos (`chave=valor`, `'chave': 'valor'`); usada nos dois pontos
      onde exceção vira `Resultado.erro`.
- [x] Testes: erro HTTP com URL assinada não vaza `access_token`/`sign` mas mantém o
      status e o path; falha na renovação não vaza `refresh_token`; mensagem sem segredo
      sai inalterada.
- [x] `uv run pytest -q` e `uv run ruff check .` passam.
      `verificar: uv run pytest -q`

## Notas de execução
Os tokens que já estão no log/estado do Pi expiram sozinhos (access_token ~4h); o
`refresh_token` nunca apareceu em mensagem de erro (ia no corpo JSON, não na URL). Os logs
antigos com token saem pela rotação do `RotatingFileHandler`; não foram editados.

**Reproduzir:** `.venv\Scripts\python.exe -m pytest tests/test_cliente_shopee.py -q`
