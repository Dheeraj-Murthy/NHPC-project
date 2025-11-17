#!/Users/dheerajmurthy/miniforge3/envs/ns3/bin/python
"""
Compare metrics from individual model runs.
Reads all model_results/*/metrics.csv files and generates comparison analysis and graphs.
"""

import json
import csv
import os
import sys
from pathlib import Path
from datetime import datetime
import statistics

# Configuration
PROJECT_PATH = "/Users/dheerajmurthy/Downloads/IIITB/sem6/NHPC/project/simulation/ns-allinone-3.42/ns-3.42/scratch/my_project"
RESULTS_DIR = Path(PROJECT_PATH) / "model_results"

def load_metrics_csv(csv_file):
    """Load and analyze metrics from a CSV file."""
    try:
        data = []
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                data.append(row)
        
        if not data:
            return None
        
        # Calculate statistics
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
        
        return {
            'total_flows': total_flows,
            'successful_flows': successful_flows,
            'failed_flows': failed_flows,
            'partial_flows': partial_flows,
            'avg_throughput': total_throughput / total_flows if total_flows > 0 else 0,
            'max_throughput': max(float(row.get('throughput_mbps', 0)) for row in data) if data else 0,
            'min_throughput': min(float(row.get('throughput_mbps', 0)) for row in data) if data else 0,
            'avg_delay': total_delay / total_flows if total_flows > 0 else 0,
            'avg_loss': total_loss / total_flows if total_flows > 0 else 0,
            'total_tx_bytes': total_tx_bytes,
            'total_rx_bytes': total_rx_bytes,
            'packet_loss_rate': (total_flows - successful_flows) / total_flows if total_flows > 0 else 0,
            'success_rate': successful_flows / total_flows if total_flows > 0 else 0,
            'throughput_std': statistics.stdev([float(row.get('throughput_mbps', 0)) for row in data]) if len(data) > 1 else 0
        }
        
    except Exception as e:
        print(f"Error loading {csv_file}: {e}")
        return None

def create_ascii_comparison(all_metrics):
    """Create ASCII comparison charts."""
    print("\n" + "="*80)
    print("DETAILED MODEL PERFORMANCE COMPARISON")
    print("="*80)
    
    models = list(all_metrics.keys())
    
    # Success Rate Comparison
    print("\n📊 SUCCESS RATE COMPARISON:")
    print("-" * 50)
    for model in models:
        metrics = all_metrics[model]
        success_rate = metrics['success_rate'] * 100
        bar_length = int(success_rate / 2)
        bar = "█" * bar_length + "░" * (50 - bar_length)
        print(f"{model:20} {bar} {success_rate:5.1f}% ({metrics['successful_flows']}/{metrics['total_flows']})")
    
    # Throughput Comparison
    print("\n💾 AVERAGE THROUGHPUT (Mbps):")
    print("-" * 50)
    max_throughput = max(m['avg_throughput'] for m in all_metrics.values())
    for model in models:
        metrics = all_metrics[model]
        throughput = metrics['avg_throughput']
        if max_throughput > 0:
            bar_length = int((throughput / max_throughput) * 50)
        else:
            bar_length = 0
        bar = "█" * bar_length + "░" * (50 - bar_length)
        print(f"{model:20} {bar} {throughput:8.3f} Mbps")
    
    # Packet Loss Comparison
    print("\n📉 PACKET LOSS RATE:")
    print("-" * 50)
    max_loss = max(m['packet_loss_rate'] for m in all_metrics.values())
    for model in models:
        metrics = all_metrics[model]
        loss_rate = metrics['packet_loss_rate'] * 100
        if max_loss > 0:
            bar_length = int((loss_rate / max_loss) * 50)
        else:
            bar_length = 0
        bar = "█" * bar_length + "░" * (50 - bar_length)
        print(f"{model:20} {bar} {loss_rate:5.1f}% ({metrics['failed_flows']} failed)")
    
    # Delay Comparison
    print("\n⏱️ AVERAGE DELAY (ms):")
    print("-" * 50)
    max_delay = max(m['avg_delay'] for m in all_metrics.values())
    for model in models:
        metrics = all_metrics[model]
        delay = metrics['avg_delay']
        if max_delay > 0:
            bar_length = int((delay / max_delay) * 50)
        else:
            bar_length = 0
        bar = "█" * bar_length + "░" * (50 - bar_length)
        print(f"{model:20} {bar} {delay:8.2f} ms")

def create_detailed_table(all_metrics):
    """Create detailed comparison table."""
    print("\n" + "="*120)
    print("DETAILED METRICS TABLE")
    print("="*120)
    
    # Header
    header = f"{'Model':<20} {'Success':<10} {'Throughput':<12} {'Delay':<10} {'Loss':<8} {'Flows':<15} {'Bytes TX':<12} {'Bytes RX':<12}"
    print(header)
    print("-" * 120)
    
    # Data rows
    for model, metrics in all_metrics.items():
        success_pct = f"{metrics['success_rate']*100:.1f}%"
        throughput = f"{metrics['avg_throughput']:.3f} Mbps"
        delay = f"{metrics['avg_delay']:.1f} ms"
        loss = f"{metrics['packet_loss_rate']*100:.1f}%"
        flows = f"{metrics['successful_flows']}/{metrics['total_flows']}"
        tx_bytes = f"{metrics['total_tx_bytes']//1000000:.1f}M"
        rx_bytes = f"{metrics['total_rx_bytes']//1000000:.1f}M"
        
        row = f"{model:<20} {success_pct:<10} {throughput:<12} {delay:<10} {loss:<8} {flows:<15} {tx_bytes:<12} {rx_bytes:<12}"
        print(row)

def find_best_performers(all_metrics):
    """Find and display best performers for each metric."""
    print("\n" + "="*80)
    print("BEST PERFORMERS BY METRIC")
    print("="*80)
    
    metrics_info = {
        'Success Rate': ('success_rate', True, '%'),
        'Avg Throughput': ('avg_throughput', True, 'Mbps'),
        'Max Throughput': ('max_throughput', True, 'Mbps'),
        'Avg Delay': ('avg_delay', False, 'ms'),
        'Packet Loss': ('packet_loss_rate', False, '%'),
        'Total Bytes RX': ('total_rx_bytes', True, 'bytes'),
        'Successful Flows': ('successful_flows', True, 'flows')
    }
    
    for metric_name, (metric_key, higher_better, unit) in metrics_info.items():
        best_model = None
        best_value = None
        
        if higher_better:
            best_model = max(all_metrics.items(), key=lambda x: x[1][metric_key])
        else:
            best_model = min(all_metrics.items(), key=lambda x: x[1][metric_key])
        
        model_name, metrics = best_model
        value = metrics[metric_key]
        
        if unit == '%':
            display_value = f"{value*100:.1f}%"
        elif unit == 'Mbps':
            display_value = f"{value:.3f} Mbps"
        elif unit == 'ms':
            display_value = f"{value:.1f} ms"
        elif unit == 'bytes':
            display_value = f"{value:,}"
        else:
            display_value = str(value)
        
        direction = "↑" if higher_better else "↓"
        print(f"{metric_name:<20}: {model_name:<20} {direction} {display_value}")

def generate_comparison_report(all_metrics):
    """Generate comprehensive comparison report."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = RESULTS_DIR / f"comparison_report_{timestamp}.json"
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "models_compared": list(all_metrics.keys()),
        "metrics": all_metrics,
        "summary": {
            "total_models": len(all_metrics),
            "best_success_rate": max(m['success_rate'] for m in all_metrics.values()),
            "best_throughput": max(m['avg_throughput'] for m in all_metrics.values()),
            "lowest_delay": min(m['avg_delay'] for m in all_metrics.values()),
            "lowest_packet_loss": min(m['packet_loss_rate'] for m in all_metrics.values())
        }
    }
    
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"\n📄 Detailed comparison report saved to: {report_file}")
    return report_file

def main():
    """Main comparison function."""
    print("="*80)
    print("MODEL METRICS COMPARISON ANALYSIS")
    print("="*80)
    
    if not RESULTS_DIR.exists():
        print(f"❌ Results directory not found: {RESULTS_DIR}")
        print("Please run run_individual_models.py first")
        return
    
    # Load all model metrics
    all_metrics = {}
    models_found = []
    
    for model_dir in RESULTS_DIR.iterdir():
        if model_dir.is_dir():
            metrics_file = model_dir / "metrics.csv"
            if metrics_file.exists():
                metrics = load_metrics_csv(metrics_file)
                if metrics:
                    all_metrics[model_dir.name] = metrics
                    models_found.append(model_dir.name)
                    print(f"✓ Loaded metrics for {model_dir.name}")
                else:
                    print(f"❌ Failed to load metrics for {model_dir.name}")
            else:
                print(f"⚠️ No metrics.csv found for {model_dir.name}")
    
    if not all_metrics:
        print("❌ No valid metrics files found")
        return
    
    print(f"\n📊 Successfully loaded metrics for {len(all_metrics)} models: {', '.join(models_found)}")
    
    # Generate comparisons
    create_ascii_comparison(all_metrics)
    create_detailed_table(all_metrics)
    find_best_performers(all_metrics)
    
    # Generate report
    report_file = generate_comparison_report(all_metrics)
    
    print("\n" + "="*80)
    print("COMPARISON ANALYSIS COMPLETED")
    print("="*80)
    print(f"Models compared: {len(all_metrics)}")
    print(f"Report saved: {report_file}")
    print(f"Results directory: {RESULTS_DIR}")

if __name__ == "__main__":
    main()