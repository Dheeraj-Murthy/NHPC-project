#!/usr/bin/env python3
"""
Script to generate comparison graphs for routing model performance.
Loads the latest comparison report and creates visualizations using matplotlib.
"""

import json
import os
import glob
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path


def load_latest_comparison_report():
    """Load the most recent comparison report from ml/results/ directory."""
    pattern = "ml/results/comparison_report_*.json"
    reports = glob.glob(pattern)
    
    if not reports:
        raise FileNotFoundError(f"No comparison reports found in {pattern}")
    
    # Sort by filename (which includes timestamp) and get the latest
    latest_report = max(reports)
    print(f"Loading latest report: {latest_report}")
    
    with open(latest_report, 'r') as f:
        return json.load(f)


def extract_metrics_data(report):
    """Extract key metrics for visualization from the comparison report."""
    metrics_to_extract = [
        'success_rate', 'total_flow', 'total_allocated', 'allocation_ratio',
        'cost_efficiency', 'fairness_index', 'avg_edge_utilization', 'total_flows_routed'
    ]
    
    models = ['max_flow', 'min_cost_max_flow', 'multi_commodity_flow', 'load_balanced_sp']
    
    data = {}
    for metric in metrics_to_extract:
        if metric in report['metrics_comparison']:
            data[metric] = {}
            for ranking in report['metrics_comparison'][metric]['rankings']:
                data[metric][ranking['model']] = ranking['value']
    
    return data, models


def create_individual_metric_graphs(data, models, output_dir):
    """Create individual bar graphs for each metric."""
    # Define colors for each model
    colors = {
        'max_flow': '#FF6B6B',
        'min_cost_max_flow': '#4ECDC4', 
        'multi_commodity_flow': '#45B7D1',
        'load_balanced_sp': '#96CEB4'
    }
    
    # Define display names and units for metrics
    metric_info = {
        'success_rate': {'name': 'Success Rate', 'unit': '', 'ylim': (0, 1.1)},
        'total_flow': {'name': 'Total Flow', 'unit': 'units', 'ylim': None},
        'total_allocated': {'name': 'Total Allocated', 'unit': 'units', 'ylim': None},
        'allocation_ratio': {'name': 'Allocation Ratio', 'unit': '', 'ylim': None},
        'cost_efficiency': {'name': 'Cost Efficiency', 'unit': '', 'ylim': None},
        'fairness_index': {'name': 'Fairness Index', 'unit': '', 'ylim': (0, 1.1)},
        'avg_edge_utilization': {'name': 'Avg Edge Utilization', 'unit': '', 'ylim': (0, 1.1)},
        'total_flows_routed': {'name': 'Total Flows Routed', 'unit': 'count', 'ylim': None}
    }
    
    for metric, values in data.items():
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Prepare data for plotting
        model_names = []
        metric_values = []
        bar_colors = []
        
        for model in models:
            if model in values:
                model_names.append(model.replace('_', '\n'))
                # Handle None or zero values
                value = values[model] if values[model] is not None else 0
                metric_values.append(value)
                bar_colors.append(colors[model])
        
        # Create bars
        bars = ax.bar(model_names, metric_values, color=bar_colors, alpha=0.8, edgecolor='black', linewidth=1)
        
        # Customize the plot
        info = metric_info.get(metric, {'name': metric, 'unit': '', 'ylim': None})
        ax.set_title(f'{info["name"]} Comparison', fontsize=14, fontweight='bold', pad=20)
        ax.set_ylabel(f'{info["name"]} {info["unit"]}', fontsize=12)
        ax.set_xlabel('Routing Models', fontsize=12)
        
        # Set y-axis limits if specified
        if info['ylim']:
            ax.set_ylim(info['ylim'])
        
        # Add value labels on bars
        for bar, value in zip(bars, metric_values):
            height = bar.get_height()
            if height > 0:
                ax.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                       f'{value:.3f}', ha='center', va='bottom', fontsize=10, fontweight='bold')
            else:
                ax.text(bar.get_x() + bar.get_width()/2., 0.01,
                       '0.000', ha='center', va='bottom', fontsize=10, fontweight='bold')
        
        # Add grid
        ax.grid(True, alpha=0.3, axis='y')
        
        # Adjust layout and save
        plt.tight_layout()
        output_path = os.path.join(output_dir, f'{metric}_comparison.png')
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"Saved: {output_path}")


def create_summary_comparison_graph(data, models, output_dir):
    """Create a summary graph with multiple metrics side by side."""
    # Select key metrics for summary
    summary_metrics = ['success_rate', 'total_flow', 'cost_efficiency', 'fairness_index']
    
    # Filter to only include metrics that exist in data
    available_metrics = [m for m in summary_metrics if m in data]
    
    if not available_metrics:
        print("No metrics available for summary graph")
        return
    
    # Define colors
    colors = {
        'max_flow': '#FF6B6B',
        'min_cost_max_flow': '#4ECDC4', 
        'multi_commodity_flow': '#45B7D1',
        'load_balanced_sp': '#96CEB4'
    }
    
    # Create subplots
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    axes = axes.flatten()
    
    metric_info = {
        'success_rate': {'name': 'Success Rate', 'ylim': (0, 1.1)},
        'total_flow': {'name': 'Total Flow', 'ylim': None},
        'cost_efficiency': {'name': 'Cost Efficiency', 'ylim': None},
        'fairness_index': {'name': 'Fairness Index', 'ylim': (0, 1.1)}
    }
    
    for i, metric in enumerate(available_metrics[:4]):  # Limit to 4 metrics
        ax = axes[i]
        values = data[metric]
        
        # Prepare data
        model_names = []
        metric_values = []
        bar_colors = []
        
        for model in models:
            if model in values:
                model_names.append(model.replace('_', '\n'))
                value = values[model] if values[model] is not None else 0
                metric_values.append(value)
                bar_colors.append(colors[model])
        
        # Create bars
        bars = ax.bar(model_names, metric_values, color=bar_colors, alpha=0.8, edgecolor='black', linewidth=1)
        
        # Customize
        info = metric_info.get(metric, {'name': metric, 'ylim': None})
        ax.set_title(info['name'], fontsize=12, fontweight='bold')
        ax.set_ylabel(info['name'], fontsize=10)
        
        if info['ylim']:
            ax.set_ylim(info['ylim'])
        
        # Add value labels
        for bar, value in zip(bars, metric_values):
            height = bar.get_height()
            if height > 0:
                ax.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                       f'{value:.3f}', ha='center', va='bottom', fontsize=9, fontweight='bold')
            else:
                ax.text(bar.get_x() + bar.get_width()/2., 0.01,
                       '0.000', ha='center', va='bottom', fontsize=9, fontweight='bold')
        
        ax.grid(True, alpha=0.3, axis='y')
    
    # Hide any unused subplots
    for i in range(len(available_metrics), 4):
        axes[i].set_visible(False)
    
    plt.suptitle('Routing Models Performance Summary', fontsize=16, fontweight='bold', y=0.98)
    plt.tight_layout()
    
    output_path = os.path.join(output_dir, 'performance_summary.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Saved: {output_path}")


def create_overall_scores_graph(report, output_dir):
    """Create a bar graph showing overall model scores."""
    model_scores = report.get('model_scores', {})
    if not model_scores:
        print("No overall scores found in report")
        return
    
    models = list(model_scores.keys())
    scores = list(model_scores.values())
    
    colors = {
        'max_flow': '#FF6B6B',
        'min_cost_max_flow': '#4ECDC4', 
        'multi_commodity_flow': '#45B7D1',
        'load_balanced_sp': '#96CEB4'
    }
    
    bar_colors = [colors.get(model, '#999999') for model in models]
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    bars = ax.bar([model.replace('_', '\n') for model in models], scores, 
                  color=bar_colors, alpha=0.8, edgecolor='black', linewidth=1)
    
    ax.set_title('Overall Model Performance Scores', fontsize=14, fontweight='bold', pad=20)
    ax.set_ylabel('Score (%)', fontsize=12)
    ax.set_xlabel('Routing Models', fontsize=12)
    ax.set_ylim(0, 100)
    
    # Add value labels on bars
    for bar, score in zip(bars, scores):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 1,
               f'{score:.1f}%', ha='center', va='bottom', fontsize=10, fontweight='bold')
    
    ax.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    output_path = os.path.join(output_dir, 'overall_scores.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Saved: {output_path}")


def main():
    """Main function to generate all comparison graphs."""
    try:
        # Load the latest comparison report
        report = load_latest_comparison_report()
        
        # Extract metrics data
        data, models = extract_metrics_data(report)
        
        # Create output directory if it doesn't exist
        output_dir = "ml/results"
        os.makedirs(output_dir, exist_ok=True)
        
        print(f"Generating comparison graphs...")
        print(f"Models: {models}")
        print(f"Available metrics: {list(data.keys())}")
        
        # Generate individual metric graphs
        create_individual_metric_graphs(data, models, output_dir)
        
        # Generate summary comparison graph
        create_summary_comparison_graph(data, models, output_dir)
        
        # Generate overall scores graph
        create_overall_scores_graph(report, output_dir)
        
        print(f"\nAll graphs saved to {output_dir}/")
        print("Generated files:")
        for metric in data.keys():
            print(f"  - {metric}_comparison.png")
        print("  - performance_summary.png")
        print("  - overall_scores.png")
        
    except Exception as e:
        print(f"Error generating graphs: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())