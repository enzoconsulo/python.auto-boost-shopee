---
id: T-014
titulo: Na subida, esperar o que falta do intervalo desde o último ciclo (restart não queima ciclo)
projeto: shopee-rodizio
status: concluida
prioridade: alta
dependencias: []
areas: [src/shopee_rodizio/estado.py, src/shopee_rodizio/__main__.py, tests/test_loop_subida_e_releitura.py, scripts/atalhos/reiniciar_servico.sh]
tentativas: 1
agente: operacao-sbc
criada: 2026-10-19
atualizada: 2026-10-19
---

## Objetivo
Corrigir o defeito 1.1 da auditoria de 2026-10-19: `executar_loop` disparava um ciclo
antes do primeiro `sleep`, sem saber quando o anterior tinha rodado.

## Contexto
Evidência de produção: restarts às 18:56 e 18:57 de 19/10 dispararam dois ciclos 2h20
depois do ciclo legítimo das 16:36; os dez boosts voltaram com
`product.error_busi: reached shop's bump slot limit`. O `estado.json` já guarda o
timestamp de cada boost, então não é preciso arquivo novo nem dependência nova.

## Critérios de aceite
- [x] `estado.ultimo_ciclo_em` e `estado.segundos_ate_proximo_ciclo` (função pura, com
      `agora` injetável): sem histórico → 0; 2h20 depois → 1h40; mais de um intervalo → 0;
      timestamp ilegível ignorado.
- [x] Relógio atrasado (o CB1 não tem RTC; antes do NTP o fake-hwclock volta no tempo) →
      espera o intervalo cheio, nunca dispara.
- [x] `executar_loop` dorme esse tempo antes do primeiro ciclo e loga a espera
      ("último ciclo em …; aguardando N min até o próximo (…)").
- [x] `uv run pytest -q` e `uv run ruff check .` passam.
      `verificar: uv run pytest -q`

## Notas de execução
Conta qualquer registro, com sucesso ou não: um ciclo que falhou inteiro por slot cheio
também ocupou a janela. Efeito colateral bom: com isso, o `Requires=` do túnel (T-016) pode
reiniciar o rodízio quando o túnel reinicia sem custo nenhum.

**Reproduzir:** `.venv\Scripts\python.exe -m pytest tests/test_loop_subida_e_releitura.py -q`

### Ciclo 2
A âncora passou a ser o último boost com sucesso (`estado.ancora_do_intervalo`), não o
último registro. Achado em produção pela aba "Relatório" (T-021): as falhas por slot cheio
das 18:57 adiaram o ciclo para 22:57, deixando a loja sem boost das 20:36 às 22:57. Ver
DECISOES 2026-10-19 ("Espera na subida conta a partir do último boost COM SUCESSO").
Testes novos: falhas depois do último sucesso não empurram o ciclo; sucesso antigo + falha
recente roda na hora; relógio atrasado vale também quando o registro futuro é uma falha.
