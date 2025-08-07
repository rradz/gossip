#!/usr/bin/env python3
"""
Comprehensive test suite for regular graph classes beyond circulants.
Tests whether gossip algorithm failures are specific to circulants or broader.
"""

import networkx as nx
import itertools
from collections import defaultdict
from gossip_cli import graph_to_adj
import random

def compute_vertex_fingerprints(adj):
    """Compute individual vertex fingerprints using the gossip process."""
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

def test_graph_pair(G1, G2, description=""):
    """Test a pair of graphs with gossip algorithm."""
    # Check if they're actually isomorphic
    nx_isomorphic = nx.is_isomorphic(G1, G2)

    # Check gossip fingerprints
    adj1 = graph_to_adj(G1)
    adj2 = graph_to_adj(G2)

    fp1 = compute_vertex_fingerprints(adj1)
    fp2 = compute_vertex_fingerprints(adj2)

    canonical_fp1 = tuple(sorted(fp1.values()))
    canonical_fp2 = tuple(sorted(fp2.values()))

    gossip_match = canonical_fp1 == canonical_fp2

    # Classification
    correct = gossip_match == nx_isomorphic
    false_positive = gossip_match and not nx_isomorphic
    false_negative = not gossip_match and nx_isomorphic

    return {
        'description': description,
        'n': G1.number_of_nodes(),
        'edges': G1.number_of_edges(),
        'degree': list(G1.degree())[0][1] if G1.number_of_nodes() > 0 else 0,
        'nx_isomorphic': nx_isomorphic,
        'gossip_match': gossip_match,
        'correct': correct,
        'false_positive': false_positive,
        'false_negative': false_negative
    }

def generate_strongly_regular_graphs():
    """Generate pairs of strongly regular graphs for testing."""
    test_cases = []

    # SRG(16,6,2,2) - multiple non-isomorphic graphs with same parameters
    try:
        # Two different constructions of SRG(16,6,2,2)
        G1 = nx.paley_graph(9)  # Actually 9 vertices, degree 4
        G2 = nx.paley_graph(9)
        # Modify one slightly while maintaining regularity
        if G1.number_of_nodes() == 9:
            # Create a different 4-regular graph on 9 vertices
            G2 = nx.cycle_graph(9)
            # Add chords to make it 4-regular
            for i in range(9):
                G2.add_edge(i, (i + 3) % 9)

        test_cases.append((G1, G2, "SRG variants (9 vertices)"))
    except:
        pass

    # Grid graphs (4-regular when wrapped)
    G1 = nx.grid_2d_graph(3, 3)
    G2 = nx.grid_2d_graph(3, 3)
    # Relabel nodes differently
    mapping = {(i,j): i*3+j for i in range(3) for j in range(3)}
    G1 = nx.relabel_nodes(G1, mapping)
    alt_mapping = {(i,j): (i*2+j*3) % 9 for i in range(3) for j in range(3)}
    G2 = nx.relabel_nodes(G2, alt_mapping)
    test_cases.append((G1, G2, "3x3 grid graphs"))

    # Different 4x4 grid variants
    G1 = nx.grid_2d_graph(4, 4)
    G2 = nx.grid_2d_graph(4, 4)
    G1 = nx.relabel_nodes(G1, {(i,j): i*4+j for i in range(4) for j in range(4)})
    G2 = nx.relabel_nodes(G2, {(i,j): (i*3+j*2) % 16 for i in range(4) for j in range(4)})
    test_cases.append((G1, G2, "4x4 grid graphs"))

    return test_cases

def generate_cayley_graphs():
    """Generate non-circulant Cayley graphs."""
    test_cases = []

    # Cayley graphs of dihedral groups
    def dihedral_cayley(n, generators):
        """Create Cayley graph of dihedral group D_n."""
        G = nx.Graph()
        vertices = [(i, 0) for i in range(n)] + [(i, 1) for i in range(n)]  # (rotation, reflection)
        G.add_nodes_from(range(2*n))

        for i, (r, f) in enumerate(vertices):
            for gen in generators:
                if gen == 'r':  # rotation
                    target = ((r + 1) % n, f)
                elif gen == 's':  # reflection
                    target = (r, 1 - f)
                elif gen == 'sr':  # reflection then rotation
                    target = ((r + 1) % n, 1 - f)
                else:
                    continue

                target_idx = target[0] + target[1] * n
                G.add_edge(i, target_idx)

        return G

    # Different generating sets for D_6
    G1 = dihedral_cayley(6, ['r', 's'])
    G2 = dihedral_cayley(6, ['r', 'sr'])
    test_cases.append((G1, G2, "Dihedral D_6 Cayley graphs"))

    # Different generating sets for D_8
    G1 = dihedral_cayley(8, ['r', 's'])
    G2 = dihedral_cayley(8, ['r', 'sr'])
    test_cases.append((G1, G2, "Dihedral D_8 Cayley graphs"))

    return test_cases

def generate_cubic_graphs():
    """Generate 3-regular (cubic) graphs."""
    test_cases = []

    # Petersen graph vs other cubic graphs
    petersen = nx.petersen_graph()

    # Möbius-Kantor graph (3,8)-cage
    mobius_kantor = nx.moebius_kantor_graph()
    test_cases.append((petersen, mobius_kantor, "Petersen vs Möbius-Kantor"))

    # Different cube graphs
    cube = nx.hypercube_graph(3)  # 3-cube (8 vertices, 3-regular)

    # Create another 3-regular graph on 8 vertices
    other_3reg = nx.cycle_graph(8)
    # Add chords to make it 3-regular
    for i in range(8):
        other_3reg.add_edge(i, (i + 3) % 8)

    test_cases.append((cube, other_3reg, "3-cube vs cycle with chords"))

    # Complete bipartite K_{3,3}
    k33 = nx.complete_bipartite_graph(3, 3)
    test_cases.append((petersen, k33, "Petersen vs K_{3,3}"))

    return test_cases

def generate_random_regular_graphs():
    """Generate random regular graphs for testing."""
    test_cases = []

    # 3-regular random graphs
    try:
        random.seed(42)
        G1 = nx.random_regular_graph(3, 10, seed=42)
        random.seed(43)
        G2 = nx.random_regular_graph(3, 10, seed=43)
        test_cases.append((G1, G2, "Random 3-regular graphs (n=10)"))
    except:
        pass

    # 4-regular random graphs
    try:
        random.seed(44)
        G1 = nx.random_regular_graph(4, 12, seed=44)
        random.seed(45)
        G2 = nx.random_regular_graph(4, 12, seed=45)
        test_cases.append((G1, G2, "Random 4-regular graphs (n=12)"))
    except:
        pass

    # 6-regular random graphs
    try:
        random.seed(46)
        G1 = nx.random_regular_graph(6, 14, seed=46)
        random.seed(47)
        G2 = nx.random_regular_graph(6, 14, seed=47)
        test_cases.append((G1, G2, "Random 6-regular graphs (n=14)"))
    except:
        pass

    return test_cases

def generate_cage_graphs():
    """Generate cage graphs (minimal regular graphs of given girth)."""
    test_cases = []

    # (3,3)-cage is K_4
    k4 = nx.complete_graph(4)

    # Another 3-regular graph with 4 vertices (impossible - need even degree sum)
    # Use 6 vertices instead
    cycle6 = nx.cycle_graph(6)
    test_cases.append((k4, cycle6, "K_4 vs C_6 (different regular graphs)"))

    # (3,4)-cage is K_{3,3}
    k33 = nx.complete_bipartite_graph(3, 3)

    # (3,5)-cage is Petersen graph
    petersen = nx.petersen_graph()
    test_cases.append((k33, petersen, "K_{3,3} vs Petersen (3-regular)"))

    return test_cases

def generate_paley_type_graphs():
    """Generate Paley-type graphs and variants."""
    test_cases = []

    # Paley graphs of different orders
    try:
        G1 = nx.paley_graph(9)
        G2 = nx.paley_graph(13)
        # These have different sizes, so create size-matched variants

        # Create 9-vertex 4-regular graphs
        cycle9 = nx.cycle_graph(9)
        for i in range(9):
            cycle9.add_edge(i, (i + 3) % 9)

        test_cases.append((G1, cycle9, "Paley(9) vs cycle variant"))
    except:
        pass

    return test_cases

def generate_vertex_transitive_graphs():
    """Generate vertex-transitive regular graphs."""
    test_cases = []

    # Platonic solids
    tetrahedron = nx.complete_graph(4)
    cube = nx.hypercube_graph(3)
    test_cases.append((tetrahedron, cube, "Tetrahedron vs cube"))

    # Octahedron vs other 4-regular graphs
    octahedron = nx.octahedral_graph()

    # Create another 4-regular graph on 6 vertices
    other_4reg = nx.cycle_graph(6)
    for i in range(6):
        other_4reg.add_edge(i, (i + 2) % 6)

    test_cases.append((octahedron, other_4reg, "Octahedron vs 4-regular variant"))

    return test_cases

def generate_symmetric_design_graphs():
    """Generate graphs from symmetric designs."""
    test_cases = []

    # Fano plane (7,3,1)-design
    fano = nx.Graph()
    fano.add_nodes_from(range(7))
    # Fano plane lines as edges
    lines = [(0,1,3), (1,2,4), (2,3,5), (3,4,6), (4,5,0), (5,6,1), (6,0,2)]
    for line in lines:
        for i in range(len(line)):
            for j in range(i+1, len(line)):
                fano.add_edge(line[i], line[j])

    # Create another 3-regular graph on 7 vertices
    other_7_3 = nx.cycle_graph(7)
    # Add one chord to each vertex to make it 3-regular (impossible with odd cycle)
    # Use different construction
    other_7_3 = nx.Graph()
    other_7_3.add_nodes_from(range(7))
    for i in range(7):
        other_7_3.add_edge(i, (i + 1) % 7)
        other_7_3.add_edge(i, (i + 2) % 7)
        other_7_3.add_edge(i, (i + 4) % 7)

    test_cases.append((fano, other_7_3, "Fano plane vs other 3-regular"))

    return test_cases

def run_regular_graph_tests():
    """Run comprehensive tests on regular graph classes."""
    print("🔬 REGULAR GRAPH CLASS TESTING")
    print("Checking if gossip failures extend beyond circulants")
    print("=" * 60)

    all_test_cases = []

    # Collect all test cases
    test_generators = [
        ("Strongly Regular", generate_strongly_regular_graphs),
        ("Cayley Graphs", generate_cayley_graphs),
        ("Cubic Graphs", generate_cubic_graphs),
        ("Random Regular", generate_random_regular_graphs),
        ("Cage Graphs", generate_cage_graphs),
        ("Paley-type", generate_paley_type_graphs),
        ("Vertex-transitive", generate_vertex_transitive_graphs),
        ("Symmetric Designs", generate_symmetric_design_graphs)
    ]

    results_by_category = {}
    total_tests = 0
    total_correct = 0
    total_false_positives = 0

    for category, generator in test_generators:
        print(f"\n📊 Testing {category}...")
        try:
            test_cases = generator()
            if not test_cases:
                print(f"  No test cases generated for {category}")
                continue

            category_results = []
            category_correct = 0
            category_fps = 0

            for G1, G2, desc in test_cases:
                if G1.number_of_nodes() != G2.number_of_nodes():
                    continue  # Skip size mismatches

                result = test_graph_pair(G1, G2, desc)
                category_results.append(result)

                total_tests += 1
                if result['correct']:
                    total_correct += 1
                    category_correct += 1
                    status = "✅"
                else:
                    if result['false_positive']:
                        total_false_positives += 1
                        category_fps += 1
                        status = "❌ FP"
                    else:
                        status = "❌ FN"

                print(f"  {status} {desc} (n={result['n']}, d={result['degree']})")

            success_rate = (category_correct / len(category_results) * 100) if category_results else 0
            fp_rate = (category_fps / len(category_results) * 100) if category_results else 0

            print(f"  {category}: {category_correct}/{len(category_results)} correct ({success_rate:.1f}%)")
            if category_fps > 0:
                print(f"  False positives: {category_fps} ({fp_rate:.1f}%)")

            results_by_category[category] = {
                'results': category_results,
                'success_rate': success_rate,
                'false_positive_rate': fp_rate
            }

        except Exception as e:
            print(f"  Error in {category}: {e}")

    # Summary
    print(f"\n{'=' * 60}")
    print(f"SUMMARY: Regular Graph Class Testing")
    print(f"{'=' * 60}")

    overall_success = (total_correct / total_tests * 100) if total_tests > 0 else 0
    overall_fp_rate = (total_false_positives / total_tests * 100) if total_tests > 0 else 0

    print(f"Total tests: {total_tests}")
    print(f"Overall success rate: {overall_success:.1f}%")
    print(f"Overall false positive rate: {overall_fp_rate:.1f}%")

    if total_false_positives == 0:
        print("✅ No false positives found in regular graph classes!")
        print("   Circulant failures appear to be class-specific.")
    else:
        print(f"⚠️  {total_false_positives} false positives found")
        print("   Regular graph vulnerability may be broader than circulants.")

    # Degree analysis
    print(f"\nDegree-wise breakdown:")
    degree_stats = defaultdict(lambda: {'total': 0, 'correct': 0, 'fp': 0})

    for category, data in results_by_category.items():
        for result in data['results']:
            d = result['degree']
            degree_stats[d]['total'] += 1
            if result['correct']:
                degree_stats[d]['correct'] += 1
            if result['false_positive']:
                degree_stats[d]['fp'] += 1

    for degree in sorted(degree_stats.keys()):
        stats = degree_stats[degree]
        success_rate = (stats['correct'] / stats['total'] * 100) if stats['total'] > 0 else 0
        fp_rate = (stats['fp'] / stats['total'] * 100) if stats['total'] > 0 else 0
        print(f"  Degree {degree}: {stats['correct']}/{stats['total']} ({success_rate:.1f}%), {stats['fp']} FP ({fp_rate:.1f}%)")

    return results_by_category

if __name__ == "__main__":
    results = run_regular_graph_tests()
