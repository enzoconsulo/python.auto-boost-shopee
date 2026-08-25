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
