#!/usr/bin/env python3
"""
Diagnostic script to investigate the failing alt_circulant_13 case.
This script recreates the exact failing test and analyzes why the gossip
algorithm produces a false positive.
"""

import networkx as nx
import random
from collections import defaultdict
from gossip_cli import gossip_fingerprint_full, graph_to_adj

def create_circulant_graphs():
    """Recreate the exact failing test case."""
    n = 13
    jumps = [1, 3, 4]

    # Original circulant
    circ1 = nx.circulant_graph(n, jumps)

    # Create alternative with different jump pattern
    # From the test code: alt_jumps = jumps[:-1] + [(jumps[-1] + 1) % (n//2) + 1]
    # jumps[-1] = 4
    # (4 + 1) % (13//2) + 1 = 5 % 6 + 1 = 5 + 1 = 6
    alt_jumps = [1, 3, 6]
    circ2 = nx.circulant_graph(n, alt_jumps)

    return circ1, circ2, jumps, alt_jumps

def analyze_graph_properties(G1, G2, name1, name2):
    """Analyze basic graph properties."""
    print(f"\n=== Graph Properties Analysis ===")
    print(f"{name1}: n={len(G1.nodes())}, m={len(G1.edges())}")
    print(f"{name2}: n={len(G2.nodes())}, m={len(G2.edges())}")

    # Degree sequences
    deg1 = sorted([G1.degree(v) for v in G1.nodes()])
    deg2 = sorted([G2.degree(v) for v in G2.nodes()])
    print(f"{name1} degree sequence: {deg1}")
    print(f"{name2} degree sequence: {deg2}")
    print(f"Degree sequences equal: {deg1 == deg2}")

    # Adjacency patterns
    print(f"\n{name1} adjacency lists:")
    for v in sorted(G1.nodes()):
        neighbors = sorted(G1.neighbors(v))
        print(f"  {v}: {neighbors}")

    print(f"\n{name2} adjacency lists:")
    for v in sorted(G2.nodes()):
        neighbors = sorted(G2.neighbors(v))
        print(f"  {v}: {neighbors}")

def analyze_circulant_structure(n, jumps1, jumps2):
    """Analyze the circulant structure differences."""
    print(f"\n=== Circulant Structure Analysis ===")
    print(f"n = {n}")
    print(f"Original jumps: {jumps1}")
    print(f"Alternative jumps: {jumps2}")

    # Analyze jump patterns
    print(f"\nJump analysis:")
    for i, (j1, j2) in enumerate(zip(jumps1, jumps2)):
        if j1 != j2:
            print(f"  Jump {i}: {j1} -> {j2} (difference: {j2-j1})")
        else:
            print(f"  Jump {i}: {j1} (unchanged)")

    # Analyze what edges each creates
    print(f"\nEdge patterns from jumps:")
    print(f"Original jumps {jumps1}:")
    edges1 = set()
    for i in range(n):
        for jump in jumps1:
            edges1.add((i, (i + jump) % n))
            edges1.add((i, (i - jump) % n))

    print(f"Alternative jumps {jumps2}:")
    edges2 = set()
    for i in range(n):
        for jump in jumps2:
            edges2.add((i, (i + jump) % n))
            edges2.add((i, (i - jump) % n))

    # Find differences
    only_in_1 = edges1 - edges2
    only_in_2 = edges2 - edges1
    common = edges1 & edges2

    print(f"  Common edges: {len(common)}")
    print(f"  Only in original: {len(only_in_1)} - {sorted(only_in_1)}")
    print(f"  Only in alternative: {len(only_in_2)} - {sorted(only_in_2)}")

def debug_gossip_fingerprint(G1, G2, name1, name2):
    """Debug the gossip fingerprint computation step by step."""
    print(f"\n=== Gossip Fingerprint Debug ===")

    adj1 = graph_to_adj(G1)
    adj2 = graph_to_adj(G2)

    print(f"Computing fingerprint for {name1}...")
    fp1 = gossip_fingerprint_full(adj1)

    print(f"Computing fingerprint for {name2}...")
    fp2 = gossip_fingerprint_full(adj2)

    print(f"\nFingerprint comparison:")
    print(f"FP1 length: {len(fp1)}")
    print(f"FP2 length: {len(fp2)}")
    print(f"Fingerprints equal: {fp1 == fp2}")

    if fp1 == fp2:
        print("❌ FALSE POSITIVE: Fingerprints match but graphs are non-isomorphic!")
    else:
        print("✅ Fingerprints correctly distinguish the graphs")

    # Compare fingerprints element by element
    print(f"\nDetailed fingerprint comparison:")
    for i, (f1, f2) in enumerate(zip(fp1, fp2)):
        if f1 != f2:
            print(f"  Position {i}: {f1} vs {f2} - DIFFERENT")
        else:
            print(f"  Position {i}: {f1} - SAME")

    return fp1, fp2

def debug_gossip_process(adj, graph_name):
    """Step through the gossip process for one graph."""
    print(f"\n=== Detailed Gossip Process for {graph_name} ===")

    fingerprints = {}
    for v in adj:
        print(f"\nStarting gossip from vertex {v}:")
        knowers = {v}
        new_knowers = {v}
        seen_edges = set()
        timeline = []
        iteration = 0

        while new_knowers:
            print(f"  Iteration {iteration}: knowers = {sorted(knowers)}")
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
                        event = (iteration, deg_u, 1, deg_w)
                        timeline.append(event)
                        next_new_knowers.add(w)
                        print(f"    {u} tells {w}: {event}")
                    elif w_knows and not u_knows:
                        event = (iteration, deg_w, 1, deg_u)
                        timeline.append(event)
                        next_new_knowers.add(u)
                        print(f"    {w} tells {u}: {event}")
                    else:
                        spreader = u if deg_u <= deg_w else w
                        listener = w if spreader == u else u
                        event = (iteration, len(adj[spreader]), 0, len(adj[listener]))
                        timeline.append(event)
                        print(f"    Both know, spreader {spreader} -> {listener}: {event}")

            knowers |= next_new_knowers
            new_knowers = next_new_knowers
            iteration += 1

        fingerprints[v] = (len(adj[v]), sorted(timeline))
        print(f"  Final fingerprint for vertex {v}: {fingerprints[v]}")

    final_fp = tuple(sorted(fingerprints.values()))
    print(f"\nFinal graph fingerprint: {final_fp}")
    return final_fp

def check_isomorphism_verification():
    """Verify that the graphs are actually non-isomorphic."""
    print(f"\n=== Isomorphism Verification ===")

    G1, G2, jumps1, jumps2 = create_circulant_graphs()

    # Use NetworkX to verify
    is_iso = nx.is_isomorphic(G1, G2)
    print(f"NetworkX isomorphism check: {is_iso}")

    if not is_iso:
        print("✅ Confirmed: Graphs are non-isomorphic")
    else:
        print("❌ Unexpected: NetworkX says graphs are isomorphic!")

    # Additional checks
    print(f"\nAdditional verification:")

    # Check if there's an obvious automorphism that maps one to the other
    # For circulant graphs, rotations are always automorphisms
    print(f"Checking rotational equivalence...")

    # Get edge sets
    edges1 = set(G1.edges())
    edges2 = set(G2.edges())

    # Try all rotations
    for rotation in range(13):
        rotated_edges2 = set()
        for u, v in edges2:
            new_u = (u + rotation) % 13
            new_v = (v + rotation) % 13
            rotated_edges2.add(tuple(sorted([new_u, new_v])))

        if edges1 == rotated_edges2:
            print(f"  Rotation by {rotation} makes graphs identical!")
            return True

    print(f"  No rotation makes the graphs identical")
    return False

def main():
    """Main diagnostic function."""
    print("🔍 DEBUGGING CIRCULANT FAILURE CASE")
    print("=" * 60)

    # Set seed for reproducibility
    random.seed(42)

    # Create the failing test case
    G1, G2, jumps1, jumps2 = create_circulant_graphs()

    # Verify they're actually non-isomorphic
    really_non_iso = not check_isomorphism_verification()

    if not really_non_iso:
        print("🚨 CRITICAL: The graphs might actually be isomorphic!")
        print("    This would mean the test case itself is wrong, not the algorithm.")
        return

    # Analyze basic properties
    analyze_graph_properties(G1, G2, "Original", "Alternative")

    # Analyze circulant structure
    analyze_circulant_structure(13, jumps1, jumps2)

    # Debug gossip fingerprints
    fp1, fp2 = debug_gossip_fingerprint(G1, G2, "Original", "Alternative")

    if fp1 == fp2:
        print(f"\n🎯 DETAILED ANALYSIS OF WHY FINGERPRINTS MATCH")
        print("=" * 50)

        # Step through gossip process for both graphs
        adj1 = graph_to_adj(G1)
        adj2 = graph_to_adj(G2)

        fp1_detailed = debug_gossip_process(adj1, "Original")
        fp2_detailed = debug_gossip_process(adj2, "Alternative")

        print(f"\n🔍 CONCLUSION:")
        if fp1_detailed == fp2_detailed:
            print("The gossip algorithm fails to distinguish these graphs because:")
            print("- Both graphs have identical local spreading patterns")
            print("- The structural differences don't affect the gossip dynamics")
            print("- This suggests a limitation in the gossip fingerprinting approach")
        else:
            print("Unexpected: Detailed analysis shows different fingerprints!")

if __name__ == "__main__":
    main()
