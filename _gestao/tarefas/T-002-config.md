---
id: T-002
titulo: Leitura e validação da configuração TOML
projeto: shopee-rodizio
status: concluida
prioridade: alta
dependencias: [T-001]
areas: [src/shopee_rodizio/config.py, config.example.toml, tests/test_config.py]
tentativas: 1
agente: config-estado
criada: 2026-08-24
atualizada: 2026-08-24
ciclo-1: verificador testou com sucesso
---

## Objetivo
Implementar `src/shopee_rodizio/config.py`: lê e valida a configuração do usuário a partir
de um arquivo TOML, expondo uma estrutura tipada (`dataclass`) com credenciais Shopee,
lista de itens com peso, intervalo do ciclo, limite de slots simultâneos e caminhos de
log/estado. Entrega também `config.example.toml`, o exemplo documentado que o usuário copia
e edita.

## Contexto
Use `tomllib` (stdlib, leitura apenas — Python 3.11+, já resolvido pelo `uv` na T-001), sem
adicionar dependência de parsing TOML. Campos mínimos do TOML:

```toml
[shopee]
partner_id = 0
partner_key = "..."
shop_id = 0
access_token = "..."
refresh_token = "..."

[ciclo]
intervalo_horas = 4
limite_slots = 5
endpoint_boost = "/api/v2/product/boost_item"   # RF-04: caminho configurável, ver DECISOES.md

[caminhos]
log = "shopee-rodizio.log"
estado = "estado.json"

[[itens]]
id = 123456789
peso = 3

[[itens]]
id = 987654321
peso = 1
```

O nome exato do endpoint (`endpoint_boost`) é um CAMPO da config, não uma constante no
código — ver `_gestao/DECISOES.md`, entrada "Endpoint de boost da Shopee: incerteza
registrada". `config.py` só precisa saber que existe essa string; quem a usa é T-004/T-005.

Validações obrigatórias, com mensagem de erro clara (não silenciar): item sem `id` ou sem
`peso`, peso `<= 0`, `intervalo_horas <= 0`, `limite_slots <= 0`, seção `[shopee]`
incompleta. Erro de validação deve ser uma exceção com mensagem que diz QUAL campo está
errado.

## Critérios de aceite
- [ ] `uv run pytest tests/test_config.py -q` → todos os testes passam, incluindo casos de
      config válida e ao menos 2 casos de config inválida (peso negativo, campo Shopee
      ausente) que devem levantar exceção com mensagem identificando o campo.
      `verificar: uv run pytest tests/test_config.py -q`
- [ ] `config.example.toml` é TOML válido.
      `verificar: uv run python -c "import tomllib,pathlib; tomllib.loads(pathlib.Path('config.example.toml').read_text())"`
- [ ] `uv run ruff check src/shopee_rodizio/config.py` → sem erros.
      `verificar: uv run ruff check src/shopee_rodizio/config.py`

## Notas de execução

Implementado `src/shopee_rodizio/config.py`: dataclasses `ShopeeCredenciais`, `CicloConfig`,
`CaminhosConfig`, `Item`, `Config` (imutáveis, `frozen=True`) e a função pública
`carregar_config(caminho)` que lê o TOML via `tomllib` (stdlib) e valida. Exceção
`ConfigError` sempre identifica o campo problemático na mensagem (ex.:
`campo ausente: shopee.partner_key`, `itens[0].peso deve ser > 0 (item id=111)`).
Validações implementadas: seções `[shopee]`/`[ciclo]`/`[caminhos]` completas,
`intervalo_horas > 0`, `limite_slots > 0`, ao menos um `[[itens]]`, cada item com `id` e
`peso`, `peso > 0`. `endpoint_boost` é lido como string simples — config.py não usa nem
valida seu conteúdo, só garante que existe (uso fica para T-004/T-005, conforme
DECISOES.md).

Criado `config.example.toml` com os campos documentados (comentários explicando
`intervalo_horas`, `limite_slots`, `endpoint_boost` e `peso`), TOML válido.

Testes em `tests/test_config.py` escritos antes da implementação (vistos falhar por
`ModuleNotFoundError` antes de `config.py` existir): config válida carrega estrutura
tipada corretamente, `config.example.toml` do próprio projeto é válido, e 6 casos de
config inválida (peso negativo, seção `[shopee]` incompleta, item sem `peso`, item sem
`id`, `intervalo_horas` inválido, `limite_slots` inválido) — todos levantam `ConfigError`
com mensagem identificando o campo.

Nenhuma dependência nova (usa só `tomllib`/stdlib, conforme já decidido em
`_gestao/DECISOES.md`).

**Reproduzir:** `uv run pytest tests/test_config.py -q`

**Commit:** `bd231b6`

## Verificação

### Ciclo 1

- **[PASSOU] [executado] Critério 1: `uv run pytest tests/test_config.py -q` → todos os testes passam**
  Comando: `python -m uv run pytest tests/test_config.py -q`
  Saída: `8 passed in 0.14s`
  Detalhes: Todos os 8 testes passaram, cobrindo config válida e 6 casos de config inválida (peso negativo, campo Shopee ausente, item sem peso, item sem id, intervalo_horas inválido, limite_slots inválido).

- **[PASSOU] [executado] Critério 2: `config.example.toml` é TOML válido**
  Comando: `python -m uv run python -c "import tomllib, pathlib; tomllib.loads(pathlib.Path('config.example.toml').read_text())"`
  Saída: Sem erros (execução bem-sucedida)

- **[PASSOU] [executado] Critério 3: `uv run ruff check src/shopee_rodizio/config.py` → sem erros**
  Comando: `python -m uv run ruff check src/shopee_rodizio/config.py`
  Saída: `All checks passed!`

Suíte completa: 8 passou, 0 falhou
Graus de prova: 3 executados, 0 inspecionados, 0 julgados



## Conformidade

Conformidade: cumpre

- `uv run pytest tests/test_config.py -q` com config válida e ≥2 casos inválidos (peso
  negativo, campo Shopee ausente) → `tests/test_config.py` (8 testes: 1 válido + 6 inválidos,
  incluindo os 2 exigidos) confirmado executando na Verificação (Ciclo 1: `8 passed in
  0.14s`).
- `config.example.toml` é TOML válido → `config.example.toml` (raiz do projeto), confirmado
  executando na Verificação (Ciclo 1, Critério 2: sem erros).
- `uv run ruff check src/shopee_rodizio/config.py` sem erros → confirmado executando na
  Verificação (Ciclo 1, Critério 3: `All checks passed!`).
- Estrutura tipada com dataclasses (`ShopeeCredenciais`, `CicloConfig`, `CaminhosConfig`,
  `Item`, `Config`) e função pública `carregar_config(caminho)` → `src/shopee_rodizio/config.py:14-63`.
- `endpoint_boost` tratado como campo configurável opaco (só existência verificada, não uso)
  → `src/shopee_rodizio/config.py:35-38` e `_CAMPOS_CICLO`; consistente com
  `_gestao/DECISOES.md` ("Endpoint de boost da Shopee: incerteza registrada") — uso fica
  para T-004/T-005, exatamente como o Contexto da tarefa exige.
- Todas as validações do Contexto implementadas com mensagem identificando o campo: item
  sem `id`/`peso`, `peso <= 0`, `intervalo_horas <= 0`, `limite_slots <= 0`, seção `[shopee]`
  incompleta → `src/shopee_rodizio/config.py:66-101` (`_validar`, `_validar_secao`,
  `_validar_item`).
- Nenhuma dependência nova (só `tomllib` da stdlib) → conforme `_gestao/DECISOES.md` ("Stack:
  Python + uv").

Objetivo satisfeito no espírito: `config.py` entrega exatamente a superfície que as tarefas
seguintes (T-004 em diante) vão consumir, sem antecipar uso do `endpoint_boost` fora de
escopo.

Nota de processo (não afeta a conformidade de T-002 em si): o commit `bd231b6` também traz
a conclusão da revisão de T-001 (Conformidade/Revisão preenchidas, status → `concluida`) e
a mudança de status de T-003 (`backlog` → `pronta`) — arquivos fora das `areas` declaradas
para T-002. Pela cronologia dos commits (`9120c72` T-001 hash da revisão vem antes de
`bd231b6`), isso indica que essas edições estavam pendentes de commit no diretório de
trabalho quando o executor de T-002 commitou, e foram arrastadas junto — não é trabalho que
o agente de T-002 tenha feito por conta própria fora de escopo.

## Revisão

Aprovado sem ressalvas. Verificado no diff de `bd231b6` (`src/shopee_rodizio/config.py`,
`tests/test_config.py`, `config.example.toml`):

- Fluxo de validação (`_validar` → `_validar_secao` → `_validar_item`) é direto e sem
  atalho: nenhuma seção nem campo obrigatório é silenciado; toda falha vira `ConfigError`
  com o nome do campo.
- Casos de borda dos testes conferidos manualmente contra o código: `test_item_sem_peso` e
  `test_item_sem_id` usam `str.replace` em ocorrência única no TOML de exemplo (`"peso = 3\n"`,
  `"id = 111\n"`), sem colisão com o segundo item (`peso = 1`) — os testes realmente exercitam
  o item `itens[0]`, não um efeito colateral de substituição múltipla.
- `_validar_secao` filtra a seção bruta para só os campos esperados antes do
  `**shopee`/`**ciclo`/`**caminhos` — não há risco de `TypeError` por chave extra no TOML do
  usuário.
- Nenhuma lógica de rede, segredo hardcoded ou I/O além da leitura do arquivo apontado por
  `caminho`; sem superfície de injeção (o TOML é parseado por `tomllib`, não interpretado).
- `[menor]` `src/shopee_rodizio/config.py:99` — `item["peso"] <= 0` presume `peso` numérico;
  um TOML com `peso = "3"` (string) levantaria `TypeError` em vez de `ConfigError` com
  mensagem clara. Não é critério de aceite desta tarefa (que só exige validar peso ausente
  e peso `<= 0`) e é cenário de erro de digitação do próprio usuário editando o TOML à mão —
  não bloqueia.
