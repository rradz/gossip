#!/usr/bin/env python3
"""
Systematic analysis of circulant graph behavior in the gossip algorithm.

This script analyzes which circulant graph patterns cause false positives
and provides detailed statistics about the algorithm's performance on
different circulant configurations.
"""

import sys
import networkx as nx
from collections import defaultdict
from itertools import combinations
from typing import Dict, List, Tuple, Set, Any

# Add src to path if needed
sys.path.insert(0, 'src')

from gossip import GossipFingerprint
from gossip.utils import graph_to_adjacency_list, are_isomorphic, generate_circulant_graph


def test_circulant_pair(n: int, jumps1: List[int], jumps2: List[int]) -> Dict[str, Any]:
    """
    Test a single pair of circulant graphs.

    Returns:
        Dictionary with test results or None if invalid configuration
    """
    # Validate jump sets
    if not jumps1 or not jumps2:
        return None
    if max(jumps1) >= n//2 + 1 or max(jumps2) >= n//2 + 1:
        return None
    if len(set(jumps1)) != len(jumps1) or len(set(jumps2)) != len(jumps2):
        return None

    try:
        G1 = generate_circulant_graph(n, jumps1)
        G2 = generate_circulant_graph(n, jumps2)
    except:
        return None

    # Check actual isomorphism
    actual_iso = are_isomorphic(G1, G2)

    # Check gossip algorithm result
    gf = GossipFingerprint()
    gossip_iso = gf.compare(G1, G2)

    # Determine result type
    correct = (actual_iso == gossip_iso)
    false_positive = (not actual_iso and gossip_iso)
    false_negative = (actual_iso and not gossip_iso)

    return {
        'n': n,
        'jumps1': jumps1,
        'jumps2': jumps2,
        'degree': len(jumps1) * 2,
        'actual_iso': actual_iso,
        'gossip_iso': gossip_iso,
        'correct': correct,
        'false_positive': false_positive,
        'false_negative': false_negative
    }


def generate_jump_combinations(n: int, degree: int) -> List[List[int]]:
    """Generate valid jump combinations for given n and degree."""
    if degree % 2 != 0:
        return []  # Degree must be even for circulant graphs

    num_jumps = degree // 2
    max_jump = n // 2

    # Generate all combinations of jumps
    possible_jumps = list(range(1, max_jump + 1))
    if len(possible_jumps) < num_jumps:
        return []

    return [list(combo) for combo in combinations(possible_jumps, num_jumps)]


def analyze_size(n: int, max_degree: int = 8) -> List[Dict[str, Any]]:
    """Analyze circulant graphs of a specific size."""
    results = []

    for degree in range(4, min(max_degree + 1, n), 2):  # Even degrees only
        jump_combos = generate_jump_combinations(n, degree)

        if len(jump_combos) < 2:
            continue

        # Test pairs of different jump patterns
        tested_pairs = 0
        max_pairs = min(10, len(jump_combos) * (len(jump_combos) - 1) // 2)

        for i, jumps1 in enumerate(jump_combos):
            for jumps2 in jump_combos[i+1:]:
                if tested_pairs >= max_pairs:
                    break

                result = test_circulant_pair(n, jumps1, jumps2)
                if result:
                    results.append(result)
                    tested_pairs += 1

            if tested_pairs >= max_pairs:
                break

    return results


def analyze_all_sizes(sizes: List[int] = None) -> List[Dict[str, Any]]:
    """Analyze circulant graphs across multiple sizes."""
    if sizes is None:
        sizes = [7, 9, 11, 13, 15, 17, 19, 21]

    all_results = []

    for n in sizes:
        print(f"Analyzing size n={n}...")
        results = analyze_size(n)
        all_results.extend(results)

    return all_results


def print_summary(results: List[Dict[str, Any]]):
    """Print analysis summary."""
    if not results:
        print("No results to analyze")
        return

    total = len(results)
    correct = sum(1 for r in results if r['correct'])
    false_positives = [r for r in results if r['false_positive']]
    false_negatives = [r for r in results if r['false_negative']]

    print("\n" + "="*70)
    print("CIRCULANT GRAPH ANALYSIS SUMMARY")
    print("="*70)

    print(f"\nTotal test pairs: {total}")
    print(f"Correct: {correct} ({100*correct/total:.1f}%)")
    print(f"False positives: {len(false_positives)} ({100*len(false_positives)/total:.1f}%)")
    print(f"False negatives: {len(false_negatives)} ({100*len(false_negatives)/total:.1f}%)")

    # Analyze by size
    print("\n" + "-"*40)
    print("Results by size:")
    print("-"*40)

    size_stats = defaultdict(lambda: {'total': 0, 'correct': 0, 'false_positive': 0})
    for r in results:
        size_stats[r['n']]['total'] += 1
        if r['correct']:
            size_stats[r['n']]['correct'] += 1
        if r['false_positive']:
            size_stats[r['n']]['false_positive'] += 1

    print(f"{'Size':>6} | {'Total':>6} | {'Correct':>7} | {'FP':>4} | {'Accuracy':>8}")
    print("-"*40)
    for n in sorted(size_stats.keys()):
        stats = size_stats[n]
        accuracy = 100 * stats['correct'] / stats['total']
        print(f"{n:6} | {stats['total']:6} | {stats['correct']:7} | "
              f"{stats['false_positive']:4} | {accuracy:7.1f}%")

    # Show problematic patterns
    if false_positives:
        print("\n" + "-"*40)
        print("False positive patterns:")
        print("-"*40)

        for fp in false_positives[:10]:  # Show first 10
            print(f"C_{fp['n']}({fp['jumps1']}) vs C_{fp['n']}({fp['jumps2']})")

        if len(false_positives) > 10:
            print(f"... and {len(false_positives) - 10} more")

    # Identify patterns
    print("\n" + "-"*40)
    print("Pattern analysis:")
    print("-"*40)

    # Check if size 13 is particularly problematic
    size_13_fps = [r for r in false_positives if r['n'] == 13]
    if size_13_fps:
        print(f"• Size 13 has {len(size_13_fps)} false positives")
        for fp in size_13_fps[:3]:
            print(f"  - C_13({fp['jumps1']}) vs C_13({fp['jumps2']})")

    # Check for degree patterns
    degree_fps = defaultdict(int)
    for fp in false_positives:
        degree_fps[fp['degree']] += 1

    if degree_fps:
        print("\nFalse positives by degree:")
        for degree, count in sorted(degree_fps.items()):
            print(f"  Degree {degree}: {count} false positives")


def main():
    """Main analysis function."""
    print("="*70)
    print("SYSTEMATIC CIRCULANT GRAPH ANALYSIS")
    print("="*70)
    print("\nAnalyzing gossip algorithm behavior on circulant graphs...")
    print("This may take a few moments.\n")

    # Run analysis
    results = analyze_all_sizes()

    # Print summary
    print_summary(results)

    # Specific known problematic case
    print("\n" + "="*70)
    print("TESTING KNOWN PROBLEMATIC CASE")
    print("="*70)

    result = test_circulant_pair(13, [1, 3, 4], [1, 3, 6])
    if result:
        print(f"\nC_13([1,3,4]) vs C_13([1,3,6]):")
        print(f"  NetworkX says: {'Isomorphic' if result['actual_iso'] else 'Non-isomorphic'}")
        print(f"  Gossip says:   {'Isomorphic' if result['gossip_iso'] else 'Non-isomorphic'}")
        print(f"  Result: {'✓ Correct' if result['correct'] else '✗ False positive'}")

    print("\n" + "="*70)
    print("ANALYSIS COMPLETE")
    print("="*70)


if __name__ == "__main__":
    main()
