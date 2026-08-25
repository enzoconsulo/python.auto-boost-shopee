# Plano — shopee-rodizio

Fundação em Python/`uv` (scaffold + config + estado) → núcleo (autenticação HMAC, chamada
de boost, sorteio ponderado, ciclo/loop) → refinamento (deploy systemd no BTT Pi +
smoke-test contra a API real). Cada fase entrega algo executável e testável isoladamente
antes da próxima somar complexidade.

## Fase 1 — Fundação
Meta: projeto Python criado pelo `uv`, com lint/format/teste rodando, mais os dois
alicerces de que todo o resto depende — leitura de config e persistência de estado — cada
um com teste passando.
Marco: reprovado 2026-08-24
Tarefas: T-001, T-002, T-003, T-011

## Fase 2 — Núcleo
Meta: ciclo de rodízio completo e funcional de ponta a ponta contra a API real da Shopee
(autenticação com renovação de token, chamada de boost, sorteio ponderado, orquestração e
log), executável manualmente (`uv run python -m shopee_rodizio`) mesmo antes do deploy
como serviço.
Marco: aprovado 2026-08-25
Tarefas: T-004, T-005, T-006, T-007, T-008

## Fase 3 — Refinamento
Meta: serviço instalável como unidade systemd no BTT Pi (sobe no boot, reinicia sozinho) e
confirmado/ajustado contra a conta Shopee real do usuário via smoke-test documentado.
Marco: pendente
Tarefas: T-009, T-010
