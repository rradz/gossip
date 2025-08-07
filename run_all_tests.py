#!/usr/bin/env python3
"""
Unified test runner for all graph isomorphism test suites.
Runs comprehensive tests and hard instances, provides detailed analysis.
"""

import time
import sys
from collections import defaultdict

try:
    from test_gossip_comprehensive import ComprehensiveGraphTests
    from test_gossip_hard_instances import HardInstanceTests
except ImportError as e:
    print(f"Error importing test modules: {e}")
    print("Make sure test_gossip_comprehensive.py and test_gossip_hard_instances.py are in the same directory.")
    sys.exit(1)


class UnifiedTestRunner:
    def __init__(self):
        self.all_results = []
        self.comprehensive_results = None
        self.hard_instance_results = None

    def run_all_tests(self):
        """Run all test suites and collect results."""
        print("🧪 GOSSIP GRAPH ISOMORPHISM ALGORITHM - UNIFIED TEST SUITE")
        print("=" * 80)
        print("This test suite evaluates the Gossip fingerprint algorithm against")
        print("a comprehensive collection of challenging graph isomorphism instances.")
        print("=" * 80)

        total_start_time = time.time()

        # Run comprehensive tests
        print("\n" + "🔬 PHASE 1: COMPREHENSIVE TEST SUITE")
        print("=" * 60)
        comprehensive_suite = ComprehensiveGraphTests()
        self.comprehensive_results = comprehensive_suite.run_all_tests()

        print("\n" + "🎯 PHASE 2: HARD INSTANCES TEST SUITE")
        print("=" * 60)
        hard_instance_suite = HardInstanceTests()
        self.hard_instance_results = hard_instance_suite.run_all_hard_tests()

        total_time = time.time() - total_start_time

        # Combine results
        self.all_results = comprehensive_suite.test_results + hard_instance_suite.test_results

        # Comprehensive analysis
        self.perform_comprehensive_analysis(total_time)

        return self.generate_final_report()

    def perform_comprehensive_analysis(self, total_time):
        """Perform detailed analysis of all test results."""
        print("\n" + "📊 COMPREHENSIVE ANALYSIS")
        print("=" * 80)

        # Overall statistics
        total_tests = len(self.all_results)
        passed_tests = sum(1 for r in self.all_results if r['correct'])
        overall_rate = passed_tests / total_tests if total_tests > 0 else 0

        print(f"Overall Performance: {passed_tests}/{total_tests} tests passed ({overall_rate*100:.1f}%)")
        print(f"Total execution time: {total_time:.2f} seconds")
        print(f"Average time per test: {total_time/total_tests:.3f} seconds")

        # Performance by test suite
        comp_rate = self.comprehensive_results['rate']
        hard_rate = self.hard_instance_results['rate']
        comp_total = self.comprehensive_results['total']
        hard_total = self.hard_instance_results['total']

        print(f"\nTest Suite Breakdown:")
        print(f"  Comprehensive Suite: {self.comprehensive_results['passed']}/{comp_total} ({comp_rate*100:.1f}%)")
        print(f"  Hard Instances:      {self.hard_instance_results['passed']}/{hard_total} ({hard_rate*100:.1f}%)")

        # Analyze by graph size
        self.analyze_by_size()

        # Analyze by category
        self.analyze_by_category()

        # Analyze failure patterns
        self.analyze_failure_patterns()

        # Performance metrics
        self.analyze_performance_metrics()

    def analyze_by_size(self):
        """Analyze performance by graph size."""
        print(f"\n📏 Performance by Graph Size:")
        print("-" * 40)

        size_stats = defaultdict(list)
        for result in self.all_results:
            size_stats[result['size']].append(result['correct'])

        # Sort by size and display
        for size in sorted(size_stats.keys()):
            results = size_stats[size]
            passed = sum(results)
            total = len(results)
            rate = passed / total if total > 0 else 0

            # Add visual indicator for performance
            if rate >= 0.95:
                indicator = "🟢"
            elif rate >= 0.80:
                indicator = "🟡"
            else:
                indicator = "🔴"

            print(f"  {indicator} Size {size:2d}: {passed:2d}/{total:2d} ({rate*100:5.1f}%)")

        # Identify problematic sizes
        problem_sizes = [size for size, results in size_stats.items()
                        if sum(results) / len(results) < 0.8]
        if problem_sizes:
            print(f"  ⚠️  Problematic sizes: {problem_sizes}")

    def analyze_by_category(self):
        """Analyze performance by test category."""
        print(f"\n📂 Performance by Category:")
        print("-" * 40)

        category_stats = defaultdict(list)
        for result in self.all_results:
            category_stats[result['category']].append(result['correct'])

        # Sort by performance rate
        category_performance = []
        for category, results in category_stats.items():
            passed = sum(results)
            total = len(results)
            rate = passed / total if total > 0 else 0
            category_performance.append((rate, category, passed, total))

        category_performance.sort(key=lambda x: x[0])

        for rate, category, passed, total in category_performance:
            if rate >= 0.95:
                indicator = "🟢"
            elif rate >= 0.80:
                indicator = "🟡"
            else:
                indicator = "🔴"

            print(f"  {indicator} {category:<20}: {passed:2d}/{total:2d} ({rate*100:5.1f}%)")

        # Highlight categories needing attention
        weak_categories = [cat for rate, cat, p, t in category_performance if rate < 0.9]
        if weak_categories:
            print(f"  ⚠️  Categories needing attention: {', '.join(weak_categories)}")

    def analyze_failure_patterns(self):
        """Analyze patterns in test failures."""
        print(f"\n🔍 Failure Pattern Analysis:")
        print("-" * 40)

        failures = [r for r in self.all_results if not r['correct']]

        if not failures:
            print("  🎉 No failures detected!")
            return

        print(f"  Total failures: {len(failures)}")

        # Analyze failure types
        false_positives = sum(1 for f in failures if f['fingerprint_match'] and not f['isomorphic'])
        false_negatives = sum(1 for f in failures if not f['fingerprint_match'] and f['isomorphic'])

        print(f"  False positives: {false_positives} (fingerprint says match, but not isomorphic)")
        print(f"  False negatives: {false_negatives} (fingerprint says no match, but isomorphic)")

        # Group failures by category
        failure_categories = defaultdict(int)
        for failure in failures:
            failure_categories[failure['category']] += 1

        if failure_categories:
            print(f"  Failures by category:")
            for category, count in sorted(failure_categories.items()):
                print(f"    {category}: {count}")

        # Analyze failure by graph properties
        failure_sizes = [f['size'] for f in failures]
        failure_edges = [f['edges'] for f in failures]

        if failure_sizes:
            avg_fail_size = sum(failure_sizes) / len(failure_sizes)
            max_fail_size = max(failure_sizes)
            min_fail_size = min(failure_sizes)
            print(f"  Failed graph sizes: avg={avg_fail_size:.1f}, range=[{min_fail_size}, {max_fail_size}]")

        if failure_edges:
            avg_fail_edges = sum(failure_edges) / len(failure_edges)
            print(f"  Average edges in failed graphs: {avg_fail_edges:.1f}")

    def analyze_performance_metrics(self):
        """Analyze algorithm performance metrics."""
        print(f"\n⚡ Algorithm Performance Metrics:")
        print("-" * 40)

        # Graph complexity analysis
        sizes = [r['size'] for r in self.all_results]
        edges = [r['edges'] for r in self.all_results]

        print(f"  Graph size range: {min(sizes)} - {max(sizes)} vertices")
        print(f"  Average graph size: {sum(sizes)/len(sizes):.1f} vertices")
        print(f"  Edge count range: {min(edges)} - {max(edges)} edges")
        print(f"  Average edge count: {sum(edges)/len(edges):.1f} edges")

        # Success rate by graph density
        dense_graphs = [r for r in self.all_results if r['edges'] / (r['size'] * (r['size'] - 1) / 2) > 0.5]
        sparse_graphs = [r for r in self.all_results if r['edges'] / (r['size'] * (r['size'] - 1) / 2) <= 0.5]

        if dense_graphs:
            dense_success = sum(1 for r in dense_graphs if r['correct']) / len(dense_graphs)
            print(f"  Dense graphs (>50% edges): {dense_success*100:.1f}% success rate")

        if sparse_graphs:
            sparse_success = sum(1 for r in sparse_graphs if r['correct']) / len(sparse_graphs)
            print(f"  Sparse graphs (≤50% edges): {sparse_success*100:.1f}% success rate")

        # Isomorphic vs non-isomorphic performance
        iso_tests = [r for r in self.all_results if r['isomorphic']]
        non_iso_tests = [r for r in self.all_results if not r['isomorphic']]

        if iso_tests:
            iso_success = sum(1 for r in iso_tests if r['correct']) / len(iso_tests)
            print(f"  Isomorphic pairs: {iso_success*100:.1f}% success rate")

        if non_iso_tests:
            non_iso_success = sum(1 for r in non_iso_tests if r['correct']) / len(non_iso_tests)
            print(f"  Non-isomorphic pairs: {non_iso_success*100:.1f}% success rate")

    def generate_final_report(self):
        """Generate final assessment and recommendations."""
        print("\n" + "🎯 FINAL ASSESSMENT")
        print("=" * 80)

        total_tests = len(self.all_results)
        passed_tests = sum(1 for r in self.all_results if r['correct'])
        overall_rate = passed_tests / total_tests if total_tests > 0 else 0

        # Overall assessment
        if overall_rate >= 0.95:
            grade = "EXCELLENT (A+)"
            color = "🟢"
            assessment = "Outstanding performance across all test categories"
        elif overall_rate >= 0.90:
            grade = "VERY GOOD (A)"
            color = "🟢"
            assessment = "Strong performance with minor areas for improvement"
        elif overall_rate >= 0.80:
            grade = "GOOD (B)"
            color = "🟡"
            assessment = "Good performance but some challenging cases need attention"
        elif overall_rate >= 0.70:
            grade = "FAIR (C)"
            color = "🟡"
            assessment = "Adequate performance with several areas needing improvement"
        else:
            grade = "NEEDS IMPROVEMENT (D)"
            color = "🔴"
            assessment = "Significant weaknesses detected, algorithm needs refinement"

        print(f"{color} Overall Grade: {grade}")
        print(f"Success Rate: {overall_rate*100:.1f}% ({passed_tests}/{total_tests})")
        print(f"Assessment: {assessment}")

        # Specific recommendations
        print(f"\n📋 Recommendations:")

        failures = [r for r in self.all_results if not r['correct']]
        if not failures:
            print("  ✅ No specific improvements needed - algorithm performs excellently!")
        else:
            # Category-specific recommendations
            failure_categories = defaultdict(int)
            for failure in failures:
                failure_categories[failure['category']] += 1

            for category, count in sorted(failure_categories.items(), key=lambda x: x[1], reverse=True):
                print(f"  🔧 Investigate {category} graphs ({count} failures)")

            # Size-based recommendations
            large_failures = [f for f in failures if f['size'] > 20]
            if large_failures:
                print(f"  📏 Consider scalability optimizations for larger graphs")

            # Density-based recommendations
            dense_failures = [f for f in failures if f['edges'] / (f['size'] * (f['size'] - 1) / 2) > 0.7]
            if dense_failures:
                print(f"  🔗 Investigate dense graph handling")

        print(f"\n🔬 Algorithm Strengths:")
        # Identify strong categories
        category_stats = defaultdict(list)
        for result in self.all_results:
            category_stats[result['category']].append(result['correct'])

        strong_categories = []
        for category, results in category_stats.items():
            rate = sum(results) / len(results)
            if rate >= 0.95:
                strong_categories.append(category)

        if strong_categories:
            for category in strong_categories[:5]:  # Top 5
                print(f"  ✨ Excellent performance on {category} graphs")

        # Summary statistics for the report
        report_data = {
            'overall_rate': overall_rate,
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'grade': grade,
            'comprehensive_rate': self.comprehensive_results['rate'],
            'hard_instance_rate': self.hard_instance_results['rate'],
            'failure_count': len(failures),
            'strong_categories': strong_categories
        }

        print(f"\n" + "=" * 80)
        print(f"📄 Test suite completed successfully!")
        print(f"   Results saved in test execution - refer to detailed output above")
        print(f"=" * 80)

        return report_data


def main():
    """Main execution function."""
    runner = UnifiedTestRunner()

    try:
        report = runner.run_all_tests()

        # Return appropriate exit code
        if report['overall_rate'] >= 0.8:
            print(f"\n✅ Test suite PASSED with {report['overall_rate']*100:.1f}% success rate")
            return 0
        else:
            print(f"\n❌ Test suite FAILED with {report['overall_rate']*100:.1f}% success rate")
            return 1

    except KeyboardInterrupt:
        print(f"\n\n⚠️ Test execution interrupted by user")
        return 130
    except Exception as e:
        print(f"\n\n💥 Test execution failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
