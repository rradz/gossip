from __future__ import annotations

from typing import List
import networkx as nx

from gossip.utils import relabel_graph
from .common import Case


def build_cases() -> List[Case]:
    cases: List[Case] = []

    # ISO cases (relabel) across grid of n and p
    for n in [40, 80, 120, 160]:
        for p in [0.1, 0.3, 0.5, 0.7]:
            G = nx.erdos_renyi_graph(n, p, seed=int(n * 1000 * p) % 2**31)
            cases.append(Case("er_complexity", f"ER (n={n}, p={p:.1f}) — relabel", G, relabel_graph(G, seed=99 + n), True))

    # NON-ISO pairs (independent ER samples with same n,p)
    for n in [60, 100, 140]:
        for p in [0.2, 0.5]:
            G1 = nx.erdos_renyi_graph(n, p, seed=n)
            G2 = nx.erdos_renyi_graph(n, p, seed=n + 1)
            cases.append(Case("er_complexity", f"ER (n={n}, p={p:.1f}) — independent", G1, G2, False))

    return cases