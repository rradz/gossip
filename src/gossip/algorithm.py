"""
Core gossip fingerprinting algorithm for graph isomorphism testing.
"""

from typing import Dict, List, Set, Tuple, Any, Optional
from collections import defaultdict
import networkx as nx


class GossipFingerprint:
    """
    Gossip fingerprinting algorithm for graph isomorphism testing.

    This algorithm propagates information through the graph like gossip,
    creating a unique fingerprint for each graph structure.
    """

    def __init__(self, normalize: bool = True):
        """
        Initialize the gossip fingerprint algorithm.

        Args:
            normalize: Whether to normalize fingerprints for comparison
        """
        self.normalize = normalize

    def compute(self, adjacency: Dict[Any, List[Any]]) -> Tuple[Tuple, ...]:
        """
        Compute the gossip fingerprint for a graph.

        Args:
            adjacency: Adjacency list representation of the graph

        Returns:
            Sorted tuple of vertex fingerprints
        """
        fingerprints = {}

        for start_vertex in adjacency:
            fingerprint = self._compute_vertex_fingerprint(adjacency, start_vertex)
            fingerprints[start_vertex] = fingerprint

        return tuple(sorted(fingerprints.values()))

    def _compute_vertex_fingerprint(
        self,
        adjacency: Dict[Any, List[Any]],
        start_vertex: Any
    ):
        """
        Compute fingerprint for a single starting vertex.

        Args:
            adjacency: Graph adjacency list
            start_vertex: Vertex to start gossip from

        Returns:
            Tuple of (degree, sorted timeline of gossip events)
        """
        knowers = {start_vertex}
        new_knowers = {start_vertex}
        seen_edges = set()
        timeline = []
        iteration = 0

        while new_knowers:
            next_new_knowers = set()

            # Collect transmissions and hit counts in a single pass
            transmissions = []
            hit_rate = {}
            for current_knower in knowers:
                for neighbor in adjacency[current_knower]:
                    edge = tuple(sorted((current_knower, neighbor)))
                    if edge in seen_edges:
                        continue
                    seen_edges.add(edge)
                    transmissions.append((current_knower, neighbor))
                    hit_rate[current_knower] = hit_rate.get(current_knower, 0)
                    if neighbor in knowers:
                        hit_rate[current_knower] += 1
                    hit_rate[neighbor] = hit_rate.get(neighbor, 0) + 1

            # Emit events using hit rates (no degrees)
            for current_knower, neighbor in transmissions:
                current_knows = current_knower in knowers
                neighbor_knows = neighbor in knowers

                if current_knows and not neighbor_knows:
                    timeline.append((iteration, 1, hit_rate[current_knower], hit_rate[neighbor]))
                    next_new_knowers.add(neighbor)
                elif neighbor_knows and not current_knows:
                    timeline.append((iteration, 1, hit_rate[neighbor], hit_rate[current_knower]))
                    next_new_knowers.add(current_knower)
                else:
                    a = hit_rate[current_knower]
                    b = hit_rate[neighbor]
                    if a <= b:
                        timeline.append((iteration, 0, a, b))
                    else:
                        timeline.append((iteration, 0, b, a))

            knowers = new_knowers | next_new_knowers
            new_knowers = next_new_knowers
            iteration += 1

        return tuple(sorted(timeline))

    def compare(self, G1: nx.Graph, G2: nx.Graph) -> bool:
        """
        Compare two NetworkX graphs using gossip fingerprints.

        Args:
            G1: First graph
            G2: Second graph

        Returns:
            True if graphs have identical fingerprints
        """
        adj1 = {v: list(G1.neighbors(v)) for v in G1.nodes()}
        adj2 = {v: list(G2.neighbors(v)) for v in G2.nodes()}

        fp1 = self.compute(adj1)
        fp2 = self.compute(adj2)

        return fp1 == fp2


def gossip_fingerprint(
    adjacency: Dict[Any, List[Any]],
    normalize: bool = True
) -> Tuple[Tuple, ...]:
    """
    Compute gossip fingerprint for a graph.

    This is a convenience function that creates a GossipFingerprint instance
    and computes the fingerprint.

    Args:
        adjacency: Adjacency list representation of the graph
        normalize: Whether to normalize the fingerprint

    Returns:
        Sorted tuple of vertex fingerprints
    """
    algorithm = GossipFingerprint(normalize=normalize)
    return algorithm.compute(adjacency)
