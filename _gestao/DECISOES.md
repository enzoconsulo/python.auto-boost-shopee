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

## 2026-08-25 — Endpoint de boost da Shopee: payload confirmado contra conta real
**Decisão:** `boost.py` chama `v2.product.boost_item` com `{"item_id_list": [item_id]}`
(lista, mesmo para um item só) em vez do palpite anterior `{"item_id": item_id, "shop_id":
...}`; `shop_id` sai do corpo (já vai assinado na query por `cliente_shopee.py`).
**Motivo:** smoke-test real (T-010) contra a conta do usuário devolveu `product.error_unknown`
com o payload antigo. Confirmado contra uma implementação irmã do mesmo usuário
(`analista_dados_shopee/utils/shopee_core.py::impulsionar_itens`, já validada ao vivo em
produção) que o endpoint espera `item_id_list` — não `item_id` singular. Resolve a incerteza
registrada em 2026-08-24 ("Endpoint de boost da Shopee: incerteza registrada"); o caminho
(`/api/v2/product/boost_item`) já estava certo, só o formato do payload estava errado.
**Quem:** usuário (via depuração ao vivo no deploy)

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

## 2026-08-26 — IP dinâmico do BTT Pi derrubou o IP Whitelist em produção; adicionado proxy opcional de IP fixo
**Decisão:** `ClienteShopee` e os scripts que chamam a Shopee (`gerar_token.py`,
`sincronizar_itens.py`, `smoke_test.py`) aceitam um `proxy_https` opcional (seção
`[rede]` do `config.toml`, campo `proxy_https`, ausente = comportamento inalterado). O
uso pretendido é um túnel SSH (SOCKS5 local) até uma VM com IP público fixo (Oracle Cloud
Free Tier — grátis, "Always Free", não é trial), documentado em
`systemd/shopee-proxy-tunnel.service` e no README ("IP de saída fixo"). Dependência nova:
`pysocks` (exigida pelo `requests` para suportar o esquema `socks5h://`).
**Motivo:** em produção real, o serviço rodou corretamente por ~8h (boosts com sucesso às
04:58 UTC) e depois toda chamada — inclusive a renovação de `access_token` — passou a
falhar com `403 Forbidden` em `/api/v2/auth/access_token/get`. Mesma assinatura do
`source_ip_undeclared` já resolvido em 2026-08-24/25, mas desta vez sem nenhuma mudança de
código: a causa mais provável é o provedor de internet residencial do usuário ter trocado
o IP público do BTT Pi (DHCP lease renovado), invalidando o IP cadastrado no whitelist da
Shopee. Como o whitelist da Shopee só aceita IP fixo cadastrado manualmente no Console (não
há API pra automatizar isso), a opção que remove a causa raiz é parar de depender do IP do
Pi: rotear as chamadas por uma VM de IP fixo. Usuário rejeitou explicitamente as alternativas
de IP fixo pago pelo provedor (não queria "ligar pro provedor e resolver pepino") e de VPN
comercial com add-on de IP dedicado (custo recorrente) — Oracle Free Tier foi a escolha por
ser gratuita permanentemente. O proxy é opcional e por seção separada (não um campo
obrigatório em `[shopee]`) porque a maioria dos deploys (IP fixo nativo, ou ainda não
tendo passado por esse problema) não precisa dele — forçar a seção quebraria configs
existentes sem necessidade.
**Quem:** usuário (causa raiz ainda não 100% confirmada — hipótese de IP dinâmico é a mais
provável dado o padrão do erro, mas não há como confirmar sem acesso ao histórico de IP do
provedor; a mitigação resolve o problema independente da causa exata ser essa ou outra
variação de IP não cadastrado).

## 2026-09-14 — token.json vira fonte única entre processos; outro app pega o token emprestado
**Decisão:** `ClienteShopee` aceita um `ArmazemToken` (`armazem_token.py`). Antes de cada
uso, o cliente relê `token.json`. A renovação acontece sob lock exclusivo de arquivo
(`token.json.lock`), relendo o arquivo dentro do lock e gravando o token novo antes de
soltá-lo. O loop do `__main__` deixou de persistir o token ao fim do ciclo.
`sincronizar_itens.py` e `smoke_test.py` passam a usar o mesmo armazém
(`cliente_da_config`), e `gerar_token.py` grava também em `token.json`. Script novo:
`scripts/emprestar_token.py`, que devolve no stdout um access_token válido por pelo menos
N minutos (renovando sob o lock se preciso) sem expor o refresh_token.
**Motivo:** o usuário vai rodar o analista_dados_shopee (PC, uso esporádico) na mesma
loja e no mesmo app. Uma cadeia de refresh_token por app tem dois problemas: a do PC vence
após 30 dias sem uso, e não há garantia do que a Shopee faz com a cadeia de um app quando a
loja é reautorizada pelo outro. Com o serviço 24/7 como único dono do token e o PC pedindo o
access_token emprestado por SSH, sobra uma autorização e uma cadeia. Para isso, o token não
podia mais ficar só em memória no serviço (lido do disco só na subida): qualquer outro
processo que renovasse invalidaria a cadeia dele. Isso já acontecia com
`sincronizar_itens.py`/`smoke_test.py`, que renovavam a partir do refresh_token do
`config.toml`, já consumido pelo serviço. Alternativa descartada: servidor HTTP no Pi para
entregar o token (mais uma porta aberta e mais um serviço; o SSH já existe e já autentica).
**Quem:** usuário (escolheu o Pi como dono do token) + executor

## 2026-10-19 — Na subida, o serviço espera o que falta do intervalo desde o último ciclo
**Decisão:** `executar_loop` lê o timestamp mais recente do `estado.json` (com sucesso ou
não) e dorme `intervalo_horas - decorrido` antes do primeiro ciclo. Se o relógio indicar
que o último ciclo está no futuro, espera o intervalo cheio.
**Motivo:** auditoria de produção: restarts às 18:56/18:57 de 19/10 dispararam dois ciclos
2h20 depois do ciclo legítimo das 16:36, e os dez boosts falharam com `reached shop's bump
slot limit`. O histórico já tinha a informação, então não entrou arquivo nem dependência
nova. O CB1 não tem RTC: antes do NTP o fake-hwclock volta o relógio, e por isso o caso
"último ciclo no futuro" erra para o lado de esperar, que não queima slots.
**Quem:** usuário (auditoria) + executor (T-014)

## 2026-10-19 — config.toml relido a cada ciclo; corrida de escrita resolvida por atomicidade + lock + versão
**Decisão:** o serviço relê o `config.toml` no início de cada ciclo, e o painel só grava o
arquivo, sem `systemctl restart`. Config inválida no disco é logada e o loop segue com a
última válida. O cliente Shopee só é recriado se `[shopee]`, `[rede]` ou o caminho do
estado mudarem. Escritores (painel, `sincronizar_itens.py`, `definir_senha_painel.py`)
passam todos por `config.atualizar_itens`/`definir_senha_painel`, que fazem ler →
regenerar → gravar sob `config.toml.lock`, gravação atômica e durável
(`arquivo.gravar_atomico`: temporário único + fsync + `os.replace` + fsync do diretório).
Validação antes de gravar: TOML válido, `Config` válida, nada fora das chaves permitidas
muda. O painel ainda faz checagem otimista (hash da versão lida → 409 se mudou).
**Motivo:** reiniciar para aplicar exigiria dar permissão de systemctl ao processo do
painel. Com a releitura por ciclo, o custo é ler ~4 KB a cada 4 h. Corrida: o serviço só
lê, e o `os.replace` garante que ele veja o arquivo velho inteiro ou o novo inteiro. Entre
escritores, o lock serializa quem coopera. O nano não coopera, e a checagem de versão do
painel cobre esse caso sem sobrescrever a edição manual. Achado no caminho: o
`config.toml` de produção tem `[rede]` DEPOIS dos `[[itens]]`, e o regenerador antigo
truncava tudo a partir do primeiro `[[itens]]`. A próxima sincronização teria apagado o
proxy. O novo troca só os blocos `[[itens]]`.
**Quem:** usuário (pediu a releitura) + executor (T-012, T-015)

## 2026-10-19 — Painel web: http.server da stdlib, sem dependência nova
**Decisão:** o painel usa `http.server.HTTPServer` (stdlib), single-thread, com
HTML/JS/CSS estáticos e JS puro, sem framework de front.
**Motivo:** o CB1 tem 1 GB e divide CPU com o Klipper, que aborta impressão com "Timer too
close" se o host engasgar. São quatro rotas. Flask/Bottle trariam dependência sem ganho
nesse tamanho, e Streamlit foi vetado pelo usuário (runtime pesado, websocket e rerun
permanentes). Ocioso, o `HTTPServer` fica bloqueado em `select()` (`poll_interval=3600`),
sem CPU nem timer. A thread única serializa as gravações por construção, e o
`timeout=15` do handler impede um cliente parado de prender a thread. As imagens o
navegador baixa direto do CDN da Shopee. A página não faz polling. Runtime continua só
`requests` + `pysocks`. No systemd: `CPUSchedulingPolicy=idle`, `IOSchedulingClass=idle`,
`Nice=19`, `CPUQuota=50%`, `MemoryMax=96M`.
**Quem:** executor (T-019, T-020)

## 2026-10-19 — Painel: autenticação HTTP Basic contra hash PBKDF2, só LAN
**Decisão:** HTTP Basic, com a senha guardada como `pbkdf2_sha256$200000$sal$hash`
(stdlib `hashlib.pbkdf2_hmac`) em `[painel].senha_hash` do `config.toml`, que não é
versionado. Sem hash, o painel responde 503 a tudo. A senha é definida por
`scripts/definir_senha_painel.py` (getpass, nunca em argv nem em log). Defesas
complementares:
- filtro de IP de origem (RFC 1918 + loopback por padrão, o que exclui Tailscale
  100.64/10);
- bind só IPv4;
- `Host` precisa ser IP ou o nome da máquina (DNS rebinding);
- POST exige JSON + header `X-Painel` (CSRF via preflight);
- CSP estrita;
- 1 s de espera por senha errada;
- cache em memória do header já validado, para não pagar PBKDF2 a cada requisição.
**Motivo:** mexer em pesos é mexer em dinheiro, mesmo na LAN, mas é uma pessoa só numa
rede doméstica. Login com sessão/cookie daria ~40 linhas a mais e estado de sessão no
servidor, para ganhar só logout. Basic na LAN trafega a senha em base64 sem TLS. Aceito
como proporcional: quem consegue farejar o Wi-Fi WPA2 da casa já está dentro da rede, e
TLS exigiria certificado autoassinado e aviso no navegador a cada acesso. Basic + cookie
em cache é vulnerável a CSRF, por isso o header obrigatório.
**Quem:** executor (T-019), escolha proposta ao usuário e aprovada em 2026-10-19

## 2026-10-19 — Porta do painel: 8790
**Decisão:** `[painel].porta = 8790` por padrão, configurável.
**Motivo:** `ss -ltn` no Pi em 2026-10-19 mostrou ocupadas 22, 53, 80 (Mainsail), 111,
1080 (SOCKS do túnel, só 127.0.0.1), 5355, 7125 (Moonraker), 8080 (ustreamer) e uma porta
alta do Tailscale. A 8790 fica fora da faixa do crowsnest (8080–8083) e das portas comuns
de desenvolvimento (3000/5000/8000/8888). O instalador confere de novo antes de subir.
**Quem:** executor (T-020)

## 2026-10-19 — Catálogo: get_model_list opcional e formato de estoque incerto
**Decisão:** preço e estoque de anúncio COM variações vêm de
`/api/v2/product/get_model_list` (uma chamada por item com `has_model`), só quando
`[painel].buscar_variacoes = true` (padrão) e só na atualização do cache. O estoque é lido
de `stock_info_v2.summary_info.total_available_stock` ou, na falta, de
`stock_info[0].normal_stock`. A ausência vira "não informado", nunca erro.
**Motivo:** o `get_item_base_info` não traz preço/estoque de item com variações. O
`get_model_list` é usado pela implementação irmã (`analista_dados_shopee`), mas este
projeto ainda não o tinha exercitado contra a conta. Mesmo ceticismo do endpoint de
boost: fica opcional, e uma falha nele só deixa o item com "preço varia". A API da Shopee
migrou o formato do estoque (`stock_info` → `stock_info_v2`) e não há como confirmar sem
login qual a conta devolve, por isso a extração aceita os dois.
**Quem:** executor (T-017, T-018)

## 2026-10-19 — Mensagem de erro do cliente Shopee nunca carrega credencial
**Decisão:** `cliente_shopee.mensagem_segura` remove a query string de URLs e o valor de
`access_token`/`refresh_token`/`sign`/`partner_key` de toda mensagem de exceção antes de
ela virar `Resultado.erro`.
**Motivo:** confirmado no Pi: o `shopee-rodizio.log` tinha 5 linhas com `access_token=` em
claro. O `HTTPError` do `requests` embute a URL assinada inteira, e o texto ia para o log
e o `estado.json` (e iria para o painel).
**Quem:** executor (T-013)

## 2026-10-19 — get_model_list e extração de preço/estoque confirmados contra a conta real
**Decisão:** mantém `[painel].buscar_variacoes = true` como padrão.
**Motivo:** no deploy de 2026-10-19, `catalogo.baixar_catalogo` rodou no Pi contra a loja
real: 29 anúncios ativos, todos com nome, imagem, preço (faixa mín–máx para os 21 com
variação, via `get_model_list`), estoque e status `NORMAL`. A atualização completa levou
36 s, com pausa de 0,2 s entre chamadas. Resolve a incerteza da entrada "Catálogo:
get_model_list opcional e formato de estoque incerto" para esta conta; o fallback de
formatos continua no código.
**Quem:** executor (deploy T-020)

## 2026-10-19 — Abas "No ar agora" e "Relatório": convenções de leitura do histórico
**Decisão:** o painel ganhou duas abas só de leitura, alimentadas por `relatorio.py` via
`GET /api/relatorio`. Convenções:
- um boost fica "no ar" por 4h depois do registro de sucesso;
- registros a menos de 10 min um do outro formam um ciclo;
- os dias do relatório usam UTC-3 fixo.
**Motivo:**
- As 4h são o comportamento observado do "Impulsionar" da Shopee (mesma janela do
  limite de 5 slots já registrado em 2026-08-24), não um dado da API. O `boost_item` não
  devolve validade e não usamos endpoint de consulta de boost ativo, porque seria mais
  um endpoint sem confirmação. Fica como constante, `relatorio.DURACAO_BOOST`.
- O Brasil não tem horário de verão desde 2019. UTC-3 fixo evita depender de tzdata no
  SBC.
- Agregação no Pi (uma passada no histórico só quando a aba abre) em vez de mandar o
  histórico inteiro para o navegador: a resposta fica pequena mesmo com o `estado.json`
  crescendo. Gráfico em CSS puro, sem biblioteca.
**Quem:** usuário (pediu as abas) + executor (T-021)

## 2026-10-19 — Espera na subida conta a partir do último boost COM SUCESSO (corrige a entrada de hoje)
**Decisão:** revisa a entrada "Na subida, o serviço espera o que falta do intervalo desde
o último ciclo". A âncora passa a ser o último registro com sucesso
(`estado.ancora_do_intervalo`), com fallback para o último registro se nunca houve
sucesso. A proteção de relógio atrasado continua olhando qualquer registro.
**Motivo:** a aba "Relatório", com dados reais, mostrou zero itens no ar logo depois do
deploy. Os boosts das 16:36 UTC expiraram às 20:36, mas as tentativas que falharam por
slot cheio às 18:57 viraram a âncora e empurraram o próximo ciclo para 22:57, deixando
~2h20 sem boost. Tentativa que falha não ocupa slot e não deve contar. Fallback para o
último registro quando nunca houve sucesso: sem ele, uma loja com falha permanente
(credencial, IP) rodaria um ciclo a cada restart.
**Quem:** executor (T-014, ciclo 2), achado pelo relatório da T-021
