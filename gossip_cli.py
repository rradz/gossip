# gossip_fingerprint_cli.py

import argparse
import networkx as nx
import itertools
import random
import time


def gossip_fingerprint_full(adj):
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

        fingerprints[v] = (len(adj[v]), sorted(timeline))

    return tuple(sorted(fingerprints.values()))

def srg_16_6_2_2():
    edges = [
        (0,1),(0,2),(0,3),(0,4),(0,5),(0,6),
        (1,2),(1,7),(1,8),(1,9),(1,10),
        (2,3),(2,11),(2,12),(2,13),
        (3,4),(3,14),(3,15),
        (4,5),(4,7),
        (5,6),(5,8),
        (6,9),(6,10),
        (7,11),(7,12),
        (8,11),(8,13),
        (9,12),(9,14),
        (10,13),(10,15),
        (11,14),
        (12,15),
        (13,14),
        (14,15)
    ]
    G = nx.Graph()
    G.add_edges_from(edges)
    return G


def make_cfi_pair(base, flip_edges):
    def build(flip=False):
        G = nx.Graph()
        for v in base.nodes():
            for i in range(3):
                G.add_edge(f"{v}_c", f"{v}_{i}")
        for (u, v) in base.edges():
            for i in range(3):
                if flip and (u, v) in flip_edges:
                    G.add_edge(f"{u}_{i}", f"{v}_{(i+1)%3}")
                else:
                    G.add_edge(f"{u}_{i}", f"{v}_{i}")
        return G
    return build(False), build(True)


def graph_to_adj(G):
    return {v: list(G.neighbors(v)) for v in G.nodes()}


def compare_graphs(G1, G2):
    adj1 = graph_to_adj(G1)
    adj2 = graph_to_adj(G2)
    f1 = gossip_fingerprint_full(adj1)
    f2 = gossip_fingerprint_full(adj2)
    iso = nx.is_isomorphic(G1, G2)
    match = f1 == f2
    return iso, match


def get_test_cases():
    tests = []

    # Standard WL traps
    for i in range(10):
        base = nx.cubical_graph()
        CFI1, CFI2 = make_cfi_pair(base, [(0,1),(2,3),(4,5),(6,7)])
        tests.append((f"CFI_{i}", CFI1, CFI2))

    for size in range(6, 20):
        G1 = nx.cycle_graph(size)
        G2 = nx.relabel_nodes(G1, lambda x: (x * 3) % size)
        tests.append((f"CycleRelabel_{size}", G1, G2))

    for size in range(6, 20):
        G1 = nx.path_graph(size)
        G2 = nx.relabel_nodes(G1, lambda x: (x * 5 + 1) % size)
        tests.append((f"PathRelabel_{size}", G1, G2))

    for i in range(5):
        G1 = nx.gnp_random_graph(15 + i, 0.3, seed=i)
        G2 = nx.relabel_nodes(G1, lambda x: (x * 7 + 3) % len(G1))
        tests.append((f"RandomRelabel_{i}", G1, G2))

    for i in range(5):
        G1 = srg_16_6_2_2()
        G2 = nx.relabel_nodes(G1, lambda x: (x * 9 + 1) % 16)
        tests.append((f"SRG_{i}", G1, G2))

    for i in range(10):
        G1 = nx.balanced_tree(r=2, h=3)
        G2 = G1.copy()
        if G2.has_edge(1, 3):
            G2.remove_edge(1, 3)
            G2.add_edge(2, 5)
        tests.append((f"TwistedTree_{i}", G1, G2))

    for i in range(10):
        G1 = nx.ladder_graph(5 + i)
        G2 = G1.copy()
        if G2.has_edge(0, 1):
            G2.remove_edge(0, 1)
            G2.add_edge(0, 3)
        tests.append((f"LadderMutate_{i}", G1, G2))

    for i in range(10):
        G1 = nx.complete_graph(10 + i)
        G2 = G1.copy()
        if G2.has_edge(0, 1):
            G2.remove_edge(0, 1)
            G2.add_edge(0, 2)
        tests.append((f"CompleteEdgeFlip_{i}", G1, G2))

    for i in range(10):
        G1 = nx.circulant_graph(12, [1, 2, 3])
        G2 = G1.copy()
        G2.remove_edge(0, 1)
        G2.add_edge(0, 4)
        tests.append((f"Circulant_{i}", G1, G2))

    return tests


def run_all_tests():
    tests = get_test_cases()
    print("\n=== Running All Gossip Fingerprint Tests ===\n")
    passed = 0
    total = 0
    start = time.time()

    for name, G1, G2 in tests:
        total += 1
        iso, match = compare_graphs(G1, G2)
        correct = (iso == match)
        print(f"[{name}] Isomorphic: {iso} | Fingerprint Match: {match} | {'✅ PASS' if correct else '❌ FAIL'}")
        if correct:
            passed += 1

    elapsed = time.time() - start
    print(f"\n=== Summary ===\n{passed}/{total} correct ({passed/total*100:.1f}%) in {elapsed:.2f} seconds")


def main():
    parser = argparse.ArgumentParser(description="Gossip fingerprint isomorphism checker")
    parser.add_argument("--graph1", help="Graph name for individual test")
    parser.add_argument("--graph2", help="Second graph name (optional)")
    parser.add_argument("--all", action="store_true", help="Run all preloaded hard tests")
    args = parser.parse_args()

    if args.all:
        run_all_tests()
        return

    if not args.graph1:
        print("Error: You must specify --graph1 or --all")
        return

    G1 = nx.read_adjlist(args.graph1) if args.graph1.endswith(".adj") else nx.gnp_random_graph(10, 0.3)
    if args.graph2:
        G2 = nx.read_adjlist(args.graph2) if args.graph2.endswith(".adj") else nx.gnp_random_graph(10, 0.3)
    else:
        G2 = nx.relabel_nodes(G1, lambda x: (hash(x) * 3) % len(G1))

    iso, match = compare_graphs(G1, G2)
    print("=== Gossip Fingerprint Comparison ===")
    print(f"Isomorphic: {iso}")
    print(f"Fingerprint Match: {match}")


if __name__ == "__main__":
    main()
