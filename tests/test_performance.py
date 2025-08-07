"""
Performance benchmarks for the gossip graph isomorphism algorithm.
"""

import pytest
import networkx as nx
import numpy as np
import time
from typing import Dict, List, Tuple, Any
import statistics

from gossip.algorithm import GossipFingerprint, gossip_fingerprint
from gossip.utils import (
    graph_to_adjacency_list,
    generate_random_regular_graph,
    generate_cfi_pair,
    generate_strongly_regular_graph,
    generate_circulant_graph,
    generate_miyazaki_graph,
    are_isomorphic,
    relabel_graph,
)


class TestPerformanceBasic:
    """Basic performance benchmarks."""

    def test_scalability_by_nodes(self):
        """Test how runtime scales with number of nodes."""
        gf = GossipFingerprint()
        results = []

        node_counts = [10, 20, 50, 100, 200, 500]
        edge_prob = 0.3

        for n in node_counts:
            G = nx.erdos_renyi_graph(n, edge_prob, seed=42)
            adj = graph_to_adjacency_list(G)

            # Run multiple times for stability
            times = []
            for _ in range(3):
                start = time.perf_counter()
                fp = gf.compute(adj)
                elapsed = time.perf_counter() - start
                times.append(elapsed)

            avg_time = statistics.mean(times)
            results.append({
                'nodes': n,
                'edges': G.number_of_edges(),
                'time': avg_time,
                'time_per_node': avg_time / n,
                'time_per_edge': avg_time / max(1, G.number_of_edges())
            })

        # Check that time increases with size
        for i in range(1, len(results)):
            assert results[i]['time'] >= results[i-1]['time'] * 0.5

        # Print results for analysis
        print("\nScalability by nodes:")
        print("Nodes | Edges | Time (s) | Time/Node | Time/Edge")
        for r in results:
            print(f"{r['nodes']:5} | {r['edges']:5} | {r['time']:.6f} | "
                  f"{r['time_per_node']:.6f} | {r['time_per_edge']:.6f}")

    def test_scalability_by_density(self):
        """Test how runtime scales with graph density."""
        gf = GossipFingerprint()
        n = 50
        results = []

        densities = [0.1, 0.2, 0.3, 0.5, 0.7, 0.9]

        for density in densities:
            G = nx.erdos_renyi_graph(n, density, seed=42)
            adj = graph_to_adjacency_list(G)

            times = []
            for _ in range(3):
                start = time.perf_counter()
                fp = gf.compute(adj)
                elapsed = time.perf_counter() - start
                times.append(elapsed)

            avg_time = statistics.mean(times)
            results.append({
                'density': density,
                'edges': G.number_of_edges(),
                'time': avg_time
            })

        print("\nScalability by density (n=50):")
        print("Density | Edges | Time (s)")
        for r in results:
            print(f"{r['density']:.1f}    | {r['edges']:5} | {r['time']:.6f}")

    def test_regular_vs_irregular_graphs(self):
        """Compare performance on regular vs irregular graphs."""
        gf = GossipFingerprint()
        sizes = [20, 50, 100]
        results = []

        for n in sizes:
            # Regular graph (3-regular if possible)
            if (n * 3) % 2 == 0:
                regular_g = nx.random_regular_graph(3, n, seed=42)
            else:
                regular_g = nx.random_regular_graph(4, n, seed=42)

            # Irregular graph with similar edge count
            p = 6.0 / n  # Approximately same number of edges
            irregular_g = nx.erdos_renyi_graph(n, p, seed=42)

            # Measure regular graph
            adj_reg = graph_to_adjacency_list(regular_g)
            start = time.perf_counter()
            fp_reg = gf.compute(adj_reg)
            time_reg = time.perf_counter() - start

            # Measure irregular graph
            adj_irreg = graph_to_adjacency_list(irregular_g)
            start = time.perf_counter()
            fp_irreg = gf.compute(adj_irreg)
            time_irreg = time.perf_counter() - start

            results.append({
                'n': n,
                'regular_time': time_reg,
                'irregular_time': time_irreg,
                'ratio': time_reg / time_irreg if time_irreg > 0 else float('inf')
            })

        print("\nRegular vs Irregular graphs:")
        print("Nodes | Regular (s) | Irregular (s) | Ratio")
        for r in results:
            print(f"{r['n']:5} | {r['regular_time']:.6f}   | "
                  f"{r['irregular_time']:.6f}     | {r['ratio']:.2f}")


@pytest.mark.benchmark
class TestPerformanceComparison:
    """Compare gossip performance with NetworkX isomorphism."""

    def test_comparison_small_graphs(self):
        """Compare with NetworkX on small graphs."""
        gf = GossipFingerprint()
        results = []

        test_cases = [
            ("complete", nx.complete_graph(10)),
            ("cycle", nx.cycle_graph(20)),
            ("path", nx.path_graph(30)),
            ("star", nx.star_graph(15)),
            ("petersen", nx.petersen_graph()),
            ("regular", nx.random_regular_graph(4, 20, seed=42)),
            ("tree", nx.random_labeled_tree(25, seed=42)),
            ("grid", nx.grid_2d_graph(5, 5))
        ]

        for name, G in test_cases:
            G2 = relabel_graph(G, seed=99)

            # Time gossip
            start = time.perf_counter()
            gossip_result = gf.compare(G, G2)
            gossip_time = time.perf_counter() - start

            # Time NetworkX
            start = time.perf_counter()
            nx_result = nx.is_isomorphic(G, G2)
            nx_time = time.perf_counter() - start

            assert gossip_result == nx_result, f"Results differ for {name}"

            results.append({
                'graph': name,
                'nodes': G.number_of_nodes(),
                'edges': G.number_of_edges(),
                'gossip_time': gossip_time,
                'nx_time': nx_time,
                'speedup': nx_time / gossip_time if gossip_time > 0 else float('inf')
            })

        print("\nComparison with NetworkX:")
        print("Graph      | Nodes | Edges | Gossip (s) | NetworkX (s) | Speedup")
        for r in results:
            print(f"{r['graph']:<10} | {r['nodes']:5} | {r['edges']:5} | "
                  f"{r['gossip_time']:.6f}  | {r['nx_time']:.6f}    | "
                  f"{r['speedup']:.2f}x")

    def test_comparison_hard_instances(self):
        """Compare performance on hard instances."""
        gf = GossipFingerprint()
        results = []

        # CFI graphs
        base = nx.cycle_graph(6)
        G1_cfi, G2_cfi = generate_cfi_pair(base)

        # SRG
        srg = generate_strongly_regular_graph(16, 6, 2, 2)
        srg2 = relabel_graph(srg, seed=42) if srg else None

        # Miyazaki
        miya = generate_miyazaki_graph(8)
        miya2 = relabel_graph(miya, seed=42)

        test_cases = [
            ("CFI", G1_cfi, G2_cfi),
            ("Miyazaki", miya, miya2),
        ]

        if srg:
            test_cases.append(("SRG(16,6,2,2)", srg, srg2))

        for name, G1, G2 in test_cases:
            # Time gossip
            start = time.perf_counter()
            gossip_result = gf.compare(G1, G2)
            gossip_time = time.perf_counter() - start

            # Time NetworkX
            start = time.perf_counter()
            nx_result = nx.is_isomorphic(G1, G2)
            nx_time = time.perf_counter() - start

            results.append({
                'instance': name,
                'nodes': G1.number_of_nodes(),
                'gossip_time': gossip_time,
                'nx_time': nx_time,
                'gossip_correct': gossip_result == nx_result
            })

        print("\nHard instances comparison:")
        print("Instance      | Nodes | Gossip (s) | NetworkX (s) | Correct")
        for r in results:
            print(f"{r['instance']:<13} | {r['nodes']:5} | "
                  f"{r['gossip_time']:.6f}  | {r['nx_time']:.6f}    | "
                  f"{'Yes' if r['gossip_correct'] else 'No'}")


@pytest.mark.slow
class TestPerformanceLarge:
    """Performance tests on large graphs."""

    def test_large_regular_graphs(self):
        """Test performance on large regular graphs."""
        gf = GossipFingerprint()
        results = []

        sizes = [100, 200, 500, 1000]
        degree = 4

        for n in sizes:
            if (n * degree) % 2 != 0:
                continue

            G = nx.random_regular_graph(degree, n, seed=42)
            adj = graph_to_adjacency_list(G)

            start = time.perf_counter()
            fp = gf.compute(adj)
            elapsed = time.perf_counter() - start

            results.append({
                'nodes': n,
                'time': elapsed,
                'time_per_node': elapsed / n
            })

        print("\nLarge regular graphs (degree=4):")
        print("Nodes | Time (s) | Time/Node")
        for r in results:
            print(f"{r['nodes']:5} | {r['time']:.6f} | {r['time_per_node']:.6f}")

        # Check scaling - should be roughly quadratic or better
        if len(results) >= 2:
            for i in range(1, len(results)):
                ratio = results[i]['nodes'] / results[i-1]['nodes']
                time_ratio = results[i]['time'] / results[i-1]['time']
                # Time should scale no worse than cubic
                assert time_ratio < ratio ** 3

    def test_large_sparse_graphs(self):
        """Test performance on large sparse graphs."""
        gf = GossipFingerprint()
        results = []

        sizes = [100, 500, 1000, 2000]

        for n in sizes:
            # Create a sparse graph (tree)
            G = nx.random_labeled_tree(n, seed=42)
            adj = graph_to_adjacency_list(G)

            start = time.perf_counter()
            fp = gf.compute(adj)
            elapsed = time.perf_counter() - start

            results.append({
                'nodes': n,
                'edges': G.number_of_edges(),
                'time': elapsed
            })

        print("\nLarge sparse graphs (trees):")
        print("Nodes | Edges | Time (s)")
        for r in results:
            print(f"{r['nodes']:5} | {r['edges']:5} | {r['time']:.6f}")


class TestMemoryEfficiency:
    """Test memory efficiency of the algorithm."""

    def test_memory_usage_scaling(self):
        """Test how memory usage scales with graph size."""
        import sys

        gf = GossipFingerprint()
        results = []

        for n in [10, 50, 100, 200]:
            G = nx.random_regular_graph(3, n, seed=42)
            adj = graph_to_adjacency_list(G)

            # Measure memory of fingerprint
            fp = gf.compute(adj)

            # Rough memory estimate
            memory = sys.getsizeof(fp)

            results.append({
                'nodes': n,
                'memory_bytes': memory,
                'memory_per_node': memory / n
            })

        print("\nMemory usage:")
        print("Nodes | Memory (bytes) | Memory/Node")
        for r in results:
            print(f"{r['nodes']:5} | {r['memory_bytes']:14} | {r['memory_per_node']:.2f}")


class TestWorstCasePerformance:
    """Test worst-case performance scenarios."""

    def test_complete_graphs(self):
        """Test performance on complete graphs (worst case for edge iteration)."""
        gf = GossipFingerprint()
        results = []

        for n in [5, 10, 15, 20, 25]:
            G = nx.complete_graph(n)
            adj = graph_to_adjacency_list(G)

            start = time.perf_counter()
            fp = gf.compute(adj)
            elapsed = time.perf_counter() - start

            results.append({
                'nodes': n,
                'edges': n * (n - 1) // 2,
                'time': elapsed
            })

        print("\nComplete graphs (worst case):")
        print("Nodes | Edges | Time (s)")
        for r in results:
            print(f"{r['nodes']:5} | {r['edges']:5} | {r['time']:.6f}")

    def test_star_graphs(self):
        """Test performance on star graphs (highly unbalanced degree)."""
        gf = GossipFingerprint()
        results = []

        for n in [10, 50, 100, 200, 500]:
            G = nx.star_graph(n - 1)  # n nodes total
            adj = graph_to_adjacency_list(G)

            start = time.perf_counter()
            fp = gf.compute(adj)
            elapsed = time.perf_counter() - start

            results.append({
                'nodes': n,
                'time': elapsed
            })

        print("\nStar graphs (unbalanced degree):")
        print("Nodes | Time (s)")
        for r in results:
            print(f"{r['nodes']:5} | {r['time']:.6f}")
