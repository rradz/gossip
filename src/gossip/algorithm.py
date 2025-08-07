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
    ) -> Tuple[int, List[Tuple[int, int, int, int]]]:
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

            for current_knower in knowers:
                for neighbor in adjacency[current_knower]:
                    edge = tuple(sorted((current_knower, neighbor)))

                    if edge in seen_edges:
                        continue
                    seen_edges.add(edge)

                    current_knows = current_knower in knowers
                    neighbor_knows = neighbor in knowers
                    current_degree = len(adjacency[current_knower])
                    neighbor_degree = len(adjacency[neighbor])

                    if current_knows and not neighbor_knows:
                        # Current spreads to neighbor
                        timeline.append((iteration, current_degree, 1, neighbor_degree))
                        next_new_knowers.add(neighbor)
                    elif neighbor_knows and not current_knows:
                        # Neighbor spreads to current
                        timeline.append((iteration, neighbor_degree, 1, current_degree))
                        next_new_knowers.add(current_knower)
                    else:
                        # Both know or both don't know
                        if current_degree <= neighbor_degree:
                            spreader, listener = current_knower, neighbor
                        else:
                            spreader, listener = neighbor, current_knower
                        timeline.append((
                            iteration,
                            len(adjacency[spreader]),
                            0,
                            len(adjacency[listener])
                        ))

            knowers |= next_new_knowers
            new_knowers = next_new_knowers
            iteration += 1

        return (len(adjacency[start_vertex]), tuple(sorted(timeline)))

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
