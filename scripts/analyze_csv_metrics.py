#!/usr/bin/env python3
"""
Script to analyze CSV metrics files directly and create comparison bar graphs.
Reads metrics.csv files from model_results/*/ directories and generates visualizations.
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
from pathlib import Path
import seaborn as sns

# Set style
plt.style.use('default')
sns.set_palette("husl")

def load_metrics_data():
    """Load metrics from all model directories."""
    base_dir = "model_results"
    models = ['load_balanced_sp', 'max_flow', 'min_cost_max_flow', 'multi_commodity_flow']

    all_data = {}

    for model in models:
        csv_path = os.path.join(base_dir, model, "metrics.csv")
        if os.path.exists(csv_path):
            df = pd.read_csv(csv_path)
            all_data[model] = df
            print(f"Loaded {len(df)} flows from {model}")
        else:
            print(f"Warning: {csv_path} not found")

    return all_data

def calculate_summary_metrics(all_data):
    """Calculate summary metrics for each model."""
    summary = {}

    for model, df in all_data.items():
        # Basic metrics
        total_flows = len(df)
        successful_flows = len(df[df['rxPkts'] > 0])
        failed_flows = len(df[df['rxPkts'] == 0])

        # Throughput metrics (only for successful flows)
        successful_df = df[df['rxPkts'] > 0]
        if len(successful_df) > 0:
            avg_throughput = successful_df['throughput_mbps'].mean()
            max_throughput = successful_df['throughput_mbps'].max()
            total_throughput = successful_df['throughput_mbps'].sum()
        else:
            avg_throughput = max_throughput = total_throughput = 0

        # Delay metrics (only for successful flows)
        if len(successful_df) > 0:
            avg_delay = successful_df['avg_delay_ms'].mean()
            max_delay = successful_df['avg_delay_ms'].max()
        else:
            avg_delay = max_delay = 0

        # Loss metrics
        avg_loss_rate = df['loss_pct'].mean()

        # Packet metrics
        total_tx_packets = df['txPkts'].sum()
        total_rx_packets = df['rxPkts'].sum()
        overall_success_rate = total_rx_packets / total_tx_packets if total_tx_packets > 0 else 0

        summary[model] = {
            'total_flows': total_flows,
            'successful_flows': successful_flows,
            'failed_flows': failed_flows,
            'success_rate': successful_flows / total_flows,
            'avg_throughput_mbps': avg_throughput,
            'max_throughput_mbps': max_throughput,
            'total_throughput_mbps': total_throughput,
            'avg_delay_ms': avg_delay,
            'max_delay_ms': max_delay,
            'avg_loss_rate': avg_loss_rate,
            'overall_packet_success_rate': overall_success_rate,
            'total_tx_packets': total_tx_packets,
            'total_rx_packets': total_rx_packets
        }

    return summary

def create_comparison_bars(summary, output_dir="ml/results"):
    """Create bar graphs comparing metrics across models."""
    os.makedirs(output_dir, exist_ok=True)

    # Colors for each model
    colors = {
        'load_balanced_sp': '#FF6B6B',
        'max_flow': '#4ECDC4',
        'min_cost_max_flow': '#45B7D1',
        'multi_commodity_flow': '#96CEB4'
    }

    models = list(summary.keys())
    model_colors = [colors[model] for model in models]

    # 1. Success Rate Comparison
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

    success_rates = [summary[model]['success_rate'] for model in models]
    packet_success_rates = [summary[model]['overall_packet_success_rate'] for model in models]

    bars1 = ax1.bar(models, success_rates, color=model_colors, alpha=0.8, edgecolor='black', linewidth=1)
    ax1.set_title('Flow Success Rate', fontsize=14, fontweight='bold')
    ax1.set_ylabel('Success Rate', fontsize=12)
    ax1.set_ylim(0, 1)
    ax1.grid(True, alpha=0.3, axis='y')

    for bar, rate in zip(bars1, success_rates):
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                f'{rate:.3f}', ha='center', va='bottom', fontsize=10, fontweight='bold')

    bars2 = ax2.bar(models, packet_success_rates, color=model_colors, alpha=0.8, edgecolor='black', linewidth=1)
    ax2.set_title('Overall Packet Success Rate', fontsize=14, fontweight='bold')
    ax2.set_ylabel('Packet Success Rate', fontsize=12)
    ax2.set_ylim(0, 1)
    ax2.grid(True, alpha=0.3, axis='y')

    for bar, rate in zip(bars2, packet_success_rates):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                f'{rate:.3f}', ha='center', va='bottom', fontsize=10, fontweight='bold')

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'success_rates_comparison.png'), dpi=300, bbox_inches='tight')
    plt.close()

    # 2. Throughput Comparison
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

    avg_throughputs = [summary[model]['avg_throughput_mbps'] for model in models]
    max_throughputs = [summary[model]['max_throughput_mbps'] for model in models]
    total_throughputs = [summary[model]['total_throughput_mbps'] for model in models]

    x = np.arange(len(models))
    width = 0.25

    bars1 = ax1.bar(x - width, avg_throughputs, width, label='Avg Throughput', color='lightblue', alpha=0.8, edgecolor='black')
    bars2 = ax1.bar(x, max_throughputs, width, label='Max Throughput', color='lightgreen', alpha=0.8, edgecolor='black')
    bars3 = ax1.bar(x + width, total_throughputs, width, label='Total Throughput', color='lightcoral', alpha=0.8, edgecolor='black')

    ax1.set_title('Throughput Metrics Comparison', fontsize=14, fontweight='bold')
    ax1.set_ylabel('Throughput (Mbps)', fontsize=12)
    ax1.set_xticks(x)
    ax1.set_xticklabels(models, rotation=45, ha='right')
    ax1.legend()
    ax1.grid(True, alpha=0.3, axis='y')

    # Add value labels
    for bars in [bars1, bars2, bars3]:
        for bar in bars:
            height = bar.get_height()
            if height > 0:
                ax1.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                        f'{height:.2f}', ha='center', va='bottom', fontsize=8)

    # Total flows comparison
    total_flows = [summary[model]['total_flows'] for model in models]
    successful_flows = [summary[model]['successful_flows'] for model in models]
    failed_flows = [summary[model]['failed_flows'] for model in models]

    bars1 = ax2.bar(x - width, total_flows, width, label='Total Flows', color='lightgray', alpha=0.8, edgecolor='black')
    bars2 = ax2.bar(x, successful_flows, width, label='Successful Flows', color='lightgreen', alpha=0.8, edgecolor='black')
    bars3 = ax2.bar(x + width, failed_flows, width, label='Failed Flows', color='lightcoral', alpha=0.8, edgecolor='black')

    ax2.set_title('Flow Count Comparison', fontsize=14, fontweight='bold')
    ax2.set_ylabel('Number of Flows', fontsize=12)
    ax2.set_xticks(x)
    ax2.set_xticklabels(models, rotation=45, ha='right')
    ax2.legend()
    ax2.grid(True, alpha=0.3, axis='y')

    for bars in [bars1, bars2, bars3]:
        for bar in bars:
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                    f'{int(height)}', ha='center', va='bottom', fontsize=8)

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'throughput_comparison.png'), dpi=300, bbox_inches='tight')
    plt.close()

    # 3. Delay and Loss Comparison
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

    avg_delays = [summary[model]['avg_delay_ms'] for model in models]
    max_delays = [summary[model]['max_delay_ms'] for model in models]

    x = np.arange(len(models))
    width = 0.35

    bars1 = ax1.bar(x - width/2, avg_delays, width, label='Avg Delay', color='orange', alpha=0.8, edgecolor='black')
    bars2 = ax1.bar(x + width/2, max_delays, width, label='Max Delay', color='red', alpha=0.8, edgecolor='black')

    ax1.set_title('Delay Metrics Comparison', fontsize=14, fontweight='bold')
    ax1.set_ylabel('Delay (ms)', fontsize=12)
    ax1.set_xticks(x)
    ax1.set_xticklabels(models, rotation=45, ha='right')
    ax1.legend()
    ax1.grid(True, alpha=0.3, axis='y')

    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            if height > 0:
                ax1.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                        f'{height:.0f}', ha='center', va='bottom', fontsize=8)

    # Loss rates
    avg_loss_rates = [summary[model]['avg_loss_rate'] for model in models]

    bars = ax2.bar(models, avg_loss_rates, color=model_colors, alpha=0.8, edgecolor='black', linewidth=1)
    ax2.set_title('Average Loss Rate Comparison', fontsize=14, fontweight='bold')
    ax2.set_ylabel('Loss Rate (%)', fontsize=12)
    ax2.grid(True, alpha=0.3, axis='y')

    for bar, rate in zip(bars, avg_loss_rates):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height + 1,
                f'{rate:.1f}', ha='center', va='bottom', fontsize=10, fontweight='bold')

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'delay_loss_comparison.png'), dpi=300, bbox_inches='tight')
    plt.close()

    # 4. Summary Dashboard
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    axes = axes.flatten()

    metrics_data = [
        ('success_rate', 'Flow Success Rate', models, [summary[m]['success_rate'] for m in models]),
        ('overall_packet_success_rate', 'Packet Success Rate', models, [summary[m]['overall_packet_success_rate'] for m in models]),
        ('avg_throughput_mbps', 'Avg Throughput (Mbps)', models, [summary[m]['avg_throughput_mbps'] for m in models]),
        ('total_throughput_mbps', 'Total Throughput (Mbps)', models, [summary[m]['total_throughput_mbps'] for m in models]),
        ('avg_delay_ms', 'Avg Delay (ms)', models, [summary[m]['avg_delay_ms'] for m in models]),
        ('avg_loss_rate', 'Avg Loss Rate (%)', models, [summary[m]['avg_loss_rate'] for m in models])
    ]

    for i, (key, title, model_names, values) in enumerate(metrics_data):
        ax = axes[i]
        bars = ax.bar(model_names, values, color=model_colors, alpha=0.8, edgecolor='black', linewidth=1)
        ax.set_title(title, fontsize=12, fontweight='bold')
        ax.grid(True, alpha=0.3, axis='y')

        # Rotate x labels for better readability
        ax.set_xticklabels(model_names, rotation=45, ha='right')

        # Add value labels
        for bar, value in zip(bars, values):
            height = bar.get_height()
            if key in ['success_rate', 'overall_packet_success_rate']:
                label = f'{value:.3f}'
            elif 'delay' in key:
                label = f'{value:.0f}'
            elif 'loss' in key:
                label = f'{value:.1f}'
            else:
                label = f'{value:.2f}'

            if height > 0:
                ax.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                       label, ha='center', va='bottom', fontsize=9, fontweight='bold')

    plt.suptitle('Routing Models Performance Dashboard', fontsize=16, fontweight='bold', y=0.98)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'performance_dashboard.png'), dpi=300, bbox_inches='tight')
    plt.close()

def print_summary_table(summary):
    """Print a summary table of metrics."""
    print("\n" + "="*80)
    print("ROUTING MODELS PERFORMANCE SUMMARY")
    print("="*80)

    print(f"{'Model':<20} {'Flows':<8} {'Success':<8} {'Avg Thr':<10} {'Total Thr':<11} {'Avg Delay':<10} {'Loss Rate':<10}")
    print("-"*80)

    for model in summary:
        metrics = summary[model]
        print(f"{model:<20} {metrics['total_flows']:<8} {metrics['success_rate']:<8.3f} "
              f"{metrics['avg_throughput_mbps']:<10.3f} {metrics['total_throughput_mbps']:<11.3f} "
              f"{metrics['avg_delay_ms']:<10.0f} {metrics['avg_loss_rate']:<10.1f}")

def main():
    """Main function to analyze CSV metrics and generate graphs."""
    print("Loading CSV metrics data...")
    all_data = load_metrics_data()

    if not all_data:
        print("No CSV data found!")
        return 1

    print("Calculating summary metrics...")
    summary = calculate_summary_metrics(all_data)

    print("Generating comparison graphs...")
    create_comparison_bars(summary)

    print_summary_table(summary)

    print(f"\nGraphs saved to ml/results/")
    print("Generated files:")
    print("  - success_rates_comparison.png")
    print("  - throughput_comparison.png")
    print("  - delay_loss_comparison.png")
    print("  - performance_dashboard.png")

    return 0

if __name__ == "__main__":
    exit(main())
