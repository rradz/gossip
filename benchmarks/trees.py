from __future__ import annotations

from typing import List, Tuple, Dict
import random
import math

import networkx as nx
import numpy as np

from gossip.utils import relabel_graph
from .common import Case


def adjacency_spectrum_signature(G: nx.Graph) -> Tuple[float, ...]:
    A = nx.to_numpy_array(G, dtype=float)
    vals = np.linalg.eigvals(A)
    # Sort and round to reduce floating noise
    sig = tuple(sorted(float(round(x.real, 8)) for x in vals))
    return sig


def find_cospectral_tree_pairs(n: int, max_pairs: int, max_trials: int = 5000, seed: int = 42) -> List[Tuple[nx.Graph, nx.Graph]]:
    rng = random.Random(seed + n)
    seen_by_sig: Dict[Tuple[float, ...], List[nx.Graph]] = {}
    pairs: List[Tuple[nx.Graph, nx.Graph]] = []

    for _ in range(max_trials):
        # Random labeled tree on n nodes
        G = nx.random_labeled_tree(n, seed=rng.randrange(1, 1 << 30))
        sig = adjacency_spectrum_signature(G)
        bucket = seen_by_sig.setdefault(sig, [])
        # Try to match against existing in bucket
        for H in bucket:
            if not nx.is_isomorphic(G, H):
                pairs.append((G, H))
                if len(pairs) >= max_pairs:
                    return pairs
        bucket.append(G)
    return pairs


def build_cases() -> List[Case]:
    cases: List[Case] = []

    # Relabel invariance for trees
    for n in [8, 10, 12, 14, 16, 20]:
        G = nx.random_labeled_tree(n, seed=10 + n)
        cases.append(Case("trees", f"Random Tree (n={n}) — relabel", G, relabel_graph(G, seed=99 + n), True))

    # Non-ISO random tree pairs with same n
    for n in [12, 14, 16, 18, 20]:
        G1 = nx.random_labeled_tree(n, seed=100 + n)
        G2 = nx.random_labeled_tree(n, seed=200 + n)
        cases.append(Case("trees", f"Random Trees (n={n}) — different seeds", G1, G2, False))

    # Cospectral non-isomorphic tree pairs (small n, bounded search)
    targets = [(8, 3), (10, 3), (12, 3)]  # (n, max_pairs)
    for n, k in targets:
        pairs = find_cospectral_tree_pairs(n, max_pairs=k, max_trials=4000)
        for idx, (G, H) in enumerate(pairs, 1):
            cases.append(Case("trees", f"Cospectral Trees (n={n}) #{idx}", G, H, False))

    return cases