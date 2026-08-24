---
id: T-006
titulo: Sorteio ponderado de itens sem reposição por ciclo
projeto: shopee-rodizio
status: backlog
prioridade: alta
dependencias: [T-002, T-003]
areas: [src/shopee_rodizio/selecao.py, tests/test_selecao.py]
tentativas: 0
agente: config-estado
criada: 2026-08-24
atualizada: 2026-08-24
---

## Objetivo
Implementar `src/shopee_rodizio/selecao.py`: a cada ciclo, sorteia por peso — sem repetir
o mesmo item duas vezes DENTRO do mesmo ciclo — um subconjunto de itens até o limite
configurável de slots simultâneos (`config.ciclo.limite_slots`).

## Contexto
Entrada: lista de itens (id + peso, de `config.py`/T-002) e limite de slots. Não é preciso
usar biblioteca externa: sorteio ponderado sem reposição é um algoritmo pequeno (repetir
"escolher 1 por peso entre os restantes, remover, repetir" `limite_slots` vezes) — cabe
tranquilamente abaixo do limiar de ~50 linhas do filtro de não-adoção de dependência em
`_sistema/BIBLIOTECAS.md`, então implemente à mão (é a regra de negócio central do
projeto — ninguém escreve isso por você).

Se `limite_slots >= número de itens configurados`, o sorteio simplesmente devolve todos os
itens (não há o que sortear). Exponha algo como
`selecionar(itens: list[Item], limite_slots: int, rng=random) -> list[Item]`, aceitando um
`rng` injetável para o teste ser determinístico (`random.Random(seed)`).

Este módulo não precisa olhar o histórico (`estado.py`) para a primeira versão — o
Objetivo do projeto (RF-03) pede sorteio por peso; usar o histórico para desempatar ou
evitar repetição ENTRE ciclos é uma melhoria futura, não bloqueia esta tarefa. Se quiser
usar `historico_recente` (T-003) para isso, documente a decisão nas Notas de execução.

## Critérios de aceite
- [ ] `uv run pytest tests/test_selecao.py -q` → todos os testes passam: (a) nunca repete
      item dentro do mesmo sorteio, (b) respeita o `limite_slots`, (c) devolve todos os
      itens quando `limite_slots >= len(itens)`, (d) teste estatístico com RNG semeado
      confirma que item de peso maior é escolhido com frequência maior ao longo de N
      sorteios (não precisa bater a distribuição exata, só a direção).
      `verificar: uv run pytest tests/test_selecao.py -q`
- [ ] `uv run ruff check src/shopee_rodizio/selecao.py` → sem erros.
      `verificar: uv run ruff check src/shopee_rodizio/selecao.py`

## Notas de execução


## Verificação


## Conformidade


## Revisão
