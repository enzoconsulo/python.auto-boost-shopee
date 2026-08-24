---
id: T-004
titulo: Cliente HTTP Shopee com assinatura HMAC e renovação de token
projeto: shopee-rodizio
status: backlog
prioridade: alta
dependencias: [T-001, T-002]
areas: [src/shopee_rodizio/cliente_shopee.py, tests/test_cliente_shopee.py]
tentativas: 0
agente: integracao-shopee
criada: 2026-08-24
atualizada: 2026-08-24
---

## Objetivo
Implementar `src/shopee_rodizio/cliente_shopee.py`: monta a assinatura HMAC-SHA256 exigida
pela Shopee Open Platform API v2, faz a chamada HTTP autenticada via `requests`, e renova
`access_token` automaticamente via `refresh_token` antes de expirar — sem NUNCA propagar
exceção de rede/API para fora do cliente.

## Contexto
Mecanismo de autenticação confirmado por pesquisa (WebSearch, 2026-08-24 — ver
`_gestao/DECISOES.md`): a assinatura é HMAC-SHA256 sobre a string
`partner_id + path + timestamp` (chamadas de nível loja acrescentam
`+ access_token + shop_id` na base assinada), usando `partner_key` como chave; o resultado
vai no query param `sign`. `access_token` tem validade de ~4 horas; `refresh_token` tem
validade de ~30 dias e é usado para obter um novo `access_token` chamando
`/api/v2/auth/access_token/get`. Implemente a renovação de forma proativa (antes de
expirar, não só reagindo a erro 401) e persista o token renovado — combine com T-003
(`estado.py`) ou com um retorno que o chamador (T-008, `ciclo.py`) grava de volta na
config/estado; deixe explícito nas Notas de execução qual caminho você escolheu.

O caminho exato do endpoint de boost (`endpoint_boost`) vem da config (T-002) — este
módulo expõe uma função genérica de chamada assinada (`chamar(path, params, ...)`), não
codifica o endpoint de boost em si (isso é T-005).

Trate qualquer falha (timeout, erro de conexão, erro HTTP, corpo de erro da API) como um
retorno estruturado de erro (não uma exceção que escapa do cliente) — é o que permite ao
ciclo (T-008) logar e seguir sem crashar, conforme RF-06.

Nos testes, mocke `requests` (`unittest.mock.patch`) — nunca bata na API real da Shopee a
partir do teste automatizado.

## Critérios de aceite
- [ ] `uv run pytest tests/test_cliente_shopee.py -q` → todos os testes passam, incluindo
      um teste que verifica a assinatura HMAC-SHA256 contra um vetor de entrada fixo
      (partner_id, path, timestamp, partner_key conhecidos → hash esperado calculado à
      parte no teste) e um teste que simula timeout/erro de conexão e confirma que a
      função retorna um resultado de erro em vez de lançar exceção.
      `verificar: uv run pytest tests/test_cliente_shopee.py -q`
- [ ] `uv run ruff check src/shopee_rodizio/cliente_shopee.py` → sem erros.
      `verificar: uv run ruff check src/shopee_rodizio/cliente_shopee.py`

## Notas de execução


## Verificação


## Conformidade


## Revisão
