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
            Sorted timeline of gossip events for the start vertex
        """
        # Spreaders are vertices that currently possess the gossip and may spread it
        spreaders = {start_vertex}
        new_spreaders = {start_vertex}
        seen_edges = set()
        timeline = []
        iteration = 0

        # Global gossip-heard counts from the start (no per-round reset)
        gossip_heard_count = {v: 0 for v in adjacency}

        while new_spreaders:
            # Receivers are vertices that newly receive the gossip in this iteration
            receivers = set()

            # Collect gossip transmissions and update global hear counts in a single pass
            gossips = []
            for current_spreader in new_spreaders:
                for neighbor in adjacency[current_spreader]:
                    edge = tuple(sorted((current_spreader, neighbor)))
                    if edge in seen_edges:
                        continue
                    seen_edges.add(edge)
                    gossips.append((current_spreader, neighbor))
                    # Receiver hears once; spreader only bumps if contacting someone who already heard
                    if neighbor in spreaders:
                        gossip_heard_count[current_spreader] += 1
                    gossip_heard_count[neighbor] += 1

            # Emit events using hear counts (no degrees)
            for u, v in gossips:
                u_is_spreader = u in spreaders
                v_is_spreader = v in spreaders

                if u_is_spreader and not v_is_spreader:
                    timeline.append((iteration, 1, gossip_heard_count[u], gossip_heard_count[v]))
                    receivers.add(v)
                elif v_is_spreader and not u_is_spreader:
                    timeline.append((iteration, 1, gossip_heard_count[v], gossip_heard_count[u]))
                    receivers.add(u)
                else:
                    a = gossip_heard_count[u]
                    b = gossip_heard_count[v]
                    if a <= b:
                        timeline.append((iteration, 0, a, b))
                    else:
                        timeline.append((iteration, 0, b, a))

            # spreaders is cumulative set of all vertices that have ever heard the gossip
            spreaders = spreaders | receivers
            # only newly informed vertices spread in the next iteration
            new_spreaders = receivers
            iteration += 1

        return tuple(sorted(timeline))

    def compute_raw_fingerprints(self, G: nx.Graph) -> Dict[Any, Tuple[Tuple, ...]]:
        """
        Compute per-vertex raw fingerprints for all start vertices.

        Returns a mapping from start vertex to its sorted timeline of events.
        """
        adjacency = {v: list(G.neighbors(v)) for v in G.nodes()}
        per_vertex: Dict[Any, Tuple[Tuple, ...]] = {}
        for v in adjacency:
            per_vertex[v] = self._compute_vertex_fingerprint(adjacency, v)
        return per_vertex

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
