---
id: T-008
titulo: Orquestração do ciclo de rodízio e loop de agendamento
projeto: shopee-rodizio
status: backlog
prioridade: alta
dependencias: [T-003, T-005, T-006, T-007]
areas: [src/shopee_rodizio/ciclo.py, src/shopee_rodizio/__main__.py, tests/test_ciclo.py]
tentativas: 0
agente: operacao-sbc
criada: 2026-08-24
atualizada: 2026-08-24
---

## Objetivo
Implementar `src/shopee_rodizio/ciclo.py` (um ciclo completo: seleciona itens via
`selecao.py`, impulsiona cada um via `boost.py`, grava resultado via `estado.py`, loga via
`logging_config.py`) e `src/shopee_rodizio/__main__.py` (entrypoint: carrega config, loga,
entra no loop `time.sleep(intervalo_horas * 3600)` chamando um ciclo a cada volta). Este é
o módulo que junta tudo — ao final desta tarefa, `uv run python -m shopee_rodizio` executa
o rodízio de verdade contra a API real (dado um `config.toml` válido do usuário).

## Contexto
Invariante mais importante do projeto inteiro (RF-06): **nenhum erro dentro de um ciclo
pode terminar o processo.** Erro de rede, de API, de token — tudo isso já deveria voltar
como resultado estruturado de `cliente_shopee.py`/`boost.py` (T-004/T-005); aqui, mesmo
assim, envolva a execução de cada ciclo num `try/except Exception` amplo que loga e segue
para o próximo ciclo, como última rede de segurança (defesa em profundidade — um bug
futuro em qualquer módulo não deve conseguir derrubar o serviço 24/7).

`__main__.py` deve aceitar o caminho do arquivo de config como argumento (ex.:
`uv run python -m shopee_rodizio caminho/para/config.toml`, com um padrão razoável tipo
`config.toml` no diretório atual se omitido).

Nos testes, mocke `boost.impulsionar` e `time.sleep` (não espere 4h de verdade nem chame a
API real) — teste o CONTEÚDO de um ciclo (`ciclo.py`) diretamente, sem depender do loop
infinito de `__main__.py`; para o loop em si, um teste com `time.sleep` mockado e um limite
de iterações (ex.: parar depois de 2 voltas) é suficiente para provar que ele não quebra.

## Critérios de aceite
- [ ] `uv run pytest tests/test_ciclo.py -q` → todos os testes passam, incluindo: ciclo com
      todos os boosts com sucesso, ciclo com pelo menos um boost falhando (rede ou API) sem
      que a exceção escape, e o histórico (estado) é gravado ao final do ciclo em ambos os
      casos.
      `verificar: uv run pytest tests/test_ciclo.py -q`
- [ ] `uv run python -m shopee_rodizio --help` (ou equivalente) não lança traceback — mostra
      uso esperado do comando.
      `verificar: uv run python -m shopee_rodizio --help`
- [ ] `uv run ruff check src/shopee_rodizio/ciclo.py src/shopee_rodizio/__main__.py` → sem
      erros.
      `verificar: uv run ruff check src/shopee_rodizio/ciclo.py src/shopee_rodizio/__main__.py`

## Notas de execução


## Verificação


## Conformidade


## Revisão
