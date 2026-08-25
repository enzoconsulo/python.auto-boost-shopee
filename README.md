# shopee-rodizio

Serviço leve, para rodar num BigTreeTech Pi 1.2.1 (SBC do Klipper), que faz rodízio
automático de impulsionamento de anúncios na Shopee (Shopee Open Platform), a cada 4
horas, respeitando um peso configurável por item.

## Como rodar

```
uv run python -m shopee_rodizio
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
SBC que já roda o Klipper). Os comandos assumem o usuário `pi`; troque por outro usuário
sem privilégio de root se o seu SBC usa um diferente — o mesmo usuário que já roda o
Klipper costuma servir, por já ter acesso de escrita ao diretório do projeto, mas não é
obrigatório.

1. **Copiar/clonar o projeto para o BTT Pi:**

   ```
   git clone <url-do-repositorio> /home/pi/shopee-rodizio
   ```

   (ou `scp -r shopee-rodizio pi@<ip-do-pi>:/home/pi/` a partir da sua máquina, se o
   repositório não estiver acessível por `git` a partir do SBC).

2. **Instalar `uv` no SBC** (confirme antes se já não está disponível: `uv --version`):

   ```
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

   Isso instala o binário em `~/.local/bin/uv` — o caminho que `systemd/shopee-rodizio.service`
   usa no `ExecStart` (unidades systemd não carregam o `PATH` do shell interativo).

3. **Criar o `config.toml` real** a partir do exemplo, com as credenciais Shopee do usuário:

   ```
   cd /home/pi/shopee-rodizio
   cp config.example.toml config.toml
   nano config.toml   # preencha [shopee] (partner_id, partner_key, shop_id, tokens) e [[itens]]
   ```

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
   tail -f /home/pi/shopee-rodizio/shopee-rodizio.log
   ```

## Confirmar o endpoint antes do primeiro deploy

O caminho exato do endpoint de impulsionamento (`ciclo.endpoint_boost`) e os nomes de
parâmetro usados em `boost.py` são um palpite plausível — a documentação pública da
Shopee Open Platform não confirma esse endpoint sem login no portal do desenvolvedor (ver
`_gestao/DECISOES.md`, "Endpoint de boost da Shopee: incerteza registrada"). Antes de
colocar o serviço em produção contínua, rode o smoke-test com suas credenciais reais para
confirmar (ou revelar que precisa ajustar) esse endpoint:

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
