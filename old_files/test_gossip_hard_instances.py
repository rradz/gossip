#!/usr/bin/env python3
"""
Additional hard instances for graph isomorphism testing.
Focuses on the most challenging cases documented in the literature.
"""

import networkx as nx
import itertools
import random
import math
from collections import defaultdict
from gossip_cli import gossip_fingerprint_full, graph_to_adj

class HardInstanceTests:
    def __init__(self):
        self.test_results = []
        random.seed(42)

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
        """Add a test case."""
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
        return result

    # =============================================================================
    # Miyazaki Graphs - Known to fool many isomorphism algorithms
    # =============================================================================

    def construct_miyazaki_graph(self, n):
        """Construct Miyazaki graph - known hard instance."""
        if n < 4 or n % 2 != 0:
            return None

        G = nx.Graph()
        # Create vertices
        vertices = []
        for i in range(n):
            for j in range(3):
                vertices.append(f"v{i}_{j}")

        G.add_nodes_from(vertices)

        # Add edges according to Miyazaki construction
        for i in range(n):
            # Connect within each vertex group
            G.add_edge(f"v{i}_0", f"v{i}_1")
            G.add_edge(f"v{i}_1", f"v{i}_2")

            # Connect to next vertex group with specific pattern
            next_i = (i + 1) % n
            G.add_edge(f"v{i}_0", f"v{next_i}_0")
            G.add_edge(f"v{i}_2", f"v{next_i}_2")

            # Cross connections for even/odd pattern
            if i % 2 == 0:
                G.add_edge(f"v{i}_1", f"v{next_i}_0")
            else:
                G.add_edge(f"v{i}_1", f"v{next_i}_2")

        return G

    def generate_miyazaki_tests(self):
        """Generate Miyazaki graph tests."""
        for n in [4, 6, 8]:
            miya1 = self.construct_miyazaki_graph(n)
            if miya1 is not None:
                # Create a similar but non-isomorphic graph by switching some connections
                miya2 = miya1.copy()
                nodes = list(miya2.nodes())
                if len(nodes) >= 6:
                    # Switch a few edges to create non-isomorphic graph
                    if miya2.has_edge(nodes[0], nodes[1]):
                        miya2.remove_edge(nodes[0], nodes[1])
                        miya2.add_edge(nodes[0], nodes[2])

                self.add_test("Miyazaki", f"miyazaki_{n}", miya1, miya2, False)

    # =============================================================================
    # Paulus Graphs - Symmetric graphs that challenge WL algorithms
    # =============================================================================

    def construct_paulus_graph(self, k):
        """Construct Paulus graph P_k."""
        if k < 2:
            return None

        # Create 2^k vertices
        n = 2 ** k
        G = nx.Graph()

        # Vertices are k-bit binary strings
        vertices = []
        for i in range(n):
            vertices.append(format(i, f'0{k}b'))

        G.add_nodes_from(vertices)

        # Add edges: two vertices are adjacent if their Hamming distance is 1 or k-1
        for i, v1 in enumerate(vertices):
            for j, v2 in enumerate(vertices):
                if i < j:
                    hamming_dist = sum(a != b for a, b in zip(v1, v2))
                    if hamming_dist == 1 or hamming_dist == k-1:
                        G.add_edge(v1, v2)

        return G

    def generate_paulus_tests(self):
        """Generate Paulus graph tests."""
        for k in [3, 4]:
            paulus = self.construct_paulus_graph(k)
            if paulus is not None:
                # Create relabeled version (should be isomorphic)
                nodes = list(paulus.nodes())
                random.shuffle(nodes)
                mapping = dict(zip(paulus.nodes(), nodes))
                paulus_relabeled = nx.relabel_nodes(paulus, mapping)

                self.add_test("Paulus", f"paulus_{k}_relabel", paulus, paulus_relabeled, True)

                # Create modified version (should be non-isomorphic)
                paulus_mod = paulus.copy()
                edges = list(paulus_mod.edges())
                if len(edges) >= 2:
                    paulus_mod.remove_edge(*edges[0])
                    # Add a different edge if possible
                    non_edges = [(u, v) for u in paulus_mod.nodes() for v in paulus_mod.nodes()
                               if u < v and not paulus_mod.has_edge(u, v)]
                    if non_edges:
                        paulus_mod.add_edge(*non_edges[0])

                self.add_test("Paulus", f"paulus_{k}_modified", paulus, paulus_mod, False)

    # =============================================================================
    # Cubic Hypohamiltonian Graphs
    # =============================================================================

    def construct_petersen_like(self, n):
        """Construct Petersen-like cubic graph."""
        if n < 5:
            return None

        G = nx.Graph()

        # Outer cycle
        for i in range(n):
            G.add_edge(i, (i + 1) % n)

        # Inner vertices and connections
        for i in range(n):
            inner = i + n
            G.add_node(inner)
            G.add_edge(i, inner)
            G.add_edge(inner, (i + 2) % n + n)

        return G

    def generate_cubic_tests(self):
        """Generate cubic hypohamiltonian-like tests."""
        # Standard Petersen graph
        petersen = nx.petersen_graph()

        # Create twisted version
        petersen_twisted = petersen.copy()
        if petersen_twisted.has_edge(0, 1) and petersen_twisted.has_edge(2, 3):
            petersen_twisted.remove_edge(0, 1)
            petersen_twisted.remove_edge(2, 3)
            petersen_twisted.add_edge(0, 2)
            petersen_twisted.add_edge(1, 3)

        self.add_test("Cubic", "petersen_twisted", petersen, petersen_twisted, False)

        # Generate Petersen-like graphs
        for n in [5, 7]:
            if n != 5:  # Skip n=5 as it would be the regular Petersen
                pet_like = self.construct_petersen_like(n)
                if pet_like is not None:
                    # Create rotation
                    rotation_map = {i: (i + 1) % (2*n) for i in range(2*n)}
                    pet_rotated = nx.relabel_nodes(pet_like, rotation_map)

                    self.add_test("Cubic", f"petersen_like_{n}", pet_like, pet_rotated, True)

    # =============================================================================
    # Strongly Regular Graphs from Finite Geometries
    # =============================================================================

    def construct_geometric_srg(self, q):
        """Construct SRG from finite geometry."""
        if q not in [4, 8, 9]:
            return None

        G = nx.Graph()

        if q == 4:
            # Complement of 2x2 grid
            grid = nx.grid_2d_graph(2, 2)
            grid_int = nx.convert_node_labels_to_integers(grid)
            G = nx.complement(grid_int)
        elif q == 8:
            # 2x4 grid complement
            grid = nx.grid_2d_graph(2, 4)
            grid_int = nx.convert_node_labels_to_integers(grid)
            G = nx.complement(grid_int)
        elif q == 9:
            # 3x3 grid complement
            grid = nx.grid_2d_graph(3, 3)
            grid_int = nx.convert_node_labels_to_integers(grid)
            G = nx.complement(grid_int)

        return G

    def generate_geometric_srg_tests(self):
        """Generate geometric SRG tests."""
        for q in [4, 8, 9]:
            geom_srg = self.construct_geometric_srg(q)
            if geom_srg is not None:
                # Test against random relabeling
                nodes = list(geom_srg.nodes())
                random.shuffle(nodes)
                mapping = dict(zip(geom_srg.nodes(), nodes))
                relabeled = nx.relabel_nodes(geom_srg, mapping)

                self.add_test("GeometricSRG", f"geometric_srg_{q}", geom_srg, relabeled, True)

    # =============================================================================
    # Random Regular Graphs - Can be challenging
    # =============================================================================

    def generate_random_regular_tests(self):
        """Generate random regular graph tests."""
        configs = [(12, 3), (16, 4), (20, 3), (24, 4)]

        for n, d in configs:
            if n * d % 2 == 0:  # Necessary condition
                try:
                    # Generate two different random regular graphs
                    G1 = nx.random_regular_graph(d, n, seed=42)
                    G2 = nx.random_regular_graph(d, n, seed=123)

                    self.add_test("RandomRegular", f"random_regular_{n}_{d}", G1, G2, False)

                    # Test isomorphic relabeling
                    nodes = list(G1.nodes())
                    random.shuffle(nodes)
                    mapping = dict(zip(G1.nodes(), nodes))
                    G1_relabeled = nx.relabel_nodes(G1, mapping)

                    self.add_test("RandomRegular", f"random_regular_{n}_{d}_relabel", G1, G1_relabeled, True)
                except:
                    pass  # Skip if construction fails

    # =============================================================================
    # Expander Graphs and High Girth Graphs
    # =============================================================================

    def construct_ramanujan_graph(self, p):
        """Construct Ramanujan-like graph (approximation)."""
        if p not in [5, 7, 11, 13]:
            return None

        # Cayley graph construction
        G = nx.Graph()
        G.add_nodes_from(range(p))

        # Use quadratic residues as generators
        if p == 5:
            generators = [1, 4]
        elif p == 7:
            generators = [1, 2, 4]
        elif p == 11:
            generators = [1, 3, 4, 5, 9]
        elif p == 13:
            generators = [1, 3, 4]
        else:
            return None

        for i in range(p):
            for gen in generators:
                G.add_edge(i, (i + gen) % p)
                G.add_edge(i, (i - gen) % p)

        return G

    def generate_expander_tests(self):
        """Generate expander graph tests."""
        for p in [7, 11, 13]:
            ramanujan = self.construct_ramanujan_graph(p)
            if ramanujan is not None:
                # Test automorphism
                shift_map = {i: (i + 3) % p for i in range(p)}
                shifted = nx.relabel_nodes(ramanujan, shift_map)

                self.add_test("Expander", f"ramanujan_{p}_shift", ramanujan, shifted, True)

    # =============================================================================
    # Circulant Graphs with Special Properties
    # =============================================================================

    def generate_special_circulant_tests(self):
        """Generate circulant graphs with special properties."""
        # Self-complementary circulants
        special_configs = [
            (5, [1, 2]),
            (13, [1, 3, 4]),
            (17, [1, 2, 4, 8]),
        ]

        for n, jumps in special_configs:
            circ = nx.circulant_graph(n, jumps)
            comp_circ = nx.complement(circ)

            # Test self-complementarity (complement should be isomorphic)
            self.add_test("SpecialCirculant", f"self_comp_circulant_{n}",
                         circ, comp_circ, True)

            # Test with different jump pattern
            if len(jumps) > 1:
                alt_jumps = jumps[:-1] + [(jumps[-1] + 1) % (n//2) + 1]
                alt_circ = nx.circulant_graph(n, alt_jumps)
                self.add_test("SpecialCirculant", f"alt_circulant_{n}",
                             circ, alt_circ, False)

    # =============================================================================
    # Graphs from Coding Theory
    # =============================================================================

    def construct_hamming_code_graph(self, r):
        """Construct graph from Hamming code."""
        if r < 2 or r > 4:
            return None

        n = 2**r - 1  # Code length
        k = n - r     # Dimension

        G = nx.Graph()

        # Vertices are codewords (simplified construction)
        codewords = []
        for i in range(2**k):
            # Generate codeword (simplified)
            word = format(i, f'0{k}b') + '0' * r
            codewords.append(word[:n])

        G.add_nodes_from(range(len(codewords)))

        # Connect codewords at specific Hamming distances
        for i, w1 in enumerate(codewords):
            for j, w2 in enumerate(codewords):
                if i < j:
                    hamming_dist = sum(a != b for a, b in zip(w1, w2))
                    if hamming_dist == 3:  # Minimum distance for Hamming codes
                        G.add_edge(i, j)

        return G

    def generate_coding_theory_tests(self):
        """Generate coding theory based tests."""
        for r in [3]:  # Keep it small
            hamming_graph = self.construct_hamming_code_graph(r)
            if hamming_graph is not None and len(hamming_graph.nodes()) > 1:
                # Test relabeling
                nodes = list(hamming_graph.nodes())
                random.shuffle(nodes)
                mapping = dict(zip(hamming_graph.nodes(), nodes))
                relabeled = nx.relabel_nodes(hamming_graph, mapping)

                self.add_test("CodingTheory", f"hamming_code_{r}",
                             hamming_graph, relabeled, True)

    # =============================================================================
    # Highly Symmetric Graphs
    # =============================================================================

    def generate_highly_symmetric_tests(self):
        """Generate tests with highly symmetric graphs."""
        # Complete multipartite graphs
        for parts in [(3, 3, 3), (2, 2, 2, 2), (4, 4)]:
            multi = nx.complete_multipartite_graph(*parts)

            # Create partition-swapped version
            nodes = list(multi.nodes())
            n_total = len(nodes)

            # Swap two partitions if possible
            if len(parts) >= 2 and parts[0] == parts[1]:
                part_size = parts[0]
                # Swap first two partitions
                mapping = {}
                for i in range(n_total):
                    if i < part_size:
                        mapping[i] = i + part_size
                    elif i < 2 * part_size:
                        mapping[i] = i - part_size
                    else:
                        mapping[i] = i

                swapped = nx.relabel_nodes(multi, mapping)
                self.add_test("HighlySymmetric", f"multipartite_{parts}_swap",
                             multi, swapped, True)

    # =============================================================================
    # Test Runner
    # =============================================================================

    def run_all_hard_tests(self):
        """Run all hard instance tests."""
        print("=" * 80)
        print("HARD INSTANCES TEST SUITE")
        print("=" * 80)

        test_generators = [
            ("Miyazaki Graphs", self.generate_miyazaki_tests),
            ("Paulus Graphs", self.generate_paulus_tests),
            ("Cubic Graphs", self.generate_cubic_tests),
            ("Geometric SRG", self.generate_geometric_srg_tests),
            ("Random Regular", self.generate_random_regular_tests),
            ("Expander Graphs", self.generate_expander_tests),
            ("Special Circulant", self.generate_special_circulant_tests),
            ("Coding Theory", self.generate_coding_theory_tests),
            ("Highly Symmetric", self.generate_highly_symmetric_tests)
        ]

        for category_name, generator in test_generators:
            print(f"\nGenerating {category_name} tests...")
            try:
                generator()
                print(f"✓ {category_name} completed")
            except Exception as e:
                print(f"✗ {category_name} failed: {e}")

        # Print results
        self.print_results()
        return self.analyze_results()

    def print_results(self):
        """Print test results."""
        print("\n" + "=" * 80)
        print("HARD INSTANCES RESULTS")
        print("=" * 80)

        categories = defaultdict(list)
        for result in self.test_results:
            categories[result['category']].append(result)

        for category in sorted(categories.keys()):
            results = categories[category]
            passed = sum(1 for r in results if r['correct'])
            total = len(results)

            print(f"\n{category.upper()}: {passed}/{total} passed ({passed/total*100:.1f}%)")
            print("-" * 60)

            for result in results:
                status = "✅ PASS" if result['correct'] else "❌ FAIL"
                iso_str = "ISO" if result['isomorphic'] else "NON-ISO"
                match_str = "MATCH" if result['fingerprint_match'] else "NO-MATCH"
                print(f"  {result['name']:<35} | {iso_str:<8} | {match_str:<8} | {status}")

    def analyze_results(self):
        """Analyze results."""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r['correct'])

        print(f"\n" + "=" * 80)
        print(f"HARD INSTANCES SUMMARY: {passed_tests}/{total_tests} passed ({passed_tests/total_tests*100:.1f}%)")
        print("=" * 80)

        return {
            'total': total_tests,
            'passed': passed_tests,
            'rate': passed_tests/total_tests if total_tests > 0 else 0
        }


def main():
    """Main test runner."""
    suite = HardInstanceTests()
    results = suite.run_all_hard_tests()

    if results['rate'] < 0.8:
        print(f"\n⚠️  Warning: Success rate below 80% on hard instances ({results['rate']*100:.1f}%)")
        print("This indicates potential weaknesses in the gossip algorithm.")
    else:
        print(f"\n🎉 Good performance on hard instances: {results['rate']*100:.1f}%")

    return results


if __name__ == "__main__":
    main()
