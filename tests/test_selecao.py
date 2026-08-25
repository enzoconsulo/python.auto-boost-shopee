import random
from collections import Counter

from shopee_rodizio.config import Item
from shopee_rodizio.selecao import selecionar


def _itens(*pesos: int) -> list[Item]:
    return [Item(id=i, peso=peso) for i, peso in enumerate(pesos, start=1)]


def test_nunca_repete_item_dentro_do_mesmo_sorteio():
    itens = _itens(1, 2, 3, 4, 5)
    rng = random.Random(42)

    selecionados = selecionar(itens, limite_slots=3, rng=rng)

    ids = [item.id for item in selecionados]
    assert len(ids) == len(set(ids))


def test_respeita_limite_de_slots():
    itens = _itens(1, 2, 3, 4, 5)
    rng = random.Random(1)

    selecionados = selecionar(itens, limite_slots=2, rng=rng)

    assert len(selecionados) == 2


def test_limite_maior_ou_igual_ao_numero_de_itens_devolve_todos():
    itens = _itens(1, 2, 3)
    rng = random.Random(7)

    selecionados = selecionar(itens, limite_slots=5, rng=rng)

    assert {item.id for item in selecionados} == {item.id for item in itens}
    assert len(selecionados) == len(itens)


def test_item_de_peso_maior_e_escolhido_com_frequencia_maior():
    itens = _itens(1, 1, 20)
    rng = random.Random(123)

    contagem = Counter()
    for _ in range(500):
        selecionados = selecionar(itens, limite_slots=1, rng=rng)
        contagem[selecionados[0].id] += 1

    assert contagem[3] > contagem[1]
    assert contagem[3] > contagem[2]
