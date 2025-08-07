from __future__ import annotations

from typing import List
import networkx as nx

from gossip.utils import relabel_graph
from .common import Case


def cayley_Zn(n: int, generators: List[int]) -> nx.Graph:
    # Cayley graph of Z_n with given generator steps (undirected)
    G = nx.Graph()
    for v in range(n):
        for g in generators:
            u = (v + g) % n
            G.add_edge(v, u)
    return G


def build_cases() -> List[Case]:
    cases: List[Case] = []

    # Approximate "zeta" family using various generator sets on Z_n (circulant/Cayley)
    examples = [
        ("Zeta-like Z_30{1,7,11}", 30, [1, 7, 11]),
        ("Zeta-like Z_32{1,3,9}", 32, [1, 3, 9]),
        ("Zeta-like Z_36{1,5,13}", 36, [1, 5, 13]),
        ("Zeta-like Z_40{1,7,9}", 40, [1, 7, 9]),
    ]
    for label, n, gens in examples:
        G = cayley_Zn(n, gens)
        cases.append(Case("zeta", f"{label} — relabel", G, relabel_graph(G, seed=n), True))

    # NON-ISO pairs with slightly different generator sets
    pairs = [
        ("Z_30{1,7,11} vs Z_30{1,7,13}", 30, [1, 7, 11], [1, 7, 13]),
        ("Z_32{1,3,9} vs Z_32{1,5,9}", 32, [1, 3, 9], [1, 5, 9]),
        ("Z_36{1,5,13} vs Z_36{1,5,11}", 36, [1, 5, 13], [1, 5, 11]),
        ("Z_40{1,7,9} vs Z_40{1,9,11}", 40, [1, 7, 9], [1, 9, 11]),
    ]
    for label, n, g1, g2 in pairs:
        G1 = cayley_Zn(n, g1)
        G2 = cayley_Zn(n, g2)
        cases.append(Case("zeta", label, G1, G2, None))

    return cases