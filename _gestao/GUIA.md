# GUIA — shopee-rodizio

Como este projeto é organizado e como se faz cada coisa nele. Escrito à mão; o índice
exaustivo de símbolos é o `MAPA.md` ao lado, que é GERADO — ver
`_sistema/PADRAO_DE_PROJETO.md` para a divisão de trabalho entre os dois.

## 1. Em uma tela

- **O que é:** serviço 24/7 num BigTreeTech Pi 1.2.1 que faz rodízio automático de
  impulsionamento de anúncios na Shopee via Shopee Open Platform API.
- **Stack:** Python (gerenciado por `uv`), `requests` para HTTP, `tomllib`/`json` (stdlib)
  para config e estado, loop próprio (`time.sleep`) para agendamento.
- **Rodar:** `uv run python -m shopee_rodizio`
- **Testar:** `uv run pytest -q` — é ele que a fábrica roda em toda verificação.

## 2. Onde fica o quê

| módulo | responsabilidade | quando mexer aqui |
|---|---|---|
| `src/shopee_rodizio/config.py` | carrega e valida a configuração (TOML): credenciais, peso por item, intervalo do rodízio | mudar como a config é lida ou validada |
| `src/shopee_rodizio/estado.py` | persiste o estado do rodízio (JSON) entre execuções | mudar o que é lembrado entre ciclos |
| `src/shopee_rodizio/cliente_shopee.py` | cliente HTTP da Shopee Open Platform (assinatura, autenticação, chamadas) | mudar autenticação ou endpoints da Shopee |
| `src/shopee_rodizio/boost.py` | aciona o impulsionamento de um item | mudar a lógica de acionar boost |
| `src/shopee_rodizio/selecao.py` | seleciona o próximo item a impulsionar respeitando o peso configurável | mudar o algoritmo de rodízio ponderado |
| `src/shopee_rodizio/ciclo.py` | orquestra um ciclo: seleciona, impulsiona cada item, grava histórico; nenhum item derruba os demais | mudar a sequência ou a defesa contra falha de um item |
| `src/shopee_rodizio/__main__.py` | entrypoint: carrega config, configura logging, loop `while True` a cada `intervalo_horas`, persiste o token renovado (`token.json`) para sobreviver a restart | mudar o agendamento, o loop principal, ou a persistência do token |
| `src/shopee_rodizio/logging_config.py` | configura logging do serviço | mudar formato/destino dos logs |
| `scripts/smoke_test.py` | diagnóstico manual: faz UMA chamada real de boost contra a API para confirmar `endpoint_boost` | confirmar/depurar o endpoint com credenciais reais (não roda em CI) |
| `systemd/shopee-rodizio.service` | unidade systemd para deploy 24/7 no BTT Pi (`Restart=on-failure`) | mudar como o serviço é deployado/reiniciado |

## 3. Receitas

### Para rodar os testes localmente
1. `uv run pytest -q` — roda a suíte.
2. `uv run ruff check .` — lint.

## 4. Já existe — não reinvente

| preciso de… | use | onde |
|---|---|---|
| dependência HTTP | `requests` (já no `pyproject.toml`) | `pyproject.toml` |

## Armadilhas conhecidas

- `uv` não estava no PATH do ambiente de execução; foi instalado via `pip install --user uv`
  e resolvido em `~/AppData/Roaming/Python/Python312/Scripts/uv.exe`. Se `uv` "não for
  encontrado", verifique esse caminho antes de reinstalar — ou use
  `.venv\Scripts\python.exe -m ...` como equivalente.
- `grep` também não está no PATH do shell não-interativo (só existe em `Git\usr\bin`, dentro
  do Git for Windows). Em comando `verificar:` de tarefa, use `find /C "str" arquivo`
  (nativo do Windows) em vez de `grep -c`.
- O endpoint de boost (`ciclo.endpoint_boost`) é um palpite não confirmado contra a Shopee
  — ver `_gestao/DECISOES.md`. Rode `scripts/smoke_test.py` antes de produção contínua.
