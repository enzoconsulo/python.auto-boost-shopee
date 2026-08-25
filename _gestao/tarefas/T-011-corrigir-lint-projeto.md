---
id: T-011
titulo: Corrigir import não utilizado que quebra o lint do projeto inteiro
projeto: shopee-rodizio
status: em-teste
prioridade: alta
dependencias: [T-003]
areas: [tests/test_estado.py]
tentativas: 1
agente: config-estado
criada: 2026-08-24
atualizada: 2026-08-25
---

## Objetivo
Remover o import não utilizado em `tests/test_estado.py` para que
`uv run ruff check .` (critério 1 de T-001, a fundação do projeto) volte a passar
limpo no projeto inteiro — hoje falha, e é por isso que o marco da Fase 1 foi
reprovado.

## Contexto
Causa raiz, já identificada na própria Revisão de T-003 (achado `[menor]`, não
corrigido porque o critério de lint daquela tarefa era escopado só a
`src/shopee_rodizio/estado.py`, não ao arquivo de teste que ela também criou):
`tests/test_estado.py:1` tem `from pathlib import Path`, nunca usado
(`ruff` acusa `F401`). Isso não quebra nenhum teste (a suíte inteira passa, `15
passed`), só o lint do projeto como um todo — que é exatamente o critério 1 de
T-001, a fundação de que todas as tarefas dependem.

Correção é de uma linha: remover o import não utilizado. Rode
`uv run ruff check tests/test_estado.py --fix` (ou edite a linha à mão) e confirme
que nada mais no arquivo dependia dele.

## Critérios de aceite
- [x] `uv run ruff check .` roda sem erro no projeto inteiro (exit 0).
      `verificar: uv run ruff check .`
- [x] `uv run pytest -q` continua com toda a suíte passando (sem regressão).
      `verificar: uv run pytest -q`

## Notas de execução

Removida a linha `from pathlib import Path` (não usada) de
`tests/test_estado.py:1` — nada mais no arquivo dependia dela.

`uv` não está no PATH deste ambiente; usei `.venv\Scripts\python.exe -m ruff` e
`.venv\Scripts\python.exe -m pytest` (equivalente ao `uv run`).

- `ruff check .` → `All checks passed!` (exit 0)
- `pytest -q` → `35 passed in 0.60s`

**Reproduzir:** `.venv\Scripts\python.exe -m ruff check . && .venv\Scripts\python.exe -m pytest -q`

**Commit:** `cf2d31f`
