"""
Pytest configuration and fixtures for the gossip test suite.
"""

import pytest
import networkx as nx
import numpy as np
import random
import time
from pathlib import Path
from typing import Generator, Tuple, List, Dict, Any

from gossip.algorithm import GossipFingerprint
from gossip.utils import (
    graph_to_adjacency_list,
    generate_random_regular_graph,
    generate_cfi_pair,
    generate_strongly_regular_graph,
    generate_circulant_graph,
    generate_miyazaki_graph,
    relabel_graph,
)


# Set random seeds for reproducibility
@pytest.fixture(autouse=True)
def set_random_seeds():
    """Set random seeds before each test for reproducibility."""
    random.seed(42)
    np.random.seed(42)
    yield
    # Reset seeds after test
    random.seed()
    np.random.seed()


@pytest.fixture
def gossip_fingerprint():
    """Provide a GossipFingerprint instance."""
    return GossipFingerprint()


@pytest.fixture
def small_test_graphs() -> Dict[str, nx.Graph]:
    """Provide a collection of small test graphs."""
    return {
        "empty": nx.empty_graph(5),
        "path": nx.path_graph(5),
        "cycle": nx.cycle_graph(6),
        "complete": nx.complete_graph(5),
        "star": nx.star_graph(4),
        "petersen": nx.petersen_graph(),
        "bipartite": nx.complete_bipartite_graph(3, 3),
        "tree": nx.balanced_tree(2, 3),
        "grid": nx.grid_2d_graph(3, 3),
        "hypercube": nx.hypercube_graph(3),
    }


@pytest.fixture
def regular_graph_pairs() -> List[Tuple[nx.Graph, nx.Graph]]:
    """Provide pairs of regular graphs for testing."""
    pairs = []

    # Isomorphic pairs (same graph, different labeling)
    G = nx.random_regular_graph(3, 10, seed=42)
    pairs.append((G, relabel_graph(G, seed=99)))

    # Non-isomorphic regular graphs
    G1 = nx.random_regular_graph(3, 10, seed=42)
    G2 = nx.random_regular_graph(3, 10, seed=43)
    pairs.append((G1, G2))

    # Petersen graph and its complement
    pairs.append((nx.petersen_graph(), nx.complement(nx.petersen_graph())))

    return pairs


@pytest.fixture
def hard_instance_pairs() -> List[Tuple[nx.Graph, nx.Graph, bool]]:
    """
    Provide pairs of hard instance graphs with expected isomorphism result.

    Returns:
        List of (G1, G2, expected_isomorphic) tuples
    """
    pairs = []

    # CFI graphs (non-isomorphic)
    base = nx.cycle_graph(6)
    G1, G2 = generate_cfi_pair(base)
    pairs.append((G1, G2, False))

    # SRG and its relabeling (isomorphic)
    srg = generate_strongly_regular_graph(16, 6, 2, 2)
    if srg:
        pairs.append((srg, relabel_graph(srg, seed=42), True))

    # Miyazaki graph and its relabeling (isomorphic)
    miyazaki = generate_miyazaki_graph(8)
    pairs.append((miyazaki, relabel_graph(miyazaki, seed=99), True))

    return pairs


@pytest.fixture
def graph_families() -> Dict[str, List[nx.Graph]]:
    """Provide families of graphs for systematic testing."""
    families = {
        "complete": [nx.complete_graph(n) for n in range(3, 8)],
        "cycle": [nx.cycle_graph(n) for n in range(4, 10)],
        "path": [nx.path_graph(n) for n in range(3, 8)],
        "star": [nx.star_graph(n) for n in range(2, 7)],
        "regular": [nx.random_regular_graph(3, n, seed=42)
                    for n in [6, 8, 10, 12] if (n * 3) % 2 == 0],
        "tree": [nx.random_labeled_tree(n, seed=42) for n in range(5, 15, 2)],
        "bipartite": [nx.complete_bipartite_graph(m, n)
                      for m, n in [(2, 3), (3, 3), (3, 4), (4, 4)]],
    }
    return families


@pytest.fixture
def performance_timer():
    """Provide a simple performance timer context manager."""
    class Timer:
        def __init__(self):
            self.times = []
            self.start_time = None

        def __enter__(self):
            self.start_time = time.perf_counter()
            return self

        def __exit__(self, *args):
            elapsed = time.perf_counter() - self.start_time
            self.times.append(elapsed)

        @property
        def last_time(self):
            return self.times[-1] if self.times else None

        @property
        def average_time(self):
            return np.mean(self.times) if self.times else None

        @property
        def total_time(self):
            return sum(self.times)

    return Timer()


@pytest.fixture
def test_output_dir(tmp_path) -> Path:
    """Provide a temporary directory for test outputs."""
    output_dir = tmp_path / "test_outputs"
    output_dir.mkdir(exist_ok=True)
    return output_dir


@pytest.fixture
def adjacency_lists() -> Dict[str, Dict[Any, List[Any]]]:
    """Provide pre-computed adjacency lists for common graphs."""
    graphs = {
        "triangle": nx.cycle_graph(3),
        "square": nx.cycle_graph(4),
        "k5": nx.complete_graph(5),
        "petersen": nx.petersen_graph(),
    }

    return {
        name: graph_to_adjacency_list(graph)
        for name, graph in graphs.items()
    }


@pytest.fixture(params=[10, 20, 50, 100])
def graph_size(request) -> int:
    """Parametrized fixture providing different graph sizes."""
    return request.param


@pytest.fixture(params=[0.1, 0.3, 0.5, 0.7, 0.9])
def edge_probability(request) -> float:
    """Parametrized fixture providing different edge probabilities."""
    return request.param


@pytest.fixture(params=[3, 4, 5])
def regularity_degree(request) -> int:
    """Parametrized fixture providing different regularity degrees."""
    return request.param


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
    config.addinivalue_line(
        "markers", "benchmark: marks tests as performance benchmarks"
    )
    config.addinivalue_line(
        "markers", "hard_instances: marks tests for hard graph instances"
    )


def pytest_collection_modifyitems(config, items):
    """Automatically mark test items based on their names."""
    for item in items:
        # Mark performance tests
        if "performance" in item.nodeid.lower() or "benchmark" in item.nodeid.lower():
            item.add_marker(pytest.mark.benchmark)

        # Mark hard instance tests
        if "hard" in item.nodeid.lower() or "cfi" in item.nodeid.lower():
            item.add_marker(pytest.mark.hard_instances)

        # Mark integration tests
        if "integration" in item.nodeid.lower():
            item.add_marker(pytest.mark.integration)

        # Mark unit tests (if not already marked as something else)
        if not any(m.name in ["slow", "integration", "benchmark"] for m in item.iter_markers()):
            item.add_marker(pytest.mark.unit)


# Hypothesis strategies for property-based testing
try:
    from hypothesis import strategies as st

    @st.composite
    def graph_strategy(draw, min_nodes=2, max_nodes=10, edge_prob=0.5):
        """Strategy for generating random graphs."""
        n = draw(st.integers(min_value=min_nodes, max_value=max_nodes))
        p = draw(st.floats(min_value=0.0, max_value=1.0))
        seed = draw(st.integers(min_value=0, max_value=2**32 - 1))
        return nx.erdos_renyi_graph(n, p, seed=seed)

    @st.composite
    def regular_graph_strategy(draw, min_nodes=4, max_nodes=20):
        """Strategy for generating regular graphs."""
        n = draw(st.integers(min_value=min_nodes, max_value=max_nodes))
        # Ensure even n*d
        max_d = n - 1
        d = draw(st.integers(min_value=1, max_value=max_d))
        if (n * d) % 2 != 0:
            d = d - 1 if d > 1 else d + 1
        if d >= n or d < 1:
            return nx.cycle_graph(n)  # Fallback to 2-regular
        seed = draw(st.integers(min_value=0, max_value=2**32 - 1))
        return nx.random_regular_graph(d, n, seed=seed)

except ImportError:
    # Hypothesis not installed, skip these strategies
    pass
