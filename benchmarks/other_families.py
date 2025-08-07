from __future__ import annotations

from typing import List, Optional
import itertools
import networkx as nx

from gossip.utils import relabel_graph
from .common import Case


def build_kneser(n: int, k: int) -> nx.Graph:
    if hasattr(nx, "kneser_graph"):
        return nx.kneser_graph(n, k)
    nodes = list(itertools.combinations(range(n), k))
    G = nx.Graph()
    G.add_nodes_from(nodes)
    for i in range(len(nodes)):
        for j in range(i + 1, len(nodes)):
            if set(nodes[i]).isdisjoint(nodes[j]):
                G.add_edge(nodes[i], nodes[j])
    return G


def build_johnson(n: int, k: int) -> nx.Graph:
    if hasattr(nx, "johnson_graph"):
        return nx.johnson_graph(n, k)
    nodes = list(itertools.combinations(range(n), k))
    G = nx.Graph()
    G.add_nodes_from(nodes)
    for i in range(len(nodes)):
        si = set(nodes[i])
        for j in range(i + 1, len(nodes)):
            sj = set(nodes[j])
            if len(si & sj) == k - 1:
                G.add_edge(nodes[i], nodes[j])
    return G


def build_paley(q: int) -> Optional[nx.Graph]:
    if hasattr(nx, "paley_graph"):
        try:
            return nx.paley_graph(q)
        except Exception:
            return None
    return None


def build_kneser_cases() -> List[Case]:
    cases: List[Case] = []
    for n, k in [(7, 2), (9, 2), (9, 3), (11, 2), (11, 3)]:
        G = build_kneser(n, k)
        cases.append(Case("kneser", f"Kneser K({n},{k}) — relabel", G, relabel_graph(G, seed=n*10+k), True))
    # Non-ISO pairs: vary k or n
    non_iso = [
        ("Kneser K(9,2) vs K(9,3)", build_kneser(9, 2), build_kneser(9, 3)),
        ("Kneser K(7,2) vs K(9,2)", build_kneser(7, 2), build_kneser(9, 2)),
        ("Kneser K(11,3) vs K(11,2)", build_kneser(11, 3), build_kneser(11, 2)),
    ]
    cases.extend(Case("kneser", name, G1, G2, False) for name, G1, G2 in non_iso)
    return cases


def build_johnson_cases() -> List[Case]:
    cases: List[Case] = []
    for n, k in [(6, 2), (7, 3), (8, 2), (9, 3), (10, 3)]:
        G = build_johnson(n, k)
        cases.append(Case("johnson", f"Johnson J({n},{k}) — relabel", G, relabel_graph(G, seed=n*10+k), True))
    # Non-ISO variations
    non_iso = [
        ("Johnson J(7,2) vs J(7,3)", build_johnson(7, 2), build_johnson(7, 3)),
        ("Johnson J(8,2) vs J(9,2)", build_johnson(8, 2), build_johnson(9, 2)),
        ("Johnson J(10,3) vs J(10,2)", build_johnson(10, 3), build_johnson(10, 2)),
    ]
    cases.extend(Case("johnson", name, G1, G2, False) for name, G1, G2 in non_iso)
    return cases


def build_paley_cases() -> List[Case]:
    cases: List[Case] = []
    for q in [5, 13, 17, 29]:
        G = build_paley(q)
        if G is not None:
            cases.append(Case("paley", f"Paley P({q}) — relabel", G, relabel_graph(G, seed=q), True))
    return cases


def build_rook_shrikhande_cases() -> List[Case]:
    cases: List[Case] = []
    R = None
    if hasattr(nx, "rooks_graph"):
        R = nx.rooks_graph(4, 4)
    else:
        # Fallback: construct rook's move graph on 4x4 board
        R = nx.Graph()
        for i in range(4):
            for j in range(4):
                for jj in range(4):
                    if jj != j:
                        R.add_edge((i, j), (i, jj))
                for ii in range(4):
                    if ii != i:
                        R.add_edge((i, j), (ii, j))
    S = nx.shrikhande_graph() if hasattr(nx, "shrikhande_graph") else None
    if R is not None and S is not None:
        cases.append(Case("rook_shrikhande", "Rook R(4,4) vs Shrikhande", R, S, False))
        cases.append(Case("rook_shrikhande", "Rook R(4,4) — relabel", R, relabel_graph(R, seed=44), True))
        cases.append(Case("rook_shrikhande", "Shrikhande — relabel", S, relabel_graph(S, seed=16), True))
    return cases


def build_gpetersen_cases() -> List[Case]:
    cases: List[Case] = []
    if hasattr(nx, "generalized_petersen_graph"):
        for n, k in [(8, 3), (10, 2), (12, 5), (14, 3), (15, 4)]:
            G = nx.generalized_petersen_graph(n, k)
            cases.append(Case("gpetersen", f"GP({n},{k}) — relabel", G, relabel_graph(G, seed=n*10+k), True))
        # Non-ISO pairs with same n different k
        cases.extend(
            [
                Case("gpetersen", "GP(10,2) vs GP(10,3)", nx.generalized_petersen_graph(10, 2), nx.generalized_petersen_graph(10, 3), False),
                Case("gpetersen", "GP(12,5) vs GP(12,4)", nx.generalized_petersen_graph(12, 5), nx.generalized_petersen_graph(12, 4), False),
                Case("gpetersen", "GP(14,3) vs GP(14,5)", nx.generalized_petersen_graph(14, 3), nx.generalized_petersen_graph(14, 5), False),
            ]
        )
    return cases