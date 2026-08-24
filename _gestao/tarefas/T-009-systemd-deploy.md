---
id: T-009
titulo: Unidade systemd e documentação de deploy no BTT Pi
projeto: shopee-rodizio
status: backlog
prioridade: media
dependencias: [T-008]
areas: [systemd/shopee-rodizio.service, README.md]
tentativas: 0
agente: operacao-sbc
criada: 2026-08-24
atualizada: 2026-08-24
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


## Verificação


## Conformidade


## Revisão
