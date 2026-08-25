# Decisões — shopee-rodizio

Registro apenas-adição (nunca apagar; decisão revertida ganha nova entrada dizendo isso).
Formato de cada entrada:

## AAAA-MM-DD — <título da decisão>
**Decisão:** <o que foi decidido>
**Motivo:** <por quê; qual alternativa foi descartada e por quê>
**Quem:** <planejador | executor (T-NNN) | orquestrador | usuário>

## 2026-08-24 — Domínio classificado como software
**Decisão:** projeto roteado pela trilha de software (planejador/executor/testador/revisor).
**Motivo:** o entregável final é um serviço que roda continuamente num SBC (BigTreeTech
Pi 1.2.1), chamando a Shopee Open Platform API e mantendo estado de rodízio — não é um
artefato estático de outro domínio.
**Quem:** orquestrador

## 2026-08-24 — Stack: Python + uv
**Decisão:** stack do projeto é Python (gerenciado por `uv`), `requests` para HTTP,
`tomllib` (stdlib) para config, `json` (stdlib) para persistência de estado, loop próprio
(`time.sleep`) para agendamento, `ruff` para lint+format, `pytest` para testes.
**Motivo:** catálogo da fábrica para "Python (geral)" em `_sistema/BIBLIOTECAS.md`. Python
foi preferido a Go compilado (footprint menor em teoria, mas fora do catálogo e exige
toolchain de cross-compilação para ARM que complica o deploy no próprio BTT Pi) e a Node
(runtime mais pesado em RAM idle) porque o hardware alvo (BigTreeTech Pi 1.2.1) já roda
Klipper/`klippy`, que é Python — não introduz interpretador novo no SBC. `requests` é a
única dependência externa fora do catálogo explícito: adotada por resolver assinatura
HTTP + timeout + tratamento de erro (filtro 1: não-trivial) sem reimplementar `urllib` à
mão; viva e permissiva (filtro 2); não conflita com nada já decidido (filtro 3). Nenhum
scheduler de terceiros (ex.: APScheduler) foi adotado — um job periódico único é ~15 linhas
de loop próprio, abaixo do limiar de 50 linhas do filtro de não-adoção.
**Quem:** planejador

## 2026-08-24 — Marco da Fase 1 reprovado: regressão de lint por critério de tarefa escopado demais
**Decisão:** criar T-011 (correção pontual, causa única) em vez de reabrir/cancelar
T-001, T-002 ou T-003.
**Motivo:** o marco da Fase 1 reprova porque `uv run ruff check .` (critério 1 de
T-001, a fundação de que todas as tarefas dependem) falha hoje no projeto inteiro —
`tests/test_estado.py:1` tem um import não utilizado (`from pathlib import Path`,
`F401`) introduzido por T-003. A própria Revisão de T-003 já tinha apontado isso como
achado `[menor]`, mas não bloqueou porque o critério de lint daquela tarefa era
escopado só a `src/shopee_rodizio/estado.py`, não ao arquivo de teste que ela também
criou — a lição fica registrada aqui para as próximas tarefas: critério de lint por
arquivo único não pega regressão em arquivo vizinho da mesma tarefa; quando fizer
sentido, prefira `uv run ruff check .` (projeto inteiro) como critério, que é
barato e já é o que T-001 estabeleceu como invariante da fundação. Nenhum teste
quebrou (`uv run pytest -q` → 15 passed) — é só lint, causa única, confirmada
rodando os dois comandos antes de criar a correção.
**Quem:** planejador

## 2026-08-24 — Endpoint de boost da Shopee: incerteza registrada
**Decisão:** o cliente HTTP da Shopee (T-004/T-005) implementa o caminho e os nomes de
parâmetro do endpoint de impulsionamento como CONFIGURÁVEIS no TOML, em vez de fixos no
código.
**Motivo:** pesquisa via WebSearch em 2026-08-24 confirmou o mecanismo de autenticação da
Shopee Open Platform API v2 (assinatura HMAC-SHA256 sobre partner_id + path + timestamp
[+ access_token + shop_id], `access_token` válido ~4h, `refresh_token` válido ~30 dias,
renovação via `/api/v2/auth/access_token/get`) e o comportamento observado publicamente do
recurso de impulsionar produto (limite historicamente relatado de até 5 produtos por
janela de ~4h), mas NÃO encontrou documentação pública, não-autenticada, do endpoint exato
(caminho e parâmetros) — a documentação completa da Open Platform exige login no portal do
desenvolvedor, ao qual o planejador não tem acesso. Fixar o endpoint de memória arriscaria
uma tarefa inteira quebrada por um caminho errado sem forma de corrigir sem redeploy;
configurável + smoke-test manual (T-010) transfere a confirmação final para quem tem
acesso à conta real (o usuário), sem bloquear o resto da decomposição.
**Quem:** planejador

## 2026-08-25 — T-009: `verificar:` de arquivo texto deve usar `find`, não `grep`, nesta máquina
**Decisão:** critérios `verificar:` que checam substring em arquivo (unidade systemd,
config, etc.) usam `find /C "<string>" <arquivo>` (nativo do Windows, `System32`), nunca
`grep`.
**Motivo:** `grep` está na allowlist de binários da passada mecânica
(`painel/servidor/src/pipeline/criterios.ts`), então passa na checagem e é efetivamente
executado via `cmd.exe` — mas o processo do painel não tem `Git\usr\bin` no `PATH`, onde
mora o `grep.exe` de verdade. O comando roda e quebra (`FALHOU`), em vez de degradar para
`[julgado]` como acontece com binário fora da allowlist (ex.: `uv`, já registrado em
`uv-nao-esta-no-path` na memória do agente). Isso girou T-009 por 3 ciclos com o conteúdo
correto desde o Ciclo 1 — o defeito era só o comando do critério. `find.exe` do Windows
(`FIND /C "string" arquivo`) tem semântica equivalente a `grep -c` (substring, sem regex,
sai != 0 quando a contagem é zero) e é resolvido nativamente pelo `cmd.exe`, sem depender
de nenhuma instalação POSIX-em-Windows. Confirmado via `cmd.exe /d /s /c` nesta máquina.
**Quem:** planejador
