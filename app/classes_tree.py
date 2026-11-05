"""Arborescence de rang (cahier 3.2.c et 3.2.e)."""


class CycleError(ValueError):
    pass


def ancestors(prev_map: dict, cid: str) -> list:
    """Chaîne des classes précédentes, la plus proche d'abord. Lève CycleError si cycle."""
    chain, seen, cur = [], {cid}, prev_map.get(cid)
    while cur is not None:
        if cur in seen:
            raise CycleError(cid)
        chain.append(cur)
        seen.add(cur)
        cur = prev_map.get(cur)
    return chain


def assert_acyclic(prev_map: dict) -> None:
    """Vérifie toutes les classes (propagation aux classes dépendantes)."""
    for cid in prev_map:
        ancestors(prev_map, cid)
