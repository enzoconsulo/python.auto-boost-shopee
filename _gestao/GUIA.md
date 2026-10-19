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
| `src/shopee_rodizio/__main__.py` | entrypoint: espera o restante do intervalo na subida, relê o `config.toml` a cada ciclo, loop `while True` a cada `intervalo_horas` | mudar o agendamento ou o loop principal |
| `src/shopee_rodizio/logging_config.py` | configura logging do serviço | mudar formato/destino dos logs |
| `src/shopee_rodizio/arquivo.py` | escrita atômica durável e lock entre processos | qualquer nova escrita em disco |
| `src/shopee_rodizio/armazem_token.py` | `token.json` compartilhado entre processos; `cliente_da_config` | qualquer código que chame a Shopee |
| `src/shopee_rodizio/catalogo.py` | catálogo real da loja + cache `catalogo.json` | mudar o que se busca da loja |
| `src/shopee_rodizio/painel.py`, `painel_web/` | painel web só-LAN dos pesos | mudar a página, rotas ou acesso |
| `src/shopee_rodizio/relatorio.py` | agregados do histórico (no ar agora, relatório) | mudar o que o relatório mostra |
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
| gravar arquivo | `gravar_atomico(caminho, texto)` | `arquivo.py` |
| mudar `[[itens]]` do config | `atualizar_itens(caminho, itens, nomes, versao_esperada)` | `config.py` |
| cliente Shopee | `cliente_da_config(config)` — nunca token do config.toml | `armazem_token.py` |
| catálogo da loja | `buscar_item_ids_ativos`, `buscar_detalhes`, `baixar_catalogo` | `catalogo.py` |

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
