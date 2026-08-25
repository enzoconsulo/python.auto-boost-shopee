---
id: T-010
titulo: Script de smoke-test contra a API real da Shopee
projeto: shopee-rodizio
status: pronta
prioridade: media
dependencias: [T-004, T-005]
areas: [scripts/smoke_test.py, README.md]
tentativas: 0
agente: integracao-shopee
criada: 2026-08-24
atualizada: 2026-08-25
---

## Objetivo
Criar `scripts/smoke_test.py`, um script standalone que o USUÁRIO roda manualmente, com
suas credenciais reais num `config.toml`, para confirmar (ou revelar que precisa ajustar)
o `endpoint_boost` e os nomes de parâmetro antes de colocar o serviço em produção contínua
— mitigação registrada em `_gestao/DECISOES.md` para a incerteza do endpoint exato de
impulsionamento (não confirmável em documentação pública sem login).

## Contexto
O script deve: carregar um `config.toml` (via `config.py`, T-002), autenticar (via
`cliente_shopee.py`, T-004) e tentar impulsionar UM único item de teste (o primeiro da
lista de itens configurada, ou um `item_id` passado por argumento de linha de comando),
imprimindo no terminal o resultado bruto da API (sucesso ou o corpo de erro completo) —
propositalmente verboso, porque o objetivo aqui é diagnóstico manual, não automação. Não
faça o script chamar a API de verdade nos testes automatizados do projeto (isso é papel do
usuário, com credenciais reais, fora do CI da fábrica) — não precisa de `tests/` para este
script.

Documente no README, numa seção "Confirmar o endpoint antes do primeiro deploy": por que
esse passo existe (a incerteza do endpoint), como rodar
(`uv run python scripts/smoke_test.py caminho/para/config.toml`), e o que fazer se a
resposta indicar `path`/parâmetro errado (editar `endpoint_boost` e os nomes de parâmetro
em `boost.py`/config e rodar de novo) — sem exigir que o agente tenha acesso à conta real
para validar isso agora.

## Critérios de aceite
- [ ] `scripts/smoke_test.py` existe, importa `config.py`/`cliente_shopee.py`/`boost.py`
      do pacote (não duplica lógica de assinatura HMAC), e `uv run python
      scripts/smoke_test.py --help` mostra uso sem traceback.
      `verificar: uv run python scripts/smoke_test.py --help`
- [ ] `uv run ruff check scripts/smoke_test.py` → sem erros.
      `verificar: uv run ruff check scripts/smoke_test.py`
- [ ] README.md tem a seção "Confirmar o endpoint antes do primeiro deploy" com o comando
      real de execução do script e a explicação da incerteza do endpoint.

## Notas de execução


## Verificação


## Conformidade


## Revisão
