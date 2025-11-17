# Baseline Routing Models

This directory contains baseline network flow algorithms for routing optimization, providing a foundation for comparison with future ML models.

## Architecture

```
ml/
├── models/                     # Individual routing algorithms
│   ├── max_flow.py            # Ford-Fulkerson maximum flow
│   ├── min_cost_max_flow.py   # Minimum cost maximum flow
│   ├── multi_commodity_flow.py # Multi-commodity flow optimization
│   └── load_balanced_sp.py    # Load-balanced shortest path
├── core/                      # Orchestration and analysis
│   ├── model_manager.py       # Manages all models
│   └── performance_comparator.py # Compares model performance
├── results/                   # Output directory for results
├── train_model.py            # Enhanced training/benchmarking script
├── infer_routes.py           # Enhanced routing inference
└── run_baselines.py          # Main entry point
```

## Models Overview

### 1. Max Flow Model (`max_flow.py`)
- **Algorithm**: Ford-Fulkerson
- **Purpose**: Calculate maximum possible throughput between source-destination pairs
- **Performance**: Lowest performer (39.6/100 score), 0 Mbps actual throughput
- **Use Case**: Theoretical analysis, not recommended for production

### 2. Min Cost Max Flow Model (`min_cost_max_flow.py`)
- **Algorithm**: NetworkX network_simplex
- **Purpose**: Optimize for both throughput and delay simultaneously
- **Cost Function**: `delay + α × utilization`
- **Strengths**: Balanced optimization, considers congestion
- **Use Case**: Performance-critical routing

### 3. Multi-Commodity Flow Model (`multi_commodity_flow.py`)
- **Algorithm**: Proportional allocation with fairness
- **Purpose**: Handle multiple flows simultaneously with fair bandwidth allocation
- **Performance**: Best overall performer (100.0/100 score), 18.98 Mbps allocated
- **Strengths**: Fair resource distribution, highest network utilization (75.5%)
- **Use Case**: Recommended for most scenarios, optimal overall performance

### 4. Load-Balanced Shortest Path (`load_balanced_sp.py`)
- **Algorithm**: Modified Dijkstra with load awareness
- **Purpose**: Avoid congestion by considering current link utilization
- **Cost Function**: `delay × (1 + β × utilization²)`
- **Strengths**: Congestion avoidance, adaptive routing
- **Use Case**: Dynamic networks, load balancing

## Usage

### Quick Start - Run All Models
```bash
cd ml
python run_baselines.py
```

### Run Individual Models
```bash
# Run specific model
python infer_routes.py --model max_flow

# Run all models with comparison
python infer_routes.py --model all --compare

# Generate training data
python train_model.py --generate-training-data
```

### Advanced Usage
```bash
# Run specific models only
python train_model.py --models max_flow min_cost_max_flow

# Custom output directory
python train_model.py --output-dir custom_results

# Generate comparison report only
python infer_routes.py --model all --compare --output custom_routing.json
```

## Output Files

### Model Results (`ml/results/`)
- `model_results_*.json`: Raw results from each model
- `comparison_report_*.json`: Performance comparison and rankings
- `training_data.json`: Training examples for ML models
- `benchmark_summary.json`: Complete benchmark summary

### Routing Output
- `routing.json`: Next-hop routing recommendations (multi_commodity_flow - best performer)

## Performance Metrics

Each model is evaluated on:

1. **Success Rate**: Percentage of flows successfully routed
2. **Throughput**: Total data flow achieved
3. **Delay**: Average end-to-end latency
4. **Cost Efficiency**: Throughput per unit cost
5. **Fairness**: Jain's fairness index for resource allocation
6. **Utilization**: Link utilization statistics
7. **Hop Count**: Average path length

## Model Comparison

The performance comparator provides:

- **Overall Rankings**: Multi-Commodity (100.0), Min-Cost (63.9), Load-Balanced (53.9), Max Flow (39.6)
- **Metric-Specific Winners**: Best model for each metric
- **Recommendations**: Multi-Commodity recommended for most use cases
- **Statistical Analysis**: 152.5% performance gap between best and worst algorithms

## Integration with NS-3

### Current Workflow
1. NS-3 simulation generates `metrics.csv`
2. Baseline models analyze network state
3. Routing recommendations written to `routing.json`
4. Results可用于future ML model training

### Future ML Integration
- Training data structure ready for supervised learning
- Baseline performance provides comparison benchmarks
- Model outputs can be used as labels for GNN/RL training

## Dependencies

- `networkx`: Graph algorithms and data structures
- `pandas`: Data analysis (optional, for detailed metrics)
- `json`: Data serialization
- `csv`: Metrics file reading

## Configuration

### Model Parameters
- **α (alpha)**: Weight for utilization in min-cost flow (default: 0.5)
- **β (beta)**: Weight for utilization in load-balanced SP (default: 0.3)

### Topology Requirements
- `topology.json`: Network structure with bandwidth and delay
- `metrics.csv`: Flow performance data from NS-3

## Extending the Framework

### Adding New Models
1. Create new model class in `models/` directory
2. Implement required methods:
   - `get_next_hop_routes()`: Generate routing recommendations
   - `get_model_metrics()`: Calculate performance metrics
3. Import and register in `model_manager.py`
4. Add to `__init__.py` exports

### Custom Metrics
1. Add metric to `performance_comparator.py` comparison list
2. Implement metric calculation in model classes
3. Update ranking logic (higher/lower is better)

## Troubleshooting

### Common Issues
1. **Import Errors**: Ensure all dependencies installed
2. **Missing Data**: Check `topology.json` and `metrics.csv` exist
3. **No Routes Generated**: Verify network connectivity in topology
4. **Memory Issues**: Reduce model complexity or network size

### Debug Mode
```bash
# Run with verbose output
python train_model.py --models max_flow
```

## Future Enhancements

1. **ML Integration**: GNN and RL model placeholders
2. **Real-time Updates**: Dynamic topology changes
3. **Advanced Metrics**: Energy efficiency, reliability
4. **Visualization**: Network graphs and performance charts
5. **API Interface**: RESTful service for routing decisions