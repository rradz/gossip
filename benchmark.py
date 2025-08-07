#!/usr/bin/env python3
"""
Benchmark runner for graph isomorphism tests.
"""

import sys
import subprocess
import argparse
from typing import List, Tuple


def run_command(cmd: List[str], quiet: bool = True) -> Tuple[int, str, str]:
    """Run a command and return exit code, stdout, and stderr."""
    if quiet:
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode, result.stdout, result.stderr
    else:
        result = subprocess.run(cmd)
        return result.returncode, "", ""


def parse_pytest_output(stdout: str) -> Tuple[int, int, int]:
    """Parse pytest output to extract passed/failed/skipped counts."""
    import re

    # Count dots and F's in the progress line
    passed = failed = skipped = 0

    # Look for the progress line with dots and F's
    for line in stdout.split('\n'):
        if line.strip() and (line[0] in '.FEsx' or line.strip()[0] in '.FEsx'):
            # Count characters
            passed = line.count('.')
            failed = line.count('F') + line.count('E')
            skipped = line.count('s')
            if passed or failed or skipped:
                return passed, failed, skipped

    # Fallback: look for summary line
    for line in stdout.split('\n'):
        if ' passed' in line or ' failed' in line:
            passed_match = re.search(r'(\d+) passed', line)
            failed_match = re.search(r'(\d+) failed', line)
            skipped_match = re.search(r'(\d+) skipped', line)

            if passed_match:
                passed = int(passed_match.group(1))
            if failed_match:
                failed = int(failed_match.group(1))
            if skipped_match:
                skipped = int(skipped_match.group(1))

            if passed_match or failed_match:
                return passed, failed, skipped

    return passed, failed, skipped


def run_basic():
    """Run basic algorithm tests."""
    print("Running basic tests...")

    cmd = ["python", "-m", "pytest",
           "tests/test_algorithm.py",
           "-q", "--tb=no"]

    returncode, stdout, stderr = run_command(cmd)

    passed, failed, skipped = parse_pytest_output(stdout)

    if returncode == 0 and passed > 0:
        print(f"  ✓ {passed} tests passed")
    elif failed > 0:
        print(f"  ✗ {failed} tests failed, {passed} passed")
    else:
        print(f"  ⚠ No tests found or error running tests")

    return returncode == 0


def run_performance():
    """Run performance comparison tests."""
    print("Running performance tests...")

    cmd = ["python", "-m", "pytest",
           "tests/test_performance.py",
           "-q", "--tb=no"]

    returncode, stdout, stderr = run_command(cmd)

    passed, failed, _ = parse_pytest_output(stdout)

    if returncode == 0 and passed > 0:
        print(f"  ✓ {passed} tests passed")
    elif failed > 0:
        print(f"  ✗ {failed} tests failed, {passed} passed")
    else:
        print(f"  ⚠ No performance tests found")

    return returncode == 0


def run_hard():
    """Run hard instance tests."""
    print("Running hard instance tests...")

    cmd = ["python", "-m", "pytest",
           "tests/test_hard_instances.py",
           "-q", "--tb=no"]

    returncode, stdout, stderr = run_command(cmd)

    passed, failed, _ = parse_pytest_output(stdout)

    if returncode == 0 and passed > 0:
        print(f"  ✓ {passed} tests passed")
    elif failed > 0:
        print(f"  ✗ {failed} tests failed, {passed} passed")
    else:
        print(f"  ⚠ No hard instance tests found")

    return returncode == 0


def run_showcase(verbose: bool = False):
    """Run showcase demonstrations."""
    print("Running showcase demonstrations...")

    if verbose:
        cmd = ["python", "-m", "pytest",
               "tests/test_showcase.py",
               "-xvs", "--tb=no"]
        run_command(cmd, quiet=False)
    else:
        cmd = ["python", "-m", "pytest",
               "tests/test_showcase.py",
               "-q", "--tb=no"]

        returncode, stdout, stderr = run_command(cmd)

        passed, failed, _ = parse_pytest_output(stdout)

        if returncode == 0 and passed > 0:
            print(f"  ✓ {passed} tests passed")
        elif failed > 0:
            print(f"  ✗ {failed} tests failed, {passed} passed")
        else:
            print(f"  ⚠ No showcase tests found")

    return True


def run_all(debug: bool = False, coverage: bool = False):
    """Run all tests."""
    print("Running all tests...")

    cmd = ["python", "-m", "pytest", "tests/"]

    if debug:
        cmd.extend(["-v", "--tb=short"])
    else:
        cmd.extend(["-q", "--tb=no"])

    if coverage:
        cmd.extend(["--cov=src/gossip", "--cov-report=term-missing:skip-covered"])

    returncode, stdout, stderr = run_command(cmd, quiet=not debug)

    if not debug:
        passed, failed, skipped = parse_pytest_output(stdout)
        total = passed + failed + skipped
        if total > 0:
            if failed == 0:
                print(f"  ✓ All {passed} tests passed")
            else:
                print(f"  ✗ {failed} failed, {passed} passed")
                if skipped > 0:
                    print(f"    ({skipped} skipped)")
        else:
            print("  ⚠ No tests found")

    return returncode == 0


def show_commands():
    """Show available commands."""
    print("""
Graph Benchmark Runner - Available Commands:

  basic      Run basic algorithm tests
  perf       Run performance comparison tests
  hard       Run hard instance tests
  showcase   Run showcase demonstrations
  all        Run all tests

Options:
  --debug    Show detailed test output
  --coverage Show code coverage report
  --verbose  Show verbose output (for showcase)

Examples:
  ./benchmark.py              # Show this help
  ./benchmark.py basic        # Run basic tests
  ./benchmark.py all          # Run all tests
  ./benchmark.py all --debug  # Run all with details
""")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Graph isomorphism benchmark runner",
        add_help=False
    )

    parser.add_argument("command", nargs="?", default=None,
                       choices=["basic", "perf", "hard", "showcase", "all"],
                       help="Test command to run")
    parser.add_argument("--debug", action="store_true",
                       help="Show detailed output")
    parser.add_argument("--coverage", action="store_true",
                       help="Include coverage report")
    parser.add_argument("--verbose", action="store_true",
                       help="Verbose output for showcase")

    args = parser.parse_args()

    if args.command is None:
        show_commands()
        return 0

    success = True

    if args.command == "basic":
        success = run_basic()
    elif args.command == "perf":
        success = run_performance()
    elif args.command == "hard":
        success = run_hard()
    elif args.command == "showcase":
        success = run_showcase(verbose=args.verbose)
    elif args.command == "all":
        success = run_all(debug=args.debug, coverage=args.coverage)

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
