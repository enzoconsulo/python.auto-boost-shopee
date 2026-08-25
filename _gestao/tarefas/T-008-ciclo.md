---
id: T-008
titulo: Orquestração do ciclo de rodízio e loop de agendamento
projeto: shopee-rodizio
status: em-teste
prioridade: alta
dependencias: [T-003, T-005, T-006, T-007]
areas: [src/shopee_rodizio/ciclo.py, src/shopee_rodizio/__main__.py, tests/test_ciclo.py]
tentativas: 1
agente: operacao-sbc
criada: 2026-08-24
atualizada: 2026-08-25
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
- [x] `uv run pytest tests/test_ciclo.py -q` → todos os testes passam, incluindo: ciclo com
      todos os boosts com sucesso, ciclo com pelo menos um boost falhando (rede ou API) sem
      que a exceção escape, e o histórico (estado) é gravado ao final do ciclo em ambos os
      casos.
      `verificar: uv run pytest tests/test_ciclo.py -q`
- [x] `uv run python -m shopee_rodizio --help` (ou equivalente) não lança traceback — mostra
      uso esperado do comando.
      `verificar: uv run python -m shopee_rodizio --help`
- [x] `uv run ruff check src/shopee_rodizio/ciclo.py src/shopee_rodizio/__main__.py` → sem
      erros.
      `verificar: uv run ruff check src/shopee_rodizio/ciclo.py src/shopee_rodizio/__main__.py`

## Notas de execução

### Ciclo 1

**Implementado:**
- `src/shopee_rodizio/ciclo.py` — `executar_ciclo(cliente, config, estado) -> Estado`:
  seleciona itens via `selecao.selecionar`, chama `boost.impulsionar` (módulo importado, não
  a função diretamente — necessário para o `patch.object(boost, "impulsionar", ...)` dos
  testes funcionar) para cada um, grava cada resultado via `estado.registrar_boost` (que já
  persiste em disco atomicamente) e loga (INFO em sucesso, WARNING em falha). Cada item é
  envolvido num `try/except Exception` — defesa em profundidade (RF-06): mesmo
  `boost.impulsionar` já não devendo lançar, um bug futuro em qualquer módulo abaixo vira
  falha registrada no histórico, não uma exceção que propaga.
- `src/shopee_rodizio/__main__.py` — `executar_loop(caminho_config, *, max_iteracoes=None)`:
  carrega config, configura logging, cria `ClienteShopee` a partir da config (token
  `expira_em=None`, então o cliente renova o `access_token` sozinho na primeira chamada) e
  carrega o `Estado`. Loop `while max_iteracoes is None or iteracao < max_iteracoes`: chama
  `executar_ciclo` dentro de outro `try/except Exception` (segunda camada de defesa, cobrindo
  também `selecao`/`estado`, não só `boost`), loga erro inesperado com `logger.exception` e
  segue; depois dorme `config.ciclo.intervalo_horas * 3600`. `max_iteracoes` existe só para
  teste (evita loop infinito/`sleep` real de 4h); em produção fica `None` e o loop não para.
  `main()` usa `argparse` com um argumento posicional opcional `config` (padrão
  `config.toml`) — `--help`/`-h` é tratado pelo próprio `argparse`, que sai com código 0
  antes de qualquer tentativa de carregar config (por isso `--help` funciona mesmo sem
  `config.toml` no diretório).
- `tests/test_ciclo.py` — 7 casos: sucesso em todos os itens; um boost falhando por erro de
  API (retorno `ResultadoBoost(sucesso=False, ...)`, sem lançar) sem que os demais itens
  sejam afetados; um boost lançando exceção inesperada (`ConnectionError`) sem que ela escape
  de `executar_ciclo`; respeito ao `limite_slots`; ciclo sem itens não grava nada; loop
  principal roda um número limitado de iterações sem travar (com `time.sleep` mockado); loop
  principal segue rodando mesmo quando `executar_ciclo` lança (RF-06 na camada do loop).

**Decisão de teste:** `ciclo.py` importa `from . import boost` (módulo) em vez de
`from .boost import impulsionar` — só assim `patch.object(boost, "impulsionar", ...)` nos
testes intercepta a chamada; com import direto da função o patch não teria efeito (o nome já
estaria vinculado no namespace de `ciclo.py` antes do patch).

**Achado corrigido no caminho:** a fixture `_config_arquivo` inicialmente usava caminhos
relativos (`log = "shopee-rodizio.log"`, `estado = "estado.json"`) no TOML de teste — como o
`pytest` roda com cwd na raiz do projeto, os dois testes do loop principal estavam gravando
`estado.json` e `shopee-rodizio.log` de verdade na raiz do repositório a cada execução da
suíte. Corrigido para usar caminhos absolutos dentro de `tmp_path`; os dois arquivos vazados
foram apagados antes do commit (não fazem parte da entrega).

**Verificação manual (fora do pytest):** rodei `executar_loop` com config real (TOML de
tempdir), `boost.impulsionar` mockado e `time.sleep` mockado por 2 iterações — confirmei que
`estado.json` e o arquivo de log são gravados corretamente com os dois registros esperados
(ver saída no relatório final).

**Reproduzir:**
`.venv\Scripts\python.exe -m pytest tests/test_ciclo.py -q`
`.venv\Scripts\python.exe -m shopee_rodizio --help`
`.venv\Scripts\python.exe -m ruff check src/shopee_rodizio/ciclo.py src/shopee_rodizio/__main__.py`

**Nota sobre o comando dos critérios:** `uv` não está no PATH desta máquina; os comandos
acima com `.venv\Scripts\python.exe -m ...` são equivalentes e foram os efetivamente
executados (ver memória de projeto sobre isso, já registrada em ciclos anteriores).

**Commit:** `PLACEHOLDER`

## Verificação


## Conformidade


## Revisão
