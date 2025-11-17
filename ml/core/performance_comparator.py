"""
Performance Comparator for analyzing and comparing results across different routing models.
Generates comparison tables, rankings, and visualizations.
"""

import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
import statistics


class PerformanceComparator:
    """Compares performance metrics across multiple routing models."""
    
    def __init__(self, results_dir: str):
        """
        Initialize with results directory.
        
        Args:
            results_dir: Directory containing model results
        """
        self.results_dir = results_dir
        self.comparison_metrics = [
            "success_rate",
            "total_flow", "total_allocated", "allocation_ratio",
            "avg_delay_per_flow", "total_cost", "cost_efficiency",
            "fairness_index", "avg_edge_utilization", "max_edge_utilization",
            "avg_hops_per_flow", "total_flows_routed"
        ]
        
    def load_results(self, results_file: str) -> Dict[str, Any]:
        """
        Load results from JSON file.
        
        Args:
            results_file: Path to results JSON file
            
        Returns:
            Loaded results dictionary
        """
        try:
            with open(results_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading results from {results_file}: {e}")
            return {}
    
    def extract_metrics(self, results: Dict[str, Any]) -> Dict[str, Dict[str, float]]:
        """
        Extract key metrics from model results.
        
        Args:
            results: Results dictionary from model manager
            
        Returns:
            Dictionary with model names as keys and metrics as values
        """
        metrics_dict = {}
        
        for model_name, model_results in results.items():
            if "error" in model_results:
                metrics_dict[model_name] = {"error": 1.0}
                continue
                
            metrics = model_results.get("metrics", {})
            extracted = {}
            
            # Extract standard metrics
            for metric in self.comparison_metrics:
                value = metrics.get(metric)
                if value is not None:
                    extracted[metric] = float(value)
                else:
                    extracted[metric] = 0.0
            
            # Add route count
            routes = model_results.get("routes", [])
            extracted["routes_generated"] = len(routes)
            
            # Add success count
            successful_routes = len([r for r in routes if r.get("next_hop") is not None])
            extracted["successful_routes"] = successful_routes
            
            metrics_dict[model_name] = extracted
        
        return metrics_dict
    
    def create_comparison_table(self, metrics_dict: Dict[str, Dict[str, float]]) -> Dict[str, Any]:
        """
        Create comparison table across all models.
        
        Args:
            metrics_dict: Dictionary of model metrics
            
        Returns:
            Comparison table with rankings
        """
        comparison = {}
        
        # For each metric, rank models
        for metric in self.comparison_metrics + ["routes_generated", "successful_routes"]:
            metric_values = {}
            
            for model_name, metrics in metrics_dict.items():
                if "error" not in metrics and metric in metrics:
                    metric_values[model_name] = metrics[metric]
            
            if metric_values:
                # Determine ranking direction (higher is better or lower is better)
                lower_is_better = metric in ["avg_delay_per_flow", "total_cost", "max_edge_utilization", "avg_hops_per_flow"]
                
                # Sort and rank
                sorted_models = sorted(metric_values.items(), 
                                    key=lambda x: x[1], 
                                    reverse=not lower_is_better)
                
                comparison[metric] = {
                    "rankings": [{"model": model, "value": value, "rank": i+1} 
                               for i, (model, value) in enumerate(sorted_models)],
                    "best_model": sorted_models[0][0] if sorted_models else None,
                    "best_value": sorted_models[0][1] if sorted_models else None,
                    "lower_is_better": lower_is_better
                }
        
        return comparison
    
    def calculate_overall_scores(self, comparison_table: Dict[str, Any]) -> Dict[str, float]:
        """
        Calculate overall performance scores for each model.
        Rewards actual routing performance, not "doing nothing".
        
        Args:
            comparison_table: Comparison table from create_comparison_table
            
        Returns:
            Dictionary with overall scores for each model
        """
        scores = {}
        
        # Collect all unique models
        all_models = set()
        for data in comparison_table.values():
            if data["rankings"]:
                for ranking in data["rankings"]:
                    all_models.add(ranking["model"])
        
        model_count = len(all_models)
        
        # Define metric weights with emphasis on actual routing performance
        metric_weights = {
            "total_flow": 15,           # Actually routing data
            "total_allocated": 15,       # Actually utilizing bandwidth  
            "allocation_ratio": 12,       # Meeting demand
            "total_flows_routed": 12,     # Actually routing flows
            "cost_efficiency": 10,       # Efficient resource use
            "fairness_index": 10,         # Fair distribution
            "avg_edge_utilization": 8,     # Network utilization
            "success_rate": 8,            # Reliability
            "avg_delay_per_flow": 5,       # Lower is better
            "avg_hops_per_flow": 3,       # Lower is better
            "max_edge_utilization": 2,       # Lower is better (avoid hotspots)
            "total_cost": 2,               # Lower is better
            "routes_generated": 1,          # Bonus for generating routes
            "successful_routes": 1           # Bonus for successful routes
        }
        
        # Calculate weighted scores
        for metric, data in comparison_table.items():
            if not data["rankings"] or metric not in metric_weights:
                continue
                
            weight = metric_weights[metric]
            lower_is_better = data["lower_is_better"]
            
            for ranking in data["rankings"]:
                model = ranking["model"]
                value = ranking["value"]
                
                # Penalize zero values for metrics that should be positive
                if metric in ["total_flow", "total_allocated", "allocation_ratio", 
                             "total_flows_routed", "cost_efficiency", "fairness_index",
                             "avg_edge_utilization"] and value == 0:
                    # Heavy penalty for not actually routing/utilizing
                    normalized_score = 0.1  # Minimal score
                else:
                    # Normalize values for this metric
                    values = [r["value"] for r in data["rankings"]]
                    min_val = min(values)
                    max_val = max(values)
                    
                    if max_val == min_val:
                        normalized_score = 0.5  # All equal
                    else:
                        if lower_is_better:
                            # Lower is better: invert the normalization
                            normalized_score = 1.0 - (value - min_val) / (max_val - min_val)
                        else:
                            # Higher is better
                            normalized_score = (value - min_val) / (max_val - min_val)
                
                if model not in scores:
                    scores[model] = 0
                scores[model] += normalized_score * weight
        
        # Normalize final scores to 0-100 scale
        if scores:
            max_score = max(scores.values())
            if max_score > 0:
                for model in scores:
                    scores[model] = 100 * scores[model] / max_score
        
        return scores
    
    def generate_summary_report(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate comprehensive summary report.
        
        Args:
            results: Model results dictionary
            
        Returns:
            Summary report with rankings and recommendations
        """
        # Extract metrics
        metrics_dict = self.extract_metrics(results)
        
        # Create comparison table
        comparison_table = self.create_comparison_table(metrics_dict)
        
        # Calculate overall scores
        overall_scores = self.calculate_overall_scores(comparison_table)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(comparison_table, overall_scores)
        
        # Create summary
        summary = {
            "timestamp": datetime.now().isoformat(),
            "models_evaluated": len(results),
            "total_flows": sum(len(r.get("routes", [])) for r in results.values()),
            "metrics_comparison": comparison_table,
            "overall_rankings": sorted(overall_scores.items(), key=lambda x: x[1], reverse=True),
            "model_scores": overall_scores,
            "recommendations": recommendations,
            "detailed_metrics": metrics_dict
        }
        
        return summary
    
    def _generate_recommendations(self, comparison_table: Dict[str, Any], 
                                overall_scores: Dict[str, float]) -> List[str]:
        """
        Generate recommendations based on performance analysis.
        
        Args:
            comparison_table: Metrics comparison table
            overall_scores: Overall performance scores
            
        Returns:
            List of recommendation strings
        """
        recommendations = []
        
        if not overall_scores:
            return ["No valid models to compare"]
        
        # Best overall model
        best_model = max(overall_scores.items(), key=lambda x: x[1])[0]
        recommendations.append(f"Best overall performer: {best_model}")
        
        # Specific metric recommendations
        metric_recommendations = {
            "total_flow": ("Highest actual throughput", "For maximum data transfer"),
            "total_allocated": ("Most bandwidth allocated", "For high utilization"),
            "allocation_ratio": ("Best demand fulfillment", "For meeting traffic requirements"),
            "total_flows_routed": ("Most flows actually routed", "For comprehensive routing"),
            "cost_efficiency": ("Most cost-efficient", "For resource-constrained environments"),
            "fairness_index": ("Highest fairness", "For fair bandwidth distribution"),
            "avg_edge_utilization": ("Best network utilization", "For efficient resource use"),
            "success_rate": ("Highest success rate", "For reliability-critical applications"),
            "avg_delay_per_flow": ("Lowest delay", "For latency-sensitive applications"),
            "max_edge_utilization": ("Best load balancing", "For avoiding congestion")
        }
        
        for metric, (title, use_case) in metric_recommendations.items():
            if metric in comparison_table and comparison_table[metric]["best_model"]:
                best = comparison_table[metric]["best_model"]
                recommendations.append(f"{title}: {best} ({use_case})")
        
        # Performance insights
        if len(overall_scores) > 1:
            scores_list = list(overall_scores.values())
            score_std = statistics.stdev(scores_list)
            if score_std < 10:
                recommendations.append("Models show similar performance - consider other factors like complexity")
            else:
                recommendations.append("Significant performance differences exist - model selection matters")
        
        return recommendations
    
    def save_comparison_report(self, summary: Dict[str, Any], filename: Optional[str] = None) -> str:
        """
        Save comparison report to file.
        
        Args:
            summary: Summary report dictionary
            filename: Optional filename (auto-generated if not provided)
            
        Returns:
            Path to saved file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"comparison_report_{timestamp}.json"
        
        filepath = os.path.join(self.results_dir, filename)
        
        try:
            with open(filepath, 'w') as f:
                json.dump(summary, f, indent=2, default=str)
            
            print(f"Comparison report saved to {filepath}")
            return filepath
            
        except Exception as e:
            print(f"Error saving comparison report: {e}")
            return ""
    
    def print_summary(self, summary: Dict[str, Any]):
        """
        Print formatted summary to console.
        
        Args:
            summary: Summary report dictionary
        """
        print("\n" + "="*60)
        print("ROUTING MODELS PERFORMANCE COMPARISON")
        print("="*60)
        
        print(f"\nModels Evaluated: {summary['models_evaluated']}")
        print(f"Total Routes Generated: {summary['total_flows']}")
        
        print("\nOVERALL RANKINGS:")
        print("-" * 30)
        for i, (model, score) in enumerate(summary['overall_rankings'], 1):
            print(f"{i}. {model}: {score:.1f}/100")
        
        print("\nRECOMMENDATIONS:")
        print("-" * 20)
        for rec in summary['recommendations']:
            print(f"• {rec}")
        
        print("\nKEY METRICS WINNERS:")
        print("-" * 25)
        metrics_comp = summary['metrics_comparison']
        for metric, data in metrics_comp.items():
            if data['best_model']:
                direction = "↓" if data['lower_is_better'] else "↑"
                print(f"{metric}: {data['best_model']} {direction} ({data['best_value']:.3f})")
        
        print("\n" + "="*60)