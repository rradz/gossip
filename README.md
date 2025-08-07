# Gossip Graph Isomorphism Algorithm

**Status: Work in Progress (hobby project)**

A Python implementation of a graph isomorphism algorithm based on gossip fingerprinting. The algorithm computes structural fingerprints for graph vertices to determine isomorphism.

## Overview

The gossip algorithm propagates local information outward ("gossip") from each vertex. For each start vertex, we collect a timeline of edge-spread events between current "knowers" and their neighbors. The multiset of per-vertex timelines (plus degrees) forms a canonical fingerprint for the whole graph; two graphs are considered isomorphic by the algorithm if their fingerprint multisets are identical.

- Deterministic and label-invariant
- Works on simple undirected graphs (self-loops are tolerated by reducing to a simple graph)
- Not guaranteed complete; we document known counterexamples

## Current Status (facts, not claims)

### What Works Reliably (in current tests)
- CFI graphs: non-isomorphic pairs are distinguished
- Standard families: paths, cycles, complete, stars, trees, wheels, hypercubes
- Many vertex-transitive graphs: Petersen, Desargues, Heawood, Möbius–Kantor, Pappus
- Strongly regular: SRG(16,6,2,2) relabel stability
- Miyazaki graphs: relabel stability
- Generalized Petersen (various GP(n,k)) relabel stability

### Known Issues
- Circulants: specific patterns are a counterexample (e.g., C13([1,3,4]) vs C13([1,3,6]) — algorithm says ISO, NX says NON-ISO)
- Dense graphs: runtime grows faster (expected; more edges)

## Requirements

- Python 3.9+
- NetworkX (tested with 3.2.x)
- NumPy
- pytest (for tests)

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

- Circulants: 8/9 correct; the C13([1,3,4]) vs C13([1,3,6]) pair is a known mismatch. Observed scaling ~ t ≈ n^2.5 for gossip on the small sizes tested.
- Hard CFI: Gossip distinguishes pairs; NetworkX (VF2) is slower on these than gossip at our small sizes.

These are small-scale, unoptimized, and indicative only.

## Tests

Tests live in `tests/` and cover:
- Algorithm basics: invariants, standard families, conversions
- Hard instances: CFI, SRG, Miyazaki, cospectral trees, products
- Integration and CLI
- Performance (small sizes to avoid long runs)

If a test becomes redundant with the new modular benchmarks, prefer keeping a minimal sanity version and moving coverage into the `benchmarks/` suite for ongoing evaluation. PRs to simplify/trim redundant tests are welcome.

## Performance and Complexity (empirical)

- Theoretical (claimed): time O(n·m), space O(n·m). Our implementation iterates edges per start vertex and sorts per-vertex timelines; small log factors may appear.
- Empirical (small sizes, laptop): on circulants, rough fit t ≈ n^2.5; on ER graphs, growth increases with density; on regular graphs, growth is milder than dense ER.

These are not optimized; they’re meant to guide further work.

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
├── tests/              # Test suite
└── benchmark.py        # Orchestrator for modular benchmarks
```

## Contributing

This is a hobby project. Contributions welcome, especially:
- Additional benchmark families (suggestions: rook graphs at other sizes, more SRGs, Johnson/Kneser variants)
- Improvements to the algorithm (addressing circulant mismatch)
- Profiling and performance improvements

## License

MIT
