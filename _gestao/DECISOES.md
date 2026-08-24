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
