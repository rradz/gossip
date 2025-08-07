#!/usr/bin/env python3
"""
Validation script for the gossip graph isomorphism algorithm.

This script runs a comprehensive test suite to validate that:
1. The algorithm works correctly on basic graph types
2. Performance is acceptable
3. Hard instances are handled properly
4. The implementation matches expected behavior
"""

import sys
import time
import traceback
from typing import List, Tuple, Dict, Any

import networkx as nx
import numpy as np

# Add src to path if running from project root
sys.path.insert(0, 'src')

from gossip import GossipFingerprint, graph_to_adjacency_list
from gossip.utils import (
    generate_random_regular_graph,
    generate_cfi_pair,
    generate_strongly_regular_graph,
    generate_miyazaki_graph,
    relabel_graph,
    are_isomorphic,
)


class ValidationSuite:
    """Comprehensive validation suite for the gossip algorithm."""

    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.gf = GossipFingerprint()
        self.results = []
        self.passed = 0
        self.failed = 0

    def log(self, message: str):
        """Print a message if verbose mode is enabled."""
        if self.verbose:
            print(message)

    def test(self, name: str, condition: bool, details: str = ""):
        """Record a test result."""
        if condition:
            self.passed += 1
            status = "PASS"
        else:
            self.failed += 1
            status = "FAIL"

        self.results.append({
            'name': name,
            'passed': condition,
            'details': details
        })

        self.log(f"  [{status}] {name}")
        if details and not condition:
            self.log(f"        {details}")

    def run_basic_tests(self):
        """Test basic graph types."""
        self.log("\n=== Basic Graph Tests ===")

        # Empty graph
        G_empty = nx.Graph()
        adj = graph_to_adjacency_list(G_empty)
        fp = self.gf.compute(adj)
        self.test("Empty graph", fp == ())

        # Single vertex
        G_single = nx.Graph()
        G_single.add_node(0)
        adj = graph_to_adjacency_list(G_single)
        fp = self.gf.compute(adj)
        self.test("Single vertex", len(fp) == 1 and fp[0][0] == 0)

        # Path graph
        G_path = nx.path_graph(5)
        adj = graph_to_adjacency_list(G_path)
        fp = self.gf.compute(adj)
        degrees = sorted([f[0] for f in fp])
        self.test("Path graph degrees", degrees == [1, 1, 2, 2, 2])

        # Cycle graph
        G_cycle = nx.cycle_graph(6)
        adj = graph_to_adjacency_list(G_cycle)
        fp = self.gf.compute(adj)
        unique_fps = len(set(fp))
        self.test("Cycle graph symmetry", unique_fps == 1)

        # Complete graph
        G_complete = nx.complete_graph(5)
        adj = graph_to_adjacency_list(G_complete)
        fp = self.gf.compute(adj)
        unique_fps = len(set(fp))
        self.test("Complete graph symmetry", unique_fps == 1)

        # Star graph
        G_star = nx.star_graph(4)
        adj = graph_to_adjacency_list(G_star)
        fp = self.gf.compute(adj)
        degrees = sorted([f[0] for f in fp])
        self.test("Star graph degrees", degrees == [1, 1, 1, 1, 4])

    def run_isomorphism_tests(self):
        """Test isomorphism detection."""
        self.log("\n=== Isomorphism Tests ===")

        # Isomorphic graphs (relabeling)
        G1 = nx.petersen_graph()
        G2 = relabel_graph(G1, seed=42)

        gossip_match = self.gf.compare(G1, G2)
        nx_iso = are_isomorphic(G1, G2)
        self.test(
            "Petersen graph relabeling",
            gossip_match == nx_iso == True,
            f"Gossip: {gossip_match}, NetworkX: {nx_iso}"
        )

        # Non-isomorphic graphs
        G3 = nx.cycle_graph(10)
        G4 = nx.complete_graph(10)

        gossip_match = self.gf.compare(G3, G4)
        nx_iso = are_isomorphic(G3, G4)
        self.test(
            "Cycle vs Complete",
            gossip_match == nx_iso == False,
            f"Gossip: {gossip_match}, NetworkX: {nx_iso}"
        )

        # Regular graphs
        G5 = nx.random_regular_graph(3, 10, seed=42)
        G6 = nx.random_regular_graph(3, 10, seed=43)

        gossip_match = self.gf.compare(G5, G6)
        nx_iso = are_isomorphic(G5, G6)
        self.test(
            "Random regular graphs",
            gossip_match == nx_iso,
            f"Gossip: {gossip_match}, NetworkX: {nx_iso}"
        )

        # Tree isomorphism
        T1 = nx.balanced_tree(2, 3)
        T2 = relabel_graph(T1, seed=99)

        gossip_match = self.gf.compare(T1, T2)
        nx_iso = are_isomorphic(T1, T2)
        self.test(
            "Balanced tree relabeling",
            gossip_match == nx_iso == True,
            f"Gossip: {gossip_match}, NetworkX: {nx_iso}"
        )

    def run_hard_instance_tests(self):
        """Test hard instances."""
        self.log("\n=== Hard Instance Tests ===")

        # CFI graphs
        try:
            base = nx.cycle_graph(6)
            edges = list(base.edges())
            if edges:
                flip_edges = {edges[0]}
                G1, G2 = generate_cfi_pair(base, flip_edges)

                gossip_match = self.gf.compare(G1, G2)
                nx_iso = are_isomorphic(G1, G2)

                self.test(
                    "CFI graphs",
                    gossip_match == nx_iso,
                    f"Gossip: {gossip_match}, NetworkX: {nx_iso}"
                )
        except Exception as e:
            self.test("CFI graphs", False, str(e))

        # Strongly regular graph
        try:
            srg = generate_strongly_regular_graph(16, 6, 2, 2)
            if srg:
                srg2 = relabel_graph(srg, seed=42)

                gossip_match = self.gf.compare(srg, srg2)
                nx_iso = are_isomorphic(srg, srg2)

                self.test(
                    "SRG(16,6,2,2)",
                    gossip_match == nx_iso == True,
                    f"Gossip: {gossip_match}, NetworkX: {nx_iso}"
                )
            else:
                self.test("SRG(16,6,2,2)", False, "Could not generate SRG")
        except Exception as e:
            self.test("SRG(16,6,2,2)", False, str(e))

        # Miyazaki graph
        try:
            miya = generate_miyazaki_graph(8)
            miya2 = relabel_graph(miya, seed=42)

            gossip_match = self.gf.compare(miya, miya2)
            nx_iso = are_isomorphic(miya, miya2)

            self.test(
                "Miyazaki graph",
                gossip_match == nx_iso == True,
                f"Gossip: {gossip_match}, NetworkX: {nx_iso}"
            )
        except Exception as e:
            self.test("Miyazaki graph", False, str(e))

    def run_performance_tests(self):
        """Test performance characteristics."""
        self.log("\n=== Performance Tests ===")

        # Small graphs
        sizes = [10, 20, 50, 100]
        times = []

        for n in sizes:
            G = nx.random_regular_graph(3, n, seed=42)
            adj = graph_to_adjacency_list(G)

            start = time.perf_counter()
            fp = self.gf.compute(adj)
            elapsed = time.perf_counter() - start
            times.append(elapsed)

            self.test(
                f"Regular graph n={n}",
                elapsed < 1.0,  # Should complete in under 1 second
                f"Time: {elapsed:.4f}s"
            )

        # Check scaling
        if len(times) >= 2:
            # Time should not grow too fast
            scaling_ok = all(
                times[i] < times[i-1] * 10  # Allow 10x growth
                for i in range(1, len(times))
            )
            self.test("Performance scaling", scaling_ok,
                     f"Times: {[f'{t:.4f}' for t in times]}")

    def run_correctness_tests(self):
        """Test algorithm correctness on known cases."""
        self.log("\n=== Correctness Tests ===")

        test_cases = [
            # (Graph1, Graph2, expected_isomorphic)
            (nx.complete_graph(4), nx.complete_graph(4), True),
            (nx.complete_graph(4), nx.complete_graph(5), False),
            (nx.cycle_graph(6), nx.cycle_graph(6), True),
            (nx.path_graph(5), nx.star_graph(4), False),
            (nx.complete_bipartite_graph(3, 3),
             nx.complete_bipartite_graph(3, 3), True),
            (nx.complete_bipartite_graph(3, 3),
             nx.complete_bipartite_graph(2, 4), False),
        ]

        for i, (G1, G2, expected) in enumerate(test_cases):
            # Relabel G2 for true test
            if expected:
                G2 = relabel_graph(G2, seed=i)

            gossip_match = self.gf.compare(G1, G2)
            nx_iso = are_isomorphic(G1, G2)

            self.test(
                f"Case {i+1}: {G1.number_of_nodes()}v vs {G2.number_of_nodes()}v",
                gossip_match == nx_iso == expected,
                f"Gossip: {gossip_match}, NetworkX: {nx_iso}, Expected: {expected}"
            )

    def run_edge_case_tests(self):
        """Test edge cases and special graphs."""
        self.log("\n=== Edge Case Tests ===")

        # Disconnected graph
        G_disc = nx.Graph()
        G_disc.add_edges_from([(0, 1), (2, 3)])
        adj = graph_to_adjacency_list(G_disc)
        fp = self.gf.compute(adj)
        self.test("Disconnected graph", len(fp) == 4)

        # Self-loops
        G_loop = nx.Graph()
        G_loop.add_edges_from([(0, 1), (1, 2), (0, 0)])
        adj = graph_to_adjacency_list(G_loop)
        try:
            fp = self.gf.compute(adj)
            self.test("Self-loops", fp is not None)
        except:
            self.test("Self-loops", False, "Exception raised")

        # Hypercube
        H3 = nx.hypercube_graph(3)
        adj = graph_to_adjacency_list(H3)
        fp = self.gf.compute(adj)
        unique_fps = len(set(fp))
        self.test("Hypercube symmetry", unique_fps == 1)

    def run_all(self):
        """Run all validation tests."""
        self.log("=" * 60)
        self.log("GOSSIP ALGORITHM VALIDATION SUITE")
        self.log("=" * 60)

        try:
            self.run_basic_tests()
            self.run_isomorphism_tests()
            self.run_hard_instance_tests()
            self.run_performance_tests()
            self.run_correctness_tests()
            self.run_edge_case_tests()
        except Exception as e:
            self.log(f"\nFATAL ERROR: {e}")
            traceback.print_exc()
            return False

        self.log("\n" + "=" * 60)
        self.log("VALIDATION SUMMARY")
        self.log("=" * 60)
        self.log(f"Tests Passed: {self.passed}")
        self.log(f"Tests Failed: {self.failed}")
        self.log(f"Total Tests:  {self.passed + self.failed}")
        self.log(f"Success Rate: {100 * self.passed / (self.passed + self.failed):.1f}%")

        if self.failed > 0:
            self.log("\nFailed Tests:")
            for result in self.results:
                if not result['passed']:
                    self.log(f"  - {result['name']}")
                    if result['details']:
                        self.log(f"    {result['details']}")

        return self.failed == 0


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Validate gossip algorithm implementation")
    parser.add_argument("--quiet", "-q", action="store_true", help="Minimal output")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    validator = ValidationSuite(verbose=not args.quiet)
    success = validator.run_all()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
