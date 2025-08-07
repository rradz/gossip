#!/usr/bin/env python3
"""
Expanded circulant graph testing to identify the failure pattern.
This generates many more examples from the special circulant class to determine
if the alt_circulant_13 failure is truly isolated or part of a pattern.
"""

import networkx as nx
import random
from collections import defaultdict
from gossip_cli import gossip_fingerprint_full, graph_to_adj

class ExpandedCirculantTests:
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

    def add_test(self, category, name, G1, G2, jumps1, jumps2, expected_iso=None):
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
            'edges': len(G1.edges()),
            'jumps1': jumps1,
            'jumps2': jumps2,
            'degree': len(G1[0]) if G1.nodes() else 0
        }
        self.test_results.append(result)
        return result

    def test_self_complementary_circulants(self):
        """Test self-complementary circulant graphs."""
        print("Testing self-complementary circulants...")

        # Known self-complementary circulant parameters
        configs = [
            (5, [1, 2]),
            (9, [1, 4]),
            (13, [1, 3, 4]),
            (17, [1, 2, 4, 8]),
            (21, [1, 4, 5, 16]),
        ]

        for n, jumps in configs:
            circ = nx.circulant_graph(n, jumps)
            comp_circ = nx.complement(circ)

            result = self.add_test(
                "SelfComplementary",
                f"self_comp_circulant_{n}_jumps_{jumps}",
                circ, comp_circ, jumps, f"complement"
            )

            status = "✅ PASS" if result['correct'] else "❌ FAIL"
            print(f"  {result['name']}: {status}")

    def test_circulant_variations_size_13(self):
        """Test many variations of size-13 circulants to find the pattern."""
        print("\nTesting size-13 circulant variations...")

        n = 13
        base_configs = [
            [1, 3, 4],  # Original failing case
            [1, 2, 3],
            [1, 2, 4],
            [1, 2, 5],
            [1, 3, 5],
            [1, 4, 5],
            [2, 3, 4],
            [2, 3, 5],
            [1, 2, 6],
            [1, 3, 6],  # This was the alternative in failing case
            [1, 4, 6],
            [2, 3, 6],
        ]

        for i, base_jumps in enumerate(base_configs):
            # Create variations by modifying one jump
            for j, alt_jumps in enumerate(base_configs):
                if i != j:  # Don't compare identical jump sets
                    circ1 = nx.circulant_graph(n, base_jumps)
                    circ2 = nx.circulant_graph(n, alt_jumps)

                    result = self.add_test(
                        "Size13Variations",
                        f"circ13_{base_jumps}_vs_{alt_jumps}",
                        circ1, circ2, base_jumps, alt_jumps
                    )

                    status = "✅ PASS" if result['correct'] else "❌ FAIL"
                    iso_str = "ISO" if result['isomorphic'] else "NON-ISO"
                    match_str = "MATCH" if result['fingerprint_match'] else "NO-MATCH"
                    print(f"  {result['name']}: {iso_str} | {match_str} | {status}")

    def test_systematic_jump_modifications(self):
        """Test systematic modifications to jump patterns."""
        print("\nTesting systematic jump modifications...")

        configs = [
            (11, [1, 3, 4]),
            (13, [1, 3, 4]),
            (15, [1, 3, 4]),
            (17, [1, 3, 4]),
            (19, [1, 3, 4]),
        ]

        for n, base_jumps in configs:
            # Test original vs incremented last jump
            for increment in [1, 2, 3]:
                alt_jumps = base_jumps[:-1] + [(base_jumps[-1] + increment) % (n//2) + 1]

                # Avoid duplicate jumps
                if len(set(alt_jumps)) != len(alt_jumps):
                    continue

                circ1 = nx.circulant_graph(n, base_jumps)
                circ2 = nx.circulant_graph(n, alt_jumps)

                result = self.add_test(
                    "SystematicMods",
                    f"circ{n}_{base_jumps}_inc{increment}",
                    circ1, circ2, base_jumps, alt_jumps
                )

                status = "✅ PASS" if result['correct'] else "❌ FAIL"
                iso_str = "ISO" if result['isomorphic'] else "NON-ISO"
                match_str = "MATCH" if result['fingerprint_match'] else "NO-MATCH"
                print(f"  {result['name']}: {iso_str} | {match_str} | {status}")

    def test_different_sized_circulants(self):
        """Test circulant graphs of different sizes with similar jump patterns."""
        print("\nTesting different sized circulants...")

        for n in [7, 9, 11, 13, 15, 17, 19, 21]:
            # Test basic 3-regular circulants
            if n > 6:
                base_jumps = [1, 2, 3]
                alt_jumps = [1, 2, (3 + 1) % (n//2) + 1] if n > 8 else [1, 2, n//2]

                # Avoid invalid jump sets
                if max(alt_jumps) < n//2 and len(set(alt_jumps)) == len(alt_jumps):
                    circ1 = nx.circulant_graph(n, base_jumps)
                    circ2 = nx.circulant_graph(n, alt_jumps)

                    result = self.add_test(
                        "DifferentSizes",
                        f"circ{n}_3reg_{base_jumps}_vs_{alt_jumps}",
                        circ1, circ2, base_jumps, alt_jumps
                    )

                    status = "✅ PASS" if result['correct'] else "❌ FAIL"
                    iso_str = "ISO" if result['isomorphic'] else "NON-ISO"
                    match_str = "MATCH" if result['fingerprint_match'] else "NO-MATCH"
                    print(f"  {result['name']}: {iso_str} | {match_str} | {status}")

    def test_specific_problematic_cases(self):
        """Test specific cases around the known failure."""
        print("\nTesting specific problematic cases...")

        # The exact failing case
        n = 13
        original_jumps = [1, 3, 4]
        problem_jumps = [1, 3, 6]

        circ1 = nx.circulant_graph(n, original_jumps)
        circ2 = nx.circulant_graph(n, problem_jumps)

        result = self.add_test(
            "ProblematicCases",
            "EXACT_FAILING_CASE_circ13_[1,3,4]_vs_[1,3,6]",
            circ1, circ2, original_jumps, problem_jumps
        )

        status = "✅ PASS" if result['correct'] else "❌ FAIL"
        iso_str = "ISO" if result['isomorphic'] else "NON-ISO"
        match_str = "MATCH" if result['fingerprint_match'] else "NO-MATCH"
        print(f"  {result['name']}: {iso_str} | {match_str} | {status}")

        # Test nearby cases
        nearby_cases = [
            ([1, 3, 4], [1, 3, 5]),
            ([1, 3, 4], [1, 2, 6]),
            ([1, 3, 4], [2, 3, 6]),
            ([1, 3, 5], [1, 3, 6]),
            ([1, 3, 6], [1, 4, 6]),
            ([1, 2, 4], [1, 2, 6]),
        ]

        for jumps1, jumps2 in nearby_cases:
            circ1 = nx.circulant_graph(n, jumps1)
            circ2 = nx.circulant_graph(n, jumps2)

            result = self.add_test(
                "ProblematicCases",
                f"nearby_circ13_{jumps1}_vs_{jumps2}",
                circ1, circ2, jumps1, jumps2
            )

            status = "✅ PASS" if result['correct'] else "❌ FAIL"
            iso_str = "ISO" if result['isomorphic'] else "NON-ISO"
            match_str = "MATCH" if result['fingerprint_match'] else "NO-MATCH"
            print(f"  {result['name']}: {iso_str} | {match_str} | {status}")

    def test_regular_circulants_same_degree(self):
        """Test regular circulants with the same degree but different jump patterns."""
        print("\nTesting regular circulants with same degree...")

        # Test 4-regular circulants
        configs_4reg = [
            (9, [1, 2], [1, 3]),
            (9, [1, 2], [1, 4]),
            (11, [1, 2], [1, 3]),
            (13, [1, 2], [1, 3]),
            (15, [1, 2], [1, 3]),
        ]

        for n, jumps1, jumps2 in configs_4reg:
            circ1 = nx.circulant_graph(n, jumps1)
            circ2 = nx.circulant_graph(n, jumps2)

            result = self.add_test(
                "SameDegree",
                f"4reg_circ{n}_{jumps1}_vs_{jumps2}",
                circ1, circ2, jumps1, jumps2
            )

            status = "✅ PASS" if result['correct'] else "❌ FAIL"
            iso_str = "ISO" if result['isomorphic'] else "NON-ISO"
            match_str = "MATCH" if result['fingerprint_match'] else "NO-MATCH"
            print(f"  {result['name']}: {iso_str} | {match_str} | {status}")

        # Test 6-regular circulants (same degree as failing case)
        configs_6reg = [
            (13, [1, 2, 3], [1, 2, 4]),
            (13, [1, 2, 3], [1, 3, 4]),
            (13, [1, 2, 4], [1, 3, 4]),
            (13, [1, 3, 4], [1, 3, 5]),
            (13, [1, 3, 4], [1, 3, 6]),  # The failing case
            (13, [1, 3, 5], [1, 3, 6]),
            (15, [1, 2, 3], [1, 2, 4]),
            (15, [1, 3, 4], [1, 3, 5]),
            (17, [1, 2, 3], [1, 2, 4]),
            (17, [1, 3, 4], [1, 3, 5]),
        ]

        for n, jumps1, jumps2 in configs_6reg:
            # Ensure valid jump sets
            if max(jumps1) < n//2 and max(jumps2) < n//2:
                circ1 = nx.circulant_graph(n, jumps1)
                circ2 = nx.circulant_graph(n, jumps2)

                result = self.add_test(
                    "SameDegree",
                    f"6reg_circ{n}_{jumps1}_vs_{jumps2}",
                    circ1, circ2, jumps1, jumps2
                )

                status = "✅ PASS" if result['correct'] else "❌ FAIL"
                iso_str = "ISO" if result['isomorphic'] else "NON-ISO"
                match_str = "MATCH" if result['fingerprint_match'] else "NO-MATCH"
                print(f"  {result['name']}: {iso_str} | {match_str} | {status}")

    def analyze_results(self):
        """Analyze the test results to identify patterns."""
        print(f"\n" + "=" * 80)
        print("EXPANDED CIRCULANT TEST ANALYSIS")
        print("=" * 80)

        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r['correct'])
        failed_tests = [r for r in self.test_results if not r['correct']]

        print(f"Total tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {len(failed_tests)}")
        print(f"Success rate: {passed_tests/total_tests*100:.1f}%")

        if failed_tests:
            print(f"\n❌ FAILED TESTS:")
            for fail in failed_tests:
                iso_str = "ISO" if fail['isomorphic'] else "NON-ISO"
                match_str = "MATCH" if fail['fingerprint_match'] else "NO-MATCH"
                print(f"  {fail['name']}")
                print(f"    Size: {fail['size']}, Degree: {fail['degree']}")
                print(f"    Jumps: {fail['jumps1']} vs {fail['jumps2']}")
                print(f"    Result: {iso_str} | {match_str}")
                print()

        # Analyze by category
        print(f"\nRESULTS BY CATEGORY:")
        categories = defaultdict(list)
        for result in self.test_results:
            categories[result['category']].append(result['correct'])

        for category, results in categories.items():
            passed = sum(results)
            total = len(results)
            rate = passed / total * 100
            print(f"  {category}: {passed}/{total} ({rate:.1f}%)")

        # Look for patterns in failures
        if failed_tests:
            print(f"\nFAILURE PATTERN ANALYSIS:")

            # Group by size
            sizes = defaultdict(list)
            for fail in failed_tests:
                sizes[fail['size']].append(fail)
            print(f"  Failures by size: {dict(sizes.keys())}")

            # Group by degree
            degrees = defaultdict(list)
            for fail in failed_tests:
                degrees[fail['degree']].append(fail)
            print(f"  Failures by degree: {list(degrees.keys())}")

            # Check if all failures are false positives or false negatives
            false_pos = sum(1 for f in failed_tests if f['fingerprint_match'] and not f['isomorphic'])
            false_neg = sum(1 for f in failed_tests if not f['fingerprint_match'] and f['isomorphic'])
            print(f"  False positives: {false_pos}")
            print(f"  False negatives: {false_neg}")

        return {
            'total': total_tests,
            'passed': passed_tests,
            'failed': len(failed_tests),
            'rate': passed_tests/total_tests,
            'failures': failed_tests
        }

    def run_all_tests(self):
        """Run all expanded circulant tests."""
        print("🔬 EXPANDED CIRCULANT GRAPH TESTING")
        print("Investigating the isolated circulant failure pattern")
        print("=" * 80)

        # Run all test categories
        self.test_self_complementary_circulants()
        self.test_circulant_variations_size_13()
        self.test_systematic_jump_modifications()
        self.test_different_sized_circulants()
        self.test_specific_problematic_cases()
        self.test_regular_circulants_same_degree()

        # Analyze results
        return self.analyze_results()


def main():
    """Main test runner."""
    suite = ExpandedCirculantTests()
    results = suite.run_all_tests()

    print(f"\n" + "🎯 CONCLUSION:")
    if results['failed'] == 0:
        print("No failures found! The original failure might be a test bug.")
    elif results['failed'] == 1:
        print("Only 1 failure confirmed - truly isolated edge case.")
    else:
        print(f"{results['failed']} failures found - there's a pattern here!")
        print("The algorithm has a systematic issue with certain circulant graphs.")

    return results


if __name__ == "__main__":
    main()
