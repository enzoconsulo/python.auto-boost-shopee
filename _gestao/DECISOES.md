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
