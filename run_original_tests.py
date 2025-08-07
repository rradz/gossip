#!/usr/bin/env python3
"""
Run the original basic test suite from gossip_cli.py for comparison.
This provides a baseline to compare against the comprehensive test suite.
"""

import time
from gossip_cli import get_test_cases, compare_graphs

def run_original_tests():
    """Run the original test suite from gossip_cli.py."""
    print("=" * 80)
    print("ORIGINAL GOSSIP FINGERPRINT TEST SUITE")
    print("=" * 80)
    print("Running the basic test cases from the original implementation.")
    print("This serves as a baseline for comparison with the comprehensive suite.")
    print("=" * 80)

    tests = get_test_cases()
    print(f"\nRunning {len(tests)} original test cases...\n")

    passed = 0
    total = 0
    start = time.time()

    results_by_category = {}

    for name, G1, G2 in tests:
        total += 1
        iso, match = compare_graphs(G1, G2)
        correct = (iso == match)

        # Extract category from test name
        category = name.split('_')[0]
        if category not in results_by_category:
            results_by_category[category] = {'passed': 0, 'total': 0, 'tests': []}

        results_by_category[category]['total'] += 1
        results_by_category[category]['tests'].append({
            'name': name,
            'iso': iso,
            'match': match,
            'correct': correct,
            'size': len(G1.nodes()),
            'edges': len(G1.edges())
        })

        if correct:
            passed += 1
            results_by_category[category]['passed'] += 1

        status = "✅ PASS" if correct else "❌ FAIL"
        iso_str = "ISO" if iso else "NON-ISO"
        match_str = "MATCH" if match else "NO-MATCH"
        print(f"[{name}] {iso_str} | {match_str} | {status}")

    elapsed = time.time() - start

    # Summary by category
    print(f"\n" + "=" * 80)
    print("RESULTS BY CATEGORY")
    print("=" * 80)

    for category in sorted(results_by_category.keys()):
        cat_data = results_by_category[category]
        cat_passed = cat_data['passed']
        cat_total = cat_data['total']
        cat_rate = cat_passed / cat_total * 100 if cat_total > 0 else 0

        print(f"\n{category.upper()}: {cat_passed}/{cat_total} passed ({cat_rate:.1f}%)")
        print("-" * 60)

        for test in cat_data['tests']:
            status = "✅ PASS" if test['correct'] else "❌ FAIL"
            iso_str = "ISO" if test['iso'] else "NON-ISO"
            match_str = "MATCH" if test['match'] else "NO-MATCH"
            size_info = f"(n={test['size']}, e={test['edges']})"
            print(f"  {test['name']:<25} | {iso_str:<8} | {match_str:<8} | {status} {size_info}")

    # Overall summary
    print(f"\n" + "=" * 80)
    print("ORIGINAL SUITE SUMMARY")
    print("=" * 80)
    print(f"Overall: {passed}/{total} correct ({passed/total*100:.1f}%)")
    print(f"Execution time: {elapsed:.2f} seconds")
    print(f"Average time per test: {elapsed/total:.3f} seconds")

    # Analysis
    if passed == total:
        print("🎉 Perfect score on original test suite!")
    elif passed/total >= 0.9:
        print("✅ Excellent performance on original tests")
    elif passed/total >= 0.8:
        print("👍 Good performance on original tests")
    else:
        print("⚠️ Some issues detected in original tests")

    # Graph size analysis
    all_tests = []
    for cat_data in results_by_category.values():
        all_tests.extend(cat_data['tests'])

    sizes = [t['size'] for t in all_tests]
    edges = [t['edges'] for t in all_tests]

    print(f"\nGraph Statistics:")
    print(f"  Size range: {min(sizes)} - {max(sizes)} vertices")
    print(f"  Average size: {sum(sizes)/len(sizes):.1f} vertices")
    print(f"  Edge range: {min(edges)} - {max(edges)} edges")
    print(f"  Average edges: {sum(edges)/len(edges):.1f} edges")

    return {
        'total': total,
        'passed': passed,
        'rate': passed/total,
        'time': elapsed,
        'categories': results_by_category
    }

def main():
    """Main execution function."""
    print("🧪 ORIGINAL GOSSIP TEST SUITE RUNNER")
    print("This runs the basic tests from the original gossip_cli.py implementation.\n")

    try:
        results = run_original_tests()

        print(f"\n" + "=" * 80)
        print("COMPARISON BASELINE ESTABLISHED")
        print("=" * 80)
        print("These results serve as a baseline for comparing the algorithm's")
        print("performance against the comprehensive test suite.")
        print(f"")
        print(f"Baseline Performance: {results['rate']*100:.1f}% success rate")
        print(f"Baseline Test Count: {results['total']} tests")
        print(f"Baseline Categories: {len(results['categories'])} categories")
        print("=" * 80)

        if results['rate'] >= 0.95:
            return 0  # Success
        else:
            print("⚠️ Warning: Baseline performance below 95%")
            return 1  # Warning

    except Exception as e:
        print(f"💥 Error running original tests: {e}")
        import traceback
        traceback.print_exc()
        return 2  # Error

if __name__ == "__main__":
    import sys
    exit_code = main()
    sys.exit(exit_code)
