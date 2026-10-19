---
id: T-021
titulo: Painel — abas "No ar agora" e "Relatório" a partir do histórico
projeto: shopee-rodizio
status: concluida
prioridade: media
dependencias: [T-019]
areas: [src/shopee_rodizio/relatorio.py, src/shopee_rodizio/painel.py, src/shopee_rodizio/painel_web/, tests/test_relatorio.py, tests/test_painel.py]
tentativas: 1
agente: operacao-sbc
criada: 2026-10-19
atualizada: 2026-10-19
---

## Objetivo
Pedido do usuário após o deploy do painel: uma aba com o que está impulsionado agora e um
relatório organizado do histórico, "nada muito pesado".

## Critérios de aceite
- [x] `relatorio.no_ar_agora`: boosts com sucesso nas últimas 4 h, com minutos até expirar,
      e o último ciclo item a item (registros a menos de 10 min um do outro = mesmo ciclo).
- [x] `relatorio.relatorio(dias)`: resumo (boosts ok/falha, taxa, ciclos com sucesso, itens
      distintos), boosts por dia em UTC-3, tabela por item (parte dos boosts × parte do
      peso atual, último boost) e as 5 falhas mais frequentes.
- [x] `GET /api/relatorio?dias=1|7|30|90` (outro valor vira 7), atrás da mesma
      autenticação; só agregados, sem credenciais.
- [x] Página com abas (Pesos / No ar agora / Relatório), lembrando a aba pelo `#hash`. O
      relatório só é pedido ao Pi quando a aba abre. Gráfico de barras em CSS puro, sem
      biblioteca.
- [x] `uv run pytest -q` e `uv run ruff check .` passam; conferido visualmente em desktop
      e largura de celular.
      `verificar: uv run pytest tests/test_relatorio.py -q`

**Reproduzir:** `.venv\Scripts\python.exe -m pytest tests/test_relatorio.py tests/test_painel.py -q`
