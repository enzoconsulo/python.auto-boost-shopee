---
id: T-003
titulo: Persistência de estado (histórico de boosts em JSON)
projeto: shopee-rodizio
status: concluida
prioridade: alta
dependencias: [T-001]
areas: [src/shopee_rodizio/estado.py, tests/test_estado.py]
tentativas: 1
agente: config-estado
criada: 2026-08-24
atualizada: 2026-08-24
---

## Objetivo
Implementar `src/shopee_rodizio/estado.py`: persiste e lê, em JSON local, o histórico de
impulsionamentos (item_id, timestamp, sucesso/erro, mensagem), com escrita atômica, e
expõe uma função de consulta ao histórico recente por item (usada pelo sorteio em T-006).

## Contexto
Formato do arquivo de estado (caminho vem de `config.caminhos.estado`, T-002):

```json
{
  "historico": [
    {"item_id": 123456789, "timestamp": "2026-08-24T12:00:00+00:00", "sucesso": true, "mensagem": "ok"}
  ]
}
```

Escrita ATÔMICA: grave em arquivo temporário no mesmo diretório (`estado.json.tmp`) e
faça `os.replace()` (rename atômico) para o caminho final — nunca escreva direto por cima
do arquivo original, para que uma queda de energia no meio da escrita (cenário real: SBC
sem UPS) não corrompa o histórico. Se o arquivo de estado não existir ainda (primeira
execução), trate como histórico vazio, não como erro.

Exponha algo como `registrar_boost(estado, item_id, sucesso, mensagem)` e
`historico_recente(estado, item_id) -> list[...]` (usado por T-006 para eventualmente
evitar repetir o mesmo item dois ciclos seguidos, se o peso permitir escolha).

## Critérios de aceite
- [ ] `uv run pytest tests/test_estado.py -q` → todos os testes passam, incluindo: gravar e
      reler histórico, primeira execução sem arquivo prévio não lança erro, e a escrita usa
      arquivo temporário + rename (teste inspeciona que não sobra `.tmp` órfão ao final de
      uma escrita normal).
      `verificar: uv run pytest tests/test_estado.py -q`
- [ ] `uv run ruff check src/shopee_rodizio/estado.py` → sem erros.
      `verificar: uv run ruff check src/shopee_rodizio/estado.py`

## Notas de execução

Testes escritos antes do código (`tests/test_estado.py`), rodados e vistos falhar
(`ModuleNotFoundError: No module named 'shopee_rodizio.estado'`) antes de implementar
`src/shopee_rodizio/estado.py`.

Implementado `estado.py` com:
- `RegistroBoost` (dataclass frozen: item_id, timestamp ISO 8601 UTC, sucesso, mensagem).
- `Estado` (dataclass frozen: caminho + lista de `RegistroBoost`), imutável — cada
  `registrar_boost` devolve um novo `Estado`, sem mutar o recebido.
- `carregar_estado(caminho)`: lê o JSON; se o arquivo não existir, devolve histórico
  vazio sem erro (primeira execução).
- `registrar_boost(estado, item_id, sucesso, mensagem)`: acrescenta um registro (com
  timestamp gerado em UTC) e grava em disco.
- `historico_recente(estado, item_id)`: filtra o histórico em memória por `item_id`, em
  ordem cronológica (usado por T-006).
- `_gravar`: escrita atômica — grava em `<caminho>.tmp` (cria o diretório pai se
  necessário) e faz `os.replace()` para o caminho final, para que uma queda de energia
  no meio da escrita (SBC sem UPS) não corrompa `estado.json`.

Nenhuma dependência nova (usa apenas `json`, `os`, `dataclasses`, `datetime`, `pathlib`
da stdlib).

**Reproduzir:** `export PATH="/c/Users/enzoc/AppData/Roaming/Python/Python312/Scripts:$PATH" && uv run pytest tests/test_estado.py -q && uv run ruff check src/shopee_rodizio/estado.py`

**Commit:** `786279b`

## Verificação

### Passada mecânica (sem modelo)

- [julgado] `uv run pytest tests/test_estado.py -q` → todos os testes passam, incluindo: gravar e reler histórico, primeira execução sem arquivo prévio não lança erro, e a escrita usa arquivo temporário + rename (teste inspeciona que não sobra `.tmp` órfão ao final de uma escrita normal). — comando recusado: binario-nao-permitido; fica para o verificador.
- [julgado] `uv run ruff check src/shopee_rodizio/estado.py` → sem erros. — comando recusado: binario-nao-permitido; fica para o verificador.

Graus de prova: 0 executado(s), 2 para julgamento (de 2).

### Ciclo 2

- **[PASSOU] [executado] Critério 1: `uv run pytest tests/test_estado.py -q` → todos os testes passam**
  Comando: `uv run pytest tests/test_estado.py -q`
  Saída: `6 passed in 0.16s`

- **[PASSOU] [executado] Critério 2: `uv run ruff check src/shopee_rodizio/estado.py` → sem erros**
  Comando: `uv run ruff check src/shopee_rodizio/estado.py`
  Saída: `All checks passed!`

Suíte completa: 6 passou — `uv run pytest tests/test_estado.py -q`

Mutação: removi `registro` da lista em `registrar_boost` → a prova FALHOU (esperado) com 3 testes falhando corretamente

Graus de prova: 2 executado(s), 0 inspecionado(s), 0 julgado(s)



## Conformidade

Conformidade: cumpre

- Persiste histórico (item_id, timestamp, sucesso, mensagem) em JSON no formato exato do
  Contexto → `RegistroBoost`/`Estado` + `carregar_estado`/`_gravar` em
  `src/shopee_rodizio/estado.py:12-59`.
- Escrita atômica via arquivo `.tmp` + `os.replace()` → `_gravar` em
  `src/shopee_rodizio/estado.py:56-60`; coberto por
  `test_escrita_usa_arquivo_temporario_e_nao_sobra_tmp_orfao`.
- Primeira execução sem arquivo prévio não lança erro → `carregar_estado`
  (`src/shopee_rodizio/estado.py:22-24`); coberto por
  `test_primeira_execucao_sem_arquivo_previo_nao_lanca_erro`.
- `registrar_boost(estado, item_id, sucesso, mensagem)` e `historico_recente(estado, item_id)`
  expostos exatamente com a assinatura sugerida no Objetivo/Contexto
  (`src/shopee_rodizio/estado.py:31-49`).
- Critério 1 (`uv run pytest tests/test_estado.py -q`) → confirmado na Verificação: 6 passou.
- Critério 2 (`uv run ruff check src/shopee_rodizio/estado.py`) → confirmado na Verificação:
  All checks passed.
- Sem dependência nova (só stdlib), consistente com a decisão de stack registrada em
  `_gestao/DECISOES.md` (2026-08-24 — Stack: Python + uv, que já lista `json` da stdlib para
  persistência de estado). Sem escopo além do pedido.

## Revisão

Aprovado sem ressalvas quanto a correção. Verifiquei: `carregar_estado` trata ausência de
arquivo e reidrata `RegistroBoost` a partir do JSON; `registrar_boost` não muta o `Estado`
recebido (constrói lista nova antes de gravar); `_gravar` cria o diretório pai, escreve em
`<caminho>.tmp` no mesmo diretório e usa `os.replace()` — rename atômico de fato, e no mesmo
filesystem que o destino, então não corrompe em queda de energia. `historico_recente` preserva
a ordem cronológica porque o histórico só cresce por append. Rodei a suíte e o lint
manualmente e confirmei os mesmos resultados da Verificação (6 passed; ruff limpo em
`estado.py`).

- [menor] `tests/test_estado.py:1` — `from pathlib import Path` importado e nunca usado
  (`ruff check tests/test_estado.py` acusa `F401`). O critério de aceite só exige lint limpo
  em `src/shopee_rodizio/estado.py`, então não bloqueia, mas vale corrigir na próxima
  passagem por esse arquivo.
