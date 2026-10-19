---
id: T-012
titulo: Escrita atômica e durável compartilhada; regravação segura do [[itens]] do config.toml
projeto: shopee-rodizio
status: concluida
prioridade: alta
dependencias: []
areas: [src/shopee_rodizio/arquivo.py, src/shopee_rodizio/config.py, src/shopee_rodizio/estado.py, src/shopee_rodizio/armazem_token.py, scripts/sincronizar_itens.py, tests/test_config_gravacao.py, tests/test_armazem_token.py]
tentativas: 1
agente: config-estado
criada: 2026-10-19
atualizada: 2026-10-19
---

## Objetivo
Corrigir o defeito 1.5 da auditoria de produção de 2026-10-19: `sincronizar_itens.py`
gravava o `config.toml` com `Path.write_text` direto (não atômico). Extrair uma escrita
atômica única, usada por todos os escritores (estado, token, config), e uma função de
regravação do `[[itens]]` que o script e o painel web (T-018) consomem.

## Contexto
- Cartão SD do BTT Pi já corrompeu arquivo em produção; o painel (T-018) passa a escrever
  no mesmo `config.toml` que o script.
- **Achado na leitura do Pi:** o `config.toml` de produção tem `[rede]` (proxy do túnel)
  DEPOIS dos `[[itens]]`. O `_regenerar_bloco_itens` antigo truncava tudo a partir do
  primeiro `[[itens]]` — a próxima sincronização apagaria o proxy e derrubaria todas as
  chamadas por IP fora do whitelist.

## Critérios de aceite
- [x] `arquivo.gravar_atomico`: temporário de nome único no mesmo diretório (`mkstemp`),
      `fsync` do arquivo e do diretório, preserva o modo do original, `os.replace`.
      `estado.py` e `armazem_token.py` passam a usá-la; o lock de `armazem_token` vira
      `arquivo.travado`, reaproveitável.
- [x] `config.regenerar_bloco_itens` troca só os blocos `[[itens]]` e preserva seções
      posteriores (com o comentário que as precede).
- [x] `config.gravar_config` só grava texto que é TOML válido, passa na validação e não
      muda nenhuma seção fora de `itens`; `config.atualizar_itens` faz ler → regenerar →
      gravar sob `config.toml.lock`, com checagem otimista de versão (`ConflitoConfig`).
- [x] `sincronizar_itens.py` usa `atualizar_itens`; falha de validação não toca no arquivo.
- [x] `uv run pytest -q` e `uv run ruff check .` passam.
      `verificar: uv run pytest -q`

## Notas de execução
- `tests/test_config_gravacao.py` (12 casos) usa um TOML com a mesma forma do de
  produção (`[rede]` depois dos itens).
- Seção `[painel]` opcional entrou em `Config` aqui (padrões; ausência = comportamento
  inalterado), porque a validação do config gravado precisa conhecê-la.

**Reproduzir:** `.venv\Scripts\python.exe -m pytest -q` · `.venv\Scripts\python.exe -m ruff check .`
