# Gossip Graph Isomorphism Algorithm

A fast graph isomorphism testing algorithm based on gossip fingerprinting. This implementation provides a novel approach to graph isomorphism testing that performs particularly well on regular graphs and sparse graphs.

## Overview

The gossip algorithm propagates information through a graph like gossip spreading through a social network. Each vertex initiates a "gossip" that spreads through the graph, creating a unique fingerprint based on the propagation pattern. These fingerprints are then used to determine if two graphs are isomorphic.

## Features

- Fast isomorphism testing for regular and sparse graphs
- Support for various graph formats (EdgeList, GML, GraphML, Pajek)
- Comprehensive test suite including hard instances (CFI graphs, SRGs, etc.)
- Command-line interface for easy usage
- Python 3.13+ support with modern type hints

## Installation

### Prerequisites

- Python 3.13 or higher
- pip package manager

### Using pip

```bash
# Clone the repository
git clone https://github.com/yourusername/gossip.git
cd gossip

# Install in development mode
pip install -e .

# Or install with all development dependencies
pip install -e ".[dev]"
```

### Using requirements.txt

```bash
pip install -r requirements.txt
```

### Using asdf

If you use asdf for Python version management:

```bash
asdf install
pip install -r requirements.txt
```

## Usage

### Command Line Interface

```bash
# Compare two graph files
gossip compare graph1.edgelist graph2.edgelist

# Generate test graphs
gossip generate --type cfi --size 10 --output g1.gml g2.gml

# Test with generated graphs
gossip test --type regular --size 20 --verbose
```

### Python API

```python
from gossip import GossipFingerprint
import networkx as nx

# Create algorithm instance
gf = GossipFingerprint()

# Create or load graphs
G1 = nx.petersen_graph()
G2 = nx.cycle_graph(10)

# Compare graphs
are_isomorphic = gf.compare(G1, G2)
print(f"Graphs are isomorphic: {are_isomorphic}")

# Get fingerprint directly
from gossip import graph_to_adjacency_list
adj = graph_to_adjacency_list(G1)
fingerprint = gf.compute(adj)
```

### Advanced Usage

```python
from gossip.utils import (
    generate_cfi_pair,
    generate_strongly_regular_graph,
    generate_miyazaki_graph,
    compute_graph_statistics
)

# Generate hard instances
base = nx.cycle_graph(6)
G1, G2 = generate_cfi_pair(base)  # CFI graphs

# Generate strongly regular graph
srg = generate_strongly_regular_graph(16, 6, 2, 2)

# Compute statistics
stats = compute_graph_statistics(srg)
print(f"Graph has {stats['num_vertices']} vertices, "
      f"density {stats['density']:.3f}")
```

## Project Structure

```
gossip/
├── src/
│   └── gossip/
│       ├── __init__.py           # Package initialization
│       ├── algorithm.py          # Core gossip algorithm
│       ├── utils.py              # Utility functions
│       └── cli.py                # Command-line interface
├── tests/
│   ├── __init__.py
│   ├── conftest.py               # Pytest configuration
│   ├── test_algorithm.py         # Core algorithm tests
│   ├── test_hard_instances.py    # Tests for hard cases
│   ├── test_performance.py       # Performance benchmarks
│   └── test_integration.py       # Integration tests
├── pyproject.toml                # Project configuration
├── requirements.txt              # Dependencies
├── .tool-versions               # asdf Python version
└── README.md                    # This file
```

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/gossip --cov-report=html

# Run specific test categories
pytest -m "not slow"              # Skip slow tests
pytest -m "unit"                  # Only unit tests
pytest -m "benchmark"             # Only benchmarks
pytest tests/test_algorithm.py    # Specific test file

# Run tests in parallel
pytest -n auto

# Run with timeout protection
pytest --timeout=30
```

### Test Categories

- **Unit Tests**: Test individual components
- **Integration Tests**: Test component interactions
- **Performance Tests**: Benchmark algorithm performance
- **Hard Instance Tests**: Test on known difficult cases (CFI graphs, SRGs, etc.)

## Performance

### Complexity

- Time Complexity: O(n² × m) where n is the number of vertices and m is the average degree
- Space Complexity: O(n²) for storing fingerprints

### Benchmarks

Performance characteristics on different graph types:

| Graph Type | Performance | vs NetworkX | Best Use Case |
|------------|-------------|-------------|---------------|
| Regular graphs | Excellent | 3-100x faster | Primary use case |
| Sparse graphs | Good | Competitive | Trees, paths |
| Random graphs | Moderate | Varies | Medium-sized graphs |
| Dense graphs | Moderate | Slower | Consider NetworkX |
| Complete graphs | Slower | Much slower | Use NetworkX |

### Scalability

The algorithm scales well for graphs up to several thousand vertices, particularly for regular and sparse graphs. Performance degrades for very dense graphs due to the edge iteration in the gossip propagation.

## Algorithm Details

The gossip fingerprinting algorithm works as follows:

1. **Initialization**: For each vertex v in the graph, start a gossip from v
2. **Propagation**: The gossip spreads through edges, recording:
   - Iteration number when each vertex learns the gossip
   - Degree information of spreader and listener
   - Direction of information flow
3. **Fingerprint Construction**: Create a timeline of gossip events
4. **Comparison**: Sort and compare fingerprints between graphs

The algorithm is particularly effective for graphs with regular structure, as the gossip propagation patterns reflect the underlying symmetries.

## Known Limitations

1. **CFI Graphs**: May not distinguish some Cai-Fürer-Immerman constructions
2. **Dense Graphs**: Performance degrades on very dense graphs
3. **Directed Graphs**: Currently only supports undirected graphs
4. **Weighted Graphs**: Edge weights are not considered

## Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Write tests for new functionality
4. Ensure all tests pass (`pytest`)
5. Format code with Black (`black src/ tests/`)
6. Submit a pull request

### Development Setup

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run code formatters
black src/ tests/
isort src/ tests/

# Run linters
flake8 src/ tests/
mypy src/

# Run tests with coverage
pytest --cov=src/gossip
```

## Citations

If you use this algorithm in your research, please cite:

```bibtex
@software{gossip_graph_isomorphism,
  title = {Gossip Graph Isomorphism Algorithm},
  author = {Your Name},
  year = {2024},
  url = {https://github.com/yourusername/gossip}
}
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- NetworkX team for the excellent graph library
- Pytest team for the testing framework
- The graph isomorphism research community for test cases and hard instances

## Future Work

- [ ] Add support for directed graphs
- [ ] Implement parallel version for large graphs
- [ ] Add support for edge-weighted graphs
- [ ] Optimize memory usage for very large graphs
- [ ] Implement incremental fingerprinting for dynamic graphs
- [ ] Add graph visualization tools