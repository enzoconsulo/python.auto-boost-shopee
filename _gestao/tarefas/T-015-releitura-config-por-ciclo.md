---
id: T-015
titulo: Reler o config.toml no início de cada ciclo (pesos aplicados sem reiniciar)
projeto: shopee-rodizio
status: concluida
prioridade: alta
dependencias: [T-012]
areas: [src/shopee_rodizio/__main__.py, tests/test_loop_subida_e_releitura.py, scripts/atalhos/editar_pesos.sh]
tentativas: 1
agente: operacao-sbc
criada: 2026-10-19
atualizada: 2026-10-19
---

## Objetivo
O painel web (T-018) só precisa gravar o `config.toml`; o serviço aplica no próximo
ciclo, sem `systemctl restart` e sem dar permissão de systemctl ao processo do painel.

## Critérios de aceite
- [x] `__main__._recarregar` relê o `config.toml` no início de cada volta do loop.
- [x] Config inválida no disco (TOML quebrado, peso inválido, arquivo sumido) → warning no
      log e o loop segue com a última config válida.
- [x] O cliente só é recriado se `[shopee]`, `[rede]` ou o caminho do estado mudarem
      (recriar sempre descartaria um token renovado ainda não gravado em disco).
- [x] Corrida de escrita: o serviço só lê; os escritores usam `config.atualizar_itens`
      (atômico, lock `config.toml.lock`, checagem de versão) — ver DECISOES 2026-10-19.
- [x] `editar_pesos.sh` não oferece mais restart; valida o arquivo ao sair do editor.
- [x] `uv run pytest -q` e `uv run ruff check .` passam.
      `verificar: uv run pytest -q`

**Reproduzir:** `.venv\Scripts\python.exe -m pytest tests/test_loop_subida_e_releitura.py -q`
