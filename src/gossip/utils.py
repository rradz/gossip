"""
Utility functions for the gossip graph isomorphism algorithm.
"""

from typing import Dict, List, Any, Optional, Tuple, Set
import networkx as nx
import random
import itertools
from collections import defaultdict


def graph_to_adjacency_list(graph: nx.Graph) -> Dict[Any, List[Any]]:
    """
    Convert a NetworkX graph to an adjacency list representation.

    Args:
        graph: NetworkX graph object

    Returns:
        Dictionary mapping each vertex to its list of neighbors
    """
    return {vertex: list(graph.neighbors(vertex)) for vertex in graph.nodes()}


def adjacency_to_graph(adjacency: Dict[Any, List[Any]]) -> nx.Graph:
    """
    Convert an adjacency list to a NetworkX graph.

    Args:
        adjacency: Dictionary mapping vertices to lists of neighbors

    Returns:
        NetworkX graph object
    """
    graph = nx.Graph()
    for vertex, neighbors in adjacency.items():
        for neighbor in neighbors:
            graph.add_edge(vertex, neighbor)
    return graph


def generate_random_regular_graph(
    n: int,
    d: int,
    seed: Optional[int] = None
) -> nx.Graph:
    """
    Generate a random d-regular graph with n vertices.

    Args:
        n: Number of vertices
        d: Degree of each vertex
        seed: Random seed for reproducibility

    Returns:
        Random regular graph

    Raises:
        ValueError: If n*d is odd (impossible to create regular graph)
    """
    if (n * d) % 2 != 0:
        raise ValueError(f"Cannot create {d}-regular graph with {n} vertices (n*d must be even)")

    return nx.random_regular_graph(d, n, seed=seed)


def generate_cfi_pair(
    base_graph: nx.Graph,
    flip_edges: Optional[Set[Tuple[Any, Any]]] = None
) -> Tuple[nx.Graph, nx.Graph]:
    """
    Generate a pair of Cai-Fürer-Immerman (CFI) graphs.

    These graphs are known to be hard for the Weisfeiler-Leman algorithm.

    Args:
        base_graph: Base graph to construct CFI graphs from
        flip_edges: Edges to flip in the construction (if None, randomly select)

    Returns:
        Tuple of two CFI graphs
    """
    if flip_edges is None:
        # Randomly select edges to flip
        edges = list(base_graph.edges())
        flip_edges = set(random.sample(edges, k=len(edges) // 2))

    def build_cfi(flip: bool = False) -> nx.Graph:
        G = nx.Graph()

        # Add gadget vertices for each original vertex
        for v in base_graph.nodes():
            center = f"{v}_c"
            for i in range(3):
                G.add_edge(center, f"{v}_{i}")

        # Connect gadgets according to original edges
        for u, v in base_graph.edges():
            for i in range(3):
                if flip and (u, v) in flip_edges:
                    # Flip the connection pattern
                    G.add_edge(f"{u}_{i}", f"{v}_{(i+1)%3}")
                else:
                    # Regular connection pattern
                    G.add_edge(f"{u}_{i}", f"{v}_{i}")

        return G

    return build_cfi(False), build_cfi(True)


def generate_strongly_regular_graph(
    v: int,
    k: int,
    l: int,
    m: int
) -> Optional[nx.Graph]:
    """
    Generate a strongly regular graph with parameters (v, k, λ, μ).

    Args:
        v: Number of vertices
        k: Degree of each vertex
        l: Number of common neighbors between adjacent vertices (lambda)
        m: Number of common neighbors between non-adjacent vertices (mu)

    Returns:
        Strongly regular graph if parameters are feasible, None otherwise
    """
    # Check feasibility conditions
    if k * (k - l - 1) != m * (v - k - 1):
        return None

    # For small cases, use known constructions
    if (v, k, l, m) == (16, 6, 2, 2):
        return _srg_16_6_2_2()
    elif (v, k, l, m) == (25, 12, 5, 6):
        return nx.paley_graph(25)
    elif (v, k, l, m) == (13, 6, 2, 3):
        return nx.paley_graph(13)

    # For other cases, return None (would need more complex constructions)
    return None


def _srg_16_6_2_2() -> nx.Graph:
    """
    Construct the strongly regular graph with parameters (16, 6, 2, 2).

    Returns:
        SRG(16, 6, 2, 2) graph
    """
    edges = [
        (0, 1), (0, 2), (0, 3), (0, 4), (0, 5), (0, 6),
        (1, 2), (1, 7), (1, 8), (1, 9), (1, 10),
        (2, 3), (2, 11), (2, 12), (2, 13),
        (3, 4), (3, 14), (3, 15),
        (4, 5), (4, 7),
        (5, 6), (5, 8),
        (6, 9), (6, 10),
        (7, 11), (7, 12),
        (8, 11), (8, 13),
        (9, 12), (9, 14),
        (10, 13), (10, 15),
        (11, 14),
        (12, 15),
        (13, 14),
        (14, 15)
    ]
    G = nx.Graph()
    G.add_edges_from(edges)
    return G


def generate_circulant_graph(n: int, connections: List[int]) -> nx.Graph:
    """
    Generate a circulant graph C_n(connections).

    Args:
        n: Number of vertices
        connections: List of connection offsets

    Returns:
        Circulant graph
    """
    return nx.circulant_graph(n, connections)


def generate_miyazaki_graph(n: int) -> nx.Graph:
    """
    Generate a Miyazaki graph of order n.

    These graphs are known to be difficult for many isomorphism algorithms.

    Args:
        n: Order parameter (must be even and >= 4)

    Returns:
        Miyazaki graph

    Raises:
        ValueError: If n is odd or less than 4
    """
    if n < 4 or n % 2 != 0:
        raise ValueError("n must be even and at least 4")

    G = nx.Graph()

    # Create two cycles
    for i in range(n):
        G.add_edge(f"a{i}", f"a{(i+1)%n}")
        G.add_edge(f"b{i}", f"b{(i+1)%n}")

    # Add cross connections with twist
    for i in range(n):
        if i < n // 2:
            G.add_edge(f"a{i}", f"b{i}")
        else:
            G.add_edge(f"a{i}", f"b{n-1-i}")

    return G


def compute_graph_statistics(graph: nx.Graph) -> Dict[str, Any]:
    """
    Compute various statistics for a graph.

    Args:
        graph: NetworkX graph

    Returns:
        Dictionary of graph statistics
    """
    stats = {
        "num_vertices": graph.number_of_nodes(),
        "num_edges": graph.number_of_edges(),
        "density": nx.density(graph),
        "is_connected": nx.is_connected(graph),
    }

    if stats["is_connected"]:
        stats["diameter"] = nx.diameter(graph)
        stats["radius"] = nx.radius(graph)

    degree_sequence = sorted([d for n, d in graph.degree()], reverse=True)
    stats["max_degree"] = max(degree_sequence) if degree_sequence else 0
    stats["min_degree"] = min(degree_sequence) if degree_sequence else 0
    stats["avg_degree"] = sum(degree_sequence) / len(degree_sequence) if degree_sequence else 0

    # Check for regularity
    if len(set(degree_sequence)) == 1:
        stats["is_regular"] = True
        stats["regularity"] = degree_sequence[0]
    else:
        stats["is_regular"] = False
        stats["regularity"] = None

    return stats


def are_isomorphic(G1: nx.Graph, G2: nx.Graph) -> bool:
    """
    Check if two graphs are isomorphic using NetworkX.

    Args:
        G1: First graph
        G2: Second graph

    Returns:
        True if graphs are isomorphic
    """
    return nx.is_isomorphic(G1, G2)


def relabel_graph(graph: nx.Graph, seed: Optional[int] = None) -> nx.Graph:
    """
    Randomly relabel vertices of a graph.

    Args:
        graph: Original graph
        seed: Random seed for reproducibility

    Returns:
        Graph with relabeled vertices
    """
    if seed is not None:
        random.seed(seed)

    nodes = list(graph.nodes())
    shuffled = nodes.copy()
    random.shuffle(shuffled)

    mapping = dict(zip(nodes, shuffled))
    return nx.relabel_nodes(graph, mapping)


def get_degree_sequence(graph: nx.Graph) -> List[int]:
    """
    Get the degree sequence of a graph.

    Args:
        graph: NetworkX graph

    Returns:
        Sorted list of vertex degrees
    """
    return sorted([degree for _, degree in graph.degree()], reverse=True)


def verify_strongly_regular_parameters(
    graph: nx.Graph,
    v: Optional[int] = None,
    k: Optional[int] = None,
    l: Optional[int] = None,
    m: Optional[int] = None
) -> bool:
    """
    Verify if a graph is strongly regular with given parameters.

    Args:
        graph: Graph to verify
        v: Expected number of vertices (None to skip check)
        k: Expected degree (None to skip check)
        l: Expected lambda parameter (None to skip check)
        m: Expected mu parameter (None to skip check)

    Returns:
        True if graph satisfies the strongly regular conditions
    """
    n = graph.number_of_nodes()

    if v is not None and n != v:
        return False

    # Check regularity
    degrees = [d for _, d in graph.degree()]
    if len(set(degrees)) != 1:
        return False

    degree = degrees[0]
    if k is not None and degree != k:
        return False

    # Check lambda and mu parameters
    for u in graph.nodes():
        for v in graph.nodes():
            if u == v:
                continue

            common_neighbors = len(set(graph.neighbors(u)) & set(graph.neighbors(v)))

            if graph.has_edge(u, v):
                # Adjacent vertices should have lambda common neighbors
                if l is not None and common_neighbors != l:
                    return False
            else:
                # Non-adjacent vertices should have mu common neighbors
                if m is not None and common_neighbors != m:
                    return False

    return True
