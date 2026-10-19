---
id: T-019
titulo: Painel web local (LAN) para ver o catálogo e ajustar os pesos do rodízio
projeto: shopee-rodizio
status: concluida
prioridade: alta
dependencias: [T-012, T-013, T-015, T-017, T-018]
areas: [src/shopee_rodizio/painel.py, src/shopee_rodizio/painel_web/, src/shopee_rodizio/config.py, scripts/definir_senha_painel.py, tests/test_painel.py]
tentativas: 1
agente: operacao-sbc
criada: 2026-10-19
atualizada: 2026-10-19
---

## Objetivo
Página servida pelo Pi, acessada de outro computador da LAN, para ver os produtos reais
(nome, imagem, preço, estoque, status), ver quais estão no rodízio e com que peso, e
ajustar pesos/incluir/remover itens visualmente.

## Critérios de aceite
- [x] `python -m shopee_rodizio.painel [config.toml]`; `http.server` da stdlib,
      single-thread, sem dependência nova (DECISOES 2026-10-19).
- [x] Rotas: `GET /` (+ `painel.js`/`painel.css`), `GET /api/estado`,
      `POST /api/catalogo/atualizar`, `POST /api/pesos`.
- [x] Gravação via `config.atualizar_itens` com checagem otimista de versão (409 se o
      arquivo mudou), validação (inteiros, peso 1..1000, sem repetidos, id conhecido, ao
      menos um item) — pedido inválido nunca toca no arquivo.
- [x] Acesso: só IPs de `[painel].redes_permitidas` (RFC 1918 + loopback), `Host` IP ou
      nome da máquina, HTTP Basic contra hash PBKDF2 em `[painel].senha_hash` (sem hash →
      503 em tudo), POST exige JSON + `X-Painel: 1` (CSRF), cabeçalhos CSP/nosniff/DENY.
- [x] Nenhuma credencial em HTML, JSON ou log (teste procura os três segredos e o hash nas
      respostas); `log_message` registra só IP, método, path sem query e status.
- [x] Catálogo via `armazem_token.cliente_da_config()` (nunca o token do config.toml).
- [x] `scripts/definir_senha_painel.py` grava só o hash (`config.definir_senha_painel`,
      atômico, só a chave `painel.senha_hash` pode mudar).
- [x] Página: busca, filtro "só no rodízio", ordenação, slider + número por item, % do
      peso total, chance estimada de entrar num ciclo (simula o sorteio sem reposição do
      `selecao.py`), histórico de 7 dias, próximo ciclo, barra de "não salvo".
- [x] `uv run pytest -q` e `uv run ruff check .` passam.
      `verificar: uv run pytest tests/test_painel.py -q`

## Notas de execução
PBKDF2 (200k iterações) custa perto de 1 s no CB1; o painel guarda em memória o digest do
header `Authorization` já validado, para não recalcular a cada requisição. Senha errada
espera 1 s (freia força bruta; a thread única serializa as tentativas).

**Reproduzir:** `.venv\Scripts\python.exe -m pytest tests/test_painel.py -q`
