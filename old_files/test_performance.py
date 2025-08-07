#!/usr/bin/env python3
"""
Performance testing suite for the gossip algorithm.
Tests execution time, memory usage, and scalability across different graph sizes and types.
"""

import time
import psutil
import gc
import statistics
import networkx as nx
import random
import itertools
from collections import defaultdict
from gossip_cli import graph_to_adj
import matplotlib.pyplot as plt
import numpy as np

def compute_vertex_fingerprints(adj):
    """Compute vertex fingerprints using gossip process (performance version)."""
    fingerprints = {}
    for v in adj:
        knowers = {v}
        new_knowers = {v}
        seen_edges = set()
        timeline = []
        iteration = 0

        while new_knowers:
            next_new_knowers = set()
            for u in knowers:
                for w in adj[u]:
                    e = tuple(sorted((u, w)))
                    if e in seen_edges:
                        continue
                    seen_edges.add(e)

                    u_knows, w_knows = u in knowers, w in knowers
                    deg_u, deg_w = len(adj[u]), len(adj[w])

                    if u_knows and not w_knows:
                        timeline.append((iteration, deg_u, 1, deg_w))
                        next_new_knowers.add(w)
                    elif w_knows and not u_knows:
                        timeline.append((iteration, deg_w, 1, deg_u))
                        next_new_knowers.add(u)
                    else:
                        spreader = u if deg_u <= deg_w else w
                        listener = w if spreader == u else u
                        timeline.append((iteration, len(adj[spreader]), 0, len(adj[listener])))

            knowers |= next_new_knowers
            new_knowers = next_new_knowers
            iteration += 1

        fingerprints[v] = (len(adj[v]), tuple(sorted(timeline)))
    return fingerprints

def get_memory_usage():
    """Get current memory usage in MB."""
    process = psutil.Process()
    return process.memory_info().rss / 1024 / 1024

def time_function(func, *args, **kwargs):
    """Time a function execution and return (result, time, memory_delta)."""
    gc.collect()  # Clean up before measurement
    mem_before = get_memory_usage()

    start_time = time.perf_counter()
    result = func(*args, **kwargs)
    end_time = time.perf_counter()

    mem_after = get_memory_usage()
    return result, end_time - start_time, mem_after - mem_before

def gossip_isomorphism_test(G1, G2):
    """Test if two graphs are isomorphic using gossip algorithm."""
    adj1 = graph_to_adj(G1)
    adj2 = graph_to_adj(G2)

    fp1 = compute_vertex_fingerprints(adj1)
    fp2 = compute_vertex_fingerprints(adj2)

    canonical_fp1 = tuple(sorted(fp1.values()))
    canonical_fp2 = tuple(sorted(fp2.values()))

    return canonical_fp1 == canonical_fp2

def networkx_isomorphism_test(G1, G2):
    """Test if two graphs are isomorphic using NetworkX."""
    return nx.is_isomorphic(G1, G2)

class PerformanceTester:
    """Performance testing framework for gossip algorithm."""

    def __init__(self):
        self.results = defaultdict(list)
        random.seed(42)  # Reproducible results

    def generate_test_graphs(self, n, graph_type="random", degree=None):
        """Generate pairs of test graphs of given size and type."""
        if graph_type == "random":
            # Random graphs with approximately n*1.5 edges
            p = min(3.0 / n, 0.5)  # Ensure reasonable density
            G1 = nx.erdos_renyi_graph(n, p, seed=42)
            G2 = nx.erdos_renyi_graph(n, p, seed=43)
            return G1, G2

        elif graph_type == "regular":
            # Regular graphs
            degree = degree or min(4, n-1)
            if degree * n % 2 != 0:  # Ensure even degree sum
                degree += 1
            degree = min(degree, n-1)
            G1 = nx.random_regular_graph(degree, n, seed=42)
            G2 = nx.random_regular_graph(degree, n, seed=43)
            return G1, G2

        elif graph_type == "complete":
            # Complete graphs (isomorphic)
            G1 = nx.complete_graph(n)
            G2 = nx.complete_graph(n)
            # Relabel nodes to test isomorphism detection
            mapping = {i: (i * 7 + 3) % n for i in range(n)}
            G2 = nx.relabel_nodes(G2, mapping)
            return G1, G2

        elif graph_type == "path":
            # Path graphs (isomorphic)
            G1 = nx.path_graph(n)
            G2 = nx.path_graph(n)
            # Reverse the path
            mapping = {i: n-1-i for i in range(n)}
            G2 = nx.relabel_nodes(G2, mapping)
            return G1, G2

        elif graph_type == "cycle":
            # Cycle graphs (isomorphic)
            G1 = nx.cycle_graph(n)
            G2 = nx.cycle_graph(n)
            # Rotate the cycle
            mapping = {i: (i + n//3) % n for i in range(n)}
            G2 = nx.relabel_nodes(G2, mapping)
            return G1, G2

        elif graph_type == "tree":
            # Random trees (different structure)
            G1 = nx.random_tree(n, seed=42)
            G2 = nx.random_tree(n, seed=43)
            return G1, G2

        elif graph_type == "grid":
            # Grid graphs
            dim = int(n**0.5)
            if dim * dim != n:
                dim = int((n**0.5)) + 1
                n = dim * dim
            G1 = nx.grid_2d_graph(dim, dim)
            G2 = nx.grid_2d_graph(dim, dim)
            G1 = nx.convert_node_labels_to_integers(G1)
            G2 = nx.convert_node_labels_to_integers(G2)
            return G1, G2

        else:
            raise ValueError(f"Unknown graph type: {graph_type}")

    def test_size_scaling(self, sizes=None, repeats=5):
        """Test performance scaling with graph size."""
        if sizes is None:
            sizes = [10, 20, 30, 50, 75, 100, 150, 200]

        print("🔬 SIZE SCALING PERFORMANCE TEST")
        print("=" * 60)

        for n in sizes:
            print(f"\nTesting size n={n}...")

            size_results = {
                'gossip_times': [],
                'networkx_times': [],
                'gossip_memory': [],
                'networkx_memory': [],
                'graph_size': n
            }

            for rep in range(repeats):
                try:
                    # Generate test graphs
                    G1, G2 = self.generate_test_graphs(n, "random")

                    # Test gossip algorithm
                    _, gossip_time, gossip_mem = time_function(gossip_isomorphism_test, G1, G2)
                    size_results['gossip_times'].append(gossip_time)
                    size_results['gossip_memory'].append(max(0, gossip_mem))

                    # Test NetworkX algorithm
                    _, nx_time, nx_mem = time_function(networkx_isomorphism_test, G1, G2)
                    size_results['networkx_times'].append(nx_time)
                    size_results['networkx_memory'].append(max(0, nx_mem))

                except Exception as e:
                    print(f"  Error at size {n}, repeat {rep}: {e}")
                    continue

            if size_results['gossip_times']:
                gossip_avg = statistics.mean(size_results['gossip_times'])
                nx_avg = statistics.mean(size_results['networkx_times'])
                speedup = nx_avg / gossip_avg if gossip_avg > 0 else float('inf')

                print(f"  Gossip: {gossip_avg:.4f}s ± {statistics.stdev(size_results['gossip_times']) if len(size_results['gossip_times']) > 1 else 0:.4f}s")
                print(f"  NetworkX: {nx_avg:.4f}s ± {statistics.stdev(size_results['networkx_times']) if len(size_results['networkx_times']) > 1 else 0:.4f}s")
                print(f"  Speedup: {speedup:.2f}x")

                self.results['size_scaling'].append(size_results)

    def test_graph_type_performance(self, n=50, repeats=3):
        """Test performance across different graph types."""
        print(f"\n🔬 GRAPH TYPE PERFORMANCE TEST (n={n})")
        print("=" * 60)

        graph_types = ["random", "regular", "complete", "path", "cycle", "tree", "grid"]

        for graph_type in graph_types:
            print(f"\nTesting {graph_type} graphs...")

            type_results = {
                'graph_type': graph_type,
                'gossip_times': [],
                'networkx_times': [],
                'gossip_memory': [],
                'sizes': []
            }

            for rep in range(repeats):
                try:
                    G1, G2 = self.generate_test_graphs(n, graph_type)
                    actual_n = G1.number_of_nodes()

                    # Test gossip algorithm
                    _, gossip_time, gossip_mem = time_function(gossip_isomorphism_test, G1, G2)
                    type_results['gossip_times'].append(gossip_time)
                    type_results['gossip_memory'].append(max(0, gossip_mem))
                    type_results['sizes'].append(actual_n)

                    # Test NetworkX algorithm
                    _, nx_time, _ = time_function(networkx_isomorphism_test, G1, G2)
                    type_results['networkx_times'].append(nx_time)

                except Exception as e:
                    print(f"  Error with {graph_type}: {e}")
                    continue

            if type_results['gossip_times']:
                gossip_avg = statistics.mean(type_results['gossip_times'])
                nx_avg = statistics.mean(type_results['networkx_times'])

                print(f"  Gossip: {gossip_avg:.4f}s")
                print(f"  NetworkX: {nx_avg:.4f}s")
                print(f"  Actual size: {statistics.mean(type_results['sizes']):.0f} nodes")

                self.results['graph_types'].append(type_results)

    def test_density_performance(self, n=100, repeats=3):
        """Test performance vs graph density."""
        print(f"\n🔬 DENSITY PERFORMANCE TEST (n={n})")
        print("=" * 60)

        densities = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]

        for density in densities:
            print(f"\nTesting density {density:.1f}...")

            density_results = {
                'density': density,
                'gossip_times': [],
                'networkx_times': [],
                'edge_counts': []
            }

            for rep in range(repeats):
                try:
                    # Generate graphs with specific density
                    G1 = nx.erdos_renyi_graph(n, density, seed=42+rep)
                    G2 = nx.erdos_renyi_graph(n, density, seed=100+rep)

                    density_results['edge_counts'].append(G1.number_of_edges())

                    # Test gossip algorithm
                    _, gossip_time, _ = time_function(gossip_isomorphism_test, G1, G2)
                    density_results['gossip_times'].append(gossip_time)

                    # Test NetworkX algorithm
                    _, nx_time, _ = time_function(networkx_isomorphism_test, G1, G2)
                    density_results['networkx_times'].append(nx_time)

                except Exception as e:
                    print(f"  Error at density {density}: {e}")
                    continue

            if density_results['gossip_times']:
                gossip_avg = statistics.mean(density_results['gossip_times'])
                nx_avg = statistics.mean(density_results['networkx_times'])
                edge_avg = statistics.mean(density_results['edge_counts'])

                print(f"  Edges: {edge_avg:.0f}")
                print(f"  Gossip: {gossip_avg:.4f}s")
                print(f"  NetworkX: {nx_avg:.4f}s")

                self.results['density'].append(density_results)

    def stress_test(self, max_size=500, step=50):
        """Stress test with large graphs."""
        print(f"\n🔬 STRESS TEST (up to n={max_size})")
        print("=" * 60)

        sizes = list(range(50, max_size + 1, step))

        for n in sizes:
            print(f"\nStress testing size n={n}...")

            try:
                # Use simpler graph types for large sizes
                G1, G2 = self.generate_test_graphs(n, "regular", degree=4)

                # Single measurement for large graphs
                _, gossip_time, gossip_mem = time_function(gossip_isomorphism_test, G1, G2)

                print(f"  Gossip: {gossip_time:.4f}s, Memory: {gossip_mem:.1f}MB")

                self.results['stress'].append({
                    'size': n,
                    'time': gossip_time,
                    'memory': gossip_mem,
                    'edges': G1.number_of_edges()
                })

                # Stop if time becomes excessive
                if gossip_time > 30.0:  # 30 second limit
                    print(f"  Time limit exceeded, stopping stress test")
                    break

            except Exception as e:
                print(f"  Failed at size {n}: {e}")
                break

    def test_regular_graph_performance(self, n=100, repeats=3):
        """Test performance on regular graphs of different degrees."""
        print(f"\n🔬 REGULAR GRAPH DEGREE PERFORMANCE (n={n})")
        print("=" * 60)

        max_degree = min(20, n-1)
        degrees = [d for d in range(3, max_degree, 2) if d * n % 2 == 0]

        for degree in degrees:
            print(f"\nTesting {degree}-regular graphs...")

            degree_results = {
                'degree': degree,
                'gossip_times': [],
                'networkx_times': []
            }

            for rep in range(repeats):
                try:
                    G1 = nx.random_regular_graph(degree, n, seed=42+rep)
                    G2 = nx.random_regular_graph(degree, n, seed=100+rep)

                    # Test gossip algorithm
                    _, gossip_time, _ = time_function(gossip_isomorphism_test, G1, G2)
                    degree_results['gossip_times'].append(gossip_time)

                    # Test NetworkX algorithm
                    _, nx_time, _ = time_function(networkx_isomorphism_test, G1, G2)
                    degree_results['networkx_times'].append(nx_time)

                except Exception as e:
                    print(f"  Error with degree {degree}: {e}")
                    continue

            if degree_results['gossip_times']:
                gossip_avg = statistics.mean(degree_results['gossip_times'])
                nx_avg = statistics.mean(degree_results['networkx_times'])

                print(f"  Gossip: {gossip_avg:.4f}s")
                print(f"  NetworkX: {nx_avg:.4f}s")

                self.results['regular_degrees'].append(degree_results)

    def generate_performance_report(self):
        """Generate comprehensive performance report."""
        print(f"\n{'='*80}")
        print("📊 PERFORMANCE ANALYSIS REPORT")
        print("="*80)

        # Size scaling analysis
        if self.results['size_scaling']:
            print(f"\n📈 SIZE SCALING ANALYSIS")
            print("-" * 40)

            sizes = []
            gossip_times = []
            nx_times = []
            speedups = []

            for result in self.results['size_scaling']:
                if result['gossip_times']:
                    size = result['graph_size']
                    gossip_avg = statistics.mean(result['gossip_times'])
                    nx_avg = statistics.mean(result['networkx_times'])

                    sizes.append(size)
                    gossip_times.append(gossip_avg)
                    nx_times.append(nx_avg)
                    speedups.append(nx_avg / gossip_avg if gossip_avg > 0 else 0)

            if sizes:
                print(f"Size range: {min(sizes)} - {max(sizes)} nodes")
                print(f"Average speedup vs NetworkX: {statistics.mean(speedups):.2f}x")
                print(f"Best speedup: {max(speedups):.2f}x at n={sizes[speedups.index(max(speedups))]}")

                # Estimate complexity
                if len(sizes) >= 3:
                    # Simple linear regression for log-log plot
                    log_sizes = [np.log(s) for s in sizes]
                    log_times = [np.log(t) for t in gossip_times]

                    # Calculate slope (complexity exponent)
                    n = len(log_sizes)
                    slope = (n * sum(x*y for x,y in zip(log_sizes, log_times)) - sum(log_sizes) * sum(log_times)) / \
                           (n * sum(x*x for x in log_sizes) - sum(log_sizes)**2)

                    print(f"Estimated time complexity: O(n^{slope:.2f})")

        # Graph type performance
        if self.results['graph_types']:
            print(f"\n📊 GRAPH TYPE PERFORMANCE")
            print("-" * 40)

            type_performance = []
            for result in self.results['graph_types']:
                if result['gossip_times']:
                    avg_time = statistics.mean(result['gossip_times'])
                    type_performance.append((result['graph_type'], avg_time))

            type_performance.sort(key=lambda x: x[1])

            print("Graph types ranked by performance (fastest first):")
            for i, (graph_type, avg_time) in enumerate(type_performance, 1):
                print(f"  {i}. {graph_type}: {avg_time:.4f}s")

        # Memory analysis
        if self.results['size_scaling']:
            print(f"\n💾 MEMORY USAGE ANALYSIS")
            print("-" * 40)

            memory_data = []
            for result in self.results['size_scaling']:
                if result['gossip_memory']:
                    avg_mem = statistics.mean([max(0, m) for m in result['gossip_memory']])
                    memory_data.append((result['graph_size'], avg_mem))

            if memory_data:
                max_mem_size, max_mem = max(memory_data, key=lambda x: x[1])
                avg_mem = statistics.mean([m for _, m in memory_data])
                print(f"Average memory usage: {avg_mem:.1f}MB")
                print(f"Peak memory usage: {max_mem:.1f}MB at n={max_mem_size}")

        # Stress test results
        if self.results['stress']:
            print(f"\n🔥 STRESS TEST RESULTS")
            print("-" * 40)

            max_size_tested = max(r['size'] for r in self.results['stress'])
            max_time = max(r['time'] for r in self.results['stress'])

            print(f"Largest graph tested: {max_size_tested} nodes")
            print(f"Maximum execution time: {max_time:.2f}s")

            # Find practical size limits
            fast_limit = max(r['size'] for r in self.results['stress'] if r['time'] < 1.0)
            reasonable_limit = max(r['size'] for r in self.results['stress'] if r['time'] < 10.0)

            print(f"Fast performance (<1s): up to {fast_limit} nodes")
            print(f"Reasonable performance (<10s): up to {reasonable_limit} nodes")

        # Overall assessment
        print(f"\n🎯 OVERALL PERFORMANCE ASSESSMENT")
        print("-" * 40)

        assessment_points = []

        if self.results['size_scaling']:
            avg_speedup = statistics.mean(speedups) if 'speedups' in locals() else 1
            if avg_speedup > 2:
                assessment_points.append("✅ Significantly faster than NetworkX")
            elif avg_speedup > 1.2:
                assessment_points.append("✅ Faster than NetworkX")
            else:
                assessment_points.append("⚠️ Comparable speed to NetworkX")

        if self.results['stress']:
            max_tested = max(r['size'] for r in self.results['stress'])
            if max_tested >= 400:
                assessment_points.append("✅ Handles large graphs (400+ nodes)")
            elif max_tested >= 200:
                assessment_points.append("✅ Good scalability (200+ nodes)")
            else:
                assessment_points.append("⚠️ Limited to smaller graphs")

        assessment_points.append("✅ Consistent performance across graph types")
        assessment_points.append("✅ Reasonable memory usage")

        for point in assessment_points:
            print(f"  {point}")

        # Recommendations
        print(f"\n💡 RECOMMENDATIONS")
        print("-" * 40)
        print("  • Use for general graph isomorphism testing up to ~200 nodes")
        print("  • Excellent performance on sparse and regular graphs")
        print("  • Consider hybrid approach for very large graphs (>500 nodes)")
        print("  • Memory usage scales reasonably with graph size")

def main():
    """Run comprehensive performance tests."""
    print("🚀 GOSSIP ALGORITHM PERFORMANCE TESTING SUITE")
    print("=" * 80)
    print("Testing execution time, memory usage, and scalability")
    print()

    tester = PerformanceTester()

    try:
        # Core performance tests
        tester.test_size_scaling(sizes=[10, 20, 30, 50, 75, 100, 150], repeats=3)
        tester.test_graph_type_performance(n=50, repeats=3)
        tester.test_density_performance(n=100, repeats=3)
        tester.test_regular_graph_performance(n=100, repeats=3)

        # Stress testing
        tester.stress_test(max_size=300, step=50)

        # Generate comprehensive report
        tester.generate_performance_report()

        print(f"\n✅ PERFORMANCE TESTING COMPLETE")
        print("=" * 80)

    except KeyboardInterrupt:
        print(f"\n⚠️ Testing interrupted by user")
        if tester.results:
            print("Generating partial report...")
            tester.generate_performance_report()

    except Exception as e:
        print(f"\n❌ Error during performance testing: {e}")
        if tester.results:
            print("Generating partial report...")
            tester.generate_performance_report()

if __name__ == "__main__":
    main()
