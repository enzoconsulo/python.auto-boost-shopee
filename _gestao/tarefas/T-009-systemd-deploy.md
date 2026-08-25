---
id: T-009
titulo: Unidade systemd e documentação de deploy no BTT Pi
projeto: shopee-rodizio
status: em-teste
prioridade: media
dependencias: [T-008]
areas: [systemd/shopee-rodizio.service, README.md]
tentativas: 1
agente: operacao-sbc
criada: 2026-08-24
atualizada: 2026-08-25
---

## Objetivo
Criar `systemd/shopee-rodizio.service` (unidade systemd que sobe o serviço no boot e
reinicia sozinho em caso de crash) e documentar no README, passo a passo, como instalar e
ativar no BigTreeTech Pi 1.2.1 (mesmo SBC do Klipper).

## Contexto
A unidade deve ter, no mínimo: `Restart=on-failure` (RF-08), `WorkingDirectory` apontando
para o diretório do projeto no SBC, `ExecStart` chamando o entrypoint via `uv run python -m
shopee_rodizio <caminho-do-config>` (ou o binário resolvido por `uv`, documentado), e rodar
sob um usuário sem privilégio de root (o mesmo usuário que já roda o Klipper costuma
servir — documente isso como recomendação, não obrigação, já que o agente não tem acesso
ao SBC real para confirmar o usuário exato).

O README precisa documentar, em passos concretos: (1) como copiar/clonar o projeto para o
BTT Pi, (2) como instalar `uv` no SBC (ou confirmar que já está disponível), (3) como criar
o `config.toml` real a partir de `config.example.toml` (T-002) com as credenciais Shopee
do usuário, (4) `sudo cp systemd/shopee-rodizio.service /etc/systemd/system/` +
`sudo systemctl daemon-reload` + `sudo systemctl enable --now shopee-rodizio` (ou os
comandos equivalentes reais), (5) como acompanhar o log (`journalctl -u shopee-rodizio -f`
e/ou o arquivo de log configurado em T-007).

Como o agente não tem acesso ao BTT Pi real, o critério da unidade `.service` é de
inspeção/sintaxe, não de execução — mas verifique a sintaxe com `systemd-analyze verify` se
a ferramenta estiver disponível no ambiente do agente; se não estiver, registre isso nas
Notas de execução e valide manualmente contra a documentação de unit files do systemd
(seções `[Unit]`, `[Service]`, `[Install]` presentes e coerentes).

## Critérios de aceite
- [ ] `systemd/shopee-rodizio.service` existe com as seções `[Unit]`, `[Service]`
      (incluindo `Restart=on-failure` e `ExecStart`) e `[Install]`.
      `verificar: grep -c Restart=on-failure systemd/shopee-rodizio.service`
- [ ] README.md tem uma seção de deploy com os 5 passos descritos no Contexto, com
      comandos reais (não placeholder).
- [ ] `uv run ruff check .` continua sem erro após esta tarefa (nenhum código Python novo
      quebrando lint).
      `verificar: uv run ruff check .`

## Notas de execução

Criado `systemd/shopee-rodizio.service` com as três seções exigidas — `[Unit]`
(`After=network-online.target`/`Wants=network-online.target`), `[Service]`
(`Type=simple`, `User=pi`, `Group=pi`, `WorkingDirectory=/home/pi/shopee-rodizio`,
`ExecStart=/home/pi/.local/bin/uv run python -m shopee_rodizio /home/pi/shopee-rodizio/config.toml`,
`Restart=on-failure`, `RestartSec=10`) e `[Install]` (`WantedBy=multi-user.target`). Usei o
caminho absoluto de `uv` (`~/.local/bin/uv`, resolvido, não o binário no `PATH`) porque
unidades systemd não carregam o `PATH` do shell interativo — documentado no comentário de
topo do arquivo e no passo 2 do README. `User=pi`/`/home/pi/...` são a recomendação (mesmo
usuário do Klipper), não obrigação — comentário no topo do `.service` e o texto do README
deixam explícito que são só o palpite mais provável, a ajustar no deploy real.

Adicionada ao README.md a seção "Deploy no BTT Pi (systemd)" com os 5 passos do Contexto:
(1) clonar/copiar via `git clone`/`scp`, (2) instalar `uv` via `curl -LsSf
https://astral.sh/uv/install.sh | sh` (com nota de conferir se já não está disponível),
(3) `cp config.example.toml config.toml` + editar, (4) `sudo cp` da unidade +
`daemon-reload` + `enable --now`, (5) `journalctl -u shopee-rodizio -f` e/ou `tail -f` do
arquivo de log configurado em `[caminhos].log`.

`systemd-analyze` não está disponível neste ambiente de agente (Windows, sem systemd
instalado — confirmado via `which systemd-analyze`); validei a sintaxe manualmente contra
a documentação de unit files: as três seções `[Unit]`/`[Service]`/`[Install]` estão
presentes, com chaves reconhecidas do systemd e coerentes entre si (`WantedBy` em
`[Install]` correspondendo a um serviço `Type=simple` de longa duração).

Nenhum código Python foi criado ou alterado nesta tarefa — `uv run ruff check .`
(via `.venv\Scripts\python.exe -m ruff check .`, já que `uv` não está no `PATH` deste
agente) passou sem erro, como esperado por não haver mudança em `.py`.

**Reproduzir:**
```
grep -c "Restart=on-failure" systemd/shopee-rodizio.service
.venv\Scripts\python.exe -m ruff check .
```

**Commit:** `9eae83f`

## Verificação


## Conformidade


## Revisão
