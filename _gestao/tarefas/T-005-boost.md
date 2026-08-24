---
id: T-005
titulo: Chamada do endpoint de impulsionamento por item
projeto: shopee-rodizio
status: backlog
prioridade: alta
dependencias: [T-004]
areas: [src/shopee_rodizio/boost.py, tests/test_boost.py]
tentativas: 0
agente: integracao-shopee
criada: 2026-08-24
atualizada: 2026-08-24
---

## Objetivo
Implementar `src/shopee_rodizio/boost.py`: usa `cliente_shopee.py` (T-004) para chamar o
endpoint de impulsionamento de UM item, lendo o caminho do endpoint e os nomes de
parâmetro da config (RF-04), e traduzindo a resposta em sucesso/erro com mensagem.

## Contexto
Este módulo NÃO decide o caminho do endpoint — ele vem de `config.ciclo.endpoint_boost`
(T-002), porque a documentação pública não confirma esse caminho sem login (ver
`_gestao/DECISOES.md`). Monte o payload/params mínimos plausíveis para um endpoint
`v2.product.boost_item`-like (tipicamente `item_id` e `shop_id`), mas deixe claro no
código (comentário curto) que o nome exato do parâmetro também pode precisar de ajuste —
é o que a T-010 (smoke-test) existe para confirmar contra a conta real.

Exponha uma função como `impulsionar(cliente, config, item_id) -> ResultadoBoost` onde
`ResultadoBoost` tem pelo menos `sucesso: bool` e `mensagem: str`. Erro retornado pelo
cliente (T-004) vira `ResultadoBoost(sucesso=False, mensagem=...)`, nunca exceção.

## Critérios de aceite
- [ ] `uv run pytest tests/test_boost.py -q` → todos os testes passam, com o cliente
      mockado simulando resposta de sucesso da API e resposta de erro da API (ex.: item já
      em boost, limite atingido) — os dois viram `ResultadoBoost` coerente, sem exceção.
      `verificar: uv run pytest tests/test_boost.py -q`
- [ ] `uv run ruff check src/shopee_rodizio/boost.py` → sem erros.
      `verificar: uv run ruff check src/shopee_rodizio/boost.py`

## Notas de execução


## Verificação


## Conformidade


## Revisão
