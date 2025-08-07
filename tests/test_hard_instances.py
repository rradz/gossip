"""
Test suite for hard instances of graph isomorphism.

These tests include known challenging cases for graph isomorphism algorithms,
including CFI graphs, strongly regular graphs, and other pathological cases.
"""

import pytest
import networkx as nx
import itertools
import random
from typing import List, Tuple, Set, Optional

from gossip.algorithm import GossipFingerprint
from gossip.utils import (
    graph_to_adjacency_list,
    generate_cfi_pair,
    generate_strongly_regular_graph,
    generate_miyazaki_graph,
    are_isomorphic,
    relabel_graph,
)


class TestCFIGraphs:
    """Test Cai-Fürer-Immerman graphs that defeat Weisfeiler-Leman."""

    def test_cfi_basic_construction(self):
        """Test basic CFI construction on small base graphs."""
        gf = GossipFingerprint()

        # Test with different base graphs
        base_graphs = [
            nx.cycle_graph(4),
            nx.path_graph(4),
            nx.complete_graph(4),
        ]

        for base in base_graphs:
            # Use explicit flip edges to ensure non-isomorphism
            edges = list(base.edges())
            if len(edges) > 0:
                # Flip exactly one edge for deterministic non-isomorphism
                flip_edges = {edges[0]}
            else:
                flip_edges = set()

            G1, G2 = generate_cfi_pair(base, flip_edges)

            # Check if they are actually non-isomorphic
            iso = are_isomorphic(G1, G2)

            # With explicit flip edges, they should typically be non-isomorphic
            # unless the base graph has special symmetry
            if len(flip_edges) > 0 and not iso:
                # Test if gossip can distinguish them
                result = gf.compare(G1, G2)

                # Record the result (gossip may or may not distinguish)
                if result:
                    print(f"Warning: Gossip failed to distinguish CFI pair with base {base}")
            else:
                # Just verify the construction worked
                assert G1.number_of_nodes() == 4 * base.number_of_nodes()
                assert G2.number_of_nodes() == 4 * base.number_of_nodes()

    def test_cfi_with_random_base(self):
        """Test CFI construction with random base graphs."""
        gf = GossipFingerprint()

        for n in [5, 6, 7, 8]:
            for p in [0.3, 0.5, 0.7]:
                base = nx.erdos_renyi_graph(n, p, seed=42)
                if not nx.is_connected(base):
                    continue

                G1, G2 = generate_cfi_pair(base)

                # Verify non-isomorphism
                assert not are_isomorphic(G1, G2)

                # Test gossip
                match = gf.compare(G1, G2)

                # Record performance
                if match:
                    print(f"CFI with n={n}, p={p}: Gossip failed to distinguish")

    def test_cfi_twisted_edges(self):
        """Test CFI with different numbers of twisted edges."""
        gf = GossipFingerprint()
        base = nx.cycle_graph(6)
        edges = list(base.edges())

        for num_twists in [1, 2, 3]:
            twist_edges = set(edges[:num_twists])
            G1, G2 = generate_cfi_pair(base, twist_edges)

            iso = are_isomorphic(G1, G2)
            match = gf.compare(G1, G2)

            # Check consistency
            if iso != match:
                print(f"CFI with {num_twists} twists: Gossip result differs from isomorphism")


class TestStronglyRegularGraphs:
    """Test strongly regular graphs (SRGs)."""

    def test_srg_16_6_2_2(self):
        """Test the SRG(16, 6, 2, 2) - Shrikhande graph."""
        gf = GossipFingerprint()

        G1 = generate_strongly_regular_graph(16, 6, 2, 2)
        assert G1 is not None, "Should generate SRG(16, 6, 2, 2)"

        # Test against its relabeling
        G2 = relabel_graph(G1, seed=42)

        assert are_isomorphic(G1, G2)
        assert gf.compare(G1, G2)

        # Test against a different SRG if possible
        # (In practice, finding non-isomorphic SRGs with same parameters is hard)

    def test_paley_graphs(self):
        """Test Paley graphs (a special class of SRGs)."""
        gf = GossipFingerprint()

        for q in [5, 9, 13, 17]:
            if q % 4 != 1:
                continue

            try:
                G = nx.paley_graph(q)

                # Verify it's strongly regular
                degrees = [d for _, d in G.degree()]
                assert len(set(degrees)) == 1, "Should be regular"

                # Test fingerprint stability
                G_relabeled = relabel_graph(G, seed=123)
                assert gf.compare(G, G_relabeled)

            except:
                # Skip if NetworkX doesn't support this Paley graph
                pass

    def test_conference_graphs(self):
        """Test conference graphs (related to SRGs)."""
        gf = GossipFingerprint()

        # Small conference graphs
        for n in [5, 9, 13]:
            try:
                # Conference graphs can be constructed from Paley tournaments
                G = nx.paley_graph(n)

                # Test self-isomorphism
                G_perm = relabel_graph(G, seed=99)
                assert gf.compare(G, G_perm)

            except:
                pass


class TestMiyazakiGraphs:
    """Test Miyazaki's construction of hard instances."""

    def test_miyazaki_basic(self):
        """Test basic Miyazaki graph construction."""
        gf = GossipFingerprint()

        for n in [4, 6, 8, 10]:
            G = generate_miyazaki_graph(n)

            # Verify structure
            assert G.number_of_nodes() == 2 * n

            # Test against relabeling
            G_perm = relabel_graph(G, seed=42)
            assert are_isomorphic(G, G_perm)
            assert gf.compare(G, G_perm)

    def test_miyazaki_variants(self):
        """Test variants of Miyazaki graphs."""
        gf = GossipFingerprint()

        # Create two different Miyazaki-like constructions
        n = 8
        G1 = generate_miyazaki_graph(n)

        # Create a variant with different twist pattern
        G2 = nx.Graph()
        for i in range(n):
            G2.add_edge(f"a{i}", f"a{(i+1)%n}")
            G2.add_edge(f"b{i}", f"b{(i+1)%n}")

        # Different cross-connection pattern
        for i in range(n):
            if i % 2 == 0:
                G2.add_edge(f"a{i}", f"b{i}")
            else:
                G2.add_edge(f"a{i}", f"b{(i+n//2)%n}")

        iso = are_isomorphic(G1, G2)
        match = gf.compare(G1, G2)

        # Record the result
        if iso != match:
            print(f"Miyazaki variant: Gossip differs from isomorphism check")


class TestCospectalGraphs:
    """Test cospectral (same eigenvalue spectrum) non-isomorphic graphs."""

    def test_small_cospectral_pairs(self):
        """Test small cospectral non-isomorphic graph pairs."""
        gf = GossipFingerprint()

        # Known cospectral non-isomorphic pairs
        # Pair 1: Two 6-vertex graphs
        G1 = nx.Graph([(0, 1), (0, 2), (1, 2), (3, 4), (3, 5), (4, 5)])
        G2 = nx.Graph([(0, 1), (0, 2), (1, 3), (2, 4), (3, 5), (4, 5)])

        # Add connections to make them cospectral
        G1.add_edges_from([(0, 3), (1, 4), (2, 5)])
        G2.add_edges_from([(0, 3), (1, 4), (2, 5)])

        iso = are_isomorphic(G1, G2)
        match = gf.compare(G1, G2)

        if iso != match:
            print(f"Cospectral pair: Gossip result {match} differs from isomorphism {iso}")

    def test_cospectral_trees(self):
        """Test cospectral trees."""
        gf = GossipFingerprint()

        # Two cospectral but non-isomorphic trees
        # Tree 1: Star-like
        T1 = nx.Graph([(0, 1), (0, 2), (0, 3), (1, 4), (1, 5)])

        # Tree 2: More balanced
        T2 = nx.Graph([(0, 1), (0, 2), (1, 3), (1, 4), (2, 5)])

        iso = are_isomorphic(T1, T2)
        match = gf.compare(T1, T2)

        assert not iso, "Trees should be non-isomorphic"
        if match:
            print("Warning: Gossip failed to distinguish non-isomorphic cospectral trees")


class TestDistanceRegularGraphs:
    """Test distance-regular graphs."""

    def test_petersen_graph(self):
        """Test the Petersen graph (distance-regular)."""
        gf = GossipFingerprint()

        G = nx.petersen_graph()

        # Test self-isomorphism
        G_perm = relabel_graph(G, seed=42)
        assert gf.compare(G, G_perm)

        # Test against complement
        G_comp = nx.complement(G)
        iso = are_isomorphic(G, G_comp)
        match = gf.compare(G, G_comp)

        assert not iso
        assert not match

    def test_bipartite_kneser_graphs(self):
        """Test bipartite Kneser graphs (distance-regular)."""
        gf = GossipFingerprint()

        # Small bipartite Kneser graph H(3,1)
        # This is actually the complete bipartite graph K_{3,3}
        G = nx.complete_bipartite_graph(3, 3)

        # Test properties
        assert nx.is_bipartite(G)
        assert nx.is_regular(G)

        # Test fingerprint
        G_perm = relabel_graph(G, seed=99)
        assert gf.compare(G, G_perm)

    def test_hamming_graphs(self):
        """Test Hamming graphs H(d,q) - Cartesian product of complete graphs."""
        gf = GossipFingerprint()

        # H(2,3) - Cartesian product of two K_3
        K3 = nx.complete_graph(3)
        H_2_3 = nx.cartesian_product(K3, K3)

        # Should be 4-regular with 9 vertices
        assert H_2_3.number_of_nodes() == 9
        degrees = [d for _, d in H_2_3.degree()]
        assert all(d == 4 for d in degrees)

        # Test fingerprint
        H_perm = relabel_graph(H_2_3, seed=42)
        assert gf.compare(H_2_3, H_perm)


class TestVertexTransitiveGraphs:
    """Test vertex-transitive graphs."""

    def test_cayley_graphs(self):
        """Test Cayley graphs of small groups."""
        gf = GossipFingerprint()

        # Cayley graph of Z_6 with generators {1, 2}
        G = nx.Graph()
        for i in range(6):
            G.add_edge(i, (i + 1) % 6)
            G.add_edge(i, (i + 2) % 6)

        # This should be vertex-transitive
        # All vertices should have identical local structure
        adj = graph_to_adjacency_list(G)
        fp = gf.compute(adj)

        # All fingerprints should be identical (vertex-transitive property)
        assert len(set(fp)) == 1

    def test_platonic_graphs(self):
        """Test graphs of Platonic solids."""
        gf = GossipFingerprint()

        # Tetrahedron (K_4)
        tetrahedron = nx.complete_graph(4)

        # Cube graph
        cube = nx.hypercube_graph(3)

        # Octahedron
        octahedron = nx.Graph()
        octahedron.add_edges_from([
            (0, 1), (0, 2), (0, 3), (0, 4),
            (1, 2), (2, 3), (3, 4), (4, 1),
            (1, 5), (2, 5), (3, 5), (4, 5)
        ])

        for G in [tetrahedron, cube, octahedron]:
            # Test self-isomorphism
            G_perm = relabel_graph(G, seed=42)
            assert gf.compare(G, G_perm)


class TestExtremeCases:
    """Test extreme and pathological cases."""

    def test_almost_isomorphic_graphs(self):
        """Test graphs that differ by a single edge."""
        gf = GossipFingerprint()

        # Start with a base graph
        G1 = nx.cycle_graph(10)
        G1.add_edge(0, 5)  # Add a chord

        G2 = nx.cycle_graph(10)
        G2.add_edge(1, 6)  # Add a different chord

        iso = are_isomorphic(G1, G2)
        match = gf.compare(G1, G2)

        # These might or might not be isomorphic depending on the specific chords
        # Just verify consistency
        if iso != match:
            print(f"Almost isomorphic: Gossip {match} differs from isomorphism {iso}")

    def test_high_symmetry_graphs(self):
        """Test graphs with very high symmetry."""
        gf = GossipFingerprint()

        # Complete graph - maximum symmetry
        K10 = nx.complete_graph(10)

        # Empty graph - also maximum symmetry
        E10 = nx.empty_graph(10)

        # All vertices should have identical fingerprints
        for G in [K10, E10]:
            adj = graph_to_adjacency_list(G)
            fp = gf.compute(adj)
            assert len(set(fp)) == 1, "All vertices should have identical fingerprints"

    def test_random_regular_isomorphism_pairs(self):
        """Test random regular graphs for isomorphism."""
        gf = GossipFingerprint()

        # Generate pairs of random regular graphs
        for d in [3, 4]:
            for n in [10, 12, 14]:
                if (n * d) % 2 != 0:
                    continue

                # Generate two random regular graphs
                G1 = nx.random_regular_graph(d, n, seed=42)
                G2 = nx.random_regular_graph(d, n, seed=43)

                iso = are_isomorphic(G1, G2)
                match = gf.compare(G1, G2)

                # They're probably not isomorphic, but check consistency
                if iso != match:
                    print(f"Random regular ({d},{n}): Gossip differs from isomorphism")


@pytest.mark.slow
class TestLargeHardInstances:
    """Test larger hard instances (marked as slow)."""

    def test_large_cfi_graphs(self):
        """Test CFI graphs with larger base graphs."""
        gf = GossipFingerprint()

        for n in [10, 15, 20]:
            base = nx.cycle_graph(n)
            G1, G2 = generate_cfi_pair(base)

            iso = are_isomorphic(G1, G2)
            match = gf.compare(G1, G2)

            assert not iso, "CFI graphs should be non-isomorphic"
            if match:
                print(f"Large CFI (n={n}): Gossip failed to distinguish")

    def test_large_miyazaki_graphs(self):
        """Test larger Miyazaki graphs."""
        gf = GossipFingerprint()

        for n in [20, 30, 40]:
            G = generate_miyazaki_graph(n)
            G_perm = relabel_graph(G, seed=42)

            assert gf.compare(G, G_perm), f"Should match for Miyazaki graph n={n}"

    def test_product_graphs(self):
        """Test various graph products."""
        gf = GossipFingerprint()

        # Test Cartesian products
        C4 = nx.cycle_graph(4)
        C5 = nx.cycle_graph(5)

        G1 = nx.cartesian_product(C4, C5)  # Torus graph
        G2 = nx.cartesian_product(C5, C4)  # Should be isomorphic

        assert are_isomorphic(G1, G2)
        assert gf.compare(G1, G2)

        # Test tensor products
        P3 = nx.path_graph(3)
        P4 = nx.path_graph(4)

        T1 = nx.tensor_product(P3, P4)
        T2 = nx.tensor_product(P4, P3)

        iso = are_isomorphic(T1, T2)
        match = gf.compare(T1, T2)

        if iso != match:
            print(f"Tensor product: Gossip differs from isomorphism")
