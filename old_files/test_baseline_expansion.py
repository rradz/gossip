#!/usr/bin/env python3
"""
Baseline test suite expansion for gossip algorithm.
Tests multiple graph classes to establish broader performance baseline.
"""

import networkx as nx
import random
import itertools
from gossip_cli import graph_to_adj

def compute_vertex_fingerprints(adj):
    """Compute vertex fingerprints using gossip process."""
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

def test_pair(G1, G2, name):
    """Test a pair of graphs."""
    nx_iso = nx.is_isomorphic(G1, G2)

    adj1 = graph_to_adj(G1)
    adj2 = graph_to_adj(G2)
    fp1 = compute_vertex_fingerprints(adj1)
    fp2 = compute_vertex_fingerprints(adj2)

    gossip_match = tuple(sorted(fp1.values())) == tuple(sorted(fp2.values()))

    correct = gossip_match == nx_iso
    false_pos = gossip_match and not nx_iso
    false_neg = not gossip_match and nx_iso

    return {
        'name': name,
        'n': G1.number_of_nodes(),
        'edges': G1.number_of_edges(),
        'regular': len(set(dict(G1.degree()).values())) == 1,
        'degree': list(G1.degree())[0][1] if G1.number_of_nodes() > 0 else 0,
        'nx_iso': nx_iso,
        'gossip_match': gossip_match,
        'correct': correct,
        'false_pos': false_pos,
        'false_neg': false_neg
    }

def generate_random_regular_pairs():
    """Generate random regular graph pairs."""
    tests = []
    random.seed(123)

    # Various (degree, size) combinations
    configs = [(3, 8), (3, 10), (4, 10), (4, 12), (5, 12), (6, 14)]

    for degree, n in configs:
        try:
            G1 = nx.random_regular_graph(degree, n, seed=random.randint(1, 1000))
            G2 = nx.random_regular_graph(degree, n, seed=random.randint(1, 1000))
            tests.append((G1, G2, f"Random {degree}-regular n={n}"))
        except:
            pass

    return tests

def generate_cayley_dihedral_pairs():
    """Generate Cayley graphs of dihedral groups."""
    tests = []

    def cayley_dihedral(n, gens):
        """Cayley graph of dihedral group D_n."""
        G = nx.Graph()
        G.add_nodes_from(range(2*n))

        for i in range(2*n):
            r, f = i % n, i // n  # rotation, flip
            for gen in gens:
                if gen == 'r':  # rotation
                    j = ((r + 1) % n) + f * n
                elif gen == 'r_inv':  # inverse rotation
                    j = ((r - 1) % n) + f * n
                elif gen == 's':  # reflection
                    j = r + (1 - f) * n
                else:
                    continue
                G.add_edge(i, j)
        return G

    # Different generating sets
    for n in [6, 8, 10]:
        G1 = cayley_dihedral(n, ['r', 's'])
        G2 = cayley_dihedral(n, ['r_inv', 's'])
        tests.append((G1, G2, f"Cayley D_{n} different gens"))

    return tests

def generate_hamming_code_graphs():
    """Generate graphs from Hamming codes."""
    tests = []

    # Hamming graphs H(d,q)
    try:
        # H(3,2) - vertices are binary strings of length 3
        def hamming_graph(d, q):
            from itertools import product
            vertices = list(product(range(q), repeat=d))
            G = nx.Graph()
            G.add_nodes_from(range(len(vertices)))

            for i, v1 in enumerate(vertices):
                for j, v2 in enumerate(vertices[i+1:], i+1):
                    # Connect if Hamming distance is 1
                    if sum(a != b for a, b in zip(v1, v2)) == 1:
                        G.add_edge(i, j)
            return G

        G1 = hamming_graph(3, 2)  # 8 vertices, 3-regular
        G2 = nx.hypercube_graph(3)  # Also 8 vertices, 3-regular
        tests.append((G1, G2, "Hamming H(3,2) vs Hypercube"))

        G1 = hamming_graph(4, 2)  # 16 vertices, 4-regular
        # Create another 4-regular graph on 16 vertices
        G2 = nx.Graph()
        G2.add_nodes_from(range(16))
        for i in range(16):
            G2.add_edge(i, (i + 1) % 16)
            G2.add_edge(i, (i + 4) % 16)
            G2.add_edge(i, (i + 7) % 16)
            G2.add_edge(i, (i + 11) % 16)
        tests.append((G1, G2, "Hamming H(4,2) vs cycle variant"))

    except:
        pass

    return tests

def generate_johnson_graph_pairs():
    """Generate Johnson graphs J(n,k)."""
    tests = []

    try:
        # J(5,2) - 2-subsets of 5-set
        from itertools import combinations

        def johnson_graph(n, k):
            subsets = list(combinations(range(n), k))
            G = nx.Graph()
            G.add_nodes_from(range(len(subsets)))

            for i, s1 in enumerate(subsets):
                for j, s2 in enumerate(subsets[i+1:], i+1):
                    # Connect if intersection size is k-1
                    if len(set(s1) & set(s2)) == k - 1:
                        G.add_edge(i, j)
            return G

        G1 = johnson_graph(5, 2)  # 10 vertices
        G2 = johnson_graph(6, 2)  # 15 vertices - different size

        # Create same-size comparison
        G1 = johnson_graph(5, 2)
        # Petersen graph is also 10 vertices, 3-regular
        G2 = nx.petersen_graph()
        tests.append((G1, G2, "Johnson J(5,2) vs Petersen"))

    except:
        pass

    return tests

def generate_grid_torus_pairs():
    """Generate grid and torus graphs."""
    tests = []

    # 2D grids vs tori
    for m, n in [(3, 4), (4, 4), (3, 5)]:
        grid = nx.grid_2d_graph(m, n)
        torus = nx.grid_2d_graph(m, n, periodic=True)

        # Relabel to integers
        grid = nx.convert_node_labels_to_integers(grid)
        torus = nx.convert_node_labels_to_integers(torus)

        tests.append((grid, torus, f"{m}x{n} grid vs torus"))

    return tests

def generate_complete_multipartite_pairs():
    """Generate complete multipartite graphs."""
    tests = []

    # Different partitions with same total size
    G1 = nx.complete_multipartite_graph(3, 3, 3)  # K_{3,3,3}
    G2 = nx.complete_multipartite_graph(4, 5)     # K_{4,5}
    if G1.number_of_nodes() == G2.number_of_nodes():
        tests.append((G1, G2, "K_{3,3,3} vs K_{4,5}"))

    G1 = nx.complete_multipartite_graph(2, 2, 2, 2)  # K_{2,2,2,2}
    G2 = nx.complete_multipartite_graph(4, 4)        # K_{4,4}
    tests.append((G1, G2, "K_{2,2,2,2} vs K_{4,4}"))

    return tests

def generate_ladder_mobius_pairs():
    """Generate ladder and Möbius ladder graphs."""
    tests = []

    for n in [6, 8, 10]:
        ladder = nx.ladder_graph(n)
        circular_ladder = nx.circular_ladder_graph(n)
        tests.append((ladder, circular_ladder, f"Ladder vs circular ladder n={n}"))

    return tests

def generate_wheel_fan_pairs():
    """Generate wheel and fan graphs."""
    tests = []

    for n in [6, 8, 10]:
        wheel = nx.wheel_graph(n)
        fan = nx.Graph()
        fan.add_nodes_from(range(n))
        # Create fan: cycle + center connected to all
        for i in range(n-1):
            fan.add_edge(i, (i + 1) % (n-1))
        for i in range(n-1):
            fan.add_edge(i, n-1)

        tests.append((wheel, fan, f"Wheel vs fan n={n}"))

    return tests

def generate_paley_tournament_pairs():
    """Generate Paley tournaments and related graphs."""
    tests = []

    try:
        # Paley graphs (when they exist)
        for q in [5, 9, 13]:
            try:
                paley = nx.paley_graph(q)

                # Create a different regular graph of same size/degree
                other = nx.Graph()
                other.add_nodes_from(range(q))
                degree = paley.degree(0)

                # Simple regular graph construction
                for i in range(q):
                    for j in range(1, degree // 2 + 1):
                        other.add_edge(i, (i + j) % q)
                        if degree % 2 == 1 and j == degree // 2:
                            break
                        other.add_edge(i, (i - j) % q)

                tests.append((paley, other, f"Paley({q}) vs regular variant"))
            except:
                pass
    except:
        pass

    return tests

def generate_platonic_solid_pairs():
    """Generate platonic solid graphs."""
    tests = []

    # Tetrahedron (K4) vs other 3-regular
    tetrahedron = nx.complete_graph(4)
    other_3reg = nx.Graph()
    other_3reg.add_edges_from([(0,1), (1,2), (2,3), (3,0), (0,2), (1,3)])
    tests.append((tetrahedron, other_3reg, "Tetrahedron vs other 3-regular"))

    # Cube vs octahedron (both vertex-transitive)
    cube = nx.hypercube_graph(3)
    octahedron = nx.octahedral_graph()
    if cube.number_of_nodes() != octahedron.number_of_nodes():
        # Create comparable regular graphs
        cube_4reg = nx.Graph()
        cube_4reg.add_nodes_from(range(6))
        for i in range(6):
            cube_4reg.add_edge(i, (i + 1) % 6)
            cube_4reg.add_edge(i, (i + 2) % 6)
            cube_4reg.add_edge(i, (i + 3) % 6)
        tests.append((octahedron, cube_4reg, "Octahedron vs 4-regular variant"))

    return tests

def run_baseline_tests():
    """Run comprehensive baseline test suite."""
    print("🔬 BASELINE TEST SUITE EXPANSION")
    print("Testing diverse graph classes for algorithm performance")
    print("=" * 70)

    # Collect all test generators
    generators = [
        ("Random Regular", generate_random_regular_pairs),
        ("Cayley Dihedral", generate_cayley_dihedral_pairs),
        ("Hamming Codes", generate_hamming_code_graphs),
        ("Johnson Graphs", generate_johnson_graph_pairs),
        ("Grid/Torus", generate_grid_torus_pairs),
        ("Complete Multipartite", generate_complete_multipartite_pairs),
        ("Ladder/Möbius", generate_ladder_mobius_pairs),
        ("Wheel/Fan", generate_wheel_fan_pairs),
        ("Paley/Tournament", generate_paley_tournament_pairs),
        ("Platonic Solids", generate_platonic_solid_pairs)
    ]

    all_results = []
    total_tests = 0
    total_correct = 0
    total_fps = 0
    total_fns = 0

    for category, generator in generators:
        print(f"\n📊 {category}")
        try:
            test_cases = generator()
            cat_correct = 0
            cat_total = len(test_cases)
            cat_fps = 0

            for G1, G2, name in test_cases:
                if G1.number_of_nodes() != G2.number_of_nodes():
                    continue

                result = test_pair(G1, G2, name)
                all_results.append(result)
                total_tests += 1
                cat_total = len([tc for tc in test_cases if tc[0].number_of_nodes() == tc[1].number_of_nodes()])

                if result['correct']:
                    total_correct += 1
                    cat_correct += 1
                    print(f"  ✅ {name} (n={result['n']}, d={result['degree']})")
                else:
                    if result['false_pos']:
                        total_fps += 1
                        cat_fps += 1
                        print(f"  ❌ FP: {name} (n={result['n']}, d={result['degree']})")
                    else:
                        total_fns += 1
                        print(f"  ❌ FN: {name} (n={result['n']}, d={result['degree']})")

            if cat_total > 0:
                success_rate = cat_correct / cat_total * 100
                print(f"  {category}: {cat_correct}/{cat_total} ({success_rate:.1f}%)")
                if cat_fps > 0:
                    fp_rate = cat_fps / cat_total * 100
                    print(f"  False positives: {cat_fps} ({fp_rate:.1f}%)")

        except Exception as e:
            print(f"  Error in {category}: {e}")

    # Summary
    print(f"\n{'=' * 70}")
    print("BASELINE EXPANSION SUMMARY")
    print("=" * 70)

    if total_tests > 0:
        success_rate = total_correct / total_tests * 100
        fp_rate = total_fps / total_tests * 100
        fn_rate = total_fns / total_tests * 100

        print(f"Total tests: {total_tests}")
        print(f"Success rate: {success_rate:.1f}%")
        print(f"False positives: {total_fps} ({fp_rate:.1f}%)")
        print(f"False negatives: {total_fns} ({fn_rate:.1f}%)")

        if total_fps == 0:
            print("\n✅ NO FALSE POSITIVES in expanded test suite")
            print("   Circulant failures appear to be class-specific")
        else:
            print(f"\n⚠️  {total_fps} false positives found")
            print("   Algorithm may have broader regular graph issues")

        # Regular vs irregular breakdown
        regular_results = [r for r in all_results if r['regular']]
        irregular_results = [r for r in all_results if not r['regular']]

        if regular_results:
            reg_correct = sum(1 for r in regular_results if r['correct'])
            reg_fps = sum(1 for r in regular_results if r['false_pos'])
            reg_success = reg_correct / len(regular_results) * 100
            reg_fp_rate = reg_fps / len(regular_results) * 100
            print(f"\nRegular graphs: {reg_correct}/{len(regular_results)} ({reg_success:.1f}%), {reg_fps} FP ({reg_fp_rate:.1f}%)")

        if irregular_results:
            irreg_correct = sum(1 for r in irregular_results if r['correct'])
            irreg_fps = sum(1 for r in irregular_results if r['false_pos'])
            irreg_success = irreg_correct / len(irregular_results) * 100
            irreg_fp_rate = irreg_fps / len(irregular_results) * 100 if irregular_results else 0
            print(f"Irregular graphs: {irreg_correct}/{len(irregular_results)} ({irreg_success:.1f}%), {irreg_fps} FP ({irreg_fp_rate:.1f}%)")

        # Degree analysis
        from collections import defaultdict
        degree_stats = defaultdict(lambda: {'total': 0, 'correct': 0, 'fps': 0})

        for result in all_results:
            d = result['degree']
            degree_stats[d]['total'] += 1
            if result['correct']:
                degree_stats[d]['correct'] += 1
            if result['false_pos']:
                degree_stats[d]['fps'] += 1

        print(f"\nBy degree:")
        for degree in sorted(degree_stats.keys()):
            stats = degree_stats[degree]
            if stats['total'] > 0:
                success = stats['correct'] / stats['total'] * 100
                fp_rate = stats['fps'] / stats['total'] * 100
                print(f"  Degree {degree}: {stats['correct']}/{stats['total']} ({success:.1f}%), {stats['fps']} FP ({fp_rate:.1f}%)")

    else:
        print("No tests completed successfully")

    return all_results

if __name__ == "__main__":
    results = run_baseline_tests()
