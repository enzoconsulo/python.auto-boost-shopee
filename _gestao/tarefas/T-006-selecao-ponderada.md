---
id: T-006
titulo: Sorteio ponderado de itens sem reposição por ciclo
projeto: shopee-rodizio
status: em-teste
prioridade: alta
dependencias: [T-002, T-003]
areas: [src/shopee_rodizio/selecao.py, tests/test_selecao.py]
tentativas: 1
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

Implementado `src/shopee_rodizio/selecao.py` com `selecionar(itens, limite_slots, rng=random)`:
sorteio ponderado sem reposição usando `rng.choices(..., weights=..., k=1)` repetido
`limite_slots` vezes, removendo o escolhido a cada rodada. Quando `limite_slots >=
len(itens)`, devolve todos os itens sem sortear. `rng` aceita `random.Random(seed)` para
determinismo em teste (assinatura usa o módulo `random` como padrão, mas qualquer objeto
com `.choices` compatível serve).

Teste escrito antes da implementação (`tests/test_selecao.py`): rodei `pytest
tests/test_selecao.py -q` e confirmei o vermelho (`ModuleNotFoundError`) antes de criar
`selecao.py`; depois da implementação, os 4 casos passaram. Cobre os 4 critérios: (a) sem
repetição dentro do sorteio, (b) respeita `limite_slots`, (c) `limite_slots >= len(itens)`
devolve todos, (d) teste estatístico (500 sorteios, RNG semeado) confirma que o item de
peso 20 é escolhido mais vezes que os de peso 1.

Não usei `estado.py`/`historico_recente` nesta versão — conforme o Contexto da tarefa,
desempate/histórico entre ciclos fica para melhoria futura (RF-03 pede só sorteio por
peso).

Não foi necessário registrar nova decisão em `DECISOES.md`: nenhuma dependência nova,
algoritmo cabe abaixo do limiar de 50 linhas (ficou com 23).

**Reproduzir:** `.venv\Scripts\python.exe -m pytest tests/test_selecao.py -q`
(nota: `uv` não está no PATH deste ambiente; usei o interpretador do venv diretamente —
mesmo comportamento do critério `uv run pytest ...`)

**Commit:** `736f2f2`

## Verificação


## Conformidade


## Revisão
