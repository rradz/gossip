# Gossip Graph Isomorphism Algorithm

**Status: Work in Progress**

A Python implementation of a graph isomorphism algorithm based on gossip fingerprinting. The algorithm computes structural fingerprints for graph vertices to determine isomorphism.

## Overview

The gossip algorithm works by computing fingerprints for each vertex based on local structural properties and their propagation through the graph. These fingerprints are then compared to determine if two graphs are isomorphic.

## Current Status

### What Works
- **CFI graphs**: Successfully distinguishes non-isomorphic Cai-Fürer-Immerman pairs
- **Regular graphs**: Good performance on most regular graph types
- **Standard graphs**: Correct on paths, cycles, complete graphs, stars, trees
- **Strongly regular graphs**: Handles SRGs correctly
- **Miyazaki graphs**: Correctly identifies isomorphic pairs

### Known Issues
- **Circulant graphs**: False positives on specific patterns (e.g., C₁₃([1,3,4]) vs C₁₃([1,3,6]))
- **Memory test**: One test with n=25 fails due to n*d not being even
- **Large dense graphs**: Performance degrades significantly above 5000 edges

### Test Results
- 74 out of 76 tests passing
- Core algorithm coverage: 96%
- Overall coverage: 67%

## Requirements

- Python 3.9+
- NetworkX 3.3
- NumPy 2.0
- pytest 8.3 (for testing)

## Installation

```bash
git clone https://github.com/yourusername/gossip.git
cd gossip
pip install -r requirements.txt
pip install -e .
```

## Usage

### Basic Example

```python
from gossip import GossipFingerprint
import networkx as nx

gf = GossipFingerprint()
G1 = nx.petersen_graph()
G2 = nx.cycle_graph(10)

are_isomorphic = gf.compare(G1, G2)
print(f"Isomorphic: {are_isomorphic}")
```

### Command Line

```bash
# Compare two graphs
gossip compare graph1.edgelist graph2.edgelist

# Run validation
python validate.py
```

## Testing

```bash
# Quick tests
python run_tests.py --quick

# Performance benchmarks
python run_tests.py --perf

# Hard instances
python run_tests.py --hard

# Full test suite
python run_tests.py --full

# Run specific test category
pytest tests/test_algorithm.py -v
```

### Test Categories

1. **Algorithm tests** (`test_algorithm.py`) - Core functionality
2. **Hard instances** (`test_hard_instances.py`) - CFI, SRG, Miyazaki, circulant graphs
3. **Performance** (`test_performance.py`) - Benchmarks and complexity analysis
4. **Integration** (`test_integration.py`) - End-to-end workflows
5. **Showcase** (`test_showcase.py`) - Demonstrations on famous graphs

## Performance

### Benchmarks (vs NetworkX)

| Graph Type | Nodes | Gossip (ms) | NetworkX (ms) | Speedup |
|------------|-------|-------------|---------------|---------|
| Petersen | 10 | 0.3 | 2.1 | 7x |
| 4-Regular | 20 | 1.2 | 15.3 | 12x |
| Complete K₁₀ | 10 | 0.2 | 1.8 | 9x |
| Grid 5×5 | 25 | 1.5 | 18.7 | 12x |

### Complexity
- Time: O(n²) empirically for sparse graphs
- Space: O(n) for fingerprint storage

## Project Structure

```
gossip/
├── src/gossip/
│   ├── algorithm.py    # Core algorithm
│   ├── cli.py          # Command line interface
│   └── utils.py        # Graph utilities
├── tests/              # Test suite
├── run_tests.py        # Test runner
├── validate.py         # Validation script
└── requirements.txt    # Dependencies
```

## Recent Changes

- Reduced performance test sizes for faster execution
- Added distinction between generation and algorithm failures in tests
- Improved test output with formatted tables
- Added circulant graph tests
- Cleaned up old files and redundant code

## Contributing

This is a work in progress. Contributions welcome, particularly for:
- Fixing the circulant graph false positive issue
- Improving performance on dense graphs
- Adding more test cases

## License

MIT

## Citation

If you use this implementation, please cite:
```bibtex
@software{gossip_algorithm,
  title = {Gossip Graph Isomorphism Algorithm},
  year = {2024},
  url = {https://github.com/yourusername/gossip}
}
```
