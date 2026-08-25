---
id: T-009
titulo: Unidade systemd e documentação de deploy no BTT Pi
projeto: shopee-rodizio
status: concluida
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
      `verificar: find /C "Restart=on-failure" systemd/shopee-rodizio.service`
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

**Fora das `areas` (detectado pelo motor):** test-fase2.log

Estes arquivos foram alterados por esta etapa e estão FORA das `areas` que a
tarefa declarou. Não entram no commit da tarefa, então não aparecem no diff que
o revisor julga — confira se a alteração era legítima (e a `area` é que estava
incompleta) ou se é sobra que precisa ser desfeita.

### Ciclo 2

A reprovação mecânica do primeiro critério (`grep -c Restart=on-failure
systemd/shopee-rodizio.service`) não aponta defeito de conteúdo — aponta ausência da
ferramenta `grep` no shell que rodou a passada mecânica. Confirmado nesta máquina:

- Via Git Bash (a shell deste agente): `grep -c "Restart=on-failure"
  systemd/shopee-rodizio.service` → `1`, saída 0. O arquivo satisfaz o critério.
- Via PowerShell (shell provável da passada mecânica, já que a mensagem de erro
  registrada — `'grep' não é reconhecido como um comando interno ou externo...` — é a
  mensagem padrão do `cmd.exe`/PowerShell do Windows, não do Git Bash): `Get-Command grep`
  não resolve. `C:\Program Files\Git\cmd` está no `PATH`, mas só tem `git.exe` — o `grep`
  de verdade mora em `Git\usr\bin`, que não está no `PATH` do shell não-interativo.

Isto é a mesma classe de problema já registrada para `uv` neste projeto (`uv` também não
está no `PATH` desta máquina fora do Git Bash) — só que agora afeta um comando `verificar:`
de critério, não um comando de execução do agente. Não alterei `systemd/shopee-rodizio.service`
nem o texto do critério (não é meu escopo mudar critério de aceite): o conteúdo já estava
certo desde o Ciclo 1. Reproduza com Git Bash, ou com o PowerShell abaixo, que dá o mesmo
resultado sem depender de `grep` estar no `PATH`:

**Reproduzir (Git Bash):** `grep -c "Restart=on-failure" systemd/shopee-rodizio.service`
**Reproduzir (PowerShell, equivalente):** `(Select-String -Path
systemd\shopee-rodizio.service -Pattern 'Restart=on-failure').Count`

Sugestão para o orquestrador/planejador: comandos `verificar:` neste projeto devem evitar
binários POSIX (`grep`, e por extensão `uv`) que não estão no `PATH` do shell não-interativo
desta máquina — preferir `Select-String`/`findstr` (Windows) ou confirmar que a passada
mecânica roda via Git Bash.

Nenhum arquivo de código foi alterado neste ciclo.

**Commit:** `527b7cf`

**Fora das `areas` (detectado pelo motor):** test-fase2.log

Estes arquivos foram alterados por esta etapa e estão FORA das `areas` que a
tarefa declarou. Não entram no commit da tarefa, então não aparecem no diff que
o revisor julga — confira se a alteração era legítima (e a `area` é que estava
incompleta) ou se é sobra que precisa ser desfeita.

### Ciclo 3

Impedimento: critério com comando impossível — `verificar: grep -c Restart=on-failure systemd/shopee-rodizio.service` (linha 46) usa `grep`, que não resolve no shell não-interativo (PowerShell/cmd) da passada mecânica; troque por `findstr` ou `Select-String` (comando abaixo). O conteúdo entregue está correto e não é o que reprova.

**Causa-raiz (uma frase):** a única reprovação é mecânica, e vem do binário `grep` ausente no PATH do shell da passada mecânica — não de defeito no `.service` nem no README.

Este é o caso exato da Regra 0 do protocolo (nascida da T-030 do banco-imobiliario): os
Ciclos 1 e 2 diagnosticaram a causa certa, mas só como prosa nas Notas, e a tarefa girou
porque a correção do `verificar:` é autoridade do **planejador**, não do executor — o canal
para isso é esta linha `Impedimento:`, que o motor lê e roteia. Não alterei critério nem
código; a `area` de conteúdo já satisfaz todos os critérios desde o Ciclo 1.

Conteúdo confirmado correto NESTE ciclo (não é o que reprova):
- `grep -c "Restart=on-failure" systemd/shopee-rodizio.service` (Git Bash) → `1`
- `findstr /C:"Restart=on-failure" systemd\shopee-rodizio.service` (PowerShell) → linha impressa, saída `0`
- `(Select-String -Path systemd\shopee-rodizio.service -Pattern 'Restart=on-failure').Count` → `1`
- `.venv\Scripts\python.exe -m ruff check .` → `All checks passed!` (saída 0)
- README.md tem a seção "Deploy no BTT Pi (systemd)" com os 5 passos do Contexto.

**Correção sugerida ao planejador** (troca só o comando `verificar:` do 1º critério; o texto
do critério e o `.service` ficam como estão):

```
verificar: findstr /C:"Restart=on-failure" systemd\shopee-rodizio.service
```

Mesma classe já registrada para `uv` neste projeto; ao redigir novos `verificar:`, prefira
`findstr`/`Select-String` a binários POSIX (`grep`, `uv`) que só existem dentro do Git for
Windows e não estão no PATH do shell não-interativo desta máquina.

Nenhum arquivo de código ou de conteúdo (`.service`, README) foi alterado neste ciclo — a
entrega já estava certa; o que falta é fora do meu escopo (o comando do critério).

**Aproveitamento:** 100% do trabalho dos Ciclos 1–2 aproveitado (conteúdo intacto e
correto); nada refeito. Este ciclo só escalou o diagnóstico pelo canal certo.

**Fora das `areas` (detectado pelo motor):** test-fase2.log

Estes arquivos foram alterados por esta etapa e estão FORA das `areas` que a
tarefa declarou. Não entram no commit da tarefa, então não aparecem no diff que
o revisor julga — confira se a alteração era legítima (e a `area` é que estava
incompleta) ou se é sobra que precisa ser desfeita.

### Resolução do Impedimento (planejador)

Diagnóstico do Ciclo 3 confirmado: o único defeito era o comando do 1º critério, não o
conteúdo entregue (`.service` e README corretos desde o Ciclo 1).

`grep` está na allowlist de binários da passada mecânica (`BINARIOS_PERMITIDOS` em
`painel/servidor/src/pipeline/criterios.ts`), então o comando passou pela checagem e foi
efetivamente executado via `cmd.exe` (`shell: true` no Windows) — mas o processo do painel
não tem `Git\usr\bin` no seu `PATH`, só o `grep` de verdade mora lá. Por isso a reprovação
veio como `FALHOU` (comando rodou e quebrou), não como `binario-nao-permitido` (que teria
degradado para `[julgado]` sem custar o ciclo) — diferente do 3º critério (`uv run ruff
check .`), que degrada normalmente porque `uv` não está na allowlist.

**Correção aplicada:** troquei o comando do 1º critério (linha 46) por
`find /C "Restart=on-failure" systemd/shopee-rodizio.service` — `find.exe` é nativo do
Windows (`System32`, sempre no `PATH`, não depende do Git for Windows), está na mesma
allowlist (`find`), não usa nenhum metacaractere proibido, e tem semântica equivalente a
`grep -c` para este caso (substring, sem regex, que é tudo que o critério precisa): conta
ocorrências e sai != 0 quando a contagem é zero. Confirmado nesta máquina via `cmd.exe /d
/s /c` (mesma invocação que a passada mecânica usa no Windows):
- `find /C "Restart=on-failure" systemd/shopee-rodizio.service` → imprime `...: 1`, saída 0.
- `find /C "NaoExisteIsso123" systemd/shopee-rodizio.service` → imprime `...: 0`, saída 1.

Texto do critério, `.service` e README **não foram alterados** — só o comando `verificar:`.
`tentativas` zerada no frontmatter (Regra 0 do protocolo: é o planejador quem zera ao
reescrever a tarefa) e `ultima-reprovacao` removida.

Decisão de projeto registrada em `_gestao/DECISOES.md` (2026-08-25) para não repetir o
mesmo desperdício em tarefas futuras.

### Confirmação após correção do `verificar:` (planejador zerou `tentativas`)

O planejador já corrigiu o único defeito real (o comando `verificar:` do 1º critério, agora
`find /C "Restart=on-failure" systemd/shopee-rodizio.service`) e zerou `tentativas`. Conteúdo
de `.service` e README não mudou desde o Ciclo 1 — só reconfirmei os três critérios nesta
execução, via `cmd.exe` (mesma invocação da passada mecânica no Windows) e PowerShell:

- `find /C "Restart=on-failure" systemd\shopee-rodizio.service` → `---------- SYSTEMD\SHOPEE-RODIZIO.SERVICE: 1`, saída 0.
- README.md tem a seção `## Deploy no BTT Pi (systemd)` (linha 25) com os 5 passos do Contexto.
- `.venv\Scripts\python.exe -m ruff check .` → `All checks passed!` (equivalente a `uv run ruff check .`, já que `uv` não está no `PATH` deste agente).

Nenhum arquivo de conteúdo foi alterado neste ciclo.

**Reproduzir:**
```
cmd /c find /C "Restart=on-failure" systemd\shopee-rodizio.service
.venv\Scripts\python.exe -m ruff check .
```

**Commit:** `9f6391a`

**Fora das `areas` (detectado pelo motor):** test-fase2.log

Estes arquivos foram alterados por esta etapa e estão FORA das `areas` que a
tarefa declarou. Não entram no commit da tarefa, então não aparecem no diff que
o revisor julga — confira se a alteração era legítima (e a `area` é que estava
incompleta) ou se é sobra que precisa ser desfeita.


## Verificação

### Passada mecânica (sem modelo)

- [executado] A suíte do projeto continua passando (não quebrou o que já existia) — `pytest` → **PASSOU**
- [executado] `systemd/shopee-rodizio.service` existe com as seções `[Unit]`, `[Service]` (incluindo `Restart=on-failure` e `ExecStart`) e `[Install]`. — `grep -c Restart=on-failure systemd/shopee-rodizio.service` → **FALHOU**

```
'grep' n�o � reconhecido como um comando interno
ou externo, um programa oper�vel ou um arquivo em lotes.
```

- [julgado] README.md tem uma seção de deploy com os 5 passos descritos no Contexto, com comandos reais (não placeholder). — sem comando declarado; fica para o verificador.
- [julgado] `uv run ruff check .` continua sem erro após esta tarefa (nenhum código Python novo quebrando lint). — comando recusado: binario-nao-permitido; fica para o verificador.

Graus de prova: 2 executado(s), 2 para julgamento (de 4).

### Passada mecânica (sem modelo)

- [executado] A suíte do projeto continua passando (não quebrou o que já existia) — `pytest` → **PASSOU**
- [executado] `systemd/shopee-rodizio.service` existe com as seções `[Unit]`, `[Service]` (incluindo `Restart=on-failure` e `ExecStart`) e `[Install]`. — `grep -c Restart=on-failure systemd/shopee-rodizio.service` → **FALHOU**

```
'grep' n�o � reconhecido como um comando interno
ou externo, um programa oper�vel ou um arquivo em lotes.
```

- [julgado] README.md tem uma seção de deploy com os 5 passos descritos no Contexto, com comandos reais (não placeholder). — sem comando declarado; fica para o verificador.
- [julgado] `uv run ruff check .` continua sem erro após esta tarefa (nenhum código Python novo quebrando lint). — comando recusado: binario-nao-permitido; fica para o verificador.

Graus de prova: 2 executado(s), 2 para julgamento (de 4).

### Passada mecânica (sem modelo)

- [executado] A suíte do projeto continua passando (não quebrou o que já existia) — `pytest` → **PASSOU**
- [executado] `systemd/shopee-rodizio.service` existe com as seções `[Unit]`, `[Service]` (incluindo `Restart=on-failure` e `ExecStart`) e `[Install]`. — `find /C "Restart=on-failure" systemd/shopee-rodizio.service` → **PASSOU**
- [julgado] README.md tem uma seção de deploy com os 5 passos descritos no Contexto, com comandos reais (não placeholder). — sem comando declarado; fica para o verificador.
- [julgado] `uv run ruff check .` continua sem erro após esta tarefa (nenhum código Python novo quebrando lint). — comando recusado: binario-nao-permitido; fica para o verificador.

Graus de prova: 2 executado(s), 2 para julgamento (de 4).

### Ciclo 1 — Verificação completa (testador)

- **[PASSOU] [executado] A suíte do projeto continua passando (não quebrou o que já existia)**
  Comando: `.venv\Scripts\python.exe -m pytest -q`
  Saída: `55 passed in 1.16s`

- **[PASSOU] [executado] `systemd/shopee-rodizio.service` existe com as seções `[Unit]`, `[Service]` (incluindo `Restart=on-failure` e `ExecStart`) e `[Install]`**
  Comando: `find /C "Restart=on-failure" systemd\shopee-rodizio.service` (via cmd.exe)
  Saída: `---------- SYSTEMD\SHOPEE-RODIZIO.SERVICE: 1`
  Inspecionado: arquivo tem as 3 seções exigidas com campos corretos

- **[PASSOU] [julgado] README.md tem uma seção de deploy com os 5 passos descritos no Contexto, com comandos reais (não placeholder)**
  Base: leitura da seção "## Deploy no BTT Pi (systemd)" (linhas 25–78 do README).
  Verificados os 5 passos:
  1. Copiar/clonar o projeto (comando `git clone` real, linhas 33–40)
  2. Instalar `uv` no SBC (script `curl -LsSf https://astral.sh/uv/install.sh | sh`, linhas 42–49)
  3. Criar `config.toml` (comando `cp config.example.toml config.toml`, linhas 51–57)
  4. Instalar e ativar systemd (comandos `sudo cp`, `daemon-reload`, `enable --now`, linhas 59–65)
  5. Acompanhar o log (`journalctl -u shopee-rodizio -f`, linhas 67–78)
  Todos com comandos reais, sem placeholders.

- **[PASSOU] [executado] `uv run ruff check .` continua sem erro após esta tarefa (nenhum código Python novo quebrando lint)**
  Comando: `.venv\Scripts\python.exe -m ruff check .` (equivalente a `uv run ruff check .`, já que `uv` não está no PATH)
  Saída: `All checks passed!`

Suíte completa: 55 passou, 0 falhou
Graus de prova: 4 executados, 0 inspecionados, 0 julgados


## Conformidade

Conformidade: cumpre

- `systemd/shopee-rodizio.service` existe com `[Unit]`, `[Service]` (`Restart=on-failure`
  linha 19, `ExecStart` linha 18) e `[Install]` → `systemd/shopee-rodizio.service:1-25`,
  confirmado no Ciclo 1 pelo testador (`find /C` → saída `1`, mecânica **PASSOU**) e
  reconfirmado neste ciclo.
- README.md tem a seção de deploy com os 5 passos do Contexto e comandos reais (não
  placeholder) → `README.md:25-78` (`git clone`/`scp`, instalação de `uv`, `cp
  config.example.toml config.toml`, `sudo cp`+`daemon-reload`+`enable --now`,
  `journalctl -u shopee-rodizio -f`/`tail -f`), confirmado pelo testador no Ciclo 1
  (**PASSOU**, julgado).
- `uv run ruff check .` sem erro após a tarefa → nenhum `.py` alterado por T-009;
  `.venv\Scripts\python.exe -m ruff check .` → `All checks passed!`, confirmado pelo
  testador no Ciclo 1 (**PASSOU**, executado).
- Objetivo satisfeito no espírito: unidade systemd reinicia sozinha em crash
  (`Restart=on-failure`/`RestartSec=10`), roda sob usuário sem root (`User=pi`/`Group=pi`,
  documentado como recomendação, não obrigação, coerente com o Contexto), e o README leva
  do zero (clonar o projeto) até o serviço rodando e observável (log).
- Escopo: os dois ciclos de retrabalho (Ciclo 2 e 3) e a "Resolução do Impedimento" do
  planejador não tocaram `.service` nem README — só o comando `verificar:` do critério 1
  (`grep` → `find`, registrado em `DECISOES.md` 2026-08-25) e, neste commit, a prosa das
  Notas de execução confirmando o resultado após a correção. Sem sobra fora de escopo.
- `areas` respeitadas: nenhum arquivo fora de `systemd/shopee-rodizio.service` e `README.md`
  foi alterado por conteúdo; `test-fase2.log`, sinalizado em todos os ciclos como fora das
  `areas`, é artefato pré-existente do motor/pipeline (não gerado por esta tarefa) e segue
  fora do commit revisado.

## Revisão

Aprovado sem ressalvas. Nenhum arquivo de conteúdo foi tocado neste commit (`9f6391a`) —
só a prosa de confirmação nas Notas de execução, a regeneração determinística de
`_gestao/MAPA.md` (HEAD atualizado) e, no commit seguinte (`9546a54`), o preenchimento do
hash `**Commit:**` que faltava. Verifiquei diretamente `systemd/shopee-rodizio.service`
(3 seções corretas, `Restart=on-failure` presente) e `README.md:25-78` (5 passos com
comandos reais) — nenhuma divergência do que o testador já havia registrado como PASSOU
no Ciclo 1. A suíte (55 passed) e o lint (`ruff check .` limpo) já estavam confirmados e
não são afetados por um commit que não muda código.

Achado `[menor]`: a "Passada mecânica" ficou registrada 3 vezes na seção Verificação
(reprovações mecânicas dos Ciclos 1–3, todas por ausência de `grep` no PATH da passada,
não por defeito de conteúdo) antes da correção do `verificar:` pelo planejador — histórico
correto e já explicado em `DECISOES.md`, só fica maior que o necessário para releitura
futura; não é motivo de reprovação.
