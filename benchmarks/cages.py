from __future__ import annotations

from typing import List
import networkx as nx

from gossip.utils import relabel_graph
from .common import Case


def build_cases() -> List[Case]:
    cases: List[Case] = []

    # Small cages / regular graphs with specified girth
    # Petersen (3-regular, girth 5) is already elsewhere; include Heawood (3,6)-cage
    if hasattr(nx, "heawood_graph"):
        H = nx.heawood_graph()
        cases.append(Case("cages", "Heawood — relabel", H, relabel_graph(H, seed=14), True))
        # Heawood vs Pappus (both cubic, non-ISO)
        if hasattr(nx, "pappus_graph"):
            Papp = nx.pappus_graph()
            cases.append(Case("cages", "Heawood vs Pappus", H, Papp, False))

    # (3,5)-Moore graph does not exist beyond Petersen; (3,7)-McGee graph (if available)
    if hasattr(nx, "mcgee_graph"):
        M = nx.mcgee_graph()
        cases.append(Case("cages", "McGee — relabel", M, relabel_graph(M, seed=24), True))

    # Cubic cages via generalized Petersen: GP(10,2) is the dodecahedral graph
    if hasattr(nx, "generalized_petersen_graph"):
        D = nx.generalized_petersen_graph(10, 2)  # dodecahedral
        cases.append(Case("cages", "Dodecahedral — relabel", D, relabel_graph(D, seed=102), True))

    return cases


