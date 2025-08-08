# Gossip Graph Isomorphism Algorithm

**Status: Work in Progress (hobby project)**

A Python implementation of a graph isomorphism algorithm based on gossip fingerprinting. The algorithm computes structural fingerprints for graph vertices to determine isomorphism.

## Overview

The gossip algorithm propagates local information outward ("gossip") from each vertex. For each start vertex, we collect a timeline of edge-spread events between current "knowers" and their neighbors. The multiset of per-vertex timelines forms a canonical fingerprint for the whole graph; two graphs are considered isomorphic by the algorithm if their fingerprint multisets are identical.

- Deterministic and label-invariant
- Works on simple undirected graphs (self-loops are tolerated by reducing to a simple graph)
 - Not proven complete; known issue: Rook R(4,4) vs Shrikhande — a classical non-isomorphic pair. Our algorithm incorrectly labels them as isomorphic. We addressed this by adding a per-round sentinel that records how many connected groups are currently discussing the gossip (number of connected components in the frontier). This feels a bit hacky, but is effective and preserves the flow model. Circulants fixed.

## Core idea

Graph structure can be uniquely captured by how information spreads through it. By watching when edges transmit new information and with what local “pressure” (how many times a vertex hears gossip in a round), we get time-ordered edge-event signatures that are highly discriminative.

## How the gossip algorithm works (line by line)

- For each start vertex s:
  - Initialize sets: `spreaders = {s}` (all who have heard), `new_spreaders = {s}` (frontier), plus `seen_edges = ∅`, `timeline = []`, and `iteration = 0`.
  - While `new_spreaders` is non-empty:
    - Compile this round’s list of edge gossips from each `current_spreader ∈ new_spreaders` to its neighbors, skipping edges in `seen_edges`.
    - Tally `gossip_heard_count[v]` for every vertex v in the round (how many times v heard gossip this iteration, including intra-frontier touches).
    - For each gossip (u, v):
      - If exactly one endpoint is in `spreaders`, emit `(iteration, 1, gossip_heard_count[spreader], gossip_heard_count[receiver])` and add the receiver to `receivers`.
      - Else (both already heard), emit a neutral event `(iteration, 0, min_count, max_count)`.
    - Append one sentinel event `(iteration, -1, group_sizes)` where `group_sizes` is the sorted vector of connected-component sizes in the frontier-induced subgraph. Intuition: how many independent conversations and how large they are.
    - Update `spreaders ← spreaders ∪ receivers`, `new_spreaders ← receivers`, and increment `iteration`.
  - Sort `timeline` and store it as the fingerprint for s.
- The graph fingerprint is the sorted multiset of all per-vertex timelines. Two graphs match if these multisets are identical.

Notes:
- Edge-first view: we operate on gossips (edge events) rather than node degrees. Degrees are implicit in the flow.
- Frontier iteration: only `new_spreaders` transmit each round, while `spreaders` accumulates all who have ever heard. This avoids re-visiting edges while retaining a global memory of who has heard.
- Per-round tallies: `gossip_heard_count` resets each round by design. On undirected graphs, long detours aren’t possible: a vertex participates in only two rounds of the process—first as a receiver (when it initially hears), then in the next round as a spreader (it may engage multiple times within that round). Not resetting across rounds could enable obfuscation; we intentionally only count what happens within the current round.
- Counting rule: receivers never increase the spreader’s tally. A spreader’s `gossip_heard_count` only increases when it contacts other vertices that have already heard in the same round.

## Current Status

### What Works Reliably (in current tests)
- CFI graphs: non-isomorphic pairs are distinguished
- Standard families: paths, cycles, complete, stars, trees, wheels, hypercubes
- Many vertex-transitive graphs: Petersen, Desargues, Heawood, Möbius–Kantor, Pappus
- Strongly regular: SRG(16,6,2,2) relabel stability
- Miyazaki graphs: relabel stability
- Generalized Petersen (various GP(n,k)) relabel stability
- Circulants: previously failing pairs now distinguished
- Kneser and Johnson (moderate sizes); Paley
- Cospectral tree pairs; grid/ladder/prism/circular ladder; barbell/lollipop/friendship

### Known Issues
 - Rook R(4,4) vs Shrikhande (both SRG(16,6,2,2)): a known non-isomorphic pair; the algorithm incorrectly labels them as isomorphic
- Dense graphs: runtime grows faster (expected; more edges)

Notes on the Rook–Shrikhande case:
- Distinguishing between a frontier-induced C6 and two disjoint C3’s (2×K3) appears hard for the current edge-event fingerprint. Each neighbor “talks to two” and six conversations happen either way, making per-vertex timelines coincide.
- It is under consideration whether this is a triangle-specific corner case (C3 is the only graph that is both a clique and a cycle) or an indicator of a broader structural gap. Further design work is ongoing.

## Requirements

- Python 3.9+
- NetworkX (tested with 3.2.x)
- NumPy

## Installation

```bash
pip install -r requirements.txt
pip install -e .
```

## Benchmarks (modular)

We ship a modular benchmark runner with grouped families under `benchmarks/`.

- Run everything (compact tables):
  ```bash
  python benchmark.py all
  ```
- Run selected groups:
  ```bash
  python benchmark.py circulant kneser johnson
  ```
- Filter by case name:
  ```bash
  python benchmark.py circulant --filter C20
  ```
- Report observed scaling per group (rough power law vs n or m):
  ```bash
  python benchmark.py circulant --complexity n
  ```

Groups:
- `basic`, `symmetry`, `families`, `circulant`, `kneser`, `johnson`, `paley`, `rook_shrikhande`, `gpetersen`, `hard`

Each row prints Gossip vs NetworkX, and a “Match” column. “Correct” means Gossip agrees with NetworkX (or with the provided expected label when available).

### Snapshot (example on a laptop)

- Groups summary from `benchmark.output`:
  - BASIC 12/12, SYMMETRY 7/7, FAMILIES 49/49, CIRCULANT 20/20, KNESER 8/8 (one NX timeout on the largest), JOHNSON 8/8, PALEY 4/4, TREES 20/20, ZETA 8/8, ER_COMPLEXITY 22/22, HARD 11/11, LEGACY_TESTS 44/44.
  - Final: 213/213 correct (NX timeouts counted neutral). Reproduce with: `python benchmark.py all`.
  - Observed scaling: circulants and regular families show sub-cubic growth on these sizes; ER shows time increasing primarily with m (edges).

These are small-scale, unoptimized, and indicative only.

## Tests

We now rely on the modular benchmarks under `benchmarks/` instead of a pytest suite. Groups include `basic`, `symmetry`, `families`, `circulant`, `kneser`, `johnson`, `paley`, `rook_shrikhande`, `gpetersen`, `trees`, `zeta`, `er_complexity`, `hard`, and `legacy_tests`. Use `--filter` and timeouts to focus runs.

## Performance and Complexity (empirical)

- Theoretical (claimed): time O(n·m), space O(n·m). We iterate edges per start vertex and sort per-vertex timelines; small log factors may appear.
- Empirical (benchmarks in `benchmark.output`):
  - On sparse/regular families (cycles, grids, hypercubes), time grows noticeably slower than dense ER.
  - On ER graphs, runtime scales primarily with edges m; denser graphs get slower.
  - On CFI and Zeta-like families, gossip is often faster than NetworkX’s VF2 at these sizes.

These are not optimized; they’re meant to guide further work.

## Possible extensions

- Directed graphs: preserve spreader→receiver direction in events (emit ordered endpoint stats; avoid symmetric sorting on endpoints).
- Weighted graphs: let the per-transmission contribution reflect novelty and edge weight (e.g., +1 for new info, −1 for already-known, times the weight) while keeping label invariance.

## Upcoming work

- Canonical labeling (produce explicit label maps, not just equality checks)
- Reconstruction (attempt to construct a graph that realizes a given fingerprint)
- Write-up: formalize the edge-event view and its relation to refinement/message-passing methods

## How this compares

- WL color refinement / message-passing: similar spirit (iterative local-to-global propagation), but our signatures are time-ordered edge events with hit-rates instead of multisets of colors.
- VF2/backtracking (NetworkX): search-based mapping vs. our direct canonical multiset; we avoid branching but don’t yet produce a label map.
- Nauty/Traces: mature canonical labeling via partitions and backtracking; our approach is a simpler, edge-centric invariant with strong practical power on many families.

## What’s unique here

- Edge-first viewpoint: events are attached to edges per iteration, not nodes; degrees and local structures emerge from the flow.
- Time-ordering: the when and how of transmissions matter, yielding rich, discriminative fingerprints that are label-invariant by construction.

## Project Structure

```
gossip/
├── src/gossip/
│   ├── algorithm.py    # Core algorithm
│   ├── cli.py          # Command line interface
│   └── utils.py        # Graph utilities
├── benchmarks/
│   ├── common.py       # Shared types, printing, complexity
│   ├── families.py     # General families
│   ├── circulant.py    # Circulants (expanded)
│   └── other_families.py # Kneser, Johnson, Paley, Rook/Shrikhande, GPetersen
└── benchmark.py        # Orchestrator for modular benchmarks
```

## Contributing

This is an educational hobby project. Contributions welcome, especially:
- Additional benchmark families/instances (e.g., more SRGs, Johnson/Kneser variants, rook graphs at other sizes)
- Stress tests and adversarial families (help search for counterexamples)
- Documentation: clearer explanations, diagrams, examples, CLI/README improvements
- Bug fixes and small usability improvements

Please do not submit performance-optimization PRs to this repository. If you want to build an optimized implementation, feel free to fork; this repo prioritizes clarity and pedagogy over speed.

## License

MIT

## Author

Rafał Radziszewski

## Citation

If you reference this repository in academic or technical work, please cite:

Rafał Radziszewski, Gossip Graph Isomorphism (educational implementation), 2025. Release date: 2025-08-08.

BibTeX:

```bibtex
@software{Radziszewski_Gossip_GI_2025,
  author = {Rafał Radziszewski},
  title = {Gossip Graph Isomorphism (educational implementation)},
  year = {2025},
  note = {Release date: 2025-08-08}
}
```
