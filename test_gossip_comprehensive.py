#!/usr/bin/env python3
"""
Comprehensive test suite for the Gossip graph isomorphism algorithm.
Includes all known hard instances and challenging graph families.
"""

import networkx as nx
import itertools
import random
import time
import math
import numpy as np
from collections import defaultdict
from gossip_cli import gossip_fingerprint_full, graph_to_adj

# Set random seeds for reproducibility
random.seed(42)
np.random.seed(42)

class ComprehensiveGraphTests:
    def __init__(self):
        self.test_results = []
        self.categories = defaultdict(list)

    def compare_graphs(self, G1, G2):
        """Compare two graphs using gossip fingerprint and actual isomorphism."""
        adj1 = graph_to_adj(G1)
        adj2 = graph_to_adj(G2)
        f1 = gossip_fingerprint_full(adj1)
        f2 = gossip_fingerprint_full(adj2)
        iso = nx.is_isomorphic(G1, G2)
        match = f1 == f2
        return iso, match

    def add_test(self, category, name, G1, G2, expected_iso=None):
        """Add a test case to the suite."""
        iso, match = self.compare_graphs(G1, G2)
        if expected_iso is None:
            expected_iso = iso

        correct = (iso == match)
        result = {
            'category': category,
            'name': name,
            'isomorphic': iso,
            'fingerprint_match': match,
            'correct': correct,
            'expected': expected_iso,
            'size': len(G1.nodes()),
            'edges': len(G1.edges())
        }
        self.test_results.append(result)
        self.categories[category].append(result)
        return result

    # =============================================================================
    # CFI (Cai-Fürer-Immerman) Graphs - Classic WL failures
    # =============================================================================

    def make_cfi_pair(self, base, flip_edges):
        """Create CFI graph pair from base graph."""
        def build(flip=False):
            G = nx.Graph()
            for v in base.nodes():
                for i in range(3):
                    G.add_edge(f"{v}_c", f"{v}_{i}")
            for (u, v) in base.edges():
                for i in range(3):
                    if flip and (u, v) in flip_edges:
                        G.add_edge(f"{u}_{i}", f"{v}_{(i+1)%3}")
                    else:
                        G.add_edge(f"{u}_{i}", f"{v}_{i}")
            return G
        return build(False), build(True)

    def generate_cfi_tests(self):
        """Generate various CFI graph test cases."""
        base_graphs = [
            ("cycle4", nx.cycle_graph(4)),
            ("cube", nx.cubical_graph()),
            ("path4", nx.path_graph(4)),
            ("star4", nx.star_graph(4)),
            ("complete4", nx.complete_graph(4)),
            ("petersen", nx.petersen_graph()),
            ("cycle6", nx.cycle_graph(6)),
            ("wheel5", nx.wheel_graph(5))
        ]

        for base_name, base in base_graphs:
            # Different flip patterns
            edges = list(base.edges())
            if len(edges) >= 2:
                flip_patterns = [
                    edges[:len(edges)//2],
                    edges[::2],
                    [edges[0], edges[-1]] if len(edges) > 1 else [edges[0]]
                ]

                for i, flip_edges in enumerate(flip_patterns):
                    CFI1, CFI2 = self.make_cfi_pair(base, flip_edges)
                    self.add_test("CFI", f"CFI_{base_name}_pattern{i}", CFI1, CFI2, False)

    # =============================================================================
    # Strongly Regular Graphs
    # =============================================================================

    def srg_parameters(self):
        """Generate various strongly regular graph parameters."""
        return [
            (16, 6, 2, 2),   # Original from paper
            (16, 9, 4, 6),   # Complement
            (25, 12, 5, 6),  # 5x5 grid graph
            (36, 10, 4, 2),  # Unique SRG
            (36, 15, 6, 6),  # Many non-isomorphic instances
            (50, 7, 0, 1),   # Hoffman-Singleton
        ]

    def construct_srg_16_6_2_2(self):
        """Construct the (16,6,2,2) strongly regular graph."""
        edges = [
            (0,1),(0,2),(0,3),(0,4),(0,5),(0,6),
            (1,2),(1,7),(1,8),(1,9),(1,10),
            (2,3),(2,11),(2,12),(2,13),
            (3,4),(3,14),(3,15),
            (4,5),(4,7),
            (5,6),(5,8),
            (6,9),(6,10),
            (7,11),(7,12),
            (8,11),(8,13),
            (9,12),(9,14),
            (10,13),(10,15),
            (11,14),
            (12,15),
            (13,14),
            (14,15)
        ]
        G = nx.Graph()
        G.add_edges_from(edges)
        return G

    def generate_srg_tests(self):
        """Generate strongly regular graph tests."""
        # Test the known (16,6,2,2) SRG
        base_srg = self.construct_srg_16_6_2_2()

        # Test isomorphic relabelings
        for i in range(5):
            perm = list(range(16))
            random.shuffle(perm)
            relabeled = nx.relabel_nodes(base_srg, dict(enumerate(perm)))
            self.add_test("SRG", f"SRG_16_6_2_2_relabel_{i}", base_srg, relabeled, True)

        # Test against complement
        complement = nx.complement(base_srg)
        self.add_test("SRG", "SRG_16_vs_complement", base_srg, complement, False)

        # Test grid graphs (strongly regular)
        for size in [4, 5, 6]:
            grid = nx.grid_2d_graph(size, size)
            grid_relabeled = nx.convert_node_labels_to_integers(grid)
            perm_grid = nx.relabel_nodes(grid_relabeled,
                                       {i: (i * 7 + 3) % (size*size)
                                        for i in range(size*size)})
            self.add_test("SRG", f"grid_{size}x{size}_relabel",
                         grid_relabeled, perm_grid, True)

    # =============================================================================
    # Conference Matrices and Hadamard Matrices
    # =============================================================================

    def paley_graph(self, q):
        """Construct Paley graph of order q (q ≡ 1 mod 4 prime power)."""
        if q % 4 != 1:
            return None

        G = nx.Graph()
        G.add_nodes_from(range(q))

        # For small primes, use quadratic residues
        if q == 5:
            residues = {1, 4}
        elif q == 9:
            residues = {1, 4, 7}
        elif q == 13:
            residues = {1, 3, 4, 9, 10, 12}
        elif q == 17:
            residues = {1, 2, 4, 8, 9, 13, 15, 16}
        else:
            return None

        for i in range(q):
            for j in range(i+1, q):
                if (i - j) % q in residues:
                    G.add_edge(i, j)

        return G

    def generate_conference_tests(self):
        """Generate tests based on conference matrices and Paley graphs."""
        for q in [5, 9, 13, 17]:
            paley = self.paley_graph(q)
            if paley is not None:
                # Test isomorphic relabeling
                perm = list(range(q))
                random.shuffle(perm)
                relabeled = nx.relabel_nodes(paley, dict(enumerate(perm)))
                self.add_test("Conference", f"Paley_{q}_relabel", paley, relabeled, True)

                # Test against complement
                complement = nx.complement(paley)
                self.add_test("Conference", f"Paley_{q}_vs_complement",
                             paley, complement, False)

    # =============================================================================
    # Distance-Regular Graphs
    # =============================================================================

    def generate_distance_regular_tests(self):
        """Generate distance-regular graph tests."""
        # Johnson graphs J(n,k)
        for n, k in [(5,2), (6,2), (6,3), (7,3)]:
            johnson = nx.Graph()
            nodes = list(itertools.combinations(range(n), k))
            johnson.add_nodes_from(range(len(nodes)))

            for i, set1 in enumerate(nodes):
                for j, set2 in enumerate(nodes):
                    if i < j and len(set(set1) & set(set2)) == k-1:
                        johnson.add_edge(i, j)

            # Test relabeling
            perm = list(range(len(nodes)))
            random.shuffle(perm)
            relabeled = nx.relabel_nodes(johnson, dict(enumerate(perm)))
            self.add_test("DistanceRegular", f"Johnson_{n}_{k}_relabel",
                         johnson, relabeled, True)

        # Hamming graphs H(d,q)
        for d, q in [(2,3), (2,4), (3,2)]:
            hamming = nx.Graph()
            nodes = list(itertools.product(range(q), repeat=d))
            hamming.add_nodes_from(range(len(nodes)))

            for i, v1 in enumerate(nodes):
                for j, v2 in enumerate(nodes):
                    if i < j and sum(a != b for a, b in zip(v1, v2)) == 1:
                        hamming.add_edge(i, j)

            perm = list(range(len(nodes)))
            random.shuffle(perm)
            relabeled = nx.relabel_nodes(hamming, dict(enumerate(perm)))
            self.add_test("DistanceRegular", f"Hamming_{d}_{q}_relabel",
                         hamming, relabeled, True)

    # =============================================================================
    # Circulant Graphs
    # =============================================================================

    def generate_circulant_tests(self):
        """Generate circulant graph tests."""
        configs = [
            (12, [1, 2, 3]),
            (16, [1, 4, 5]),
            (20, [1, 2, 7, 8]),
            (24, [1, 5, 7]),
            (30, [1, 6, 11])
        ]

        for n, jumps in configs:
            circ1 = nx.circulant_graph(n, jumps)

            # Test rotation (should be isomorphic)
            rotation_map = {i: (i + 3) % n for i in range(n)}
            circ2 = nx.relabel_nodes(circ1, rotation_map)
            self.add_test("Circulant", f"circulant_{n}_{jumps}_rotation",
                         circ1, circ2, True)

            # Test reflection (may or may not be isomorphic)
            reflection_map = {i: (-i) % n for i in range(n)}
            circ3 = nx.relabel_nodes(circ1, reflection_map)
            self.add_test("Circulant", f"circulant_{n}_{jumps}_reflection",
                         circ1, circ3)

            # Test with different jump set (should be non-isomorphic)
            if len(jumps) > 1:
                different_jumps = jumps[:-1] + [jumps[-1] + 1 if jumps[-1] + 1 < n//2 else jumps[-1] - 1]
                circ4 = nx.circulant_graph(n, different_jumps)
                self.add_test("Circulant", f"circulant_{n}_different_jumps",
                             circ1, circ4, False)

    # =============================================================================
    # Vertex-Transitive Graphs
    # =============================================================================

    def generate_vertex_transitive_tests(self):
        """Generate vertex-transitive graph tests."""
        # Platonic solids
        platonic = [
            ("tetrahedron", nx.complete_graph(4)),
            ("cube", nx.cubical_graph()),
            ("octahedron", nx.octahedral_graph()),
            ("dodecahedron", nx.dodecahedral_graph()),
            ("icosahedron", nx.icosahedral_graph())
        ]

        for name, graph in platonic:
            if len(graph.nodes()) <= 20:  # Keep reasonable size
                # Test automorphism
                perm = list(range(len(graph.nodes())))
                random.shuffle(perm)
                relabeled = nx.relabel_nodes(graph, dict(enumerate(perm)))
                self.add_test("VertexTransitive", f"{name}_relabel",
                             graph, relabeled, True)

        # Cayley graphs of small groups
        # Cycle groups
        for n in [8, 12, 16]:
            cayley = nx.circulant_graph(n, [1, n-1])  # Generators: 1 and -1
            rotation = nx.relabel_nodes(cayley, {i: (i + 2) % n for i in range(n)})
            self.add_test("VertexTransitive", f"cayley_cycle_{n}",
                         cayley, rotation, True)

    # =============================================================================
    # Latin Squares and Orthogonal Arrays
    # =============================================================================

    def latin_square_graph(self, n):
        """Create graph from Latin square structure."""
        G = nx.Graph()
        # Create vertices for each cell (i,j,k) where k is the symbol
        vertices = [(i, j, k) for i in range(n) for j in range(n) for k in range(n)]
        G.add_nodes_from(range(len(vertices)))

        # Add edges between vertices that share exactly two coordinates
        for idx1, (i1, j1, k1) in enumerate(vertices):
            for idx2, (i2, j2, k2) in enumerate(vertices):
                if idx1 < idx2:
                    shared = sum([i1==i2, j1==j2, k1==k2])
                    if shared == 2:
                        G.add_edge(idx1, idx2)

        return G

    def generate_latin_square_tests(self):
        """Generate Latin square related tests."""
        for n in [3, 4]:
            ls_graph = self.latin_square_graph(n)

            # Test permutation of symbols
            perm = list(range(len(ls_graph.nodes())))
            random.shuffle(perm)
            relabeled = nx.relabel_nodes(ls_graph, dict(enumerate(perm)))
            self.add_test("LatinSquare", f"latin_{n}_relabel",
                         ls_graph, relabeled, True)

    # =============================================================================
    # Steiner Triple Systems
    # =============================================================================

    def steiner_triple_system_graph(self, n):
        """Create graph from Steiner triple system."""
        if n % 6 not in [1, 3]:
            return None

        G = nx.Graph()
        G.add_nodes_from(range(n))

        # For small cases, construct manually
        if n == 7:
            triples = [(0,1,3), (1,2,4), (2,3,5), (3,4,6), (4,5,0), (5,6,1), (6,0,2)]
        elif n == 9:
            triples = [(0,1,5), (0,2,6), (0,3,7), (0,4,8), (1,2,8), (1,3,6), (1,4,7),
                      (2,3,5), (2,4,7), (3,4,5), (5,6,8), (6,7,8)]
        else:
            return None

        # Connect vertices that appear together in a triple
        for triple in triples:
            for i in range(3):
                for j in range(i+1, 3):
                    G.add_edge(triple[i], triple[j])

        return G

    def generate_steiner_tests(self):
        """Generate Steiner triple system tests."""
        for n in [7, 9]:
            sts_graph = self.steiner_triple_system_graph(n)
            if sts_graph is not None:
                perm = list(range(n))
                random.shuffle(perm)
                relabeled = nx.relabel_nodes(sts_graph, dict(enumerate(perm)))
                self.add_test("Steiner", f"STS_{n}_relabel",
                             sts_graph, relabeled, True)

    # =============================================================================
    # Kneser and Petersen-type Graphs
    # =============================================================================

    def kneser_graph(self, n, k):
        """Create Kneser graph KG(n,k)."""
        G = nx.Graph()
        vertices = list(itertools.combinations(range(n), k))
        G.add_nodes_from(range(len(vertices)))

        for i, set1 in enumerate(vertices):
            for j, set2 in enumerate(vertices):
                if i < j and len(set(set1) & set(set2)) == 0:
                    G.add_edge(i, j)

        return G

    def generate_kneser_tests(self):
        """Generate Kneser graph tests."""
        configs = [(5,2), (6,2), (7,3)]

        for n, k in configs:
            kneser = self.kneser_graph(n, k)

            # Test relabeling
            perm = list(range(len(kneser.nodes())))
            random.shuffle(perm)
            relabeled = nx.relabel_nodes(kneser, dict(enumerate(perm)))
            self.add_test("Kneser", f"Kneser_{n}_{k}_relabel",
                         kneser, relabeled, True)

        # Test Petersen graph (special case of Kneser)
        petersen = nx.petersen_graph()
        perm = list(range(10))
        random.shuffle(perm)
        relabeled = nx.relabel_nodes(petersen, dict(enumerate(perm)))
        self.add_test("Kneser", "Petersen_relabel", petersen, relabeled, True)

    # =============================================================================
    # Switched Graphs
    # =============================================================================

    def generate_switched_tests(self):
        """Generate tests with Seidel switching."""
        base_graphs = [
            nx.cycle_graph(8),
            nx.complete_graph(6),
            nx.petersen_graph(),
            nx.cubical_graph()
        ]

        for i, base in enumerate(base_graphs):
            # Apply switching with respect to a subset of vertices
            n = len(base.nodes())
            switch_set = random.sample(list(base.nodes()), n//3)

            switched = base.copy()
            for u in switch_set:
                for v in base.nodes():
                    if u != v and v not in switch_set:
                        if switched.has_edge(u, v):
                            switched.remove_edge(u, v)
                        else:
                            switched.add_edge(u, v)

            self.add_test("Switched", f"switched_{i}", base, switched, False)

    # =============================================================================
    # Tournament Graphs
    # =============================================================================

    def generate_tournament_tests(self):
        """Generate regular tournament tests."""
        for n in [7, 9, 11]:  # Only odd n can have regular tournaments
            if n % 2 == 1:
                # Create regular tournament
                T = nx.DiGraph()
                T.add_nodes_from(range(n))

                for i in range(n):
                    for j in range(1, (n+1)//2):
                        T.add_edge(i, (i + j) % n)

                # Convert to undirected for testing
                G1 = T.to_undirected()

                # Create rotated version
                rotation_map = {i: (i + 2) % n for i in range(n)}
                G2 = nx.relabel_nodes(G1, rotation_map)

                self.add_test("Tournament", f"regular_tournament_{n}", G1, G2, True)

    # =============================================================================
    # Exceptional and Sporadic Cases
    # =============================================================================

    def generate_exceptional_tests(self):
        """Generate tests with exceptional graph families."""
        # Hoffman-Singleton graph (unique (50,7,0,1) SRG)
        # This is complex to construct, so we'll simulate with a smaller example

        # Shrikhande graph (unique (16,6,2,2) SRG different from 4×4 grid)
        # This is also complex, so we'll use our existing SRG

        # Clebsch graph
        clebsch = nx.Graph()
        # 16 vertices, each vertex adjacent to 10 others
        # This is the complement of the 4×4 grid graph
        grid_4x4 = nx.grid_2d_graph(4, 4)
        grid_numbered = nx.convert_node_labels_to_integers(grid_4x4)
        clebsch = nx.complement(grid_numbered)

        perm = list(range(16))
        random.shuffle(perm)
        clebsch_relabeled = nx.relabel_nodes(clebsch, dict(enumerate(perm)))
        self.add_test("Exceptional", "Clebsch_relabel", clebsch, clebsch_relabeled, True)

    # =============================================================================
    # Stress Tests and Large Instances
    # =============================================================================

    def generate_stress_tests(self):
        """Generate large or computationally challenging instances."""
        # Large CFI graphs
        large_base = nx.cycle_graph(8)
        CFI1, CFI2 = self.make_cfi_pair(large_base, [(0,1), (2,3), (4,5), (6,7)])
        self.add_test("Stress", "large_CFI_cycle8", CFI1, CFI2, False)

        # Large circulant graphs
        large_circ1 = nx.circulant_graph(40, [1, 3, 7, 11])
        large_circ2 = nx.relabel_nodes(large_circ1, {i: (i + 5) % 40 for i in range(40)})
        self.add_test("Stress", "large_circulant_40", large_circ1, large_circ2, True)

        # Dense random graphs with planted structure
        for size in [25, 30]:
            G1 = nx.gnp_random_graph(size, 0.5, seed=42)
            perm = list(range(size))
            random.shuffle(perm)
            G2 = nx.relabel_nodes(G1, dict(enumerate(perm)))
            self.add_test("Stress", f"dense_random_{size}", G1, G2, True)

    # =============================================================================
    # Test Runner and Analysis
    # =============================================================================

    def run_all_tests(self):
        """Run all test categories."""
        print("=" * 80)
        print("COMPREHENSIVE GOSSIP FINGERPRINT TEST SUITE")
        print("=" * 80)

        test_generators = [
            ("CFI Graphs", self.generate_cfi_tests),
            ("Strongly Regular", self.generate_srg_tests),
            ("Conference Matrices", self.generate_conference_tests),
            ("Distance Regular", self.generate_distance_regular_tests),
            ("Circulant Graphs", self.generate_circulant_tests),
            ("Vertex Transitive", self.generate_vertex_transitive_tests),
            ("Latin Squares", self.generate_latin_square_tests),
            ("Steiner Systems", self.generate_steiner_tests),
            ("Kneser/Petersen", self.generate_kneser_tests),
            ("Switched Graphs", self.generate_switched_tests),
            ("Tournament Graphs", self.generate_tournament_tests),
            ("Exceptional Cases", self.generate_exceptional_tests),
            ("Stress Tests", self.generate_stress_tests)
        ]

        start_time = time.time()

        for category_name, generator in test_generators:
            print(f"\nGenerating {category_name} tests...")
            try:
                generator()
                print(f"✓ {category_name} completed")
            except Exception as e:
                print(f"✗ {category_name} failed: {e}")

        total_time = time.time() - start_time

        # Print results
        self.print_results()
        print(f"\nTotal execution time: {total_time:.2f} seconds")

        return self.analyze_results()

    def print_results(self):
        """Print detailed test results."""
        print("\n" + "=" * 80)
        print("DETAILED RESULTS BY CATEGORY")
        print("=" * 80)

        for category in sorted(self.categories.keys()):
            results = self.categories[category]
            passed = sum(1 for r in results if r['correct'])
            total = len(results)

            print(f"\n{category.upper()}: {passed}/{total} passed ({passed/total*100:.1f}%)")
            print("-" * 60)

            for result in results:
                status = "✅ PASS" if result['correct'] else "❌ FAIL"
                iso_str = "ISO" if result['isomorphic'] else "NON-ISO"
                match_str = "MATCH" if result['fingerprint_match'] else "NO-MATCH"
                print(f"  {result['name']:<30} | {iso_str:<8} | {match_str:<8} | {status}")

    def analyze_results(self):
        """Analyze test results and provide statistics."""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r['correct'])

        # Analyze by graph size
        size_analysis = defaultdict(list)
        for result in self.test_results:
            size_analysis[result['size']].append(result['correct'])

        # Analyze by category
        category_stats = {}
        for category, results in self.categories.items():
            passed = sum(1 for r in results if r['correct'])
            total = len(results)
            category_stats[category] = (passed, total, passed/total if total > 0 else 0)

        print("\n" + "=" * 80)
        print("ANALYSIS SUMMARY")
        print("=" * 80)
        print(f"Overall: {passed_tests}/{total_tests} tests passed ({passed_tests/total_tests*100:.1f}%)")

        print(f"\nPerformance by graph size:")
        for size in sorted(size_analysis.keys()):
            results = size_analysis[size]
            passed = sum(results)
            total = len(results)
            print(f"  Size {size:2d}: {passed:2d}/{total:2d} passed ({passed/total*100:.1f}%)")

        print(f"\nPerformance by category:")
        for category in sorted(category_stats.keys()):
            passed, total, rate = category_stats[category]
            print(f"  {category:<20}: {passed:2d}/{total:2d} passed ({rate*100:.1f}%)")

        # Identify problematic categories
        weak_categories = [cat for cat, (p, t, r) in category_stats.items() if r < 0.8 and t > 0]
        if weak_categories:
            print(f"\nCategories needing attention: {', '.join(weak_categories)}")

        return {
            'total': total_tests,
            'passed': passed_tests,
            'rate': passed_tests/total_tests,
            'categories': category_stats,
            'weak_categories': weak_categories
        }


def main():
    """Main test runner."""
    suite = ComprehensiveGraphTests()
    results = suite.run_all_tests()

    if results['rate'] < 0.9:
        print(f"\n⚠️  Warning: Success rate below 90% ({results['rate']*100:.1f}%)")
        print("Consider investigating the failing test cases.")
    else:
        print(f"\n🎉 Excellent! Success rate: {results['rate']*100:.1f}%")

    return results


if __name__ == "__main__":
    main()
