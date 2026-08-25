---
id: T-007
titulo: Log em arquivo com rotação
projeto: shopee-rodizio
status: concluida
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

### Ciclo 1

Conformidade: cumpre

- `RotatingFileHandler` da stdlib configurando o logger `"shopee_rodizio"` → `src/shopee_rodizio/logging_config.py:31-41`, coberto por `tests/test_logging_config.py:test_configurar_cria_arquivo_de_log_com_mensagem` e `test_configurar_rotaciona_quando_arquivo_excede_max_bytes` (rotação por tamanho gera `.1`).
- Assinatura `configurar(caminho_log: str, max_bytes=..., backup_count=...) -> None` bate exatamente com a sugerida no Contexto da tarefa (`logging_config.py:20-24`).
- Formato de linha com timestamp, nível e mensagem (RF-07, auditável com `tail -f`) → `_FORMATO = "%(asctime)s %(levelname)s %(message)s"` com `datefmt="%Y-%m-%d %H:%M:%S"` (`logging_config.py:9-10`), coberto por `test_configurar_formato_de_linha_inclui_timestamp_nivel_e_mensagem`.
- Padrão razoável para SBC com pouco espaço (`max_bytes=2 MiB`, `backup_count=3`, ~8 MiB de teto) documentado nas Notas de execução, conforme pedido explicitamente pelo Contexto.
- Nenhuma dependência nova além da stdlib (`logging`, `logging.handlers`, `pathlib`) — confirmado no diff e sem entrada nova em `DECISOES.md`, correto pois não há decisão de biblioteca a registrar.
- Escopo: tocou só `src/shopee_rodizio/logging_config.py` e `tests/test_logging_config.py`, exatamente as `areas` declaradas no frontmatter — nenhuma sobra.
- Critério 1 (`pytest tests/test_logging_config.py -q`, incluindo o teste de rotação) → reexecutei: 5 passed. Critério 2 (`ruff check src/shopee_rodizio/logging_config.py`) → reexecutei: All checks passed!. Ambos batem com o que o testador registrou na Verificação.

## Revisão

### Ciclo 1

Aprovado sem ressalvas. Verifiquei o diff inteiro de `cbcf02d`:

- `configurar` é idempotente por fechar e remover handlers antigos antes de adicionar o novo (`logging_config.py:34-37`) — chamada dupla no mesmo processo (cenário real: um teste futuro ou um restart de config em `T-008`) não duplica linhas de log, confirmado por `test_configurar_chamado_duas_vezes_nao_duplica_handlers`.
- `caminho.parent.mkdir(parents=True, exist_ok=True)` cobre o caso de `config.caminhos.log` apontar para um diretório ainda não criado no primeiro boot do serviço no SBC — cenário plausível dado que é 24/7 num sistema recém-instalado.
- `encoding="utf-8"` explícito no `RotatingFileHandler` evita o padrão `cp1252` do Windows (ambiente de desenvolvimento atual), o que teria corrompido mensagens com acentos.
- `logger.propagate` fica no padrão (`True`), mas como nada no projeto chama `logging.basicConfig` nem adiciona handler ao logger raiz, não há duplicação de saída — não é achado.
- Suíte completa (40 passed) e lint do projeto seguem verdes após a mudança.
