#!/Users/dheerajmurthy/miniforge3/envs/ns3/bin/python
"""
Run individual models with ns-3 simulation to generate separate metrics for each model.
This script:
1. Runs each routing model individually
2. Generates routing.json for each model
3. Runs ns-3 simulation with each routing configuration
4. Saves metrics.csv for each model
5. Creates comparison analysis
"""

import subprocess
import sys
import os
import json
import shutil
from datetime import datetime
from pathlib import Path

# Configuration
NS3_BINARY = "/Users/dheerajmurthy/Downloads/IIITB/sem6/NHPC/project/simulation/ns-allinone-3.42/ns-3.42/ns3"
PROJECT_DIR = "scratch/my_project"
FULL_PROJECT_PATH = "/Users/dheerajmurthy/Downloads/IIITB/sem6/NHPC/project/simulation/ns-allinone-3.42/ns-3.42/scratch/my_project"

# Models to test
MODELS = ["max_flow", "min_cost_max_flow", "multi_commodity_flow", "load_balanced_sp"]

def create_model_directories():
    """Create directories for each model's results."""
    base_dir = Path(FULL_PROJECT_PATH) / "model_results"
    base_dir.mkdir(exist_ok=True)
    
    for model in MODELS:
        model_dir = base_dir / model
        model_dir.mkdir(exist_ok=True)
        print(f"Created directory: {model_dir}")
    
    return base_dir

def backup_original_files():
    """Backup original files before modifying them."""
    backup_dir = Path(FULL_PROJECT_PATH) / "backups"
    backup_dir.mkdir(exist_ok=True)
    
    files_to_backup = ["routing.json", "metrics.csv"]
    for file in files_to_backup:
        src = Path(FULL_PROJECT_PATH) / file
        if src.exists():
            dst = backup_dir / f"{file}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            shutil.copy2(src, dst)
            print(f"Backed up {file} to {dst}")

def run_model_inference(model_name):
    """Run routing inference for a specific model."""
    print(f"\n=== Running {model_name} inference ===")
    
    cmd = [
        "python", f"{FULL_PROJECT_PATH}/ml/infer_routes.py",
        "--model", model_name,
        "--output", f"{FULL_PROJECT_PATH}/routing.json"
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=FULL_PROJECT_PATH)
        if result.returncode != 0:
            print(f"Error running {model_name} inference:")
            print(f"STDOUT: {result.stdout}")
            print(f"STDERR: {result.stderr}")
            return False
        
        print(f"✓ {model_name} inference completed")
        print(f"Output: {result.stdout}")
        return True
        
    except Exception as e:
        print(f"Exception running {model_name} inference: {e}")
        return False

def run_ns3_simulation(model_name, model_dir):
    """Run ns-3 simulation with the model's routing."""
    print(f"\n=== Running ns-3 simulation for {model_name} ===")
    
    # Output files for this model
    model_metrics = model_dir / "metrics.csv"
    model_anim = model_dir / "sim-anim.xml"
    model_routing = model_dir / "routing.json"
    
    # Copy current routing to model directory
    current_routing = Path(FULL_PROJECT_PATH) / "routing.json"
    if current_routing.exists():
        shutil.copy2(current_routing, model_routing)
        print(f"Copied routing.json to {model_routing}")
    
    # ns-3 command
    ns3_cmd = [
        NS3_BINARY,
        "run",
        f"{PROJECT_DIR}/ns3_sim",
        "--",
        f"--topo={PROJECT_DIR}/topology.json",
        f"--routes={model_routing}",
        f"--metrics={PROJECT_DIR}/metrics.csv",
        f"--anim={PROJECT_DIR}/sim-anim.xml",
        f"--flows=30"
    ]
    
    try:
        result = subprocess.run(ns3_cmd, capture_output=True, text=True, 
                             cwd=f"{FULL_PROJECT_PATH}/../../..")
        
        if result.returncode != 0:
            print(f"Error running ns-3 simulation for {model_name}:")
            print(f"STDOUT: {result.stdout}")
            print(f"STDERR: {result.stderr}")
            return False
        
        print(f"✓ {model_name} simulation completed")
        
        # Copy results to model directory
        metrics_src = Path(FULL_PROJECT_PATH) / "metrics.csv"
        anim_src = Path(FULL_PROJECT_PATH) / "sim-anim.xml"
        
        if metrics_src.exists():
            shutil.copy2(metrics_src, model_metrics)
            print(f"Copied metrics.csv to {model_metrics}")
        
        if anim_src.exists():
            shutil.copy2(anim_src, model_anim)
            print(f"Copied sim-anim.xml to {model_anim}")
        
        return True
        
    except Exception as e:
        print(f"Exception running ns-3 simulation for {model_name}: {e}")
        return False

def analyze_model_metrics_basic(model_name, model_dir):
    """Basic metrics analysis without pandas."""
    metrics_file = model_dir / "metrics.csv"
    
    try:
        import csv
        with open(metrics_file, 'r') as f:
            reader = csv.DictReader(f)
            data = list(reader)
        
        if not data:
            return {"error": f"No data in metrics file for {model_name}"}
        
        total_flows = len(data)
        successful_flows = 0
        failed_flows = 0
        partial_flows = 0
        total_throughput = 0
        total_delay = 0
        total_loss = 0
        total_tx_bytes = 0
        total_rx_bytes = 0
        
        for row in data:
            loss_pct = float(row.get('loss_pct', 0))
            throughput = float(row.get('throughput_mbps', 0))
            delay = float(row.get('avg_delay_ms', 0))
            tx_bytes = int(row.get('txBytes', 0))
            rx_bytes = int(row.get('rxBytes', 0))
            
            total_throughput += throughput
            total_delay += delay
            total_loss += loss_pct
            total_tx_bytes += tx_bytes
            total_rx_bytes += rx_bytes
            
            if loss_pct == 0:
                successful_flows += 1
            elif loss_pct == 100:
                failed_flows += 1
            else:
                partial_flows += 1
        
        analysis = {
            "model": model_name,
            "total_flows": total_flows,
            "successful_flows": successful_flows,
            "failed_flows": failed_flows,
            "partial_flows": partial_flows,
            "avg_throughput": total_throughput / total_flows if total_flows > 0 else 0,
            "max_throughput": max(float(row.get('throughput_mbps', 0)) for row in data) if data else 0,
            "min_throughput": min(float(row.get('throughput_mbps', 0)) for row in data) if data else 0,
            "avg_delay": total_delay / total_flows if total_flows > 0 else 0,
            "avg_loss": total_loss / total_flows if total_flows > 0 else 0,
            "total_tx_bytes": total_tx_bytes,
            "total_rx_bytes": total_rx_bytes,
            "packet_loss_rate": (total_flows - successful_flows) / total_flows if total_flows > 0 else 0,
            "success_rate": successful_flows / total_flows if total_flows > 0 else 0
        }
        
        # Save analysis
        analysis_file = model_dir / "analysis.json"
        with open(analysis_file, 'w') as f:
            json.dump(analysis, f, indent=2, default=str)
        
        print(f"✓ Basic analysis saved for {model_name}")
        return analysis
        
    except Exception as e:
        print(f"Error in basic analysis for {model_name}: {e}")
        return {"model": model_name, "error": str(e)}

def analyze_model_metrics(model_name, model_dir):
    """Analyze metrics for a specific model."""
    metrics_file = model_dir / "metrics.csv"
    
    if not metrics_file.exists():
        return {"error": f"No metrics file found for {model_name}"}
    
    try:
        try:
            import pandas as pd
        except ImportError:
            print("pandas not available, using basic CSV analysis")
            return analyze_model_metrics_basic(model_name, model_dir)
        
        df = pd.read_csv(metrics_file)
        
        analysis = {
            "model": model_name,
            "total_flows": len(df),
            "successful_flows": len(df[df["loss_pct"] == 0]),
            "failed_flows": len(df[df["loss_pct"] == 100]),
            "partial_flows": len(df[(df["loss_pct"] > 0) & (df["loss_pct"] < 100)]),
            "avg_throughput": df["throughput_mbps"].mean() if "throughput_mbps" in df.columns else 0,
            "max_throughput": df["throughput_mbps"].max() if "throughput_mbps" in df.columns else 0,
            "min_throughput": df["throughput_mbps"].min() if "throughput_mbps" in df.columns else 0,
            "avg_delay": df["avg_delay_ms"].mean() if "avg_delay_ms" in df.columns else 0,
            "avg_loss": df["loss_pct"].mean() if "loss_pct" in df.columns else 0,
            "total_tx_bytes": df["txBytes"].sum() if "txBytes" in df.columns else 0,
            "total_rx_bytes": df["rxBytes"].sum() if "rxBytes" in df.columns else 0,
            "packet_loss_rate": (df["loss_pct"] > 0).sum() / len(df) if len(df) > 0 else 0,
            "success_rate": (df["loss_pct"] == 0).sum() / len(df) if len(df) > 0 else 0
        }
        
        # Save analysis
        analysis_file = model_dir / "analysis.json"
        with open(analysis_file, 'w') as f:
            json.dump(analysis, f, indent=2, default=str)
        
        print(f"✓ Analysis saved for {model_name}")
        return analysis
        
    except ImportError:
        print("pandas not available, skipping detailed analysis")
        return {"model": model_name, "error": "pandas not available"}
    except Exception as e:
        print(f"Error analyzing metrics for {model_name}: {e}")
        return {"model": model_name, "error": str(e)}

def create_comparison_summary(all_analyses, base_dir):
    """Create a summary comparison of all models."""
    print(f"\n=== Creating comparison summary ===")
    
    # Filter out error analyses
    valid_analyses = [a for a in all_analyses if "error" not in a]
    
    if not valid_analyses:
        print("No valid analyses to compare")
        return
    
    comparison = {
        "timestamp": datetime.now().isoformat(),
        "models_tested": len(valid_analyses),
        "summary": {}
    }
    
    # Create comparison metrics
    metrics_to_compare = [
        "total_flows", "successful_flows", "failed_flows", "partial_flows",
        "avg_throughput", "max_throughput", "min_throughput", "avg_delay", 
        "avg_loss", "total_tx_bytes", "total_rx_bytes", "packet_loss_rate", "success_rate"
    ]
    
    for metric in metrics_to_compare:
        comparison["summary"][metric] = {}
        for analysis in valid_analyses:
            model = analysis["model"]
            comparison["summary"][metric][model] = analysis.get(metric, 0)
    
    # Find best performers
    comparison["best_performers"] = {}
    
    # Higher is better
    higher_better = ["successful_flows", "avg_throughput", "max_throughput", 
                   "min_throughput", "total_tx_bytes", "total_rx_bytes", "success_rate"]
    
    # Lower is better
    lower_better = ["failed_flows", "partial_flows", "avg_delay", "avg_loss", "packet_loss_rate"]
    
    for metric in higher_better:
        if metric in comparison["summary"]:
            best_model = max(comparison["summary"][metric].items(), key=lambda x: x[1])
            comparison["best_performers"][f"highest_{metric}"] = {"model": best_model[0], "value": best_model[1]}
    
    for metric in lower_better:
        if metric in comparison["summary"]:
            best_model = min(comparison["summary"][metric].items(), key=lambda x: x[1])
            comparison["best_performers"][f"lowest_{metric}"] = {"model": best_model[0], "value": best_model[1]}
    
    # Save comparison
    comparison_file = base_dir / "comparison_summary.json"
    with open(comparison_file, 'w') as f:
        json.dump(comparison, f, indent=2, default=str)
    
    print(f"✓ Comparison summary saved to {comparison_file}")
    
    # Print summary
    print(f"\n{'='*60}")
    print("MODEL PERFORMANCE COMPARISON SUMMARY")
    print(f"{'='*60}")
    
    for analysis in valid_analyses:
        model = analysis["model"]
        print(f"\n{model.upper()}:")
        print(f"  Success Rate: {analysis.get('success_rate', 0):.2%}")
        print(f"  Avg Throughput: {analysis.get('avg_throughput', 0):.3f} Mbps")
        print(f"  Avg Delay: {analysis.get('avg_delay', 0):.2f} ms")
        print(f"  Packet Loss Rate: {analysis.get('packet_loss_rate', 0):.2%}")
        print(f"  Successful Flows: {analysis.get('successful_flows', 0)}/{analysis.get('total_flows', 0)}")
    
    print(f"\n{'='*60}")
    print("BEST PERFORMERS BY METRIC")
    print(f"{'='*60}")
    
    for metric, performer in comparison["best_performers"].items():
        metric_name = metric.replace("highest_", "").replace("lowest_", "")
        direction = "↑" if "highest" in metric else "↓"
        print(f"{metric_name}: {performer['model']} {direction} ({performer['value']:.3f})")

def main():
    """Main execution function."""
    print("="*80)
    print("INDIVIDUAL MODEL TESTING WITH NS-3 SIMULATION")
    print("="*80)
    
    # Create directories
    base_dir = create_model_directories()
    
    # Backup original files
    backup_original_files()
    
    all_analyses = []
    
    # Run each model
    for model in MODELS:
        print(f"\n{'='*60}")
        print(f"TESTING MODEL: {model.upper()}")
        print(f"{'='*60}")
        
        model_dir = base_dir / model
        
        # Step 1: Run model inference
        if not run_model_inference(model):
            print(f"❌ Failed to run {model} inference, skipping")
            continue
        
        # Step 2: Run ns-3 simulation
        if not run_ns3_simulation(model, model_dir):
            print(f"❌ Failed to run {model} simulation, skipping")
            continue
        
        # Step 3: Analyze results
        analysis = analyze_model_metrics(model, model_dir)
        all_analyses.append(analysis)
        
        print(f"✓ Completed testing for {model}")
    
    # Step 4: Create comparison summary
    if all_analyses:
        create_comparison_summary(all_analyses, base_dir)
    
    print(f"\n{'='*80}")
    print("INDIVIDUAL MODEL TESTING COMPLETED")
    print(f"{'='*80}")
    print(f"Results saved in: {base_dir}")
    print(f"Models tested: {len([a for a in all_analyses if 'error' not in a])}/{len(MODELS)}")
    
    # Restore original files if needed
    print(f"\nTo restore original files, check the backups directory")

if __name__ == "__main__":
    main()