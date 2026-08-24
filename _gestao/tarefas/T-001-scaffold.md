---
id: T-001
titulo: Scaffold do projeto Python (uv) com lint, teste e GUIA.md
projeto: shopee-rodizio
status: concluida
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

### Passada mecânica (sem modelo)

- [julgado] `uv run ruff check .` roda sem erro (exit 0). — comando recusado: binario-nao-permitido; fica para o verificador.
- [julgado] `uv run pytest -q` roda e pelo menos 1 teste passa (exit 0). — comando recusado: binario-nao-permitido; fica para o verificador.
- [julgado] `pyproject.toml` declara `requests` como dependência de runtime e `ruff`+`pytest` como dependências de dev (inspecionável abrindo o arquivo). — sem comando declarado; fica para o verificador.
- [julgado] README.md tem as seções "Como rodar" e "Como testar" preenchidas com comandos reais (não o placeholder original). — sem comando declarado; fica para o verificador.
- [julgado] `_gestao/GUIA.md` está preenchido (sem o texto de instrução do template) com pelo menos as seções 1 e 2. — sem comando declarado; fica para o verificador.
- [executado] Existe um commit no repositório do projeto contendo o scaffold. — `git log --oneline -1` → **PASSOU**

Graus de prova: 1 executado(s), 5 para julgamento (de 6).

### Ciclo 2

- **[PASSOU] [executado] Critério 1: `uv run ruff check .` roda sem erro (exit 0)**
  Comando: `& "C:\Users\enzoc\AppData\Roaming\Python\Python312\Scripts\uv.exe" run ruff check .`
  Saída: `All checks passed!` (exit 0)

- **[PASSOU] [executado] Critério 2: `uv run pytest -q` roda e pelo menos 1 teste passa (exit 0)**
  Comando: `& "C:\Users\enzoc\AppData\Roaming\Python\Python312\Scripts\uv.exe" run pytest -q`
  Saída: `.` (1 test); `1 passed in 0.05s` (exit 0)

- **[PASSOU] [inspecionado] Critério 3: `pyproject.toml` declara `requests` como dependência de runtime e `ruff`+`pytest` como dependências de dev**
  Comando: Inspeção de arquivo
  Base: Arquivo `pyproject.toml` contém `dependencies = ["requests>=2.34.2"]` (runtime) e `[dependency-groups] dev = ["pytest>=9.1.1", "ruff>=0.16.4"]` (dev)

- **[PASSOU] [inspecionado] Critério 4: README.md tem as seções "Como rodar" e "Como testar" preenchidas com comandos reais**
  Comando: Inspeção de arquivo
  Base: README.md contém seção "## Como rodar" com `uv run python -m shopee_rodizio` e seção "## Como testar" com `uv run pytest -q` e `uv run ruff check .`

- **[PASSOU] [inspecionado] Critério 5: `_gestao/GUIA.md` está preenchido (sem o texto de instrução do template) com pelo menos as seções 1 e 2**
  Comando: Inspeção de arquivo
  Base: GUIA.md contém seção "1. Em uma tela" (stack Python/uv, rodar, testar) e seção "2. Onde fica o quê" (tabela de módulos config.py, estado.py, cliente_shopee.py, boost.py, selecao.py, ciclo.py, logging_config.py). Seções 3 e 4 presentes. Sem texto remanescente de instrução do template.

- **[PASSOU] [executado] Critério 6: Existe um commit no repositório do projeto contendo o scaffold**
  Comando: `git log --oneline -5`
  Saída: `8e43db8 T-001: scaffold do projeto Python (uv) com lint, teste e GUIA.md`

Suíte completa: 1 passou, 0 falharam — `& "C:\Users\enzoc\AppData\Roaming\Python\Python312\Scripts\uv.exe" run pytest -q`
Graus de prova: 3 executados, 3 inspecionados, 0 julgados



## Conformidade

Conformidade: cumpre

- `uv run ruff check .` sem erro → confirmado pela Verificação (Ciclo 2, Critério 1: `All checks passed!`, exit 0); `[tool.ruff]` em `pyproject.toml:27-29` (`target-version = "py312"`, `line-length = 100`).
- `uv run pytest -q` com ao menos 1 teste passando → `tests/test_scaffold.py` (importa `shopee_rodizio` e confere `hasattr(shopee_rodizio, "main")`); Verificação confirma `1 passed`.
- `pyproject.toml` declara `requests` runtime e `ruff`+`pytest` dev → `pyproject.toml:9-11` (`dependencies = ["requests>=2.34.2"]`) e `pyproject.toml:25-28` (`[dependency-groups] dev = ["pytest>=9.1.1", "ruff>=0.16.4"]`).
- README.md com "Como rodar"/"Como testar" reais → `README.md` (seções adicionadas, substituindo o placeholder do commit anterior; `git show a394a69:README.md` só tinha a descrição sem essas seções).
- `_gestao/GUIA.md` preenchido, seções 1 e 2 presentes, sem texto de instrução do template → confirmado por diff contra `_sistema/templates/GUIA.md` (bloco `> Preencha as quatro seções...` ausente; seção 2 lista os 7 módulos do `_gestao/PLANO.md`).
- Commit contendo o scaffold → `8e43db8` (mensagem "T-001: scaffold do projeto Python (uv)..."), com `9120c72` registrando o hash na própria tarefa.

Objetivo satisfeito no espírito: fundação Python/uv com lint, teste e documentação mínima
para as tarefas seguintes dependerem. `python -m shopee_rodizio` ainda falha por falta de
`__main__.py` — mas o Contexto da tarefa autoriza explicitamente documentar o comando alvo
antes do entrypoint existir (implementação fica para T-008). Escopo: `.gitignore` e
`.python-version` são efeitos colaterais esperados de `uv init` / necessidade de excluir
`.venv` e caches do controle de versão — não é scope creep.

## Revisão

Aprovado sem ressalvas. Verificado no diff de `8e43db8`:
- `pyproject.toml`: dependências, `[tool.ruff]` e `[project.scripts]` corretos; nenhuma
  incoerência entre o entrypoint declarado (`shopee_rodizio:main`) e `src/shopee_rodizio/__init__.py:1-2`
  (`main()` existe e é chamável).
- `tests/test_scaffold.py`: teste trivial, mas legítimo (confere o contrato mínimo do
  pacote em vez de só `assert True`).
- Nenhuma lógica de negócio nesta tarefa — superfície de risco (bugs de correção/segurança)
  é nula por natureza do escopo (scaffold).
- `[menor]` `pyproject.toml:4` — `description = "Add your description here"` é o
  placeholder default do `uv init`, não preenchido. Cosmético, não é critério de aceite.
