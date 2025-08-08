from __future__ import annotations

from typing import List
import networkx as nx

from gossip.utils import relabel_graph, generate_cfi_pair
from .common import Case


def build_cases() -> List[Case]:
    cases: List[Case] = []

    # Single vertex
    G = nx.Graph()
    G.add_node(0)
    cases.append(Case("legacy", "Single Vertex — relabel", G, relabel_graph(G, seed=1), True))

    # Paths
    cases.append(Case("legacy", "Path P5 — relabel", nx.path_graph(5), relabel_graph(nx.path_graph(5), seed=5), True))

    # Complete graphs (small and larger)
    for n in [3, 4, 5, 6, 10, 20, 30]:
        K = nx.complete_graph(n)
        cases.append(Case("legacy", f"Complete K{n} — relabel", K, relabel_graph(K, seed=n), True))

    # Cycles
    for n in [4, 5, 6, 7, 8]:
        C = nx.cycle_graph(n)
        cases.append(Case("legacy", f"Cycle C{n} — relabel", C, relabel_graph(C, seed=n), True))

    # Stars
    S = nx.star_graph(5)  # 6 vertices total
    cases.append(Case("legacy", "Star S6 — relabel", S, relabel_graph(S, seed=6), True))

    # Hypercubes
    for dim in [2, 4]:  # Q3 already in basic
        Q = nx.hypercube_graph(dim)
        cases.append(Case("legacy", f"Hypercube Q{dim} — relabel", Q, relabel_graph(Q, seed=dim), True))

    # Disconnected: two triangles
    H = nx.Graph()
    H.add_edges_from([(0, 1), (1, 2), (0, 2)])
    H.add_edges_from([(3, 4), (4, 5), (3, 5)])
    cases.append(Case("legacy", "Two triangles (disconnected) — relabel", H, relabel_graph(H, seed=12), True))

    # Triangle from directed conversion (equivalent to C3)
    DG = nx.DiGraph([(0, 1), (1, 2), (2, 0)])
    T = DG.to_undirected()
    cases.append(Case("legacy", "Directed triangle → undirected — relabel", T, relabel_graph(T, seed=33), True))

    # Random regular graphs (relabel invariance)
    for d in [3, 4, 5]:
        for n in [10, 20, 30]:
            if (n * d) % 2 != 0:
                continue
            R = nx.random_regular_graph(d, n, seed=n + d)
            cases.append(Case("legacy", f"Random {d}-regular (n={n}) — relabel", R, relabel_graph(R, seed=n * 10 + d), True))

    # Random regular graphs (distinct random instances likely NON-ISO)
    for d in [3, 4]:
        for n in [10, 12, 14]:
            if (n * d) % 2 != 0:
                continue
            G1 = nx.random_regular_graph(d, n, seed=42)
            G2 = nx.random_regular_graph(d, n, seed=43)
            cases.append(Case("legacy", f"Random {d}-regular pair (n={n})", G1, G2, None))

    # Petersen graph sanity pairs
    P = nx.petersen_graph()
    cases.append(Case("legacy", "Petersen — relabel", P, relabel_graph(P, seed=7), True))
    cases.append(Case("legacy", "Petersen vs K10", P, nx.complete_graph(10), False))

    # ER graphs (exclude very large; add up to n=200 as sanity/perf samples)
    for n in [10, 20, 50, 100, 200]:
        G = nx.erdos_renyi_graph(n, 0.3, seed=42)
        cases.append(Case("legacy", f"ER G({n},0.3) — relabel", G, relabel_graph(G, seed=n), True))

    # Large CFI pairs from tests (let NetworkX be the oracle)
    for n in [10, 15, 20]:
        base = nx.cycle_graph(n)
        G1, G2 = generate_cfi_pair(base)
        cases.append(Case("legacy", f"CFI (cycle {n})", G1, G2, None))

    return cases


