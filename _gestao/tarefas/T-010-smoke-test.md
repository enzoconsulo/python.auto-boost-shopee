---
id: T-010
titulo: Script de smoke-test contra a API real da Shopee
projeto: shopee-rodizio
status: em-execucao
prioridade: media
dependencias: [T-004, T-005]
areas: [scripts/smoke_test.py, README.md]
tentativas: 1
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

Criado `scripts/smoke_test.py`: importa `carregar_config`/`ConfigError` de `config.py`,
`ClienteShopee` de `cliente_shopee.py` e `impulsionar` de `boost.py` — a chamada real de
impulsionamento é feita via `boost.impulsionar(cliente, config, item_id)`, o mesmo caminho
usado em produção por `ciclo.py`; nenhuma lógica de assinatura HMAC é reimplementada (o
cliente já cuida disso via `ClienteShopee.chamar`). Faz UMA única chamada por execução
(item consome o limite real da conta), imprime endpoint/shop_id/item_id antes de chamar e,
depois, sucesso ou a mensagem de erro completa devolvida pela API (via
`ResultadoBoost.mensagem`, que já concatena `error: message` do corpo de erro da Shopee) —
inclui aviso se o `access_token` foi renovado durante a chamada. Erro ao carregar o
`config.toml` (arquivo ausente ou inválido) é capturado e vira mensagem amigável em vez de
traceback. `--item-id` (opcional) sobrepõe o primeiro item de `[[itens]]`.

Testado manualmente: `--help` mostra uso e sai com código 0; caminho de config inexistente
mostra erro amigável (código 1, sem traceback); rodando com `config.example.toml` (valores
de exemplo, não credenciais reais) a chamada de rede realmente sai e a Shopee responde com
erro de validação (`partner_id inválido`), confirmando que o fluxo de assinatura + POST
funciona ponta a ponta e que o script imprime o corpo de erro completo.

README.md ganhou a seção "Confirmar o endpoint antes do primeiro deploy": por que o passo
existe (incerteza do endpoint, ver DECISOES.md), o comando de execução e o que fazer se a
resposta indicar path/parâmetro errado.

Não há `tests/` para este script (a tarefa dispensa, propositalmente: ele faz uma chamada
de rede real e não deve rodar em CI).

**Reproduzir:**
`.venv/Scripts/python.exe scripts/smoke_test.py --help && .venv/Scripts/python.exe -m ruff check scripts/smoke_test.py`
(`uv` não está no PATH deste ambiente — os critérios usam `uv run`, mas o efeito é o
mesmo via o Python do `.venv` do projeto.)

Nota: havia mudanças pré-existentes e não commitadas em `src/shopee_rodizio/__main__.py`,
`tests/test_ciclo.py` e `_gestao/tarefas/T-008-ciclo.md` (de T-008) antes desta execução —
não fazem parte de T-010 e não foram tocadas nem commitadas por mim.

## Verificação


## Conformidade


## Revisão
