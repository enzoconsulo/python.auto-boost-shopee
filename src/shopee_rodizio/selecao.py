"""Sorteio ponderado de itens, sem reposição, para um único ciclo de boost."""

from __future__ import annotations

import random

from shopee_rodizio.config import Item


def selecionar(itens: list[Item], limite_slots: int, rng: random.Random = random) -> list[Item]:
    """Sorteia por peso até `limite_slots` itens de `itens`, sem repetir nenhum.

    Se `limite_slots >= len(itens)`, devolve todos os itens (nada a sortear).
    """
    if limite_slots >= len(itens):
        return list(itens)

    restantes = list(itens)
    selecionados: list[Item] = []
    for _ in range(limite_slots):
        pesos = [item.peso for item in restantes]
        escolhido = rng.choices(restantes, weights=pesos, k=1)[0]
        restantes.remove(escolhido)
        selecionados.append(escolhido)
    return selecionados
