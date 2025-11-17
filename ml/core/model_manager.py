"""
Model Manager for orchestrating all baseline routing models.
Handles data loading, model initialization, and result collection.
"""

import json
import csv
import os
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime

# Import model classes
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.max_flow import MaxFlowModel
from models.min_cost_max_flow import MinCostMaxFlowModel
from models.multi_commodity_flow import MultiCommodityFlowModel
from models.load_balanced_sp import LoadBalancedShortestPathModel


class ModelManager:
    """Orchestrates multiple routing models and manages their execution."""
    
    def __init__(self, project_path: str):
        """
        Initialize with project path.
        
        Args:
            project_path: Absolute path to the project directory
        """
        self.project_path = project_path
        self.topology_file = f"{project_path}/topology.json"
        self.metrics_file = f"{project_path}/metrics.csv"
        self.results_dir = f"{project_path}/ml/results"
        
        # Ensure results directory exists
        os.makedirs(self.results_dir, exist_ok=True)
        
        # Load data
        self.topology = self._load_topology()
        self.flow_demands, self.demands = self._load_flow_demands()
        
        # Initialize models
        self.models = self._initialize_models()
        
    def _load_topology(self) -> Dict[str, Any]:
        """Load network topology from JSON file."""
        try:
            with open(self.topology_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Warning: Topology file {self.topology_file} not found")
            return {"nodes": 0, "links": []}
        except json.JSONDecodeError as e:
            print(f"Error parsing topology file: {e}")
            return {"nodes": 0, "links": []}
    
    def _load_flow_demands(self) -> Tuple[List[Tuple[int, int]], List[float]]:
        """
        Load flow demands from metrics.csv.
        
        Returns:
            Tuple of (flow_demands, demands) where flow_demands is list of (src, dst)
            and demands is list of demand values
        """
        flow_demands = []
        demands = []
        
        try:
            with open(self.metrics_file, 'r') as f:
                reader = csv.DictReader(f)
                
                # Aggregate flows by source-destination pair
                flow_aggregation = {}
                
                for row in reader:
                    try:
                        src = int(row.get("src_idx", -1))
                        dst = int(row.get("dst_idx", -1))
                        
                        if src >= 0 and dst >= 0 and src != dst:
                            # Use throughput as demand indicator, fallback to 1.0
                            throughput = float(row.get("throughput_mbps", 1.0))
                            # Ensure minimum demand for routing attempts
                            demand = max(throughput, 0.1)  # Minimum 0.1 Mbps demand
                            key = (src, dst)
                            
                            if key in flow_aggregation:
                                flow_aggregation[key] += demand
                            else:
                                flow_aggregation[key] = demand
                                
                    except (ValueError, TypeError):
                        continue
                
                # Convert to lists
                for (src, dst), demand in flow_aggregation.items():
                    flow_demands.append((src, dst))
                    demands.append(demand)
                    
        except FileNotFoundError:
            print(f"Warning: Metrics file {self.metrics_file} not found")
        except Exception as e:
            print(f"Error reading metrics file: {e}")
        
        return flow_demands, demands
    
    def _initialize_models(self) -> Dict[str, Any]:
        """Initialize all baseline models."""
        models = {}
        
        try:
            models["max_flow"] = MaxFlowModel(self.topology)
            models["min_cost_max_flow"] = MinCostMaxFlowModel(self.topology, alpha=0.5)
            models["multi_commodity_flow"] = MultiCommodityFlowModel(self.topology)
            models["load_balanced_sp"] = LoadBalancedShortestPathModel(self.topology, beta=0.3)
            
            print(f"Initialized {len(models)} models: {list(models.keys())}")
            
        except Exception as e:
            print(f"Error initializing models: {e}")
            
        return models
    
    def run_single_model(self, model_name: str) -> Dict[str, Any]:
        """
        Run a single model and return results.
        
        Args:
            model_name: Name of the model to run
            
        Returns:
            Dictionary with model results
        """
        if model_name not in self.models:
            return {
                "error": f"Model '{model_name}' not available",
                "model_name": model_name,
                "routes": [],
                "metrics": {}
            }
        
        model = self.models[model_name]
        
        try:
            # Get routes from model
            if model_name == "max_flow":
                routes = model.get_next_hop_routes(self.flow_demands)
                metrics = model.get_model_metrics(self.flow_demands)
            elif model_name == "min_cost_max_flow":
                routes = model.get_next_hop_routes(self.flow_demands, self.demands)
                metrics = model.get_model_metrics(self.flow_demands, self.demands)
            elif model_name == "multi_commodity_flow":
                routes = model.get_next_hop_routes(self.flow_demands, self.demands)
                metrics = model.get_model_metrics(self.flow_demands, self.demands)
            elif model_name == "load_balanced_sp":
                routes = model.get_next_hop_routes(self.flow_demands, self.demands)
                metrics = model.get_model_metrics(self.flow_demands, self.demands)
            else:
                routes = []
                metrics = {}
            
            return {
                "model_name": model_name,
                "routes": routes,
                "metrics": metrics,
                "timestamp": datetime.now().isoformat(),
                "flow_demands": len(self.flow_demands),
                "topology_nodes": self.topology.get("nodes", 0)
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "model_name": model_name,
                "routes": [],
                "metrics": {}
            }
    
    def run_all_models(self) -> Dict[str, Dict[str, Any]]:
        """
        Run all available models and return results.
        
        Returns:
            Dictionary with model names as keys and results as values
        """
        results = {}
        
        print(f"Running {len(self.models)} models on {len(self.flow_demands)} flow demands...")
        
        for model_name in self.models:
            print(f"Running {model_name}...")
            result = self.run_single_model(model_name)
            results[model_name] = result
            
            if "error" in result:
                print(f"  Error: {result['error']}")
            else:
                metrics = result.get("metrics", {})
                print(f"  Completed: {len(result.get('routes', []))} routes generated")
                if metrics:
                    print(f"  Key metrics: {list(metrics.keys())[:3]}")
        
        return results
    
    def save_results(self, results: Dict[str, Dict[str, Any]], filename: Optional[str] = None) -> str:
        """
        Save results to JSON file.
        
        Args:
            results: Results dictionary from run_all_models or run_single_model
            filename: Optional filename (auto-generated if not provided)
            
        Returns:
            Path to saved file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"model_results_{timestamp}.json"
        
        filepath = os.path.join(self.results_dir, filename)
        
        try:
            with open(filepath, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            
            print(f"Results saved to {filepath}")
            return filepath
            
        except Exception as e:
            print(f"Error saving results: {e}")
            return ""
    
    def get_available_models(self) -> List[str]:
        """Get list of available model names."""
        return list(self.models.keys())
    
    def get_data_summary(self) -> Dict[str, Any]:
        """Get summary of loaded data."""
        return {
            "topology_nodes": self.topology.get("nodes", 0),
            "topology_links": len(self.topology.get("links", [])),
            "flow_demands": len(self.flow_demands),
            "total_demand": sum(self.demands) if self.demands else 0,
            "available_models": self.get_available_models()
        }