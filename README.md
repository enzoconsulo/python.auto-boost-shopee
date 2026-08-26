# shopee-rodizio

Serviço leve, para rodar num BigTreeTech Pi 1.2.1 (SBC do Klipper), que faz rodízio
automático de impulsionamento de anúncios na Shopee (Shopee Open Platform), a cada 4
horas, respeitando um peso configurável por item.

## Funcionalidades

- Sorteio ponderado (sem reposição) dos itens de `[[itens]]` em `config.toml` a cada
  ciclo — item com `peso` maior é escolhido com mais frequência.
- Renovação automática do `access_token` da Shopee antes de expirar, com o token
  renovado persistido em disco (`token.json`) para sobreviver a um restart do serviço.
- Histórico de boosts (sucesso/falha) persistido em `estado.json`, escrita atômica.
- Log em arquivo com rotação por tamanho.
- Falha em um item (erro da API, exceção inesperada, falha ao gravar histórico) nunca
  derruba o processo — é registrada e o rodízio segue.
- Unidade systemd pronta para deploy 24/7 (`Restart=on-failure`).
- Script de smoke-test manual para confirmar o endpoint de boost contra credenciais reais.

## Como rodar

```
uv run python -m shopee_rodizio [caminho/para/config.toml]   # padrão: ./config.toml
```

## Como testar

```
uv run pytest -q
```

Lint (`ruff`):

```
uv run ruff check .
```

## Deploy no BTT Pi (systemd)

Passo a passo para instalar e deixar o serviço rodando 24/7 no BigTreeTech Pi 1.2.1 (mesmo
SBC que já roda o Klipper). Os comandos assumem o usuário `biqu` — padrão de fábrica da
imagem BTT Pi/CB1 (diferente do `pi` do Raspberry Pi OS original); troque por outro
usuário sem privilégio de root se o seu SBC usa um diferente.

1. **Copiar/clonar o projeto para o BTT Pi:**

   ```
   git clone <url-do-repositorio> /home/biqu/shopee-rodizio
   ```

   (ou `scp -r shopee-rodizio biqu@<ip-do-pi>:/home/biqu/` a partir da sua máquina, se o
   repositório não estiver acessível por `git` a partir do SBC).

2. **Instalar `uv` no SBC** (confirme antes se já não está disponível: `uv --version`):

   ```
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

   Isso instala o binário em `~/.local/bin/uv` — o caminho que `systemd/shopee-rodizio.service`
   usa no `ExecStart` (unidades systemd não carregam o `PATH` do shell interativo).

3. **Criar o `config.toml` real** a partir do exemplo, com as credenciais Shopee do usuário:

   ```
   cd /home/biqu/shopee-rodizio
   cp config.example.toml config.toml
   nano config.toml   # preencha [shopee] partner_id, partner_key, e [[itens]]
   ```

   `shop_id`, `access_token` e `refresh_token` não precisam ser digitados à mão: com
   `partner_id`/`partner_key` preenchidos, rode `scripts/gerar_token.py` (abaixo) para
   obter e gravar os três automaticamente.

4. **Instalar e ativar a unidade systemd:**

   ```
   sudo cp systemd/shopee-rodizio.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable --now shopee-rodizio
   ```

5. **Acompanhar o log:**

   ```
   journalctl -u shopee-rodizio -f
   ```

   ou, direto no arquivo configurado em `[caminhos].log` do `config.toml` (por padrão
   `shopee-rodizio.log`, relativo ao `WorkingDirectory` do serviço):

   ```
   tail -f /home/biqu/shopee-rodizio/shopee-rodizio.log
   ```

## Gerar shop_id/access_token/refresh_token automaticamente

A Shopee exige um login humano do dono da loja no navegador para autorizar o app — é o
mecanismo de consentimento do OAuth, não dá para automatizar por completo. Fora esse
clique único, o resto do processo (montar o link assinado, trocar o código pelos tokens,
gravar no `config.toml`) é feito pelo script:

```
uv run python scripts/gerar_token.py caminho/para/config.toml
```

Com `partner_id`/`partner_key` já preenchidos em `config.toml`, o script imprime um link;
abra-o, faça login como a conta vendedora da loja, clique em "Autorizar" e cole de volta a
URL para a qual você foi redirecionado (por padrão `https://google.com/?code=...&shop_id=...`
— troque com `--redirect` se o app cadastrado na Open Platform usa outra URL). O script
extrai `shop_id`, troca o `code` pelo par `access_token`/`refresh_token` e grava os três
direto no `config.toml`.

Depois desse passo único, nunca mais é preciso rodar esse script (nem intervir manualmente
de novo): `cliente_shopee.py` renova o `access_token` sozinho a cada ciclo e persiste o
`refresh_token` rotacionado em `token.json`, sobrevivendo a restarts do systemd.

Se a Shopee recusar a troca do código com `source_ip_undeclared`, o app está com IP
Whitelist ativado no Open Platform Console — descubra o IP público do BTT Pi
(`curl -4 ifconfig.me`) e cadastre-o em App list > IP Address Whitelist antes de tentar de
novo (o `code` copiado da URL expira rápido; se expirar, rode `gerar_token.py` de novo para
pegar um `code` fresco).

## Preencher [[itens]] automaticamente

Não precisa digitar item por item: com `config.toml` já com tokens válidos (passo
anterior), rode:

```
uv run python scripts/sincronizar_itens.py caminho/para/config.toml
```

Ele lista os anúncios ativos (`item_status = NORMAL`) da loja via `get_item_list` e
regenera o `[[itens]]` sozinho — pesos já definidos são preservados, itens novos entram
com peso 1 (ajustável com `--peso-padrao`), e itens que saíram do ar são removidos da
rotação (a lista de removidos é impressa, nada some silenciosamente). Rode de novo sempre
que o catálogo mudar.

## Confirmar o endpoint antes do primeiro deploy

O caminho do endpoint de impulsionamento (`/api/v2/product/boost_item`) e o formato do
payload (`item_id_list`) já foram confirmados contra uma conta real em 2026-08-25 (ver
`_gestao/DECISOES.md`), mas cada conta/app tem suas próprias permissões e restrições —
antes de colocar o serviço em produção contínua, rode o smoke-test com suas credenciais
reais para confirmar que o boost funciona na sua conta especificamente:

```
uv run python scripts/smoke_test.py caminho/para/config.toml
```

Por padrão ele impulsiona o primeiro item de `[[itens]]` do seu `config.toml`; passe
`--item-id ID` para escolher outro. O script imprime o resultado bruto da chamada — em
caso de sucesso, confirmação; em caso de erro, a mensagem completa devolvida pela API.
Se a mensagem indicar `path`/parâmetro inválido, ajuste `ciclo.endpoint_boost` no
`config.toml` e os nomes de parâmetro em `boost.py`, e rode o script de novo.

Atenção: cada execução faz uma chamada real de impulsionamento (consome o limite da sua
conta), então rode-o manualmente, não em automação.

## Atalhos do dia a dia (scripts/atalhos/)

Depois do deploy inicial, o operacional do dia a dia é só isto — rode a partir da raiz do
projeto no BTT Pi (`bash scripts/atalhos/<nome>.sh`, funciona mesmo sem o bit de execução):

| Script | O que faz |
|---|---|
| `instalar_servico.sh` | Copia a unidade systemd, `daemon-reload`, `enable --now`. Idempotente — rode de novo após um `git pull` que mude `systemd/shopee-rodizio.service`. |
| `iniciar_servico.sh` | `systemctl start` (serviço já instalado, só parado). |
| `parar_servico.sh` | `systemctl stop` (não desabilita o start automático no boot). |
| `reiniciar_servico.sh` | `systemctl restart` — necessário depois de editar `config.toml` ou atualizar o código. |
| `status_servico.sh` | Mostra se está rodando, há quanto tempo, e as últimas linhas de log. |
| `ver_logs.sh [N]` | Segue o log ao vivo (`journalctl -f`); `Ctrl+C` só fecha a visualização, o serviço continua rodando. |
| `editar_pesos.sh` | Abre `config.toml` no editor e, ao sair, já oferece reiniciar o serviço para aplicar. |
| `sincronizar_itens.sh` | `scripts/sincronizar_itens.py` já apontando pro `config.toml` do projeto. |
| `gerar_token.sh` | `scripts/gerar_token.py` já apontando pro `config.toml` do projeto. |
| `smoke_test.sh` | `scripts/smoke_test.py` já apontando pro `config.toml` do projeto (chamada real de boost). |
