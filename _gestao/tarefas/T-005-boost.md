---
id: T-005
titulo: Chamada do endpoint de impulsionamento por item
projeto: shopee-rodizio
status: concluida
prioridade: alta
dependencias: [T-004]
areas: [src/shopee_rodizio/boost.py, tests/test_boost.py]
tentativas: 1
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

Criado `src/shopee_rodizio/boost.py`: `impulsionar(cliente, config, item_id) -> ResultadoBoost`
chama `cliente.chamar(config.ciclo.endpoint_boost, {"item_id": ..., "shop_id": config.shopee.shop_id})`
e traduz o `Resultado` do cliente (T-004) em `ResultadoBoost(sucesso, mensagem)`, sem exceção.
Payload (`item_id` + `shop_id`) é o palpite plausível descrito no Contexto da tarefa — comentário
no topo do módulo deixa isso explícito para a T-010 (smoke-test) confirmar contra a conta real.

Teste escrito antes da implementação (`tests/test_boost.py`), mockando `ClienteShopee.chamar`
diretamente (não o HTTP — a assinatura/renovação já é responsabilidade testada em T-004):
sucesso vira `ResultadoBoost(sucesso=True, ...)`, erro da API vira `ResultadoBoost(sucesso=False,
mensagem=...)` sem lançar, e um caso cobre erro sem mensagem (`erro=None`) para a mensagem
genérica. Também confere que `endpoint_boost` e `shop_id` vêm da config, não hardcoded.

Rodei manualmente (via `.venv\Scripts\python.exe -m pytest`, porque `uv` não está no PATH
deste ambiente — ver `_gestao/GUIA.md`/memória do agente):
- `pytest tests/test_boost.py -q` → 4 passed.
- `ruff check src/shopee_rodizio/boost.py tests/test_boost.py` → All checks passed!

Nenhuma dependência nova.

**Reproduzir:** `.venv\Scripts\python.exe -m pytest tests/test_boost.py -q`

**Commit:** `d6b2ba2`

## Verificação

### Ciclo 1

- **[PASSOU] [executado] Critério 1: pytest tests/test_boost.py -q → todos os testes passam, com o cliente mockado simulando resposta de sucesso da API e resposta de erro da API — os dois viram `ResultadoBoost` coerente, sem exceção.**
  Comando: `.\.venv\Scripts\python.exe -m pytest tests/test_boost.py -q`
  Saída: `4 passed in 0.33s`

- **[PASSOU] [executado] Critério 2: ruff check src/shopee_rodizio/boost.py → sem erros.**
  Comando: `.\.venv\Scripts\python.exe -m ruff check src/shopee_rodizio/boost.py`
  Saída: `All checks passed!`

Suíte completa: 31 passed — `.\.venv\Scripts\python.exe -m pytest -q`
Graus de prova: 2 executados



## Conformidade
Conformidade: cumpre

- Critério 1 (`pytest tests/test_boost.py -q` com cliente mockado simulando sucesso e erro
  da API, sem exceção) → `tests/test_boost.py` (4 testes: `test_impulsionar_com_sucesso_
  devolve_resultado_positivo` e `test_impulsionar_usa_endpoint_e_shop_id_da_config` cobrem
  sucesso, `test_impulsionar_erro_da_api_devolve_resultado_negativo_sem_lancar` e
  `test_impulsionar_erro_sem_mensagem_devolve_mensagem_generica` cobrem erro da API).
  Confirmado nesta revisão: `.venv\Scripts\python.exe -m pytest tests/test_boost.py -q` →
  4 passed.
- Critério 2 (`ruff check` limpo em `boost.py`) → confirmado nesta revisão:
  `.venv\Scripts\python.exe -m ruff check src/shopee_rodizio/boost.py` → All checks passed!
- Objetivo: `impulsionar(cliente, config, item_id) -> ResultadoBoost` (`boost.py:24-35`)
  usa `cliente_shopee.py` (T-004) via `cliente.chamar(...)`, lê o caminho do endpoint de
  `config.ciclo.endpoint_boost` e o `shop_id` de `config.shopee.shop_id` (RF-04, nada
  hardcoded), e traduz `Resultado` em `ResultadoBoost(sucesso, mensagem)` sem nunca deixar
  exceção escapar — bate com o Objetivo e o Contexto da tarefa.
- Payload (`item_id` + `shop_id`) documentado como palpite plausível em comentário no topo
  do módulo (`boost.py:1-8`), exatamente como o Contexto pede, remetendo à T-010 para
  confirmação contra a conta real.
- Escopo do código: apenas `src/shopee_rodizio/boost.py` e `tests/test_boost.py`, batendo
  com `areas:` da tarefa. `_gestao/MAPA.md` também tocado — regeneração esperada
  (`mapa.mjs`), não é sobra de escopo.
- Achado de escopo do COMMIT (não do código): o commit `d6b2ba2`, associado a esta tarefa,
  também carrega uma reescrita completa de `_gestao/tarefas/T-004-cliente-shopee.md`
  (Verificação Ciclo 3, Conformidade e Revisão Ciclo 4, incluindo o veredito "Aprovado sem
  ressalvas" e a mudança de `status: em-teste` → `concluida`) — conteúdo tecnicamente
  consistente com o que já estava registrado como pendente/reprovado em T-004 antes deste
  ciclo, então trato como revisão genuína de T-004 que ficou sem commit próprio e foi
  arrastada por um `git add` amplo ao commitar T-005, não como fabricação desta tarefa.
  Ainda assim é sobra fora do escopo declarado (`areas: [src/shopee_rodizio/boost.py,
  tests/test_boost.py]`) e mistura o rastro de auditoria de duas tarefas num commit só —
  ver achado `menor` na Revisão.

## Revisão

### Ciclo 1 (revisão)

Diff revisado: `d6b2ba2` (código novo — `boost.py` + `test_boost.py` — e as mudanças de
gestão associadas). Commit registrado corretamente em `**Commit:**` desta vez (ao contrário
do achado já sinalizado em T-004).

Revisão de código:
- `impulsionar()` (`boost.py:24-35`) chama `cliente.chamar(config.ciclo.endpoint_boost,
  {"item_id": item_id, "shop_id": config.shopee.shop_id})` — nomes de campo de `CicloConfig`
  e `ShopeeCredenciais` conferem com `config.py` (`endpoint_boost`, `shop_id`).
- Tradução de `Resultado` (`cliente_shopee.py`) para `ResultadoBoost`: `sucesso=False` vira
  `mensagem=resultado.erro or "erro desconhecido"` (cobre erro com e sem texto);
  `sucesso=True` vira mensagem fixa não vazia. Nenhum caminho lança exceção — `chamar()` já
  garante isso (T-004), e `impulsionar()` só lê campos do `Resultado`, não chama nada que
  possa lançar.
- `resultado.token_renovado` não é propagado por `ResultadoBoost` — não é bug: o objeto
  `cliente` já é mutado in-place por `chamar()` (`self._token = novo` em
  `_aplicar_renovacao`), então quem orquestra o ciclo (T-008) ainda tem acesso ao token
  renovado via `cliente.token` depois de chamar `impulsionar()`, sem precisar que
  `ResultadoBoost` o carregue. Consistente com o Objetivo da tarefa, que pede só
  `sucesso`/`mensagem` ("pelo menos").
- Reexecutei nesta revisão: `pytest tests/test_boost.py -q` → 4 passed; `ruff check
  src/shopee_rodizio/boost.py tests/test_boost.py` → All checks passed!; suíte completa
  `pytest -q` → 31 passed, sem regressão.

Achados:
- [menor] commit `d6b2ba2` — mistura a revisão/fechamento de T-004 (arquivo
  `_gestao/tarefas/T-004-cliente-shopee.md`, fora de `areas:` desta tarefa) dentro do commit
  de código de T-005. Não é defeito de T-005 em si (conteúdo revisado é consistente com o
  histórico de T-004), mas quebra o rastreamento 1-commit-por-tarefa que o protocolo espera.
  Recomendo, nas próximas tarefas, `git add` restrito aos arquivos da própria tarefa antes
  de commitar.

Aprovado sem ressalvas quanto a correção e conformidade — o achado acima é de higiene de
commit, não de código.
