---
id: T-003
titulo: Persistência de estado (histórico de boosts em JSON)
projeto: shopee-rodizio
status: em-teste
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

## Verificação


## Conformidade


## Revisão
