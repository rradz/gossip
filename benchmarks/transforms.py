from __future__ import annotations

from typing import List
import networkx as nx

from gossip.utils import relabel_graph
from .common import Case


def build_cases() -> List[Case]:
    cases: List[Case] = []

    # Line-graph identities and exceptions (Whitney's theorem exception)
    L = nx.line_graph
    K3 = nx.complete_graph(3)
    K1_3 = nx.star_graph(3)  # K_{1,3}
    cases.append(Case("transforms", "Line L(K3) vs L(K1,3)", L(K3), L(K1_3), True))
    # Non-invertibility: non-isomorphic graphs with isomorphic line graphs beyond Whitney pair are rare; add a sanity non-ISO pair
    cases.append(Case("transforms", "Line L(P4) vs L(C4)", L(nx.path_graph(4)), L(nx.cycle_graph(4)), False))

    P6 = nx.path_graph(6)
    cases.append(Case("transforms", "Line L(P6) — relabel", L(P6), relabel_graph(L(P6), seed=6), True))
    C8 = nx.cycle_graph(8)
    cases.append(Case("transforms", "Line L(C8) — relabel", L(C8), relabel_graph(L(C8), seed=8), True))
    cases.append(Case("transforms", "Line L(P5) vs L(P6)", L(nx.path_graph(5)), L(P6), False))

    # Complement transforms
    comp = nx.complement
    # Self-complementary: C5 is not self-complementary; use Paley(5) which is C5
    C5 = nx.cycle_graph(5)
    cases.append(Case("transforms", "C5 vs complement(C5)", C5, comp(C5), False))
    # Add a known self-complementary graph: 4-vertex path P4 is self-complementary
    P4 = nx.path_graph(4)
    cases.append(Case("transforms", "Self-complementary P4 vs complement(P4)", P4, comp(P4), True))
    # Add an explicit self-complementary example (n ≡ 0 or 1 mod 4), e.g., Paley(5) = C5 is not; use known 4-vertex: cycle C4 is self-complementary? (No.)
    # Keep complement relabel checks instead
    C4 = nx.cycle_graph(4)
    cases.append(Case("transforms", "C4 vs complement(C4)", C4, comp(C4), False))
    P = nx.petersen_graph()
    cases.append(Case("transforms", "Complement(Petersen) — relabel", comp(P), relabel_graph(comp(P), seed=10), True))

    return cases


