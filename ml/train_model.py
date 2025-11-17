#!/Users/dheerajmurthy/miniforge3/envs/ns3/bin/python
"""
Enhanced training script that generates baseline performance benchmarks.
Reads metrics.csv and runs baseline models to establish performance benchmarks.
Generates training data for future ML models.
"""
import sys
import os
import json
from datetime import datetime
from argparse import ArgumentParser

# Add ml directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__)))

from core.model_manager import ModelManager
from core.performance_comparator import PerformanceComparator

FULL_PROJECT_PATH = "/Users/dheerajmurthy/Downloads/IIITB/sem6/NHPC/project/simulation/ns-allinone-3.42/ns-3.42/scratch/my_project"
METRICS = f"{FULL_PROJECT_PATH}/metrics.csv"

def parse_arguments():
    """Parse command line arguments."""
    parser = ArgumentParser(description="Generate baseline performance benchmarks")
    parser.add_argument("--models", type=str, nargs="+",
                       choices=["max_flow", "min_cost_max_flow", "multi_commodity_flow", "load_balanced_sp"],
                       help="Specific models to run (default: all)")
    parser.add_argument("--output-dir", type=str, default="ml/results",
                       help="Output directory for results (default: ml/results)")
    parser.add_argument("--generate-training-data", action="store_true",
                       help="Generate training data for ML models")
    return parser.parse_args()

def analyze_metrics_data():
    """
    Analyze metrics.csv to understand network characteristics.

    Returns:
        Dictionary with metrics analysis
    """
    if not os.path.exists(METRICS):
        print("No metrics.csv found — no data to analyze.")
        return {}

    try:
        import pandas as pd
        df = pd.read_csv(METRICS)

        analysis = {
            "total_flows": len(df),
            "unique_sources": df["src_idx"].nunique() if "src_idx" in df.columns else 0,
            "unique_destinations": df["dst_idx"].nunique() if "dst_idx" in df.columns else 0,
            "unique_pairs": df[["src_idx", "dst_idx"]].drop_duplicates().shape[0],
            "avg_throughput": df["throughput_mbps"].mean() if "throughput_mbps" in df.columns else 0,
            "avg_delay": df["avg_delay_ms"].mean() if "avg_delay_ms" in df.columns else 0,
            "avg_loss": df["loss_pct"].mean() if "loss_pct" in df.columns else 0,
            "total_tx_bytes": df["txBytes"].sum() if "txBytes" in df.columns else 0,
            "total_rx_bytes": df["rxBytes"].sum() if "rxBytes" in df.columns else 0,
        }

        # Add flow characteristics
        if "throughput_mbps" in df.columns:
            analysis["throughput_std"] = df["throughput_mbps"].std()
            analysis["throughput_range"] = [df["throughput_mbps"].min(), df["throughput_mbps"].max()]

        if "loss_pct" in df.columns:
            analysis["lossy_flows"] = (df["loss_pct"] > 0).sum()
            analysis["loss_rate"] = analysis["lossy_flows"] / len(df)

        return analysis

    except ImportError:
        print("pandas not available, skipping detailed analysis")
        return {}
    except Exception as e:
        print(f"Error analyzing metrics: {e}")
        return {}

def generate_training_data(results, output_dir):
    """
    Generate training data for future ML models from baseline results.

    Args:
        results: Results from model manager
        output_dir: Directory to save training data
    """
    training_data = {
        "metadata": {
            "purpose": "Training data for ML routing models",
            "baseline_models": list(results.keys()),
            "features": ["topology_info", "flow_demands", "link_utilization", "delay_patterns"],
            "labels": ["optimal_next_hop", "flow_allocation", "performance_metrics"]
        },
        "training_examples": []
    }

    # Extract training examples from each model
    for model_name, model_results in results.items():
        if "error" in model_results:
            continue

        routes = model_results.get("routes", [])
        metrics = model_results.get("metrics", {})

        for route in routes:
            example = {
                "input_features": {
                    "src_node": route.get("src"),
                    "dst_node": route.get("dst"),
                    "model_used": model_name,
                    "topology_context": "linear_topology"  # Could be enhanced
                },
                "output_labels": {
                    "next_hop": route.get("next_hop"),
                    "model_confidence": 1.0,  # Baseline models are deterministic
                    "performance_class": "high" if metrics.get("success_rate", 0) > 0.8 else "medium"
                }
            }
            training_data["training_examples"].append(example)

    # Save training data
    training_file = os.path.join(output_dir, "training_data.json")
    try:
        with open(training_file, 'w') as f:
            json.dump(training_data, f, indent=2)
        print(f"Training data saved to {training_file}")
        print(f"Generated {len(training_data['training_examples'])} training examples")
    except Exception as e:
        print(f"Error saving training data: {e}")

def run_baseline_benchmarking(models=None, output_dir="ml/results", generate_training=False):
    """
    Run comprehensive baseline benchmarking.

    Args:
        models: List of specific models to run (None for all)
        output_dir: Output directory for results
        generate_training: Whether to generate training data
    """
    print("Starting baseline performance benchmarking...")

    # Analyze metrics data first
    print("\nAnalyzing network metrics data...")
    metrics_analysis = analyze_metrics_data()

    if metrics_analysis:
        print("Network Characteristics:")
        print(f"  Total flows: {metrics_analysis.get('total_flows', 0)}")
        print(f"  Unique source-destination pairs: {metrics_analysis.get('unique_pairs', 0)}")
        print(f"  Average throughput: {metrics_analysis.get('avg_throughput', 0):.2f} Mbps")
        print(f"  Average delay: {metrics_analysis.get('avg_delay', 0):.2f} ms")
        print(f"  Lossy flows: {metrics_analysis.get('loss_rate', 0):.2%}")

    # Initialize model manager
    manager = ModelManager(FULL_PROJECT_PATH)

    # Override output directory if specified
    if output_dir != "ml/results":
        manager.results_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    # Run specified models or all models
    if models:
        print(f"\nRunning specified models: {models}")
        results = {}
        for model_name in models:
            if model_name in manager.models:
                print(f"Running {model_name}...")
                result = manager.run_single_model(model_name)
                results[model_name] = result
            else:
                print(f"Model {model_name} not available")
    else:
        print(f"\nRunning all available models...")
        results = manager.run_all_models()

    # Save results
    results_file = manager.save_results(results)

    # Generate comparison report
    print("\nGenerating performance comparison...")
    comparator = PerformanceComparator(manager.results_dir)
    comparison_summary = comparator.generate_summary_report(results)

    # Save comparison report
    report_file = comparator.save_comparison_report(comparison_summary)

    # Print summary
    comparator.print_summary(comparison_summary)

    # Generate training data if requested
    if generate_training:
        print("\nGenerating training data for ML models...")
        generate_training_data(results, output_dir)

    # Save benchmark summary
    benchmark_summary = {
        "timestamp": datetime.now().isoformat(),
        "data_summary": manager.get_data_summary(),
        "metrics_analysis": metrics_analysis,
        "models_evaluated": list(results.keys()),
        "results_file": results_file,
        "comparison_report": report_file,
        "training_data_generated": generate_training
    }

    summary_file =  f"{FULL_PROJECT_PATH}/ml/results/benchmark_summary.json"
    try:
        with open(summary_file, 'w') as f:
            json.dump(benchmark_summary, f, indent=2, default=str)
        print(f"\nBenchmark summary saved to {summary_file}")
    except Exception as e:
        print(f"Error saving benchmark summary: {e}")

    print(f"\nBaseline benchmarking completed!")
    print(f"Results saved in: {output_dir}")
    print(f"Models evaluated: {len(results)}")

    return results, comparison_summary

if __name__ == "__main__":
    args = parse_arguments()
    run_baseline_benchmarking(args.models, args.output_dir, args.generate_training_data)
