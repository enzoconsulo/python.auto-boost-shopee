# shopee-rodizio

Serviço leve que roda 24/7 num BigTreeTech Pi 1.2.1 (mesmo SBC que controla o Klipper da
Ender 3 V3 SE) e faz rodízio automático de impulsionamento de anúncios na Shopee, via
Shopee Open Platform API, respeitando um peso configurável por item.

Este projeto faz parte da fábrica Gerador_de_projetos. Gestão (especificação, plano,
tarefas, decisões) em `_gestao/`; o protocolo de tarefas está em
`../../_sistema/PROTOCOLO_TAREFAS.md`. Trabalhe em português (BR).

## Stack

Python >=3.12, gerenciado por `uv`. Dependência de runtime: `requests` (HTTP). Config em
TOML (`tomllib`, stdlib), estado e token persistidos em JSON (stdlib), agendamento via
loop próprio (`time.sleep`) — sem framework de scheduler nem banco de dados. Dev:
`pytest` + `ruff`.

## Como rodar

```
uv run python -m shopee_rodizio [caminho/para/config.toml]   # padrão: ./config.toml
```

Smoke-test manual contra a API real (uma chamada de boost de verdade, não roda em CI):

```
uv run python scripts/smoke_test.py caminho/para/config.toml
```

Deploy 24/7 no BTT Pi via systemd: ver seção "Deploy no BTT Pi (systemd)" do `README.md`.

## Como testar

```
uv run pytest -q
uv run ruff check .
```

## Arquitetura em 1 minuto

- `src/shopee_rodizio/config.py` — carrega e valida `config.toml` (credenciais, itens com
  peso, intervalo do ciclo).
- `src/shopee_rodizio/cliente_shopee.py` — cliente HTTP da Shopee Open Platform API v2:
  assinatura HMAC-SHA256, renovação automática do `access_token` expirado.
- `src/shopee_rodizio/boost.py` — chama o endpoint de impulsionamento de UM item.
- `src/shopee_rodizio/selecao.py` — sorteio ponderado (sem reposição) dos itens de um ciclo.
- `src/shopee_rodizio/estado.py` — histórico de boosts em JSON, escrita atômica (tmp +
  `os.replace`).
- `src/shopee_rodizio/ciclo.py` — orquestra um ciclo: seleciona, impulsiona cada item,
  grava histórico; nunca deixa uma falha de item escapar.
- `src/shopee_rodizio/__main__.py` — entrypoint: carrega config, configura logging, entra
  no loop `while True: executar_ciclo(...); sleep(intervalo_horas * 3600)`; persiste o
  token renovado (`token.json`, irmão do `estado.json`) para sobreviver a um restart do
  systemd.
- `src/shopee_rodizio/logging_config.py` — log em arquivo com rotação por tamanho.
- `scripts/smoke_test.py` — diagnóstico manual de `endpoint_boost` contra a API real.
- `systemd/shopee-rodizio.service` — unidade para deploy 24/7 no BTT Pi.

`_gestao/MAPA.md` tem a assinatura de cada símbolo público; regenere com
`node ../../_sistema/ferramentas/mapa.mjs .` após mudança estrutural.

## Convenções

- Testes em português, nomeando o comportamento (`test_ciclo_com_boost_falhando_...`).
- Módulos internos que precisam ser interceptados por `patch.object` em teste são
  importados como módulo (`from . import boost`), não a função direta — ver `ciclo.py`.
- Dataclasses de domínio (`Token`, `Item`, etc.) são `frozen=True`; comparação de token
  por valor é o que detecta renovação em `__main__.executar_loop`.
- Escrita em disco de estado/token é sempre atômica (arquivo temporário + `os.replace`).

## Armadilhas conhecidas

- **`uv` não está no PATH** do shell não-interativo desta máquina (fora do Git Bash). Use
  `.venv\Scripts\python.exe -m pytest` / `-m ruff check .` / `-m shopee_rodizio` como
  equivalente. Caminho resolvido do binário:
  `~/AppData/Roaming/Python/Python312/Scripts/uv.exe` (instalado via `pip install --user uv`).
- **`grep` também não está no PATH** do shell não-interativo (só existe dentro do Git for
  Windows, em `Git\usr\bin`). Em comando `verificar:` de tarefa, prefira `find /C "str" arquivo`
  (nativo do Windows, mesma semântica de contagem de substring que `grep -c` para casos
  sem regex) ou `Select-String`/`findstr`.
- O endpoint de impulsionamento (`ciclo.endpoint_boost` em `config.toml`) e os nomes de
  parâmetro em `boost.py` são um palpite plausível, não confirmado contra a documentação
  pública da Shopee — ver `_gestao/DECISOES.md`. Rode `scripts/smoke_test.py` com
  credenciais reais antes de colocar em produção contínua.
- Unidades systemd não carregam o `PATH` do shell interativo — `ExecStart` usa o caminho
  absoluto do `uv` (`~/.local/bin/uv`), não o binário do `PATH`.
