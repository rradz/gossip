from __future__ import annotations

from typing import List
import networkx as nx

from gossip.utils import relabel_graph
from .common import Case


def build_cases() -> List[Case]:
    cases: List[Case] = []

    # Complete, cycles, paths
    for n in [5, 7, 9, 11, 13]:
        G = nx.complete_graph(n)
        cases.append(Case("families", f"Complete K{n} — relabel", G, relabel_graph(G, seed=n), True))
    for n in [8, 12, 16, 20, 24]:
        G = nx.cycle_graph(n)
        cases.append(Case("families", f"Cycle C{n} — relabel", G, relabel_graph(G, seed=n), True))
    for n in [8, 12, 16, 20, 24]:
        G = nx.path_graph(n)
        cases.append(Case("families", f"Path P{n} — relabel", G, relabel_graph(G, seed=n), True))

    # Star, wheel
    for n in [8, 16, 24, 32]:
        G = nx.star_graph(n)
        cases.append(Case("families", f"Star S{n+1} — relabel", G, relabel_graph(G, seed=n), True))
    for n in [8, 12, 16, 20]:
        G = nx.wheel_graph(n)
        cases.append(Case("families", f"Wheel W{n} — relabel", G, relabel_graph(G, seed=n), True))

    # Grid, ladder, circular ladder, prism
    for a, b in [(3, 4), (4, 5), (5, 5), (6, 6)]:
        G = nx.grid_2d_graph(a, b)
        cases.append(Case("families", f"Grid {a}×{b} — relabel", G, relabel_graph(G, seed=a*10+b), True))
    for n in [5, 8, 12, 16]:
        G = nx.ladder_graph(n)
        cases.append(Case("families", f"Ladder L{n} — relabel", G, relabel_graph(G, seed=n), True))
    for n in [6, 10, 14, 18]:
        if hasattr(nx, "circular_ladder_graph"):
            G = nx.circular_ladder_graph(n)
            cases.append(Case("families", f"Circular Ladder CL{n} — relabel", G, relabel_graph(G, seed=n), True))
        # prism graph (Cartesian product C_n × K_2)
        if hasattr(nx, "prism_graph"):
            Gp = nx.prism_graph(n)
        else:
            Gp = nx.cartesian_product(nx.cycle_graph(n), nx.complete_graph(2))
        cases.append(Case("families", f"Prism Π{n} — relabel", Gp, relabel_graph(Gp, seed=n+1), True))

    # Friendship, barbell, lollipop
    for n in [3, 5, 7, 9]:
        if hasattr(nx, "friendship_graph"):
            G = nx.friendship_graph(n)
            cases.append(Case("families", f"Friendship F({n}) — relabel", G, relabel_graph(G, seed=n), True))
    for a, b in [(4, 4), (6, 6), (8, 8)]:
        G = nx.barbell_graph(a, b)
        cases.append(Case("families", f"Barbell B({a},{b}) — relabel", G, relabel_graph(G, seed=a*100+b), True))
    for m, n in [(4, 4), (6, 6), (8, 8)]:
        G = nx.lollipop_graph(m, n)
        cases.append(Case("families", f"Lollipop L({m},{n}) — relabel", G, relabel_graph(G, seed=m*100+n), True))

    # Non-ISO pairs across families with same n when possible
    pairs = [
        ("Cycle C12 vs Path P12", nx.cycle_graph(12), nx.path_graph(12)),
        ("Star S17 vs Path P17", nx.star_graph(16), nx.path_graph(17)),
        ("Wheel W12 vs Cycle C12", nx.wheel_graph(12), nx.cycle_graph(12)),
        ("Grid 4×4 vs Ladder L8", nx.grid_2d_graph(4, 4), nx.ladder_graph(8)),
    ]
    for name, G1, G2 in pairs:
        cases.append(Case("families", name, G1, G2, False))

    return cases