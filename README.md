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
