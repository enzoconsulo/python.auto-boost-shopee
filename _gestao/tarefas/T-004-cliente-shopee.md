---
id: T-004
titulo: Cliente HTTP Shopee com assinatura HMAC e renovação de token
projeto: shopee-rodizio
status: em-execucao
prioridade: alta
dependencias: [T-001, T-002]
areas: [src/shopee_rodizio/cliente_shopee.py, tests/test_cliente_shopee.py]
tentativas: 1
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

**Retrabalho (executor reforçado, 2026-08-24).** As seções Verificação/Conformidade/Revisão
chegaram vazias e nada de T-004 estava commitado (ambos os arquivos `??` no git) — o ciclo
anterior produziu o código mas não fechou o contrato de estado. Diagnóstico de abertura:

- **Causa raiz:** o `chamar()` descartava o `token_renovado` sempre que a renovação dava
  certo mas a chamada-alvo seguinte falhava (erro de API ou exceção de rede). Como a
  renovação bem-sucedida já invalida o `refresh_token` antigo, o retorno de erro com
  `token_renovado=None` fazia o chamador perder o token novo — violando a invariante "token
  renovado é persistido (nunca só em memória)". Caminho não coberto por teste.
- **Correção (mínima):** os dois retornos de erro pós-renovação (`erro` de API e o `except`
  de `RequestException`) agora carregam `token_renovado=token_renovado`. Só retornos foram
  tocados; assinatura/fluxo intactos. +1 teste cobrindo renovação-ok + alvo-com-erro.
- **Aproveitamento:** ~95% do código anterior mantido (assinatura HMAC, renovação proativa,
  tratamento de erro já corretos e passando). Refiz apenas o repasse do token nos retornos
  de erro.

**Persistência do token renovado — caminho escolhido:** retorno estruturado. O cliente NÃO
grava estado; devolve `Resultado.token_renovado` (um `Token` imutável) para o chamador
(T-008 `ciclo.py`) persistir via T-003 `estado.py`. Escolhido em vez de acoplar o cliente ao
`estado.py` para manter o cliente sem I/O de disco (testável só com `requests` mockado) e a
persistência num único lugar. Fora do escopo de T-004: o `tests/test_estado.py:1` F401 que
faz `ruff check .` (projeto inteiro) falhar é regressão de T-003, já endereçada por T-011 —
o critério de lint desta tarefa é escopado a `cliente_shopee.py`, que passa limpo.

## Verificação
Rodado com o Python do `.venv` do projeto (o wrapper `uv` não está no PATH desta máquina;
`.venv\Scripts\python.exe -m pytest/ruff` é equivalente — mesma suíte, mesmas versões).

- `python -m pytest tests/test_cliente_shopee.py -q` → **12 passed** (10 anteriores + 2
  novos cobrindo renovação-ok seguida de erro de API e de timeout no alvo). Inclui o teste
  de vetor HMAC fixo (`test_assinatura_publica_bate_com_vetor_conhecido`) e os de
  timeout/erro-de-conexão retornando `Resultado` sem lançar.
- `python -m ruff check src/shopee_rodizio/cliente_shopee.py` → **All checks passed!**
- Suíte completa: `python -m pytest -q` → **27 passed** (25 anteriores + 2).

Nota fora de escopo: `ruff check .` (projeto inteiro) ainda acusa 1 F401 em
`tests/test_estado.py:1` — regressão de T-003 endereçada por T-011, não por esta tarefa
(critério de lint de T-004 é escopado a `cliente_shopee.py`).

## Conformidade
Objetivo atendido: assinatura HMAC-SHA256 (`partner_id+path+timestamp` [+access_token+shop_id
na loja]), chamada HTTP via `requests`, renovação proativa via `/api/v2/auth/access_token/get`
com margem antes de expirar, e nenhuma exceção de rede/API escapando (tudo vira `Resultado`).
Endpoint de boost NÃO hardcoded: `chamar(path, params)` recebe o caminho da config (T-002),
conforme DECISOES 2026-08-24. Invariante de persistência do token corrigida (token renovado
volta ao chamador mesmo em erro do alvo). Ambos os critérios de aceite executados e passando.

## Revisão
