---
id: T-006
titulo: Sorteio ponderado de itens sem reposição por ciclo
projeto: shopee-rodizio
status: concluida
prioridade: alta
dependencias: [T-002, T-003]
areas: [src/shopee_rodizio/selecao.py, tests/test_selecao.py]
tentativas: 1
agente: config-estado
criada: 2026-08-24
atualizada: 2026-08-25
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

### Ciclo 1

- **[PASSOU] [executado] Critério 1: `uv run pytest tests/test_selecao.py -q` → todos os 4 testes passam**
  Comando: `.venv\Scripts\python.exe -m pytest tests/test_selecao.py -q`
  Saída: `....                                                                     [100%]` `4 passed in 0.08s`
  Testes verificados:
  - (a) Nunca repete item dentro do mesmo sorteio ✓
  - (b) Respeita o `limite_slots` ✓
  - (c) Devolve todos os itens quando `limite_slots >= len(itens)` ✓
  - (d) Teste estatístico (500 sorteios) confirma que item de peso 20 é escolhido com frequência maior ✓

- **[PASSOU] [executado] Critério 2: `uv run ruff check src/shopee_rodizio/selecao.py` → sem erros**
  Comando: `.venv\Scripts\python.exe -m ruff check src/shopee_rodizio/selecao.py`
  Saída: `All checks passed!`

Suíte completa: 35 passou, 0 falhou — `.venv\Scripts\python.exe -m pytest -q`
Graus de prova: 2 executados, 0 inspecionados, 0 julgados



## Conformidade

### Ciclo 1

Conformidade: cumpre

- Sorteio ponderado sem repetir item dentro do mesmo ciclo → `src/shopee_rodizio/selecao.py:17-24` (loop `for _ in range(limite_slots)` remove o escolhido de `restantes` a cada rodada), coberto por `tests/test_selecao.py:test_nunca_repete_item_dentro_do_mesmo_sorteio`.
- Respeita `limite_slots` → `src/shopee_rodizio/selecao.py:20` (`range(limite_slots)`), coberto por `test_respeita_limite_de_slots`.
- `limite_slots >= len(itens)` devolve todos → `src/shopee_rodizio/selecao.py:14-15`, coberto por `test_limite_maior_ou_igual_ao_numero_de_itens_devolve_todos`.
- Item de peso maior escolhido com frequência maior → `rng.choices(restantes, weights=pesos, k=1)` em `selecao.py:22-23`, coberto estatisticamente (500 sorteios, RNG semeado) por `test_item_de_peso_maior_e_escolhido_com_frequencia_maior`.
- Assinatura `selecionar(itens, limite_slots, rng=random)` bate com a sugerida no Contexto da tarefa; `rng` injetável confirmado pelo uso de `random.Random(seed)` nos 4 testes.
- Escopo: nenhuma sobra fora do pedido — não tocou `estado.py`/`historico_recente`, conforme o Contexto autorizava explicitamente deixar de fora.
- Reexecutei os dois comandos dos critérios (`pytest tests/test_selecao.py -q` e `ruff check src/shopee_rodizio/selecao.py`) e confirmo os mesmos resultados que o testador registrou: 4 testes passam, lint limpo.

## Revisão

### Ciclo 1

Aprovado sem ressalvas. Verifiquei o diff inteiro de `736f2f2`: a remoção sem reposição via `restantes.remove(escolhido)` é segura mesmo em tese de itens com id/peso idênticos, porque `Item` é um dataclass congelado com igualdade estrutural — remover qualquer ocorrência equivalente ao escolhido é funcionalmente idêntico, e `config.py` não permite peso ≤ 0 nem itens sem id, então não há caso plausível de item indistinguível causar sorteio inconsistente. O parâmetro `rng: random.Random = random` usa o módulo como valor padrão (não uma instância) — diverge do tipo anotado, mas é exatamente a assinatura sugerida pelo Contexto da tarefa e o projeto não roda checagem de tipos (só `ruff`), então não é achado.
