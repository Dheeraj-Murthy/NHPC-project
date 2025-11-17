# Network Routing Optimization with NS-3

A comprehensive framework for evaluating and comparing network routing
algorithms using NS-3 simulation. This project implements multiple baseline
routing models and provides performance analysis capabilities for network
optimization research.

## Overview

This project combines NS-3 network simulation with advanced routing algorithms
to analyze and compare different network flow optimization strategies. It serves
as both a benchmarking platform and a foundation for developing machine
learning-based routing solutions.

## Architecture

```
my_project/
├── topology.json              # Network topology definition
├── routing.json               # Generated routing recommendations
├── ns3_sim.cc                 # NS-3 simulation core
├── main.py                    # Main orchestration script
├── ml/                        # Routing algorithms framework
│   ├── models/                # Individual routing models
│   │   ├── max_flow.py       # Ford-Fulkerson maximum flow
│   │   ├── min_cost_max_flow.py # Minimum cost maximum flow
│   │   ├── multi_commodity_flow.py # Multi-commodity flow
│   │   └── load_balanced_sp.py # Load-balanced shortest path
│   ├── core/                  # Framework components
│   │   ├── model_manager.py   # Model orchestration
│   │   └── performance_comparator.py # Performance analysis
│   ├── results/               # Model outputs and comparisons
│   ├── train_model.py         # Training/benchmarking
│   ├── infer_routes.py        # Route inference
│   └── run_baselines.py       # Baseline model execution
├── model_results/             # Individual model results
│   ├── max_flow/
│   ├── min_cost_max_flow/
│   ├── multi_commodity_flow/
│   └── load_balanced_sp/
├── scripts/                   # Analysis utilities
└── results/                   # Simulation outputs
```

## Quick Start

### Prerequisites

1. **NS-3 Setup**

   ```bash
   ./ns3 configure --enable-modules=core,network,internet,point-to-point,applications,flow-monitor,netanim,mobility
   ./ns3 build
   ```

2. **Dependencies**

   ```bash
   pip3 install networkx pandas
   ```

3. **JSON Library**
   - Place `nlohmann/json.hpp` in your include path or next to `ns3_sim.cc`

### Running the Complete Pipeline

Execute all routing models with NS-3 simulation:

```bash
python3 main.py
```

This will:

- Run each routing model individually
- Generate routing configurations
- Execute NS-3 simulations for each model
- Create performance comparisons
- Save results to `model_results/`

### Individual Model Testing

Run specific routing models:

```bash
cd ml
python infer_routes.py --model multi_commodity_flow
python infer_routes.py --model all --compare
```

## Routing Models

### 1. Multi-Commodity Flow (Recommended)

- **Performance**: Best overall (100.0/100 score)
- **Throughput**: 18.98 Mbps allocated
- **Network Utilization**: 75.5%
- **Use Case**: Most scenarios requiring optimal performance

### 2. Minimum Cost Maximum Flow

- **Algorithm**: NetworkX network_simplex
- **Cost Function**: `delay + α × utilization`
- **Strengths**: Balanced optimization, congestion awareness
- **Use Case**: Performance-critical routing

### 3. Load-Balanced Shortest Path

- **Algorithm**: Modified Dijkstra with load awareness
- **Cost Function**: `delay × (1 + β × utilization²)`
- **Strengths**: Dynamic congestion avoidance
- **Use Case**: Load balancing in dynamic networks

### 4. Maximum Flow

- **Algorithm**: Ford-Fulkerson
- **Performance**: Baseline comparison (39.6/100 score)
- **Use Case**: Theoretical analysis only

## Performance Metrics

Each model is evaluated on:

- **Success Rate**: Percentage of flows successfully routed
- **Throughput**: Total data flow achieved (Mbps)
- **Delay**: Average end-to-end latency (ms)
- **Packet Loss**: Percentage of packets lost
- **Network Utilization**: Link usage efficiency
- **Fairness**: Resource allocation equity (Jain's index)

## Output Files

### Simulation Results

- `metrics.csv`: Flow performance metrics from NS-3
- `sim-anim.xml`: Network animation for NetAnim
- `routing.json`: Next-hop routing recommendations

### Model Analysis

- `model_results/[model]/analysis.json`: Individual model performance
- `model_results/comparison_summary.json`: Cross-model comparison
- `ml/results/comparison_report_*.json`: Detailed performance reports

## Configuration

### Topology Format

`topology.json` should define:

- Network nodes and connections
- Link bandwidth and delay characteristics
- Flow requirements and constraints

### Model Parameters

- **α (alpha)**: Utilization weight in min-cost flow (default: 0.5)
- **β (beta)**: Utilization weight in load-balanced SP (default: 0.3)

## Advanced Usage

### Custom Model Integration

1. Create new model class in `ml/models/`
2. Implement `get_next_hop_routes()` and `get_model_metrics()`
3. Register in `model_manager.py`
4. Add to `__init__.py` exports

### Performance Analysis

```bash
# Generate comparison graphs
python scripts/create_comparison_graphs.py

# Analyze CSV metrics
python scripts/analyze_csv_metrics.py
```

### Debug Mode

```bash
# Verbose model execution
python ml/train_model.py --models max_flow
```

## Research Applications

This framework supports:

- **Algorithm Benchmarking**: Compare routing strategies systematically
- **ML Model Development**: Generate training data for supervised learning
- **Network Optimization**: Test novel routing approaches
- **Performance Analysis**: Detailed metric evaluation and visualization

## Troubleshooting

### Common Issues

1. **Import Errors**: Verify Python dependencies installation
2. **Build Failures**: Ensure NS-3 modules are correctly configured
3. **Missing Data**: Check `topology.json` and `metrics.csv` existence
4. **Simulation Errors**: Validate network connectivity in topology

### Performance Optimization

- Reduce network size for faster testing
- Use fewer flows for initial debugging
- Disable animation generation for batch processing

## Future Enhancements

- **Machine Learning Integration**: GNN and RL model placeholders
- **Real-time Adaptation**: Dynamic topology changes
- **Advanced Metrics**: Energy efficiency, reliability analysis
- **Visualization Tools**: Interactive network graphs
- **API Interface**: RESTful routing service

## Citation

If you use this framework in your research, please acknowledge the NS-3
simulator and the NetworkX library for graph algorithms.
