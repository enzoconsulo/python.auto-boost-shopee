---
id: T-007
titulo: Log em arquivo com rotação
projeto: shopee-rodizio
status: backlog
prioridade: media
dependencias: [T-002]
areas: [src/shopee_rodizio/logging_config.py, tests/test_logging_config.py]
tentativas: 0
agente: operacao-sbc
criada: 2026-08-24
atualizada: 2026-08-24
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


## Verificação


## Conformidade


## Revisão
