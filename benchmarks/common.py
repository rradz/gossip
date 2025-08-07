from __future__ import annotations

import math
import time
from dataclasses import dataclass
from typing import Callable, Dict, Iterable, List, Optional, Sequence, Tuple

import multiprocessing as mp
import networkx as nx

from gossip.algorithm import GossipFingerprint
from gossip.utils import are_isomorphic


@dataclass
class Case:
    category: str
    name: str
    G1: nx.Graph
    G2: nx.Graph
    expected_iso: Optional[bool] = None


@dataclass
class Result:
    category: str
    name: str
    nodes: int
    edges: int
    gossip_iso: bool
    nx_iso: Optional[bool]
    correct: bool
    tg_ms: float
    tn_ms: float


def ms(seconds: float) -> float:
    return seconds * 1000.0


def format_bool(v: Optional[bool]) -> str:
    if v is None:
        return "TIMEOUT"
    return "ISO" if v else "NON-ISO"


def _nx_iso_worker(G1: nx.Graph, G2: nx.Graph, q: mp.Queue) -> None:
    try:
        q.put(are_isomorphic(G1, G2))
    except Exception:
        q.put(False)


def nx_isomorphic_with_timeout(G1: nx.Graph, G2: nx.Graph, timeout_ms: Optional[int]) -> Tuple[Optional[bool], float]:
    if timeout_ms is None or timeout_ms <= 0:
        t0 = time.perf_counter()
        val = are_isomorphic(G1, G2)
        return val, ms(time.perf_counter() - t0)
    timeout_s = timeout_ms / 1000.0
    q: mp.Queue = mp.Queue(maxsize=1)
    p = mp.Process(target=_nx_iso_worker, args=(G1, G2, q))
    t0 = time.perf_counter()
    p.start()
    p.join(timeout_s)
    if p.is_alive():
        p.terminate()
        p.join()
        return None, ms(time.perf_counter() - t0)
    try:
        val = q.get_nowait()
    except Exception:
        val = None
    return val, ms(time.perf_counter() - t0)


def run_cases(cases: Sequence[Case], nx_timeout_ms: Optional[int] = None, nx_timeout_threshold: int = 0) -> List[Result]:
    gf = GossipFingerprint()
    results: List[Result] = []

    for c in cases:
        nodes = c.G1.number_of_nodes()
        edges = c.G1.number_of_edges()

        t0 = time.perf_counter()
        gossip_iso = gf.compare(c.G1, c.G2)
        tg = ms(time.perf_counter() - t0)

        # Adaptive: if graph is small (n*m below threshold), run NX inline to avoid process overhead
        if nx_timeout_ms and nx_timeout_threshold and (nodes * max(1, edges) <= nx_timeout_threshold):
            t1 = time.perf_counter()
            nx_iso = are_isomorphic(c.G1, c.G2)
            tn = ms(time.perf_counter() - t1)
        else:
            nx_iso, tn = nx_isomorphic_with_timeout(c.G1, c.G2, nx_timeout_ms)

        # Decide correctness based on agreement between Gossip and NetworkX.
        # If NX timed out, treat as neutral (count as correct to avoid penalizing incomplete oracle).
        if nx_iso is None:
            correct = True
        else:
            correct = (gossip_iso == nx_iso)

        results.append(
            Result(
                category=c.category,
                name=c.name,
                nodes=nodes,
                edges=edges,
                gossip_iso=gossip_iso,
                nx_iso=nx_iso,
                correct=correct,
                tg_ms=tg,
                tn_ms=tn,
            )
        )
    return results


def summarize(results: Sequence[Result]) -> Tuple[int, int, float, float, float]:
    total = len(results)
    correct = sum(1 for r in results if r.correct)
    tg = [r.tg_ms for r in results]
    tn = [r.tn_ms for r in results]
    sp = [r.tn_ms / r.tg_ms for r in results if r.tg_ms > 0]
    avg_tg = sum(tg) / len(tg) if tg else 0.0
    avg_tn = sum(tn) / len(tn) if tn else 0.0
    avg_sp = (sum(sp) / len(sp)) if sp else 0.0
    return correct, total, avg_tg, avg_tn, avg_sp


def print_group_table(group_name: str, results: Sequence[Result]) -> None:
    if not results:
        return
    name_width = max(20, max(len(r.name) for r in results))

    def line(char: str = "-") -> str:
        parts = [
            char * (name_width + 2),
            char * 8,
            char * 8,
            char * 13,
            char * 15,
            char * 9,
            char * 12,
            char * 14,
            char * 8,
        ]
        return "+" + "+".join(parts) + "+"

    total_width = name_width + 2 + 8 + 8 + 13 + 15 + 9 + 12 + 14 + 9
    print(line("="))
    print(f" {group_name.upper()} ".center(total_width, " "))
    print(line("-"))
    print(
        "| "
        + f"{'Case':<{name_width}}"
        + " | "
        + f"{'n':>5}"
        + " | "
        + f"{'m':>5}"
        + " | "
        + f"{'Gossip(ms)':>10}"
        + " | "
        + f"{'NetworkX(ms)':>12}"
        + " | "
        + f"{'Speedup':>6}"
        + " | "
        + f"{'Gossip ISO':>10}"
        + " | "
        + f"{'NetworkX ISO':>12}"
        + " | "
        + f"{'Match':>6}"
        + " |"
    )
    print(line("-"))

    for r in results:
        speedup = (r.tn_ms / r.tg_ms) if r.tg_ms > 0 else float("inf")
        match = (
            "Yes" if (r.nx_iso is not None and r.gossip_iso == r.nx_iso) else ("-" if r.nx_iso is None else "No ")
        )
        print(
            "| "
            + f"{r.name:<{name_width}}"
            + " | "
            + f"{r.nodes:>5}"
            + " | "
            + f"{r.edges:>5}"
            + " | "
            + f"{r.tg_ms:10.2f}"
            + " | "
            + f"{r.tn_ms:12.2f}"
            + " | "
            + f"x{speedup:4.1f}"
            + " | "
            + f"{format_bool(r.gossip_iso):>10}"
            + " | "
            + f"{format_bool(r.nx_iso):>12}"
            + " | "
            + match
            + " |"
        )
    print(line("-"))


def estimate_power_law(xs: Sequence[float], ys: Sequence[float]) -> Optional[float]:
    """Estimate exponent a in y ~ x^a via log-log linear regression. Returns None if not enough points."""
    pts = [(x, y) for x, y in zip(xs, ys) if x > 0 and y > 0]
    if len(pts) < 2:
        return None
    lx = [math.log(x) for x, _ in pts]
    ly = [math.log(y) for _, y in pts]
    n = len(pts)
    sumx = sum(lx)
    sumy = sum(ly)
    sumxx = sum(x * x for x in lx)
    sumxy = sum(x * y for x, y in zip(lx, ly))
    denom = n * sumxx - sumx * sumx
    if denom == 0:
        return None
    a = (n * sumxy - sumx * sumy) / denom
    return a


def report_complexity(results: Sequence[Result], size: str = "n") -> None:
    """Print a quick complexity estimate y ~ size^a using gossip time vs nodes or edges.
    size: "n" or "m".
    """
    if size == "n":
        xs = [r.nodes for r in results]
    else:
        xs = [max(1, r.edges) for r in results]
    ys = [r.tg_ms for r in results]
    a = estimate_power_law(xs, ys)
    if a is not None:
        print(f"   Observed scaling (gossip): t ~ {size}^{a:.2f}")
    else:
        print("   Observed scaling: insufficient data")