from __future__ import annotations

from typing import List
import networkx as nx

from gossip.utils import relabel_graph
from .common import Case


def build_cases() -> List[Case]:
    cases: List[Case] = []

    # Cartesian products (□)
    C4 = nx.cycle_graph(4)
    C5 = nx.cycle_graph(5)
    torus_4x5 = nx.cartesian_product(C4, C5)
    torus_5x4 = nx.cartesian_product(C5, C4)
    cases.append(Case("products", "Torus C4□C5 vs C5□C4", torus_4x5, torus_5x4, True))

    # Hamming graph H(2,3) = K3 □ K3 (regular, distance-regular)
    K3 = nx.complete_graph(3)
    H_2_3 = nx.cartesian_product(K3, K3)
    cases.append(Case("products", "Hamming H(2,3) — relabel", H_2_3, relabel_graph(H_2_3, seed=23), True))

    # Square grid via product C4 □ C4
    torus_4x4 = nx.cartesian_product(C4, C4)
    cases.append(Case("products", "Torus C4□C4 — relabel", torus_4x4, relabel_graph(torus_4x4, seed=44), True))

    # Tensor (Kronecker) products (⊗) — commutative up to isomorphism
    P3 = nx.path_graph(3)
    P4 = nx.path_graph(4)
    T1 = nx.tensor_product(P3, P4)
    T2 = nx.tensor_product(P4, P3)
    cases.append(Case("products", "Tensor P3⊗P4 vs P4⊗P3", T1, T2, True))

    # Strong product (⨳) commutes up to isomorphism
    S1 = nx.strong_product(C4, P4)
    S2 = nx.strong_product(P4, C4)
    cases.append(Case("products", "Strong C4⨳P4 vs P4⨳C4", S1, S2, True))

    # Lexicographic product (⋅) is not commutative in general
    L1 = nx.lexicographic_product(C4, P4)
    L2 = nx.lexicographic_product(P4, C4)
    cases.append(Case("products", "Lexico C4⋅P4 vs P4⋅C4", L1, L2, False))

    # Non-ISO variation across products
    P4x = nx.cartesian_product(C4, P4)
    P5x = nx.cartesian_product(C4, nx.path_graph(5))
    cases.append(Case("products", "C4□P4 vs C4□P5", P4x, P5x, False))

    # Complete bipartite graphs
    K33 = nx.complete_bipartite_graph(3, 3)
    cases.append(Case("products", "Complete bipartite K3,3 — relabel", K33, relabel_graph(K33, seed=33), True))
    K45 = nx.complete_bipartite_graph(4, 5)
    cases.append(Case("products", "Complete bipartite K4,5 — relabel", K45, relabel_graph(K45, seed=45), True))
    cases.append(Case("products", "K3,4 vs K4,4", nx.complete_bipartite_graph(3, 4), nx.complete_bipartite_graph(4, 4), False))

    return cases


