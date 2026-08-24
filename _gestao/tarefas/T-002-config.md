---
id: T-002
titulo: Leitura e validação da configuração TOML
projeto: shopee-rodizio
status: backlog
prioridade: alta
dependencias: [T-001]
areas: [src/shopee_rodizio/config.py, config.example.toml, tests/test_config.py]
tentativas: 0
agente: config-estado
criada: 2026-08-24
atualizada: 2026-08-24
---

## Objetivo
Implementar `src/shopee_rodizio/config.py`: lê e valida a configuração do usuário a partir
de um arquivo TOML, expondo uma estrutura tipada (`dataclass`) com credenciais Shopee,
lista de itens com peso, intervalo do ciclo, limite de slots simultâneos e caminhos de
log/estado. Entrega também `config.example.toml`, o exemplo documentado que o usuário copia
e edita.

## Contexto
Use `tomllib` (stdlib, leitura apenas — Python 3.11+, já resolvido pelo `uv` na T-001), sem
adicionar dependência de parsing TOML. Campos mínimos do TOML:

```toml
[shopee]
partner_id = 0
partner_key = "..."
shop_id = 0
access_token = "..."
refresh_token = "..."

[ciclo]
intervalo_horas = 4
limite_slots = 5
endpoint_boost = "/api/v2/product/boost_item"   # RF-04: caminho configurável, ver DECISOES.md

[caminhos]
log = "shopee-rodizio.log"
estado = "estado.json"

[[itens]]
id = 123456789
peso = 3

[[itens]]
id = 987654321
peso = 1
```

O nome exato do endpoint (`endpoint_boost`) é um CAMPO da config, não uma constante no
código — ver `_gestao/DECISOES.md`, entrada "Endpoint de boost da Shopee: incerteza
registrada". `config.py` só precisa saber que existe essa string; quem a usa é T-004/T-005.

Validações obrigatórias, com mensagem de erro clara (não silenciar): item sem `id` ou sem
`peso`, peso `<= 0`, `intervalo_horas <= 0`, `limite_slots <= 0`, seção `[shopee]`
incompleta. Erro de validação deve ser uma exceção com mensagem que diz QUAL campo está
errado.

## Critérios de aceite
- [ ] `uv run pytest tests/test_config.py -q` → todos os testes passam, incluindo casos de
      config válida e ao menos 2 casos de config inválida (peso negativo, campo Shopee
      ausente) que devem levantar exceção com mensagem identificando o campo.
      `verificar: uv run pytest tests/test_config.py -q`
- [ ] `config.example.toml` é TOML válido.
      `verificar: uv run python -c "import tomllib,pathlib; tomllib.loads(pathlib.Path('config.example.toml').read_text())"`
- [ ] `uv run ruff check src/shopee_rodizio/config.py` → sem erros.
      `verificar: uv run ruff check src/shopee_rodizio/config.py`

## Notas de execução


## Verificação


## Conformidade


## Revisão
