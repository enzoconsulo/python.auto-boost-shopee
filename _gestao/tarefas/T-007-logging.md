---
id: T-007
titulo: Log em arquivo com rotação
projeto: shopee-rodizio
status: em-revisao
prioridade: media
dependencias: [T-002]
areas: [src/shopee_rodizio/logging_config.py, tests/test_logging_config.py]
tentativas: 1
agente: operacao-sbc
criada: 2026-08-24
atualizada: 2026-08-25
---

## Objetivo
Implementar `src/shopee_rodizio/logging_config.py`: configura logging do projeto para
escrever em arquivo (caminho de `config.caminhos.log`) com rotação por tamanho, usando
`logging.handlers.RotatingFileHandler` da stdlib — sem adicionar dependência de log.

## Contexto
Exponha uma função `configurar(caminho_log: str, max_bytes=..., backup_count=...) -> None`
(ou equivalente) que o entrypoint (T-008) chama uma vez no início do processo. Formato de
linha deve incluir timestamp, nível e mensagem — é o que o usuário vai ler com `tail -f`
para auditar o que foi impulsionado e quando (RF-07). Valores padrão razoáveis para um
SBC com pouco espaço em disco (ex.: `max_bytes` na casa de poucos MB, `backup_count`
pequeno, tipo 3) — documente o padrão escolhido nas Notas de execução.

## Critérios de aceite
- [ ] `uv run pytest tests/test_logging_config.py -q` → todos os testes passam, incluindo
      um teste que escreve várias mensagens forçando rotação (arquivo pequeno de propósito
      no teste) e confirma que um arquivo `.1` (backup) é criado.
      `verificar: uv run pytest tests/test_logging_config.py -q`
- [ ] `uv run ruff check src/shopee_rodizio/logging_config.py` → sem erros.
      `verificar: uv run ruff check src/shopee_rodizio/logging_config.py`

## Notas de execução

Implementado `src/shopee_rodizio/logging_config.py` com uma única função pública
`configurar(caminho_log: str, max_bytes: int = ..., backup_count: int = ...) -> None`,
que configura o logger nomeado `"shopee_rodizio"` com um `RotatingFileHandler` (stdlib).
Formato de linha: `%(asctime)s %(levelname)s %(message)s` (`asctime` no formato
`AAAA-MM-DD HH:MM:SS`) — dá para auditar com `tail -f` o que foi impulsionado e quando
(RF-07).

Padrões escolhidos para o SBC (pouco espaço em disco): `max_bytes=2 MiB`,
`backup_count=3` — até ~8 MiB de log no total. `configurar` cria o diretório pai de
`caminho_log` se não existir, e é idempotente (fecha e remove handlers antigos antes de
adicionar o novo), para suportar reconfiguração sem duplicar linhas — não há uso disso no
projeto ainda (T-008 chama uma vez no início do processo), mas evita duplicação
silenciosa se algum teste ou script futuro chamar mais de uma vez no mesmo processo.

Arquivos criados:
- `src/shopee_rodizio/logging_config.py`
- `tests/test_logging_config.py` (5 casos: escreve e persiste mensagem, formato de linha
  com timestamp/nível/mensagem, rotação por tamanho gera `.1`, cria diretório pai
  ausente, chamada dupla não duplica handlers — todos escritos antes da implementação e
  vistos falhar por `ModuleNotFoundError` antes de existir o módulo).

Nenhuma dependência nova (só `logging`/`logging.handlers`/`pathlib` da stdlib, conforme
pedido pela tarefa).

**Reproduzir:** `.venv\Scripts\python.exe -m pytest tests/test_logging_config.py -q`

**Commit:** `cbcf02d`

## Verificação

### Ciclo 2

- **[PASSOU] [executado] Critério 1: `uv run pytest tests/test_logging_config.py -q` → todos os testes passam, incluindo um teste que escreve várias mensagens forçando rotação (arquivo pequeno de propósito no teste) e confirma que um arquivo `.1` (backup) é criado.**
  Comando: `.venv\Scripts\python.exe -m pytest tests/test_logging_config.py -q`
  Saída: `.....` (5 passed in 0.51s)

- **[PASSOU] [executado] Critério 2: `uv run ruff check src/shopee_rodizio/logging_config.py` → sem erros.**
  Comando: `.venv\Scripts\python.exe -m ruff check src/shopee_rodizio/logging_config.py`
  Saída: `All checks passed!`

Suíte completa: 40 passed — `.venv\Scripts\python.exe -m pytest tests/ -q`
Graus de prova: 3 executados





## Conformidade


## Revisão
