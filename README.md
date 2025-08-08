# Gossip Graph Isomorphism Algorithm

**Status: Work in Progress (hobby project)**

A Python implementation of a graph isomorphism algorithm based on gossip fingerprinting. The algorithm computes structural fingerprints for graph vertices to determine isomorphism.

## Overview

The gossip algorithm propagates local information outward ("gossip") from each vertex. For each start vertex, we collect a timeline of edge-spread events between current "knowers" and their neighbors. The multiset of per-vertex timelines forms a canonical fingerprint for the whole graph; two graphs are considered isomorphic by the algorithm if their fingerprint multisets are identical.

- Deterministic and label-invariant
- Works on simple undirected graphs (self-loops are tolerated by reducing to a simple graph)
 - Not proven complete; currently no known counterexamples in our tests/benchmarks (circulants fixed)

## Core idea

Graph structure can be uniquely captured by how information spreads through it. By watching when edges transmit new information and with what local “pressure” (neighbor hit counts), we get time-ordered edge-event signatures that are highly discriminative.

## How the gossip algorithm works (line by line)

- For each start vertex s:
  - Initialize `knowers = {s}`, `new_knowers = {s}`, `seen_edges = ∅`, `timeline = []`, and `iteration = 0`.
  - While `new_knowers` is non-empty:
    - Build a single-pass list of edge transmissions from all current `knowers` to their neighbors, skipping edges already in `seen_edges`.
    - Compute a per-vertex `hit_rate` that counts how often each endpoint is “touched” this iteration (including contacts inside the current frontier).
    - For each transmission (u, v):
      - If exactly one endpoint knows, emit an event `(iteration, 1, hits_knower, hits_receiver)` and add the receiver to `next_new_knowers`.
      - Else (both know or both don’t yet know), emit a neutral event `(iteration, 0, min_hits, max_hits)`.
    - Update `knowers ← knowers ∪ next_new_knowers`, `new_knowers ← next_new_knowers`, and increment `iteration`.
  - Sort `timeline` and store it as the fingerprint for s.
- The graph fingerprint is the sorted multiset of all per-vertex timelines. Two graphs match if these multisets are identical.

Notes:
- The algorithm focuses on edges, not degrees. Degrees are implicit in the event flow. Sorting within each iteration uses only hit-rates and event type, which preserves label-invariance.

## Current Status

### What Works Reliably (in current tests)
- CFI graphs: non-isomorphic pairs are distinguished
- Standard families: paths, cycles, complete, stars, trees, wheels, hypercubes
- Many vertex-transitive graphs: Petersen, Desargues, Heawood, Möbius–Kantor, Pappus
- Strongly regular: SRG(16,6,2,2) relabel stability
- Miyazaki graphs: relabel stability
- Generalized Petersen (various GP(n,k)) relabel stability
- Circulants: previously failing pairs now distinguished
- Kneser and Johnson (moderate sizes); Paley; Rook vs Shrikhande sanity
- Cospectral tree pairs; grid/ladder/prism/circular ladder; barbell/lollipop/friendship

### Known Issues
- Dense graphs: runtime grows faster (expected; more edges)

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
