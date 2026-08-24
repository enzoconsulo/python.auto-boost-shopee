# Especificação — shopee-rodizio

## Objetivo
Serviço leve, rodando 24/7 no mesmo BigTreeTech Pi 1.2.1 que controla o Klipper da Ender 3
V3 SE do usuário, que substitui a tarefa manual e repetitiva de impulsionar anúncios no
site da Shopee. A cada ciclo (padrão 4 horas, configurável), sorteia — por peso definido
pelo usuário — um subconjunto de itens do catálogo dele e chama a Shopee Open Platform API
para impulsioná-los, respeitando o limite de itens simultaneamente impulsionáveis da conta.

## Usuários
Um único usuário: o vendedor dono da conta Shopee e do BTT Pi. Sem multiusuário, sem UI
web — configuração e auditoria são feitas por arquivo (TOML) e log (arquivo texto), lidos/
editados diretamente no SBC (SSH ou cartão SD) ou via os mesmos meios que ele já usa para
mexer no `printer.cfg`/config do Klipper.

## Escopo
- Ler config local (TOML) com: credenciais Shopee (partner_id, partner_key, shop_id,
  access_token/refresh_token iniciais), lista de itens (item_id + peso), intervalo do
  ciclo, limite de slots simultâneos de boost, caminhos de log/estado.
- Autenticar na Shopee Open Platform API (assinatura HMAC-SHA256) e renovar o
  `access_token` automaticamente via `refresh_token` antes de expirar.
- A cada ciclo: sortear itens por peso (sem reposição dentro do ciclo) até o limite
  configurado de slots simultâneos, e chamar o endpoint de impulsionamento para cada um.
- Persistir em arquivo local (JSON) o histórico de impulsionamentos (item, timestamp,
  sucesso/erro) — usado tanto para auditoria quanto para informar o sorteio seguinte.
- Rodar como serviço systemd: inicia com o boot, reinicia sozinho em caso de crash, log
  em arquivo com rotação simples.
- Nunca derrubar o processo por erro de rede/API/token — logar e tentar de novo no
  próximo ciclo.

## Fora de escopo
- Obter aprovação de app / criar app na Shopee Open Platform (o usuário já tem app e
  credenciais).
- Interface gráfica ou web — configuração e leitura de status são só por arquivo.
- Gerenciar campanhas de Ads pagas (CPC, `v2.ads.*` de compra de anúncio) — só o boost
  gratuito de produto ("impulsionar").
- Multi-loja simultânea (uma instância cuida de uma `shop_id`; rodar duas lojas é duas
  instâncias, fora deste escopo inicial).
- Notificações externas (e-mail, Telegram, etc.) — o canal de auditoria é o arquivo de
  log local.
- Alteração de preço, estoque, descrição de anúncio, ou qualquer outra automação de
  catálogo além do impulsionamento.

## Stack
**Python + `uv`** (scaffold oficial do catálogo da fábrica para projetos Python, seção
"Python (geral)" de `_sistema/BIBLIOTECAS.md`), com:

| Papel | Escolha | Por quê |
|---|---|---|
| Scaffold/deps | `uv` (`uv init`, `uv add`, `uv run`) | scaffold oficial do catálogo |
| HTTP | `requests` | requisição + timeout + tratamento de erro sem reimplementar `urllib` à mão; viva, BSD, ~1 dependência transitiva |
| Config | `tomllib` (stdlib, leitura) | TOML é legível/editável à mão pelo usuário (comentários, seções), como o `printer.cfg` do Klipper; sem dependência nova — Python 3.11+ já traz leitura de TOML na stdlib |
| Persistência de estado | `json` (stdlib) | histórico pequeno (dezenas de itens); SQLite seria overhead sem ganho aqui |
| Agendamento | loop próprio (`time.sleep`) | um único job periódico não justifica um scheduler (APScheduler etc.) — resolve algo que ~15 linhas óbvias já resolvem |
| Lint + format | `ruff` | catálogo da fábrica para Python, um binário só |
| Testes | `pytest` | catálogo da fábrica para Python |

**Justificativa em 1 parágrafo:** o hardware alvo é um SBC de classe Raspberry Pi Zero/3
(BigTreeTech Pi 1.2.1) que já roda o firmware Klipper — e o Klipper (`klippy`) é escrito em
Python, então o interpretador Python já convive com esse hardware em produção; adotar
Python de novo não introduz runtime novo no sistema, ao contrário de Go (binário compilado,
menor footprint em teoria, mas exigiria toolchain de cross-compilação para ARM e não consta
no catálogo da fábrica) ou Node (runtime mais pesado em RAM idle para um processo que passa
quase todo o tempo dormindo). A lista de dependências foi mantida propositalmente curta —
`requests` é a única dependência externa real — porque cada pacote a mais é RAM residente
27x7 num SBC com poucas dezenas de MB livres depois do Klipper/Moonraker.

**Alternativa descartada:** Go compilado para ARM (menor footprint teórico, sem
interpretador residente) — descartado por não estar no catálogo da fábrica e por exigir
toolchain de cross-compilação que complica o deploy no próprio BTT Pi (o usuário precisaria
compilar em outra máquina e copiar o binário, ou instalar Go no SBC só para compilar uma
vez). Registrado em `_gestao/DECISOES.md`.

## Requisitos funcionais
- RF-01: O sistema lê itens (id + peso) e parâmetros de operação (intervalo do ciclo,
  limite de slots simultâneos, caminhos de log/estado) de um arquivo TOML local editável
  pelo usuário, com validação de formato e mensagem de erro clara se algo estiver errado.
- RF-02: O sistema autentica na Shopee Open Platform API com assinatura HMAC-SHA256
  (partner_id + path + timestamp [+ access_token + shop_id quando aplicável], assinado com
  partner_key) e renova o `access_token` (validade ~4h) via `refresh_token` (validade ~30
  dias) automaticamente antes de expirar, persistindo o token renovado.
- RF-03: A cada ciclo, o sistema sorteia por peso, sem reposição dentro do mesmo ciclo, um
  subconjunto de itens até o limite configurável de slots simultâneos (padrão 5) e chama o
  endpoint de impulsionamento da API para cada item sorteado.
- RF-04: O caminho e os nomes de parâmetro do endpoint de impulsionamento são configuráveis
  (não fixos no código), dado que a documentação pública da Shopee Open Platform não expõe
  com certeza o endpoint exato de boost gratuito sem login no portal de desenvolvedor (ver
  Riscos).
- RF-05: O sistema persiste em JSON local o histórico de impulsionamentos (item, timestamp,
  sucesso/erro, mensagem da API) e usa esse histórico para informar o sorteio do ciclo
  seguinte (auditável pelo usuário).
- RF-06: Erro de rede, token expirado/inválido, ou erro retornado pela API é logado com
  detalhe suficiente para diagnóstico e NUNCA derruba o processo — o ciclo seguinte tenta
  de novo.
- RF-07: Log em arquivo com rotação por tamanho (N backups), legível por `tail`/editor de
  texto comum.
- RF-08: O serviço sobe como unidade systemd (arquivo `.service` incluído no repo),
  reinicia sozinho em caso de crash (`Restart=on-failure`), e o README documenta o comando
  exato de instalação/ativação no BTT Pi.

## Requisitos não-funcionais
- **Footprint:** uso de RAM em idle compatível com um SBC de poucas dezenas/centenas de MB
  livres (o processo passa a maior parte do tempo dormindo entre ciclos de 4h); sem
  dependências pesadas (nada de Electron, JVM, containers, banco de dados servidor).
- **Resiliência 24/7 sem supervisão:** nenhum caminho de erro pode terminar o processo;
  systemd cobre crash duro, o próprio loop cobre erro de API/rede.
- **Auditabilidade:** todo boost tentado (sucesso ou falha) fica registrado em log e no
  estado JSON, com timestamp.
- **Configuração sem código:** trocar peso de item, intervalo do ciclo ou limite de slots
  não exige tocar em `.py` nenhum — só no TOML.

## Riscos
- **Endpoint exato de impulsionamento não confirmado publicamente.** A pesquisa feita
  durante o planejamento (WebSearch, 2026-08-24) confirmou o mecanismo de autenticação
  (HMAC-SHA256, `access_token` de 4h, `refresh_token` de 30 dias, renovação via
  `/api/v2/auth/access_token/get`) e o comportamento observado do recurso de impulsionar
  produto na Shopee (limite histórico relatado de até 5 produtos por janela de ~4h, um
  impulso por vez por produto), mas **não encontrou documentação pública e não-autenticada
  do endpoint exato** (caminho, módulo `v2.product.*` vs `v2.ads.*`, nomes de parâmetro) —
  a documentação completa da Shopee Open Platform exige login no portal de desenvolvedor,
  ao qual o usuário tem acesso mas o planejador não. **Mitigação:** RF-04 (endpoint e nomes
  de parâmetro configuráveis) + uma tarefa dedicada de smoke-test (T-010) que o usuário
  roda manualmente contra a própria conta para confirmar/ajustar o endpoint antes de
  colocar o serviço em produção contínua, documentada no README.
- **Limite real de slots simultâneos e duração do boost podem diferir do assumido (5
  itens / 4h).** Valor vira `default` configurável (RF-01), não constante fixa — se a
  conta do usuário tiver outro limite, ele ajusta sem mexer em código.
- **Mudança de contrato da API pela Shopee** (a Open Platform já teve breaking changes
  entre versões) — mitigado por RF-06 (erro da API só loga, não derruba o serviço) e pelo
  endpoint configurável.
