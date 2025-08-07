from __future__ import annotations

import networkx as nx
from typing import List

from gossip.utils import generate_circulant_graph, relabel_graph
from .common import Case


def build_cases() -> List[Case]:
    cases: List[Case] = []
    # Relabel invariance for many sizes/connection sets
    examples = [
        ("C12[1,3]", 12, [1, 3]),
        ("C16[1,2,4]", 16, [1, 2, 4]),
        ("C18[1,5]", 18, [1, 5]),
        ("C20[1,2,5]", 20, [1, 2, 5]),
        ("C22[1,3,7]", 22, [1, 3, 7]),
        ("C24[1,3,5]", 24, [1, 3, 5]),
    ]
    for label, n, conn in examples:
        G = generate_circulant_graph(n, conn)
        cases.append(Case("circulant", f"Circulant {label} — relabel", G, relabel_graph(G, seed=n), True))

    # Known tricky non-isomorphic pair (README)
    A = generate_circulant_graph(13, [1, 3, 4])
    B = generate_circulant_graph(13, [1, 3, 6])
    cases.append(Case("circulant", "Circulant C13[1,3,4] vs C13[1,3,6]", A, B, None))

    # Reversed connection list should be isomorphic
    G1 = generate_circulant_graph(20, [1, 3, 7])
    G2 = generate_circulant_graph(20, [7, 3, 1])
    cases.append(Case("circulant", "Circulant C20[1,3,7] vs C20[7,3,1]", G1, G2, True))

    # Systematic NON-ISO attempts: same n, small varying connection sets
    # Keep bounded to not blow up runtime
    grid = [
        (14, [[1, 3], [1, 5], [1, 6]]),
        (16, [[1, 3], [1, 5], [1, 7]]),
        (18, [[1, 4, 7], [1, 5, 7], [1, 3, 8]]),
        (20, [[1, 4], [1, 6], [1, 8]]),
        (22, [[1, 5], [1, 7], [1, 9]]),
        (24, [[1, 3, 7], [1, 5, 7], [1, 3, 9]]),
    ]
    for n, conn_list in grid:
        base = generate_circulant_graph(n, conn_list[0])
        for conn in conn_list[1:]:
            cand = generate_circulant_graph(n, conn)
            cases.append(Case("circulant", f"Circulant C{n}{conn_list[0]} vs C{n}{conn}", base, cand, None))

    return cases