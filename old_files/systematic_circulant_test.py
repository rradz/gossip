#!/usr/bin/env python3
"""
Systematic circulant graph testing across sizes and degrees.
This tests whether the failures we found are exceptional cases or part of a broader pattern.
"""

import networkx as nx
import itertools
from collections import defaultdict
from gossip_cli import graph_to_adj

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

def gossip_fingerprints_match(G1, G2):
    """Check if two graphs have identical gossip fingerprints."""
    adj1 = graph_to_adj(G1)
    adj2 = graph_to_adj(G2)

    fp1 = compute_vertex_fingerprints(adj1)
    fp2 = compute_vertex_fingerprints(adj2)

    # Convert to canonical form
    canonical_fp1 = tuple(sorted(fp1.values()))
    canonical_fp2 = tuple(sorted(fp2.values()))

    return canonical_fp1 == canonical_fp2

def canonical_edge_sets_match(G1, G2):
    """Check if canonical edge sets match using gossip-based canonical labeling."""
    adj1 = graph_to_adj(G1)
    adj2 = graph_to_adj(G2)

    fp1 = compute_vertex_fingerprints(adj1)
    fp2 = compute_vertex_fingerprints(adj2)

    # Group vertices by fingerprints and create canonical mapping
    def create_canonical_edges(G, fps):
        fingerprint_groups = defaultdict(list)
        for vertex, fingerprint in fps.items():
            fingerprint_groups[fingerprint].append(vertex)

        # Sort fingerprints and assign canonical labels
        sorted_fingerprints = sorted(fingerprint_groups.keys())
        canonical_mapping = {}
        canonical_label = 0

        for fingerprint in sorted_fingerprints:
            vertices_with_this_fp = sorted(fingerprint_groups[fingerprint])
            for vertex in vertices_with_this_fp:
                canonical_mapping[vertex] = canonical_label
                canonical_label += 1

        # Create canonical edge set
        canonical_edges = set()
        for u, v in G.edges():
            canon_u = canonical_mapping[u]
            canon_v = canonical_mapping[v]
            canonical_edges.add(tuple(sorted([canon_u, canon_v])))

        return canonical_edges

    edges1 = create_canonical_edges(G1, fp1)
    edges2 = create_canonical_edges(G2, fp2)

    return edges1 == edges2

def test_circulant_pair(n, jumps1, jumps2):
    """Test a single pair of circulant graphs."""
    # Skip invalid jump sets
    if max(jumps1) >= n//2 or max(jumps2) >= n//2:
        return None
    if len(set(jumps1)) != len(jumps1) or len(set(jumps2)) != len(jumps2):
        return None

    G1 = nx.circulant_graph(n, jumps1)
    G2 = nx.circulant_graph(n, jumps2)

    # Check if they're actually isomorphic
    nx_isomorphic = nx.is_isomorphic(G1, G2)

    # Check gossip fingerprints
    gossip_match = gossip_fingerprints_match(G1, G2)

    # Check canonical edge sets (only if fingerprints match)
    if gossip_match:
        canonical_match = canonical_edge_sets_match(G1, G2)
    else:
        canonical_match = False

    degree = len(jumps1) * 2  # Each jump creates 2 edges (forward and backward)

    result = {
        'n': n,
        'jumps1': jumps1,
        'jumps2': jumps2,
        'degree': degree,
        'nx_isomorphic': nx_isomorphic,
        'gossip_match': gossip_match,
        'canonical_match': canonical_match,
        'gossip_correct': gossip_match == nx_isomorphic,
        'false_positive': gossip_match and not canonical_match,
        'edges': len(G1.edges())
    }

    return result

def generate_jump_combinations(n, degree):
    """Generate all valid jump combinations for given n and degree."""
    if degree % 2 != 0:
        return []  # Degree must be even for circulant graphs

    num_jumps = degree // 2
    max_jump = n // 2

    # Generate all combinations of jumps
    possible_jumps = list(range(1, max_jump))
    if len(possible_jumps) < num_jumps:
        return []

    combinations = list(itertools.combinations(possible_jumps, num_jumps))
    return [list(combo) for combo in combinations]

def systematic_size_analysis():
    """Test circulants systematically across different sizes."""
    print("🔬 SYSTEMATIC CIRCULANT ANALYSIS ACROSS SIZES")
    print("="*80)

    results = []

    # Test sizes from 7 to 21 (odd numbers work best for circulants)
    test_sizes = [7, 9, 11, 13, 15, 17, 19, 21]

    for n in test_sizes:
        print(f"\nTesting size n={n}...")

        # Test different degrees
        max_degree = min(10, n-1)  # Limit degree for computational feasibility

        for degree in range(4, max_degree+1, 2):  # Even degrees only
            jump_combinations = generate_jump_combinations(n, degree)

            if len(jump_combinations) < 2:
                continue

            # Test pairs of different jump combinations
            tested_pairs = 0
            max_pairs_per_degree = 20  # Limit for computational feasibility

            for i, jumps1 in enumerate(jump_combinations):
                if tested_pairs >= max_pairs_per_degree:
                    break

                for j, jumps2 in enumerate(jump_combinations[i+1:], i+1):
                    if tested_pairs >= max_pairs_per_degree:
                        break

                    result = test_circulant_pair(n, jumps1, jumps2)
                    if result is not None:
                        results.append(result)
                        tested_pairs += 1

                        # Print immediate results for false positives
                        if result['false_positive']:
                            print(f"  ❌ FALSE POSITIVE: C_{n}({jumps1}) vs C_{n}({jumps2})")
                        elif not result['gossip_correct']:
                            status = "FN" if result['nx_isomorphic'] and not result['gossip_match'] else "?"
                            print(f"  ⚠️  {status}: C_{n}({jumps1}) vs C_{n}({jumps2})")

    return results

def analyze_results_by_size(results):
    """Analyze results broken down by graph size."""
    print(f"\n{'='*80}")
    print("ANALYSIS BY SIZE")
    print("="*80)

    size_stats = defaultdict(lambda: {
        'total': 0, 'correct': 0, 'false_positive': 0, 'false_negative': 0,
        'degrees': defaultdict(lambda: {'total': 0, 'correct': 0, 'false_positive': 0})
    })

    for result in results:
        n = result['n']
        degree = result['degree']

        size_stats[n]['total'] += 1
        size_stats[n]['degrees'][degree]['total'] += 1

        if result['gossip_correct']:
            size_stats[n]['correct'] += 1
            size_stats[n]['degrees'][degree]['correct'] += 1

        if result['false_positive']:
            size_stats[n]['false_positive'] += 1
            size_stats[n]['degrees'][degree]['false_positive'] += 1

        if result['nx_isomorphic'] and not result['gossip_match']:
            size_stats[n]['false_negative'] += 1

    print(f"{'Size':<6} {'Total':<8} {'Correct':<8} {'Rate':<8} {'FP':<4} {'FN':<4} {'Degrees Tested'}")
    print("-" * 70)

    overall_stats = {'total': 0, 'correct': 0, 'fp': 0, 'fn': 0}

    for n in sorted(size_stats.keys()):
        stats = size_stats[n]
        rate = stats['correct'] / stats['total'] * 100 if stats['total'] > 0 else 0
        degrees_tested = sorted(stats['degrees'].keys())

        print(f"{n:<6} {stats['total']:<8} {stats['correct']:<8} {rate:<7.1f}% "
              f"{stats['false_positive']:<4} {stats['false_negative']:<4} {degrees_tested}")

        overall_stats['total'] += stats['total']
        overall_stats['correct'] += stats['correct']
        overall_stats['fp'] += stats['false_positive']
        overall_stats['fn'] += stats['false_negative']

    overall_rate = overall_stats['correct'] / overall_stats['total'] * 100
    print("-" * 70)
    print(f"{'TOTAL':<6} {overall_stats['total']:<8} {overall_stats['correct']:<8} "
          f"{overall_rate:<7.1f}% {overall_stats['fp']:<4} {overall_stats['fn']:<4}")

    return size_stats, overall_stats

def analyze_results_by_degree(results):
    """Analyze results broken down by degree."""
    print(f"\n{'='*80}")
    print("ANALYSIS BY DEGREE")
    print("="*80)

    degree_stats = defaultdict(lambda: {
        'total': 0, 'correct': 0, 'false_positive': 0, 'false_negative': 0,
        'sizes': defaultdict(lambda: {'total': 0, 'correct': 0, 'false_positive': 0})
    })

    for result in results:
        degree = result['degree']
        n = result['n']

        degree_stats[degree]['total'] += 1
        degree_stats[degree]['sizes'][n]['total'] += 1

        if result['gossip_correct']:
            degree_stats[degree]['correct'] += 1
            degree_stats[degree]['sizes'][n]['correct'] += 1

        if result['false_positive']:
            degree_stats[degree]['false_positive'] += 1
            degree_stats[degree]['sizes'][n]['false_positive'] += 1

        if result['nx_isomorphic'] and not result['gossip_match']:
            degree_stats[degree]['false_negative'] += 1

    print(f"{'Degree':<8} {'Total':<8} {'Correct':<8} {'Rate':<8} {'FP':<4} {'FN':<4} {'Sizes Tested'}")
    print("-" * 75)

    for degree in sorted(degree_stats.keys()):
        stats = degree_stats[degree]
        rate = stats['correct'] / stats['total'] * 100 if stats['total'] > 0 else 0
        sizes_tested = sorted(stats['sizes'].keys())

        print(f"{degree:<8} {stats['total']:<8} {stats['correct']:<8} {rate:<7.1f}% "
              f"{stats['false_positive']:<4} {stats['false_negative']:<4} {sizes_tested}")

    return degree_stats

def identify_problematic_patterns(results):
    """Identify specific patterns that cause failures."""
    print(f"\n{'='*80}")
    print("PROBLEMATIC PATTERN ANALYSIS")
    print("="*80)

    false_positives = [r for r in results if r['false_positive']]

    if not false_positives:
        print("✅ No false positives found!")
        return

    print(f"Found {len(false_positives)} false positive cases:")
    print()

    # Group by size and degree
    pattern_groups = defaultdict(list)
    for fp in false_positives:
        key = (fp['n'], fp['degree'])
        pattern_groups[key].append(fp)

    for (n, degree), cases in pattern_groups.items():
        print(f"Size {n}, Degree {degree}: {len(cases)} false positives")
        for case in cases[:5]:  # Show first 5 cases
            print(f"  C_{n}({case['jumps1']}) vs C_{n}({case['jumps2']})")
        if len(cases) > 5:
            print(f"  ... and {len(cases)-5} more")
        print()

    # Look for common jump patterns
    print("Jump pattern analysis:")
    jump_involvement = defaultdict(int)
    for fp in false_positives:
        for jump in fp['jumps1'] + fp['jumps2']:
            jump_involvement[jump] += 1

    common_jumps = sorted(jump_involvement.items(), key=lambda x: x[1], reverse=True)[:10]
    print("Most frequently involved jumps:")
    for jump, count in common_jumps:
        print(f"  Jump {jump}: appears in {count} false positive cases")

def main():
    """Main analysis function."""
    print("🚀 SYSTEMATIC CIRCULANT ANALYSIS")
    print("Testing whether our discovered failures are exceptional or systematic...")
    print()

    # Run systematic analysis
    results = systematic_size_analysis()

    if not results:
        print("❌ No valid test cases generated!")
        return

    print(f"\n📊 Generated {len(results)} test cases")

    # Analyze results
    size_stats, overall_stats = analyze_results_by_size(results)
    degree_stats = analyze_results_by_degree(results)
    identify_problematic_patterns(results)

    # Final assessment
    print(f"\n{'='*80}")
    print("FINAL ASSESSMENT")
    print("="*80)

    overall_rate = overall_stats['correct'] / overall_stats['total'] * 100
    fp_rate = overall_stats['fp'] / overall_stats['total'] * 100

    print(f"Overall success rate: {overall_rate:.1f}%")
    print(f"False positive rate: {fp_rate:.1f}%")
    print(f"Total false positives: {overall_stats['fp']}")

    if overall_stats['fp'] == 0:
        print("✅ No systematic failures found - size 13 cases were exceptional!")
    elif fp_rate < 5:
        print("⚠️  Low failure rate - some systematic issues but generally robust")
    elif fp_rate < 15:
        print("🚨 Moderate failure rate - systematic algorithmic limitations identified")
    else:
        print("💥 High failure rate - fundamental issues with circulant graph handling")

    # Compare to our original findings
    size_13_results = [r for r in results if r['n'] == 13]
    if size_13_results:
        size_13_fp_rate = sum(1 for r in size_13_results if r['false_positive']) / len(size_13_results) * 100
        print(f"\nSize 13 false positive rate: {size_13_fp_rate:.1f}% ({len([r for r in size_13_results if r['false_positive']])}/{len(size_13_results)})")

    degree_6_results = [r for r in results if r['degree'] == 6]
    if degree_6_results:
        degree_6_fp_rate = sum(1 for r in degree_6_results if r['false_positive']) / len(degree_6_results) * 100
        print(f"Degree 6 false positive rate: {degree_6_fp_rate:.1f}% ({len([r for r in degree_6_results if r['false_positive']])}/{len(degree_6_results)})")

    return results

if __name__ == "__main__":
    results = main()
