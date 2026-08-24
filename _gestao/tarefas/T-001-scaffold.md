---
id: T-001
titulo: Scaffold do projeto Python (uv) com lint, teste e GUIA.md
projeto: shopee-rodizio
status: em-teste
prioridade: alta
dependencias: []
areas: [pyproject.toml, README.md, tests/test_scaffold.py, _gestao/GUIA.md]
tentativas: 1
criada: 2026-08-24
atualizada: 2026-08-24
---

## Objetivo
Criar a estrutura do projeto Python com `uv` (layout `src/shopee_rodizio/`), lint+format
(`ruff`) configurados e rodando, `pytest` instalado com pelo menos um teste trivial
passando, README com os comandos reais de rodar/testar, `_gestao/GUIA.md` preenchido (a
partir do template), e um commit contendo tudo isso. Esta é a fundação: toda tarefa
seguinte depende dela.

## Contexto
O repositório do projeto já existe e já tem um commit inicial de gestão (CLAUDE.md,
README.md placeholder, `_gestao/DECISOES.md`, `_gestao/PROGRESSO.md`, `_gestao/MAPA.md`) —
não rode `git init` de novo, só adicione o commit do scaffold em cima.

Rode `uv init --package --name shopee_rodizio .` na raiz do projeto (isso cria
`pyproject.toml` e `src/shopee_rodizio/__init__.py`; mantenha o `README.md` já existente,
mesclando/reescrevendo o conteúdo em vez de deixar o `uv` sobrescrever com o template
genérico dele). Adicione as dependências do catálogo desta especificação:
`uv add requests` (runtime) e `uv add --dev ruff pytest` (dev).

Configure o `ruff` no `pyproject.toml` (seção `[tool.ruff]`): `target-version` compatível
com a versão de Python resolvida pelo `uv`, `line-length = 100`. Crie `tests/` com um
`tests/test_scaffold.py` mínimo (ex.: `def test_scaffold(): assert True` ou um teste que
importa `shopee_rodizio` e confere que o pacote existe) — é só para provar que o runner
está de pé; as tarefas seguintes escrevem os testes de verdade.

Preencha `_gestao/GUIA.md` a partir de `_sistema/templates/GUIA.md` (caminho absoluto:
`C:\Users\enzoc\OneDrive\Documentos\Gerador_de_projetos\_sistema\templates\GUIA.md`) — seção
1 (stack Python/uv, comando de rodar `uv run python -m shopee_rodizio`, comando de testar
`uv run pytest`), seção 2 com os módulos que ESTA tarefa já sabe que vão existir
(`src/shopee_rodizio/config.py`, `estado.py`, `cliente_shopee.py`, `boost.py`,
`selecao.py`, `ciclo.py`, `logging_config.py` — mesmo que ainda não existam, é o plano
combinado com o planejador em `_gestao/PLANO.md`), seções 3 e 4 podem ficar enxutas nesta
tarefa e crescer nas próximas (não deixe o texto de instrução do template — "Preencha as
quatro seções..." — no arquivo final).

Atualize `README.md` do projeto com "Como rodar" (`uv run python -m shopee_rodizio` —
mesmo que o entrypoint ainda não exista, documente o comando alvo) e "Como testar"
(`uv run pytest`), substituindo os placeholders `<preenchido pelo planejador...>` que
estão lá hoje.

## Critérios de aceite
- [ ] `uv run ruff check .` roda sem erro (exit 0).
      `verificar: uv run ruff check .`
- [ ] `uv run pytest -q` roda e pelo menos 1 teste passa (exit 0).
      `verificar: uv run pytest -q`
- [ ] `pyproject.toml` declara `requests` como dependência de runtime e `ruff`+`pytest`
      como dependências de dev (inspecionável abrindo o arquivo).
- [ ] README.md tem as seções "Como rodar" e "Como testar" preenchidas com comandos reais
      (não o placeholder original).
- [ ] `_gestao/GUIA.md` está preenchido (sem o texto de instrução do template) com pelo
      menos as seções 1 e 2.
- [ ] Existe um commit no repositório do projeto contendo o scaffold.
      `verificar: git log --oneline -1`

## Notas de execução

`uv` não estava instalado no ambiente (nem no PATH do bash nem do PowerShell). Instalado
via `pip install --user uv` (resolveu para
`~/AppData/Roaming/Python/Python312/Scripts/uv.exe`); anotado em Armadilhas conhecidas do
`_gestao/GUIA.md` para os próximos ciclos.

Rodado `uv init --package --name shopee_rodizio .` na raiz (criou `pyproject.toml`,
`src/shopee_rodizio/__init__.py`, `.python-version` em 3.12) — o `README.md` já existente
foi preservado pelo `uv` (não sobrescreveu). Adicionado `requests` (runtime) via `uv add
requests` e `ruff`+`pytest` (dev) via `uv add --dev ruff pytest`. Configurado
`[tool.ruff]` em `pyproject.toml` com `target-version = "py312"` (versão resolvida pelo
`uv`) e `line-length = 100`.

Criado `tests/test_scaffold.py` (importa `shopee_rodizio` e confere que `main` existe).
Criado `.gitignore` (`uv init` não gerou um automaticamente) excluindo `.venv/`,
`.pytest_cache/`, `.ruff_cache/`, `__pycache__/`, `*.pyc`.

Atualizado `README.md` com "Como rodar" (`uv run python -m shopee_rodizio`) e "Como
testar" (`uv run pytest -q` + `uv run ruff check .`). O comando de rodar ainda falha
("No module named shopee_rodizio.__main__") porque o entrypoint real só será
implementado em T-008 (ciclo) — conforme o Contexto desta tarefa autoriza
explicitamente ("mesmo que o entrypoint ainda não exista, documente o comando alvo").

Preenchido `_gestao/GUIA.md` a partir do template: seção 1 (stack, rodar, testar) e
seção 2 com os módulos planejados (`config.py`, `estado.py`, `cliente_shopee.py`,
`boost.py`, `selecao.py`, `ciclo.py`, `logging_config.py`, ainda não criados). Seções 3 e
4 deixadas enxutas, a crescer nas próximas tarefas.

Regenerado `_gestao/MAPA.md`.

**Reproduzir:** `export PATH="/c/Users/enzoc/AppData/Roaming/Python/Python312/Scripts:$PATH" && cd projetos/shopee-rodizio && uv run ruff check . && uv run pytest -q`

**Commit:** `8e43db8`

## Verificação


## Conformidade


## Revisão
