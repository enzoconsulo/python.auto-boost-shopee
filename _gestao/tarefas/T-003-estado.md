---
id: T-003
titulo: Persistência de estado (histórico de boosts em JSON)
projeto: shopee-rodizio
status: pronta
prioridade: alta
dependencias: [T-001]
areas: [src/shopee_rodizio/estado.py, tests/test_estado.py]
tentativas: 0
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


## Verificação


## Conformidade


## Revisão
