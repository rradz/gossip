"""
Showcase tests demonstrating the gossip algorithm on famous graph instances.

These tests are designed to be informative and educational, showing how the
algorithm performs on well-known graphs and hard instances from the literature.
"""

import pytest
import networkx as nx
import time
from typing import List, Tuple

from gossip.algorithm import GossipFingerprint
from gossip.utils import (
    generate_cfi_pair,
    generate_miyazaki_graph,
    generate_strongly_regular_graph,
    relabel_graph,
    are_isomorphic
)


@pytest.mark.showcase
def test_famous_graphs_showcase():
    """Demonstrate the algorithm on famous graphs from graph theory."""
    print("\n" + "="*70)
    print("FAMOUS GRAPHS SHOWCASE")
    print("="*70)
    print("\nTesting graph isomorphism on famous graphs from mathematics...")
    print("These graphs have interesting properties and symmetries.\n")

    gf = GossipFingerprint()

    famous_graphs = []

    # Add graphs that are available in this version of NetworkX
    graph_generators = [
        ("Petersen Graph", "petersen_graph",
         "The Petersen graph is a small graph that serves as a counterexample\n"
         "   to many conjectures in graph theory. It's 3-regular with 10 vertices."),

        ("Dodecahedral Graph", "dodecahedral_graph",
         "The skeleton of a dodecahedron - one of the five Platonic solids.\n"
         "   It has 20 vertices and is 3-regular."),

        ("Desargues Graph", "desargues_graph",
         "A symmetric bipartite cubic graph with 20 vertices.\n"
         "   Named after the French mathematician Girard Desargues."),

        ("Heawood Graph", "heawood_graph",
         "The smallest cubic graph of girth 6. It has 14 vertices\n"
         "   and represents the projective plane of order 2."),

        ("Möbius-Kantor Graph", "moebius_kantor_graph",
         "A symmetric bipartite cubic graph with 16 vertices.\n"
         "   It's the generalized Petersen graph GP(8,3)."),

        ("Pappus Graph", "pappus_graph",
         "An 18-vertex bipartite 3-regular graph.\n"
         "   It's the incidence graph of Pappus's configuration."),

        ("Tutte Graph", "tutte_graph",
         "A 3-regular graph with 46 vertices.\n"
         "   First counterexample to Tait's conjecture on Hamiltonian cycles."),
    ]

    for name, generator_name, description in graph_generators:
        if hasattr(nx, generator_name):
            graph_func = getattr(nx, generator_name)
            famous_graphs.append((name, graph_func(), description))

    if not famous_graphs:
        print("   ⚠️  No famous graphs available - using basic graphs")
        famous_graphs = [
            ("Petersen", nx.petersen_graph(), "Classic 3-regular graph"),
            ("Complete K5", nx.complete_graph(5), "Complete graph on 5 vertices"),
            ("Cycle C10", nx.cycle_graph(10), "10-vertex cycle"),
        ]

    print("┌" + "─"*68 + "┐")
    print("│" + " "*26 + "FAMOUS GRAPHS" + " "*29 + "│")
    print("├" + "─"*20 + "┬" + "─"*9 + "┬" + "─"*9 + "┬" + "─"*12 + "┬" + "─"*14 + "┤")
    print("│ Graph              │ Vertices│ Edges   │ Time (ms)  │ Result       │")
    print("├" + "─"*20 + "┼" + "─"*9 + "┼" + "─"*9 + "┼" + "─"*12 + "┼" + "─"*14 + "┤")

    for name, graph, description in famous_graphs:
        # Test against a relabeled version
        graph_perm = relabel_graph(graph, seed=42)

        # Time the comparison
        start = time.perf_counter()
        result = gf.compare(graph, graph_perm)
        elapsed = (time.perf_counter() - start) * 1000

        # Verify with NetworkX
        nx_result = are_isomorphic(graph, graph_perm)

        status = "✅ Pass" if result == nx_result else "❌ FAIL"

        print(f"│ {name:18} │ {graph.number_of_nodes():7} │ {graph.number_of_edges():7} │ "
              f"{elapsed:10.3f} │ {status:12} │")

    print("└" + "─"*20 + "┴" + "─"*9 + "┴" + "─"*9 + "┴" + "─"*12 + "┴" + "─"*14 + "┘")


@pytest.mark.showcase
def test_hard_instances_showcase():
    """Showcase performance on known hard instances for graph isomorphism."""
    print("\n" + "="*70)
    print("HARD INSTANCES SHOWCASE")
    print("="*70)
    print("\nThese are graphs specifically designed to be difficult for")
    print("graph isomorphism algorithms. They exploit various weaknesses")
    print("in different algorithmic approaches.\n")

    gf = GossipFingerprint()

    hard_instances = []

    # 1. CFI Graphs (Cai-Fürer-Immerman)
    print("🔬 Generating CFI graphs...")
    for base_size in [4, 5, 6]:
        base = nx.cycle_graph(base_size)
        try:
            G1, G2 = generate_cfi_pair(base)
            hard_instances.append((
                f"CFI (C_{base_size} base)",
                G1, G2,
                "Defeats the Weisfeiler-Leman algorithm"
            ))
        except:
            print(f"   ⚠️  Could not generate CFI with C_{base_size} base")

    # 2. Strongly Regular Graphs
    print("🔷 Generating strongly regular graphs...")
    try:
        srg = generate_strongly_regular_graph(16, 6, 2, 2)
        if srg:
            srg_perm = relabel_graph(srg, seed=42)
            hard_instances.append((
                "SRG(16,6,2,2)",
                srg, srg_perm,
                "Highly symmetric with regular structure"
            ))
    except:
        print("   ⚠️  Could not generate SRG(16,6,2,2)")

    # 3. Miyazaki Graphs
    print("🔀 Generating Miyazaki graphs...")
    for n in [6, 8]:
        try:
            miya = generate_miyazaki_graph(n)
            miya_perm = relabel_graph(miya, seed=42)
            hard_instances.append((
                f"Miyazaki-{n}",
                miya, miya_perm,
                "Special twist patterns challenge algorithms"
            ))
        except:
            print(f"   ⚠️  Could not generate Miyazaki-{n}")

    # 4. Random Regular Graphs
    print("🎲 Generating random regular graphs...")
    for k in [3, 4]:
        n = 20
        try:
            G1 = nx.random_regular_graph(k, n, seed=42)
            G2 = nx.random_regular_graph(k, n, seed=99)
            hard_instances.append((
                f"{k}-regular (n={n})",
                G1, G2,
                "Random regular graphs are often hard to distinguish"
            ))
        except:
            print(f"   ⚠️  Could not generate {k}-regular graph")

    # Print results table
    print("\n┌" + "─"*68 + "┐")
    print("│" + " "*24 + "HARD INSTANCES" + " "*30 + "│")
    print("├" + "─"*20 + "┬" + "─"*9 + "┬" + "─"*12 + "┬" + "─"*11 + "┬" + "─"*11 + "┤")
    print("│ Instance           │ Nodes   │ Gossip     │ NetworkX  │ Match?    │")
    print("├" + "─"*20 + "┼" + "─"*9 + "┼" + "─"*12 + "┼" + "─"*11 + "┼" + "─"*11 + "┤")

    for name, G1, G2, description in hard_instances:
        # Time gossip algorithm
        start = time.perf_counter()
        gossip_result = gf.compare(G1, G2)
        gossip_time = (time.perf_counter() - start) * 1000

        # Time NetworkX
        start = time.perf_counter()
        nx_result = are_isomorphic(G1, G2)
        nx_time = (time.perf_counter() - start) * 1000

        match = "✅" if gossip_result == nx_result else "❌"

        print(f"│ {name:18} │ {G1.number_of_nodes():7} │ {gossip_time:8.2f}ms │ "
              f"{nx_time:7.2f}ms │ {match:9} │")

    print("└" + "─"*20 + "┴" + "─"*9 + "┴" + "─"*12 + "┴" + "─"*11 + "┴" + "─"*11 + "┘")


@pytest.mark.showcase
def test_graph_families_showcase():
    """Demonstrate algorithm performance across different graph families."""
    print("\n" + "="*70)
    print("GRAPH FAMILIES PERFORMANCE")
    print("="*70)
    print("\nComparing algorithm performance across different graph types...")
    print("Each family has distinct structural properties.\n")

    gf = GossipFingerprint()

    families = [
        ("Complete", [nx.complete_graph(n) for n in [5, 10, 15]]),
        ("Cycle", [nx.cycle_graph(n) for n in [10, 20, 30]]),
        ("Path", [nx.path_graph(n) for n in [10, 20, 30]]),
        ("Star", [nx.star_graph(n) for n in [10, 20, 30]]),
        ("Grid", [nx.grid_2d_graph(n, n) for n in [3, 4, 5]]),
        ("Hypercube", [nx.hypercube_graph(n) for n in [3, 4, 5]]),
        ("Binary Tree", [nx.balanced_tree(2, h) for h in [3, 4, 5]]),
        ("Wheel", [nx.wheel_graph(n) for n in [10, 20, 30]]),
    ]

    print("┌" + "─"*68 + "┐")
    print("│" + " "*23 + "PERFORMANCE BY FAMILY" + " "*24 + "│")
    print("├" + "─"*15 + "┬" + "─"*8 + "┬" + "─"*8 + "┬" + "─"*10 + "┬" + "─"*10 + "┬" + "─"*11 + "┤")
    print("│ Family        │ Size   │ Edges  │ Time(ms) │ Speedup  │ Unique FPs │")
    print("├" + "─"*15 + "┼" + "─"*8 + "┼" + "─"*8 + "┼" + "─"*10 + "┼" + "─"*10 + "┼" + "─"*11 + "┤")

    for family_name, graphs in families:
        for G in graphs:
            # Create a relabeled version
            G_perm = relabel_graph(G, seed=42)

            # Time gossip
            start = time.perf_counter()
            gossip_result = gf.compare(G, G_perm)
            gossip_time = (time.perf_counter() - start) * 1000

            # Time NetworkX
            start = time.perf_counter()
            nx_result = are_isomorphic(G, G_perm)
            nx_time = (time.perf_counter() - start) * 1000

            # Count unique fingerprints (for symmetry analysis)
            from gossip.utils import graph_to_adjacency_list
            adj = graph_to_adjacency_list(G)
            fp = gf.compute(adj)
            unique_fps = len(set(fp))

            speedup = nx_time / gossip_time if gossip_time > 0 else float('inf')

            print(f"│ {family_name:13} │ {G.number_of_nodes():6} │ {G.number_of_edges():6} │ "
                  f"{gossip_time:8.2f} │ {speedup:7.1f}x │ {unique_fps:10} │")

    print("└" + "─"*15 + "┴" + "─"*8 + "┴" + "─"*8 + "┴" + "─"*10 + "┴" + "─"*10 + "┴" + "─"*11 + "┘")


@pytest.mark.showcase
def test_isomorphism_vs_non_isomorphism():
    """Compare algorithm behavior on isomorphic vs non-isomorphic pairs."""
    print("\n" + "="*70)
    print("ISOMORPHISM DETECTION SHOWCASE")
    print("="*70)
    print("\nDemonstrating correct detection of isomorphic and non-isomorphic pairs...\n")

    gf = GossipFingerprint()

    test_pairs = []

    # Isomorphic pairs (relabelings)
    print("✅ Creating isomorphic pairs (relabelings)...")
    for name, G in [
        ("Petersen", nx.petersen_graph()),
        ("4-Cube", nx.hypercube_graph(4)),
        ("K₆", nx.complete_graph(6)),
    ]:
        G_perm = relabel_graph(G, seed=99)
        test_pairs.append((name, G, G_perm, True, "Relabeled version"))

    # Non-isomorphic pairs with same parameters
    print("❌ Creating non-isomorphic pairs...")

    # Different graph types with same node count
    test_pairs.append((
        "Cycle vs Path",
        nx.cycle_graph(10),
        nx.path_graph(10),
        False,
        "Different structure"
    ))

    test_pairs.append((
        "Star vs Wheel",
        nx.star_graph(10),
        nx.wheel_graph(10),
        False,
        "Different degree sequences"
    ))

    # Same regular degree but different structure
    test_pairs.append((
        "Petersen vs 3-reg",
        nx.petersen_graph(),
        nx.random_regular_graph(3, 10, seed=42),
        False,
        "Same regularity, different structure"
    ))

    print("\n┌" + "─"*68 + "┐")
    print("│" + " "*21 + "ISOMORPHISM DETECTION" + " "*26 + "│")
    print("├" + "─"*20 + "┬" + "─"*10 + "┬" + "─"*10 + "┬" + "─"*10 + "┬" + "─"*12 + "┤")
    print("│ Pair               │ Expected │ Gossip   │ NetworkX │ Result     │")
    print("├" + "─"*20 + "┼" + "─"*10 + "┼" + "─"*10 + "┼" + "─"*10 + "┼" + "─"*12 + "┤")

    all_correct = True
    for name, G1, G2, expected_iso, reason in test_pairs:
        gossip_result = gf.compare(G1, G2)
        nx_result = are_isomorphic(G1, G2)

        expected_str = "ISO" if expected_iso else "NON-ISO"
        gossip_str = "ISO" if gossip_result else "NON-ISO"
        nx_str = "ISO" if nx_result else "NON-ISO"

        if gossip_result == nx_result == expected_iso:
            result = "✅ Correct"
        else:
            result = "❌ WRONG"
            all_correct = False

        print(f"│ {name:18} │ {expected_str:8} │ {gossip_str:8} │ "
              f"{nx_str:8} │ {result:10} │")

    print("└" + "─"*20 + "┴" + "─"*10 + "┴" + "─"*10 + "┴" + "─"*10 + "┴" + "─"*12 + "┘")

    if all_correct:
        print("\n🎉 All isomorphism tests passed correctly!")
    else:
        print("\n⚠️  Some tests failed - algorithm may need investigation")
