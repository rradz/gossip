#!/usr/bin/env python3
"""
Curated benchmark runner for the gossip graph isomorphism algorithm.

Goals:
- Readable, concise per-test output with clear mismatches
- Grouped runs (basic, symmetry, circulant, products, hard, families, kneser, johnson, paley, rook_shrikhande, gpetersen, performance, all)
- Side-by-side comparison with NetworkX for every test
- Final performance summary with theoretical O(n*m) and measured stats
"""

from __future__ import annotations

import sys
import argparse
import pathlib
from typing import List, Optional, Sequence, Tuple

# Ensure local imports work without installation
PROJECT_ROOT = pathlib.Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

# Local benchmarks package
BENCH_DIR = PROJECT_ROOT / "benchmarks"
if str(BENCH_DIR) not in sys.path:
    sys.path.insert(0, str(BENCH_DIR))

from benchmarks.common import (
    Case,
    Result,
    run_cases,
    summarize,
    print_group_table,
    report_complexity,
)

# Import group builders
from benchmarks.families import build_cases as build_families
from benchmarks.circulant import build_cases as build_circulant
from benchmarks.other_families import (
    build_kneser_cases,
    build_johnson_cases,
    build_paley_cases,
    build_rook_shrikhande_cases,
    build_gpetersen_cases,
)
from benchmarks.trees import build_cases as build_trees
from benchmarks.zeta import build_cases as build_zeta
from benchmarks.er_complexity import build_cases as build_er_complexity

import networkx as nx
from gossip.utils import relabel_graph, generate_cfi_pair, generate_miyazaki_graph, generate_strongly_regular_graph


def build_basic_cases() -> List[Case]:
    cases: List[Case] = []
    basics = [
        ("Triangle", nx.cycle_graph(3)),
        ("Path (n=6)", nx.path_graph(6)),
        ("Cycle (n=10)", nx.cycle_graph(10)),
        ("Star (n=9)", nx.star_graph(8)),
        ("Complete K6", nx.complete_graph(6)),
        ("Grid 5×5", nx.grid_2d_graph(5, 5)),
        ("Random Tree (n=15)", nx.random_labeled_tree(15, seed=1)),
        ("Hypercube Q3", nx.hypercube_graph(3)),
        ("Wheel (n=10)", nx.wheel_graph(10)),
    ]
    for name, G in basics:
        cases.append(Case("basic", f"{name} — relabel", G, relabel_graph(G, seed=42), True))

    cases.extend(
        [
            Case("basic", "Cycle (10) vs Path (10)", nx.cycle_graph(10), nx.path_graph(10), False),
            Case("basic", "Star (11) vs Wheel (11)", nx.star_graph(10), nx.wheel_graph(10), False),
            Case("basic", "Petersen vs 3-regular(n=10)", nx.petersen_graph(), nx.random_regular_graph(3, 10, seed=2), False),
        ]
    )
    return cases


def build_symmetry_cases() -> List[Case]:
    cases: List[Case] = []
    for gen_name, disp in [
        ("petersen_graph", "Petersen"),
        ("dodecahedral_graph", "Dodecahedral"),
        ("desargues_graph", "Desargues"),
        ("heawood_graph", "Heawood"),
        ("moebius_kantor_graph", "Möbius–Kantor"),
        ("pappus_graph", "Pappus"),
    ]:
        if hasattr(nx, gen_name):
            G = getattr(nx, gen_name)()
            cases.append(Case("symmetry", f"{disp} — relabel", G, relabel_graph(G, seed=7), True))
    if hasattr(nx, "petersen_graph"):
        G = nx.petersen_graph()
        cases.append(Case("symmetry", "Petersen vs Complement", G, nx.complement(G), False))
    return cases


def build_hard_cases() -> List[Case]:
    cases: List[Case] = []
    for n in [6, 8]:
        base = nx.cycle_graph(n)
        G1, G2 = generate_cfi_pair(base)
        cases.append(Case("hard", f"CFI (cycle {n})", G1, G2, False))
    srg = generate_strongly_regular_graph(16, 6, 2, 2)
    if srg is not None:
        cases.append(Case("hard", "SRG(16,6,2,2) — relabel", srg, relabel_graph(srg, seed=11), True))
    for n in [6, 8, 10]:
        G = generate_miyazaki_graph(n)
        cases.append(Case("hard", f"Miyazaki (n={n}) — relabel", G, relabel_graph(G, seed=5), True))
    # Cospectral trees from tests
    T1 = nx.Graph([(0, 1), (0, 2), (0, 3), (1, 4), (1, 5)])
    T2 = nx.Graph([(0, 1), (0, 2), (1, 3), (1, 4), (2, 5)])
    cases.append(Case("hard", "Cospectral Trees (n=6)", T1, T2, False))
    # Random regular pairs
    for d in [3, 4]:
        for n in [12, 16]:
            if (n * d) % 2 == 0:
                cases.append(Case("hard", f"Random {d}-regular (n={n})", nx.random_regular_graph(d, n, seed=n + d), nx.random_regular_graph(d, n, seed=n + d + 1), None))
    return cases


def collect_groups(selected: Sequence[str]) -> List[Tuple[str, List[Case]]]:
    builders = {
        "basic": build_basic_cases,
        "symmetry": build_symmetry_cases,
        "families": build_families,
        "circulant": build_circulant,
        "kneser": build_kneser_cases,
        "johnson": build_johnson_cases,
        "paley": build_paley_cases,
        "rook_shrikhande": build_rook_shrikhande_cases,
        "gpetersen": build_gpetersen_cases,
        "trees": build_trees,
        "zeta": build_zeta,
        "er_complexity": build_er_complexity,
        "hard": build_hard_cases,
    }
    if not selected:
        names = list(builders.keys())
    elif "all" in selected:
        names = list(builders.keys())
    else:
        names = [n for n in builders.keys() if n in set(selected)]
    groups: List[Tuple[str, List[Case]]] = []
    for name in names:
        groups.append((name, builders[name]()))
    return groups


def print_usage(groups: List[str]) -> None:
    print("\nGossip Benchmarks — grouped runner")
    print("\nUsage:")
    print("  ./benchmark.py [group ...] [options]\n")
    print("Groups:")
    print("  " + ", ".join(groups))
    print("\nCommon options:")
    print("  --filter SUBSTR             Filter cases by substring in case name")
    print("  --complexity {n,m}          Fit observed scaling per group")
    print("  --nx-timeout-ms MS          Per-case NetworkX timeout (0 to disable)")
    print("  --nx-timeout-threshold K    If n*m <= K, run NX inline (no process)\n")
    print("Examples:")
    print("  ./benchmark.py                       # show this help")
    print("  ./benchmark.py circulant             # run circulant group")
    print("  ./benchmark.py kneser --filter K(9)  # run kneser cases matching 'K(9)'")
    print("  ./benchmark.py er_complexity --complexity n")
    print("  ./benchmark.py trees circulant --nx-timeout-ms 1500 --nx-timeout-threshold 5000\n")


def main(argv: Optional[Sequence[str]] = None) -> int:
    # If no args provided, show help and exit
    if argv is None and len(sys.argv) == 1:
        groups = [
            "basic",
            "symmetry",
            "families",
            "circulant",
            "kneser",
            "johnson",
            "paley",
            "rook_shrikhande",
            "gpetersen",
            "trees",
            "zeta",
            "er_complexity",
            "hard",
            "all",
        ]
        print_usage(groups)
        return 0

    parser = argparse.ArgumentParser(description="Gossip isomorphism benchmarks (modular groups)")
    parser.add_argument(
        "group",
        nargs="*",
        choices=[
            "basic",
            "symmetry",
            "families",
            "circulant",
            "kneser",
            "johnson",
            "paley",
            "rook_shrikhande",
            "gpetersen",
            "trees",
            "zeta",
            "er_complexity",
            "hard",
            "all",
        ],
        help="Groups to run (default: all)",
    )
    parser.add_argument("--filter", default=None, help="Substring to filter case names")
    parser.add_argument("--complexity", choices=["n", "m"], default=None, help="Report observed scaling vs n or m per group")
    parser.add_argument("--nx-timeout-ms", type=int, default=3000, help="Timeout in ms for NetworkX isomorphism per case (0 to disable)")
    parser.add_argument("--nx-timeout-threshold", type=int, default=3000, help="If n*m <= threshold, run NX inline to avoid process overhead")

    args = parser.parse_args(argv)

    groups = collect_groups(args.group or ["all"])
    all_results: List[Result] = []

    print("\n============================================================")
    print("Gossip Graph Isomorphism Benchmarks")
    print("============================================================")
    print(" Comparing Gossip vs NetworkX per test (times in ms).\n")

    for group_name, cases in groups:
        if args.filter:
            cases = [c for c in cases if args.filter.lower() in c.name.lower()]
        if not cases:
            continue
        group_results = run_cases(cases, nx_timeout_ms=args.nx_timeout_ms, nx_timeout_threshold=args.nx_timeout_threshold)
        print_group_table(group_name, group_results)
        correct, total, avg_tg, avg_tn, avg_sp = summarize(group_results)
        print(f" -> Summary: {correct}/{total} correct | avg gossip {avg_tg:.2f}ms | avg nx {avg_tn:.2f}ms | avg speedup x{avg_sp:.1f}")
        if args.complexity:
            report_complexity(group_results, size=args.complexity)
        all_results.extend(group_results)

    # Final performance report
    print("\n============================================================")
    print("Final Performance Report")
    print("============================================================")
    correct, total, avg_tg, avg_tn, avg_sp = summarize(all_results)
    print(f" -> Summary: {correct}/{total} correct | avg gossip {avg_tg:.2f}ms | avg nx {avg_tn:.2f}ms | avg speedup x{avg_sp:.1f}")
    print(
        "\nTheoretical complexity (claimed): time O(n*m), space O(n*m).\n"
        "This is a hobby project; results above are empirical and small-scale."
    )

    mismatches = [r for r in all_results if not r.correct]
    return 1 if mismatches else 0


if __name__ == "__main__":
    sys.exit(main())