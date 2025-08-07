"""
Gossip Graph Isomorphism Algorithm

A fast graph isomorphism testing algorithm based on gossip fingerprinting.
"""

from .algorithm import GossipFingerprint, gossip_fingerprint
from .utils import graph_to_adjacency_list

__version__ = "0.1.0"
__all__ = [
    "GossipFingerprint",
    "gossip_fingerprint",
    "graph_to_adjacency_list",
]
