"""
Command-line interface for the gossip graph isomorphism algorithm.
"""

import argparse
import sys
import time
from pathlib import Path
from typing import Optional, Tuple

import networkx as nx

from .algorithm import GossipFingerprint
from .utils import (
    graph_to_adjacency_list,
    generate_random_regular_graph,
    generate_cfi_pair,
    generate_strongly_regular_graph,
    generate_circulant_graph,
    generate_miyazaki_graph,
    compute_graph_statistics,
    are_isomorphic,
    relabel_graph,
)


def load_graph(filepath: Path, format: str = "auto") -> nx.Graph:
    """
    Load a graph from a file.

    Args:
        filepath: Path to the graph file
        format: File format (auto, edgelist, gml, graphml, pajek)

    Returns:
        NetworkX graph object

    Raises:
        ValueError: If format is not supported or file cannot be read
    """
    if format == "auto":
        suffix = filepath.suffix.lower()
        format_map = {
            ".edges": "edgelist",
            ".edgelist": "edgelist",
            ".gml": "gml",
            ".graphml": "graphml",
            ".net": "pajek",
            ".pajek": "pajek",
        }
        format = format_map.get(suffix, "edgelist")

    try:
        if format == "edgelist":
            return nx.read_edgelist(filepath)
        elif format == "gml":
            return nx.read_gml(filepath)
        elif format == "graphml":
            return nx.read_graphml(filepath)
        elif format == "pajek":
            return nx.read_pajek(filepath)
        else:
            raise ValueError(f"Unsupported format: {format}")
    except Exception as e:
        raise ValueError(f"Failed to load graph from {filepath}: {e}")


def save_graph(graph: nx.Graph, filepath: Path, format: str = "auto") -> None:
    """
    Save a graph to a file.

    Args:
        graph: NetworkX graph to save
        filepath: Path to save the graph
        format: File format (auto, edgelist, gml, graphml, pajek)

    Raises:
        ValueError: If format is not supported or file cannot be written
    """
    if format == "auto":
        suffix = filepath.suffix.lower()
        format_map = {
            ".edges": "edgelist",
            ".edgelist": "edgelist",
            ".gml": "gml",
            ".graphml": "graphml",
            ".net": "pajek",
            ".pajek": "pajek",
        }
        format = format_map.get(suffix, "edgelist")

    try:
        if format == "edgelist":
            nx.write_edgelist(graph, filepath)
        elif format == "gml":
            nx.write_gml(graph, filepath)
        elif format == "graphml":
            nx.write_graphml(graph, filepath)
        elif format == "pajek":
            nx.write_pajek(graph, filepath)
        else:
            raise ValueError(f"Unsupported format: {format}")
    except Exception as e:
        raise ValueError(f"Failed to save graph to {filepath}: {e}")


def compare_graphs_cli(
    graph1: nx.Graph,
    graph2: nx.Graph,
    verbose: bool = False
) -> Tuple[bool, bool, float]:
    """
    Compare two graphs using gossip fingerprint and NetworkX isomorphism.

    Args:
        graph1: First graph
        graph2: Second graph
        verbose: Whether to print detailed information

    Returns:
        Tuple of (gossip_match, networkx_isomorphic, gossip_time)
    """
    if verbose:
        print("\nGraph Statistics:")
        print("-" * 50)
        stats1 = compute_graph_statistics(graph1)
        stats2 = compute_graph_statistics(graph2)

        print(f"Graph 1: {stats1['num_vertices']} vertices, {stats1['num_edges']} edges")
        print(f"  Density: {stats1['density']:.3f}")
        print(f"  Degree range: {stats1['min_degree']}-{stats1['max_degree']}")
        print(f"  Regular: {stats1['is_regular']}")

        print(f"Graph 2: {stats2['num_vertices']} vertices, {stats2['num_edges']} edges")
        print(f"  Density: {stats2['density']:.3f}")
        print(f"  Degree range: {stats2['min_degree']}-{stats2['max_degree']}")
        print(f"  Regular: {stats2['is_regular']}")

    # Compute gossip fingerprints
    gf = GossipFingerprint()

    start_time = time.perf_counter()
    gossip_match = gf.compare(graph1, graph2)
    gossip_time = time.perf_counter() - start_time

    # Check with NetworkX
    nx_iso = are_isomorphic(graph1, graph2)

    if verbose:
        print("\nResults:")
        print("-" * 50)
        print(f"Gossip fingerprint match: {gossip_match}")
        print(f"NetworkX isomorphic: {nx_iso}")
        print(f"Gossip computation time: {gossip_time:.6f} seconds")

        if gossip_match != nx_iso:
            print("\nWARNING: Gossip result differs from NetworkX!")
            # Print per-vertex fingerprints to aid debugging
            gf_dbg = GossipFingerprint()
            fp1 = gf_dbg.compute_raw_fingerprints(graph1)
            fp2 = gf_dbg.compute_raw_fingerprints(graph2)
            print("\nPer-vertex fingerprints (Graph 1):")
            for v in sorted(graph1.nodes()):
                print(f"  {v}: {fp1[v]}")
            print("\nPer-vertex fingerprints (Graph 2):")
            for v in sorted(graph2.nodes()):
                print(f"  {v}: {fp2[v]}")

    return gossip_match, nx_iso, gossip_time


def generate_test_graphs(
    graph_type: str,
    size: int,
    **kwargs
) -> Tuple[nx.Graph, nx.Graph]:
    """
    Generate a pair of test graphs.

    Args:
        graph_type: Type of graph to generate
        size: Size parameter for the graph
        **kwargs: Additional parameters for specific graph types

    Returns:
        Tuple of two graphs (may be isomorphic or not depending on type)
    """
    if graph_type == "regular":
        degree = kwargs.get("degree", 3)
        G1 = generate_random_regular_graph(size, degree, seed=42)
        G2 = generate_random_regular_graph(size, degree, seed=43)
        return G1, G2

    elif graph_type == "cfi":
        base = nx.random_graphs.erdos_renyi_graph(size, 0.3, seed=42)
        return generate_cfi_pair(base)

    elif graph_type == "srg":
        # Default to SRG(16, 6, 2, 2)
        G1 = generate_strongly_regular_graph(16, 6, 2, 2)
        if G1 is None:
            raise ValueError("Could not generate strongly regular graph")
        G2 = relabel_graph(G1, seed=42)
        return G1, G2

    elif graph_type == "circulant":
        connections = kwargs.get("connections", [1, 2])
        G1 = generate_circulant_graph(size, connections)
        G2 = generate_circulant_graph(size, connections[::-1])
        return G1, G2

    elif graph_type == "miyazaki":
        G1 = generate_miyazaki_graph(size)
        G2 = relabel_graph(G1, seed=42)
        return G1, G2

    elif graph_type == "rook_shrikhande":
        # Build 4x4 rook's graph
        if hasattr(nx, "rooks_graph"):
            R = nx.rooks_graph(4, 4)
        else:
            R = nx.Graph()
            for i in range(4):
                for j in range(4):
                    for jj in range(4):
                        if jj != j:
                            R.add_edge((i, j), (i, jj))
                    for ii in range(4):
                        if ii != i:
                            R.add_edge((i, j), (ii, j))
        # Build Shrikhande
        if hasattr(nx, "shrikhande_graph"):
            S = nx.shrikhande_graph()
        else:
            S = nx.Graph()
            for x in range(4):
                for y in range(4):
                    S.add_node((x, y))
            conn = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1)]
            for x in range(4):
                for y in range(4):
                    for dx, dy in conn:
                        nx2 = (x + dx) % 4
                        ny2 = (y + dy) % 4
                        S.add_edge((x, y), (nx2, ny2))
        return R, S

    elif graph_type == "shrikhande_torus":
        # Shrikhande vs torus C4□C4
        if hasattr(nx, "shrikhande_graph"):
            S = nx.shrikhande_graph()
        else:
            S = nx.Graph()
            for x in range(4):
                for y in range(4):
                    S.add_node((x, y))
            conn = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1)]
            for x in range(4):
                for y in range(4):
                    for dx, dy in conn:
                        nx2 = (x + dx) % 4
                        ny2 = (y + dy) % 4
                        S.add_edge((x, y), (nx2, ny2))
        T = nx.cartesian_product(nx.cycle_graph(4), nx.cycle_graph(4))
        return S, T

    elif graph_type == "random":
        p = kwargs.get("probability", 0.3)
        G1 = nx.random_graphs.erdos_renyi_graph(size, p, seed=42)
        G2 = nx.random_graphs.erdos_renyi_graph(size, p, seed=43)
        return G1, G2

    else:
        raise ValueError(f"Unknown graph type: {graph_type}")


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="Gossip graph isomorphism algorithm",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Compare two graph files
  gossip compare graph1.edgelist graph2.edgelist

  # Generate and test specific graph types
  gossip test --type cfi --size 10

  # Run with verbose output
  gossip compare graph1.gml graph2.gml --verbose

  # Generate test graphs and save them
  gossip generate --type srg --output graph1.gml graph2.gml
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Compare command
    compare_parser = subparsers.add_parser("compare", help="Compare two graphs")
    compare_parser.add_argument("graph1", type=Path, help="First graph file")
    compare_parser.add_argument("graph2", type=Path, help="Second graph file")
    compare_parser.add_argument(
        "--format", default="auto",
        choices=["auto", "edgelist", "gml", "graphml", "pajek"],
        help="Graph file format (default: auto-detect)"
    )
    compare_parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="Show detailed output"
    )

    # Test command
    test_parser = subparsers.add_parser("test", help="Test with generated graphs")
    test_parser.add_argument(
        "--type", default="random",
        choices=["regular", "cfi", "srg", "circulant", "miyazaki", "rook_shrikhande", "shrikhande_torus", "random"],
        help="Type of test graphs to generate"
    )
    test_parser.add_argument(
        "--size", type=int, default=10,
        help="Size of graphs to generate"
    )
    test_parser.add_argument(
        "--degree", type=int, default=3,
        help="Degree for regular graphs"
    )
    test_parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="Show detailed output"
    )

    # Generate command
    gen_parser = subparsers.add_parser("generate", help="Generate test graphs")
    gen_parser.add_argument(
        "--type", default="random",
        choices=["regular", "cfi", "srg", "circulant", "miyazaki", "rook_shrikhande", "shrikhande_torus", "random"],
        help="Type of graphs to generate"
    )
    gen_parser.add_argument(
        "--size", type=int, default=10,
        help="Size of graphs to generate"
    )
    gen_parser.add_argument(
        "--output", nargs=2, type=Path,
        default=[Path("graph1.edgelist"), Path("graph2.edgelist")],
        help="Output files for the two graphs"
    )
    gen_parser.add_argument(
        "--format", default="auto",
        choices=["auto", "edgelist", "gml", "graphml", "pajek"],
        help="Output format (default: auto-detect from extension)"
    )

    args = parser.parse_args()

    if args.command == "compare":
        try:
            G1 = load_graph(args.graph1, args.format)
            G2 = load_graph(args.graph2, args.format)
            gossip_match, nx_iso, time_taken = compare_graphs_cli(
                G1, G2, verbose=args.verbose
            )

            if not args.verbose:
                print(f"Gossip match: {gossip_match}")
                print(f"NetworkX isomorphic: {nx_iso}")
                print(f"Time: {time_taken:.6f}s")

            sys.exit(0 if gossip_match == nx_iso else 1)

        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.command == "test":
        try:
            G1, G2 = generate_test_graphs(
                args.type,
                args.size,
                degree=getattr(args, "degree", 3)
            )

            print(f"Testing {args.type} graphs with size {args.size}")
            gossip_match, nx_iso, time_taken = compare_graphs_cli(
                G1, G2, verbose=args.verbose
            )

            if not args.verbose:
                print(f"Gossip match: {gossip_match}")
                print(f"NetworkX isomorphic: {nx_iso}")
                print(f"Time: {time_taken:.6f}s")

            if gossip_match != nx_iso:
                print("WARNING: Results differ!", file=sys.stderr)
                sys.exit(1)
            else:
                print("Results match!")

        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.command == "generate":
        try:
            G1, G2 = generate_test_graphs(
                args.type,
                args.size
            )

            save_graph(G1, args.output[0], args.format)
            save_graph(G2, args.output[1], args.format)

            print(f"Generated {args.type} graphs:")
            print(f"  Graph 1: {args.output[0]} ({G1.number_of_nodes()} nodes, {G1.number_of_edges()} edges)")
            print(f"  Graph 2: {args.output[1]} ({G2.number_of_nodes()} nodes, {G2.number_of_edges()} edges)")

        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
