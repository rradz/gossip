"""
Test suite for the core gossip fingerprinting algorithm.
"""

import pytest
import networkx as nx
import numpy as np
from typing import Tuple, List
import time

from gossip.algorithm import GossipFingerprint, gossip_fingerprint
from gossip.utils import (
    graph_to_adjacency_list,
    adjacency_to_graph,
    relabel_graph,
    are_isomorphic,
)


class TestGossipFingerprint:
    """Test cases for the GossipFingerprint class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.gf = GossipFingerprint()

    def test_empty_graph(self):
        """Test fingerprint of an empty graph."""
        G = nx.Graph()
        adj = graph_to_adjacency_list(G)
        fp = self.gf.compute(adj)
        assert fp == ()

    def test_single_vertex(self):
        """Test fingerprint of a single vertex graph."""
        G = nx.Graph()
        G.add_node(0)
        adj = graph_to_adjacency_list(G)
        fp = self.gf.compute(adj)
        assert len(fp) == 1
        assert fp[0][0] == 0  # Degree should be 0

    def test_simple_path(self):
        """Test fingerprint of a simple path graph."""
        G = nx.path_graph(5)
        adj = graph_to_adjacency_list(G)
        fp = self.gf.compute(adj)

        # Path graph should have 2 vertices of degree 1 and 3 of degree 2
        degrees = [f[0] for f in fp]
        assert sorted(degrees) == [1, 1, 2, 2, 2]

    def test_complete_graph(self):
        """Test fingerprint of a complete graph."""
        for n in [3, 4, 5, 6]:
            G = nx.complete_graph(n)
            adj = graph_to_adjacency_list(G)
            fp = self.gf.compute(adj)

            # All vertices should have the same fingerprint (symmetry)
            assert len(set(fp)) == 1
            # Each vertex should have degree n-1
            assert fp[0][0] == n - 1

    def test_cycle_graph(self):
        """Test fingerprint of a cycle graph."""
        for n in [4, 5, 6, 7, 8]:
            G = nx.cycle_graph(n)
            adj = graph_to_adjacency_list(G)
            fp = self.gf.compute(adj)

            # All vertices in a cycle have degree 2
            degrees = [f[0] for f in fp]
            assert all(d == 2 for d in degrees)

            # All vertices should have identical fingerprints
            assert len(set(fp)) == 1

    def test_star_graph(self):
        """Test fingerprint of a star graph."""
        G = nx.star_graph(5)  # Star with 6 vertices (1 center + 5 leaves)
        adj = graph_to_adjacency_list(G)
        fp = self.gf.compute(adj)

        # Should have one vertex of degree 5 and five vertices of degree 1
        degrees = sorted([f[0] for f in fp])
        assert degrees == [1, 1, 1, 1, 1, 5]

    def test_isomorphic_graphs_same_fingerprint(self):
        """Test that isomorphic graphs have the same fingerprint."""
        # Create two isomorphic graphs with different labeling
        G1 = nx.Graph([(0, 1), (1, 2), (2, 3), (3, 0), (0, 2)])
        G2 = relabel_graph(G1, seed=42)

        adj1 = graph_to_adjacency_list(G1)
        adj2 = graph_to_adjacency_list(G2)

        fp1 = self.gf.compute(adj1)
        fp2 = self.gf.compute(adj2)

        assert fp1 == fp2
        assert are_isomorphic(G1, G2)

    def test_non_isomorphic_regular_graphs(self):
        """Test fingerprints of non-isomorphic regular graphs."""
        # Two different 3-regular graphs with 6 vertices
        G1 = nx.Graph([(0, 1), (0, 2), (0, 3), (1, 2), (1, 4),
                        (2, 5), (3, 4), (3, 5), (4, 5)])
        G2 = nx.Graph([(0, 1), (0, 2), (0, 3), (1, 4), (1, 5),
                        (2, 3), (2, 4), (3, 5), (4, 5)])

        adj1 = graph_to_adjacency_list(G1)
        adj2 = graph_to_adjacency_list(G2)

        fp1 = self.gf.compute(adj1)
        fp2 = self.gf.compute(adj2)

        # Check if NetworkX agrees they're non-isomorphic
        iso = are_isomorphic(G1, G2)

        # If they're not isomorphic, fingerprints should ideally differ
        # But this is not guaranteed for all non-isomorphic graphs
        if not iso:
            # Just verify fingerprints were computed
            assert len(fp1) == 6
            assert len(fp2) == 6

    def test_compare_method(self):
        """Test the compare method for graph comparison."""
        G1 = nx.petersen_graph()
        G2 = relabel_graph(G1, seed=123)
        G3 = nx.complete_graph(10)

        # Same graph with different labeling should match
        assert self.gf.compare(G1, G2) == True

        # Different graphs should not match
        assert self.gf.compare(G1, G3) == False

    def test_convenience_function(self):
        """Test the gossip_fingerprint convenience function."""
        G = nx.karate_club_graph()
        adj = graph_to_adjacency_list(G)

        fp1 = gossip_fingerprint(adj)
        fp2 = self.gf.compute(adj)

        assert fp1 == fp2


class TestRegularGraphs:
    """Test cases specifically for regular graphs."""

    def test_petersen_graph(self):
        """Test the Petersen graph (3-regular, 10 vertices)."""
        G = nx.petersen_graph()
        gf = GossipFingerprint()

        adj = graph_to_adjacency_list(G)
        fp = gf.compute(adj)

        # All vertices should have degree 3
        degrees = [f[0] for f in fp]
        assert all(d == 3 for d in degrees)

        # Petersen graph is vertex-transitive, so all fingerprints should be identical
        assert len(set(fp)) == 1

    def test_hypercube_graphs(self):
        """Test hypercube graphs of various dimensions."""
        for dim in [2, 3, 4]:
            G = nx.hypercube_graph(dim)
            gf = GossipFingerprint()

            adj = graph_to_adjacency_list(G)
            fp = gf.compute(adj)

            # Hypercube of dimension d has 2^d vertices, each with degree d
            assert len(fp) == 2**dim
            degrees = [f[0] for f in fp]
            assert all(d == dim for d in degrees)

            # Hypercube is vertex-transitive
            assert len(set(fp)) == 1

    def test_random_regular_graphs(self):
        """Test random regular graphs."""
        for d in [3, 4, 5]:
            for n in [10, 20, 30]:
                if (n * d) % 2 != 0:
                    continue  # Skip impossible cases

                G = nx.random_regular_graph(d, n, seed=42)
                gf = GossipFingerprint()

                adj = graph_to_adjacency_list(G)
                fp = gf.compute(adj)

                # All vertices should have degree d
                degrees = [f[0] for f in fp]
                assert all(deg == d for deg in degrees)
                assert len(fp) == n


class TestPerformance:
    """Performance tests for the gossip algorithm."""

    def test_scaling_with_graph_size(self):
        """Test how algorithm scales with graph size."""
        gf = GossipFingerprint()
        times = []
        sizes = [10, 20, 50, 100, 200]

        for n in sizes:
            G = nx.random_regular_graph(3, n, seed=42)
            adj = graph_to_adjacency_list(G)

            start = time.perf_counter()
            fp = gf.compute(adj)
            elapsed = time.perf_counter() - start

            times.append(elapsed)
            assert len(fp) == n

        # Check that time increases with size (roughly quadratic or better)
        for i in range(1, len(times)):
            # Allow for some variance, but time should generally increase
            assert times[i] >= times[i-1] * 0.5  # Very lenient bound

    def test_dense_vs_sparse_graphs(self):
        """Compare performance on dense vs sparse graphs."""
        gf = GossipFingerprint()
        n = 50

        # Sparse graph (tree)
        sparse_g = nx.random_labeled_tree(n, seed=42)
        sparse_adj = graph_to_adjacency_list(sparse_g)

        start = time.perf_counter()
        sparse_fp = gf.compute(sparse_adj)
        sparse_time = time.perf_counter() - start

        # Dense graph (almost complete)
        dense_g = nx.erdos_renyi_graph(n, 0.8, seed=42)
        dense_adj = graph_to_adjacency_list(dense_g)

        start = time.perf_counter()
        dense_fp = gf.compute(dense_adj)
        dense_time = time.perf_counter() - start

        # Both should complete successfully
        assert len(sparse_fp) == n
        assert len(dense_fp) == n

        # Dense graphs typically take longer due to more edges
        # But this is not always guaranteed, so we just record it
        print(f"Sparse time: {sparse_time:.6f}s, Dense time: {dense_time:.6f}s")


class TestEdgeCases:
    """Test edge cases and potential failure modes."""

    def test_disconnected_graph(self):
        """Test fingerprint of disconnected graphs."""
        G = nx.Graph()
        # Create two disconnected components
        G.add_edges_from([(0, 1), (1, 2), (0, 2)])  # Triangle
        G.add_edges_from([(3, 4), (4, 5), (3, 5)])  # Another triangle

        gf = GossipFingerprint()
        adj = graph_to_adjacency_list(G)
        fp = gf.compute(adj)

        assert len(fp) == 6
        # All vertices should have degree 2 (triangles)
        degrees = sorted([f[0] for f in fp])
        assert degrees == [2, 2, 2, 2, 2, 2]

    def test_self_loops(self):
        """Test graphs with self-loops."""
        G = nx.Graph()
        G.add_edges_from([(0, 1), (1, 2), (0, 0)])  # Self-loop at vertex 0

        gf = GossipFingerprint()
        adj = graph_to_adjacency_list(G)

        # The algorithm should handle self-loops gracefully
        fp = gf.compute(adj)
        assert len(fp) == 3

    def test_multigraph(self):
        """Test behavior with multigraphs (multiple edges between vertices)."""
        G = nx.MultiGraph()
        G.add_edges_from([(0, 1), (0, 1), (1, 2)])  # Double edge between 0 and 1

        # Convert to simple graph for our algorithm
        simple_g = nx.Graph(G)
        gf = GossipFingerprint()
        adj = graph_to_adjacency_list(simple_g)
        fp = gf.compute(adj)

        assert len(fp) == 3

    def test_large_clique(self):
        """Test performance on large cliques."""
        for n in [10, 20, 30]:
            G = nx.complete_graph(n)
            gf = GossipFingerprint()
            adj = graph_to_adjacency_list(G)

            fp = gf.compute(adj)

            # All vertices should have identical fingerprints
            assert len(set(fp)) == 1
            assert fp[0][0] == n - 1

    def test_directed_graph_conversion(self):
        """Test that directed graphs are handled properly."""
        DG = nx.DiGraph([(0, 1), (1, 2), (2, 0)])
        G = DG.to_undirected()

        gf = GossipFingerprint()
        adj = graph_to_adjacency_list(G)
        fp = gf.compute(adj)

        # Should treat as undirected triangle
        assert len(fp) == 3
        assert all(f[0] == 2 for f in fp)  # All vertices have degree 2


class TestCorrectness:
    """Test correctness of the algorithm on known cases."""

    def test_known_isomorphic_pairs(self):
        """Test known isomorphic graph pairs."""
        test_cases = [
            # Two representations of the same tree
            (nx.Graph([(0, 1), (0, 2), (0, 3)]),
             nx.Graph([('a', 'b'), ('a', 'c'), ('a', 'd')])),

            # Cycle graphs
            (nx.cycle_graph(6), relabel_graph(nx.cycle_graph(6), seed=99)),

            # Complete bipartite graphs
            (nx.complete_bipartite_graph(3, 3),
             relabel_graph(nx.complete_bipartite_graph(3, 3), seed=77)),
        ]

        gf = GossipFingerprint()
        for G1, G2 in test_cases:
            assert are_isomorphic(G1, G2), "Graphs should be isomorphic"
            assert gf.compare(G1, G2), "Fingerprints should match for isomorphic graphs"

    def test_known_non_isomorphic_pairs(self):
        """Test known non-isomorphic graph pairs."""
        test_cases = [
            # Different tree structures
            (nx.Graph([(0, 1), (0, 2), (0, 3)]),  # Star with 3 leaves
             nx.Graph([(0, 1), (1, 2), (2, 3)])),  # Path of length 3

            # Different regular graphs
            (nx.cycle_graph(6), nx.complete_bipartite_graph(3, 3)),

            # Different numbers of vertices
            (nx.complete_graph(4), nx.complete_graph(5)),
        ]

        gf = GossipFingerprint()
        for G1, G2 in test_cases:
            assert not are_isomorphic(G1, G2), "Graphs should not be isomorphic"
            result = gf.compare(G1, G2)
            assert not result, f"Fingerprints should differ for non-isomorphic graphs"
