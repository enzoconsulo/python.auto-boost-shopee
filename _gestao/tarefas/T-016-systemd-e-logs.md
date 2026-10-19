---
id: T-016
titulo: Unidade systemd dependente do túnel, SIGTERM sem falha, ver_logs.sh lendo o log do app
projeto: shopee-rodizio
status: concluida
prioridade: alta
dependencias: [T-014]
areas: [systemd/shopee-rodizio.service, scripts/esperar_porta.sh, scripts/atalhos/ver_logs.sh, scripts/atalhos/status_servico.sh, scripts/atalhos/instalar_servico.sh, README.md]
tentativas: 1
agente: operacao-sbc
criada: 2026-10-19
atualizada: 2026-10-19
---

## Objetivo
Corrigir os defeitos 1.2, 1.3 e 1.4 da auditoria de 2026-10-19.

## Critérios de aceite
- [x] 1.2 — `ver_logs.sh` segue o arquivo de `[caminhos].log` (lido do `config.toml`,
      relativo à raiz do projeto, `tail -F` para sobreviver à rotação); `-j` segue o journal
      do rodízio, do painel e do túnel. `status_servico.sh` mostra as últimas linhas do log
      do app.
- [x] 1.3 — `[Unit]` com `After=`/`Requires=shopee-proxy-tunnel.service`, mais
      `ExecStartPre` que espera a porta SOCKS (`scripts/esperar_porta.sh`, até 30 s): o
      túnel é `Type=simple`, "ativo" não significa "escutando". README documenta que o
      drop-in `tunel.conf` pode ser removido; `instalar_servico.sh` o remove sozinho se ele
      só contiver essas duas linhas.
- [x] 1.4 — `SuccessExitStatus=143`.
- [x] `bash -n` em todos os scripts; `uv run pytest -q` e `uv run ruff check .` passam.

## Notas de execução
O `ExecStart` continua `uv run …` (compatível com o deploy atual: o `uv run` também
sincroniza dependências após um `git pull`). Validado no Pi com `systemd-analyze verify`
(ver PROGRESSO 2026-10-19).
