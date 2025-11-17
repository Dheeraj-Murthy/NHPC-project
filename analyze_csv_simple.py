#!/usr/bin/env python3
"""
Simple script to analyze CSV metrics files without external dependencies.
Reads metrics.csv files and creates text-based comparisons.
"""

import csv
import os
from pathlib import Path

def load_metrics_data():
    """Load metrics from all model directories."""
    base_dir = "model_results"
    models = ['load_balanced_sp', 'max_flow', 'min_cost_max_flow', 'multi_commodity_flow']
    
    all_data = {}
    
    for model in models:
        csv_path = os.path.join(base_dir, model, "metrics.csv")
        if os.path.exists(csv_path):
            with open(csv_path, 'r') as f:
                reader = csv.DictReader(f)
                data = list(reader)
                all_data[model] = data
                print(f"Loaded {len(data)} flows from {model}")
        else:
            print(f"Warning: {csv_path} not found")
    
    return all_data

def calculate_summary_metrics(all_data):
    """Calculate summary metrics for each model."""
    summary = {}
    
    for model, data in all_data.items():
        # Initialize counters
        total_flows = len(data)
        successful_flows = 0
        failed_flows = 0
        total_throughput = 0
        total_delay = 0
        total_loss = 0
        total_tx_packets = 0
        total_rx_packets = 0
        max_throughput = 0
        max_delay = 0
        
        # Process each flow
        for flow in data:
            tx_pkts = int(flow['txPkts'])
            rx_pkts = int(flow['rxPkts'])
            throughput = float(flow['throughput_mbps'])
            delay = float(flow['avg_delay_ms'])
            loss = float(flow['loss_pct'])
            
            total_tx_packets += tx_pkts
            total_rx_packets += rx_pkts
            
            if rx_pkts > 0:
                successful_flows += 1
                total_throughput += throughput
                total_delay += delay
                max_throughput = max(max_throughput, throughput)
                max_delay = max(max_delay, delay)
            else:
                failed_flows += 1
                total_loss += loss
        
        # Calculate averages
        success_rate = successful_flows / total_flows if total_flows > 0 else 0
        avg_throughput = total_throughput / successful_flows if successful_flows > 0 else 0
        avg_delay = total_delay / successful_flows if successful_flows > 0 else 0
        avg_loss = total_loss / total_flows if total_flows > 0 else 0
        packet_success_rate = total_rx_packets / total_tx_packets if total_tx_packets > 0 else 0
        
        summary[model] = {
            'total_flows': total_flows,
            'successful_flows': successful_flows,
            'failed_flows': failed_flows,
            'success_rate': success_rate,
            'avg_throughput_mbps': avg_throughput,
            'max_throughput_mbps': max_throughput,
            'total_throughput_mbps': total_throughput,
            'avg_delay_ms': avg_delay,
            'max_delay_ms': max_delay,
            'avg_loss_rate': avg_loss,
            'packet_success_rate': packet_success_rate,
            'total_tx_packets': total_tx_packets,
            'total_rx_packets': total_rx_packets
        }
    
    return summary

def create_bar_chart(values, labels, title, max_width=50):
    """Create a simple text-based bar chart."""
    print(f"\n{title}")
    print("=" * len(title))
    
    if not values:
        print("No data to display")
        return
    
    max_val = max(values) if max(values) > 0 else 1
    
    for label, value in zip(labels, values):
        bar_length = int((value / max_val) * max_width) if max_val > 0 else 0
        bar = "█" * bar_length
        print(f"{label:<20} {bar:<{max_width}} {value:.3f}")

def create_comparison_bars(summary):
    """Create text-based bar charts for comparison."""
    models = list(summary.keys())
    
    # Success Rate Comparison
    success_rates = [summary[model]['success_rate'] for model in models]
    create_bar_chart(success_rates, models, "FLOW SUCCESS RATE COMPARISON")
    
    # Packet Success Rate Comparison
    packet_rates = [summary[model]['packet_success_rate'] for model in models]
    create_bar_chart(packet_rates, models, "PACKET SUCCESS RATE COMPARISON")
    
    # Average Throughput Comparison
    avg_throughputs = [summary[model]['avg_throughput_mbps'] for model in models]
    create_bar_chart(avg_throughputs, models, "AVERAGE THROUGHPUT COMPARISON (Mbps)")
    
    # Total Throughput Comparison
    total_throughputs = [summary[model]['total_throughput_mbps'] for model in models]
    create_bar_chart(total_throughputs, models, "TOTAL THROUGHPUT COMPARISON (Mbps)")
    
    # Average Delay Comparison
    avg_delays = [summary[model]['avg_delay_ms'] for model in models]
    create_bar_chart(avg_delays, models, "AVERAGE DELAY COMPARISON (ms)")
    
    # Loss Rate Comparison
    loss_rates = [summary[model]['avg_loss_rate'] for model in models]
    create_bar_chart(loss_rates, models, "AVERAGE LOSS RATE COMPARISON (%)")

def print_detailed_summary(summary):
    """Print a detailed summary table."""
    print("\n" + "="*100)
    print("DETAILED ROUTING MODELS PERFORMANCE SUMMARY")
    print("="*100)
    
    print(f"{'Model':<20} {'Total':<6} {'Success':<8} {'Packet':<8} {'Avg Thr':<9} {'Max Thr':<9} {'Total Thr':<10} {'Avg Del':<9} {'Max Del':<9} {'Loss':<7}")
    print(f"{'':<20} {'Flows':<6} {'Rate':<8} {'Rate':<8} {'(Mbps)':<9} {'(Mbps)':<9} {'(Mbps)':<10} {'(ms)':<9} {'(ms)':<9} {'(%)':<7}")
    print("-"*100)
    
    for model in sorted(summary.keys()):
        m = summary[model]
        print(f"{model:<20} {m['total_flows']:<6} {m['success_rate']:<8.3f} {m['packet_success_rate']:<8.3f} "
              f"{m['avg_throughput_mbps']:<9.3f} {m['max_throughput_mbps']:<9.3f} {m['total_throughput_mbps']:<10.3f} "
              f"{m['avg_delay_ms']:<9.0f} {m['max_delay_ms']:<9.0f} {m['avg_loss_rate']:<7.1f}")

def print_key_insights(summary):
    """Print key insights and comparisons."""
    print("\n" + "="*80)
    print("KEY INSIGHTS AND COMPARISONS")
    print("="*80)
    
    # Best performers for each metric
    best_success_rate = max(summary.keys(), key=lambda x: summary[x]['success_rate'])
    best_packet_rate = max(summary.keys(), key=lambda x: summary[x]['packet_success_rate'])
    best_avg_throughput = max(summary.keys(), key=lambda x: summary[x]['avg_throughput_mbps'])
    best_total_throughput = max(summary.keys(), key=lambda x: summary[x]['total_throughput_mbps'])
    lowest_delay = min(summary.keys(), key=lambda x: summary[x]['avg_delay_ms'])
    lowest_loss = min(summary.keys(), key=lambda x: summary[x]['avg_loss_rate'])
    
    print(f"🏆 Best Flow Success Rate: {best_success_rate} ({summary[best_success_rate]['success_rate']:.3f})")
    print(f"🏆 Best Packet Success Rate: {best_packet_rate} ({summary[best_packet_rate]['packet_success_rate']:.3f})")
    print(f"🏆 Best Average Throughput: {best_avg_throughput} ({summary[best_avg_throughput]['avg_throughput_mbps']:.3f} Mbps)")
    print(f"🏆 Best Total Throughput: {best_total_throughput} ({summary[best_total_throughput]['total_throughput_mbps']:.3f} Mbps)")
    print(f"🏆 Lowest Average Delay: {lowest_delay} ({summary[lowest_delay]['avg_delay_ms']:.0f} ms)")
    print(f"🏆 Lowest Loss Rate: {lowest_loss} ({summary[lowest_loss]['avg_loss_rate']:.1f}%)")
    
    print(f"\n📊 Flow Distribution:")
    for model in sorted(summary.keys()):
        m = summary[model]
        print(f"  {model}: {m['successful_flows']}/{m['total_flows']} flows successful ({m['success_rate']:.1%})")

def main():
    """Main function to analyze CSV metrics."""
    print("Loading CSV metrics data...")
    all_data = load_metrics_data()
    
    if not all_data:
        print("No CSV data found!")
        return 1
    
    print("Calculating summary metrics...")
    summary = calculate_summary_metrics(all_data)
    
    print("Creating comparison visualizations...")
    create_comparison_bars(summary)
    
    print_detailed_summary(summary)
    print_key_insights(summary)
    
    print(f"\n✅ Analysis complete!")
    
    return 0

if __name__ == "__main__":
    exit(main())