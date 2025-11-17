#!/Users/dheerajmurthy/miniforge3/envs/ns3/bin/python
"""
Enhanced routing inference using multiple baseline flow algorithms.
Reads:
 - topology.json
 - metrics.csv (to determine which src-dst pairs exist)
Writes:
 - routing.json (routes: src, dst, next_hop)
 - comparison reports in ml/results/
"""
import json
import csv
import sys
import os
from argparse import ArgumentParser

# Add ml directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from core.model_manager import ModelManager
from core.performance_comparator import PerformanceComparator

FULL_PROJECT_PATH = "/Users/dheerajmurthy/Downloads/IIITB/sem6/NHPC/project/simulation/ns-allinone-3.42/ns-3.42/scratch/my_project"

TOPO = f"{FULL_PROJECT_PATH}/topology.json"
METRICS = f"{FULL_PROJECT_PATH}/metrics.csv"
OUT = f"{FULL_PROJECT_PATH}/routing.json"

def parse_arguments():
    """Parse command line arguments."""
    parser = ArgumentParser(description="Run routing inference with baseline models")
    parser.add_argument("--model", type=str, choices=["max_flow", "min_cost_max_flow", 
                        "multi_commodity_flow", "load_balanced_sp", "all"],
                        default="all", help="Model to run (default: all)")
    parser.add_argument("--compare", action="store_true", 
                       help="Generate comparison report")
    parser.add_argument("--output", type=str, default=OUT,
                       help=f"Output routing file (default: {OUT})")
    return parser.parse_args()

def run_baseline_routing(model_name="all", compare=False, output_file=OUT):
    """
    Run routing inference using baseline models.
    
    Args:
        model_name: Model to run or "all" for all models
        compare: Whether to generate comparison report
        output_file: Output file for routing results
    """
    print("Starting baseline routing inference...")
    
    # Initialize model manager
    manager = ModelManager(FULL_PROJECT_PATH)
    
    # Print data summary
    summary = manager.get_data_summary()
    print(f"\nData Summary:")
    print(f"  Topology: {summary['topology_nodes']} nodes, {summary['topology_links']} links")
    print(f"  Flow demands: {summary['flow_demands']} pairs")
    print(f"  Available models: {summary['available_models']}")
    
    # Run models
    if model_name == "all":
        print(f"\nRunning all models...")
        results = manager.run_all_models()
        
        # Save all results
        results_file = manager.save_results(results)
        
        # Generate comparison if requested
        if compare:
            print("\nGenerating comparison report...")
            comparator = PerformanceComparator(manager.results_dir)
            comparison_summary = comparator.generate_summary_report(results)
            
            # Save comparison report
            report_file = comparator.save_comparison_report(comparison_summary)
            
            # Print summary
            comparator.print_summary(comparison_summary)
        
        # Use best model for routing output
        if results:
            # Use multi_commodity_flow as it's the best overall performer
            preferred_model = "multi_commodity_flow"
            
            if preferred_model in results and "error" not in results[preferred_model]:
                best_model = preferred_model
                metrics = results[preferred_model].get("metrics", {})
                success_rate = metrics.get("success_rate", 0)
                print(f"\nUsing {best_model} for routing output (best overall performer)")
                routes = results[best_model].get("routes", [])
            else:
                # Fallback to model with highest success rate
                best_model = None
                best_success_rate = -1
                
                for model_name, model_results in results.items():
                    if "error" not in model_results:
                        metrics = model_results.get("metrics", {})
                        success_rate = metrics.get("success_rate", 0)
                        if success_rate > best_success_rate:
                            best_success_rate = success_rate
                            best_model = model_name
                
                if best_model:
                    print(f"\nUsing {best_model} for routing output (success rate: {best_success_rate:.2f})")
                    routes = results[best_model].get("routes", [])
                else:
                    print("No successful model found, using empty routes")
                    routes = []
        else:
            routes = []
            
    else:
        print(f"\nRunning single model: {model_name}")
        result = manager.run_single_model(model_name)
        
        if "error" in result:
            print(f"Error running {model_name}: {result['error']}")
            routes = []
        else:
            routes = result.get("routes", [])
            metrics = result.get("metrics", {})
            print(f"Model completed: {len(routes)} routes generated")
            if metrics:
                print(f"Key metrics: success_rate={metrics.get('success_rate', 0):.2f}")
    
    # Write routing output
    routing_output = {
        "routes": routes,
        "metadata": {
            "model_used": model_name,
            "total_routes": len(routes),
            "timestamp": manager.get_data_summary().get("available_models", [])
        }
    }
    
    with open(output_file, "w") as f:
        json.dump(routing_output, f, indent=2)
    
    print(f"\nRouting results written to {output_file}")
    print(f"Total routes: {len(routes)}")
    
    # Print sample routes
    if routes:
        print("\nSample routes:")
        for i, route in enumerate(routes[:5]):
            print(f"  {route['src']} -> {route['dst']} via {route['next_hop']} "
                  f"(model: {route.get('model', 'unknown')})")
        if len(routes) > 5:
            print(f"  ... and {len(routes) - 5} more routes")

if __name__ == "__main__":
    args = parse_arguments()
    run_baseline_routing(args.model, args.compare, args.output)
