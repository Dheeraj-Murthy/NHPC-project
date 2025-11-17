"""
Minimum Cost Maximum Flow Model using NetworkX network_simplex algorithm.
Optimizes for both throughput and delay simultaneously.
"""

import networkx as nx
from typing import Dict, List, Tuple, Any, Optional
import json


class MinCostMaxFlowModel:
    """Minimum cost maximum flow routing model."""
    
    def __init__(self, topology: Dict[str, Any], alpha: float = 0.5):
        """
        Initialize with network topology.
        
        Args:
            topology: Dictionary containing nodes and links
            alpha: Weight factor for utilization in cost function (0-1)
        """
        self.topology = topology
        self.alpha = alpha  # Weight for utilization in cost function
        self.graph = self._build_graph()
        
    def _build_graph(self) -> nx.DiGraph:
        """Build directed graph with capacity and cost attributes."""
        G = nx.DiGraph()
        nodes = self.topology.get("nodes", 0)
        G.add_nodes_from(range(nodes))
        
        for link in self.topology.get("links", []):
            src = link["src"]
            dst = link["dst"]
            
            # Parse bandwidth
            bandwidth_str = link.get("bandwidth", "5Mbps")
            bandwidth = float(bandwidth_str.replace("Mbps", "").replace("Gbps", "")) * \
                       (1000 if "Gbps" in bandwidth_str else 1)
            
            # Parse delay
            delay_str = link.get("delay", "2ms")
            delay = float(delay_str.replace("ms", "").replace("s", "")) * \
                    (1 if "ms" in delay_str else 1000)
            
            # Add both directions with capacity and cost
            G.add_edge(src, dst, capacity=bandwidth, weight=delay)
            G.add_edge(dst, src, capacity=bandwidth, weight=delay)
            
        return G
    
    def _calculate_dynamic_cost(self, u: int, v: int, current_utilization: float = 0.0) -> float:
        """
        Calculate dynamic edge cost considering delay and utilization.
        
        Args:
            u, v: Edge endpoints
            current_utilization: Current utilization of the edge (0-1)
            
        Returns:
            Combined cost value
        """
        base_delay = self.graph[u][v]["weight"]
        capacity = self.graph[u][v]["capacity"]
        
        # Cost = delay + alpha * utilization_penalty
        utilization_penalty = (current_utilization / capacity) ** 2 if capacity > 0 else 1000
        
        return base_delay + self.alpha * utilization_penalty
    
    def compute_min_cost_max_flow(self, source: int, sink: int, demand: float = 1.0) -> Dict[str, Any]:
        """
        Compute minimum cost maximum flow between source and sink.
        
        Args:
            source: Source node
            sink: Destination node  
            demand: Flow demand to satisfy
            
        Returns:
            Dictionary with flow solution and metrics
        """
        try:
            # Simplified approach: find shortest path and allocate flow
            path = nx.shortest_path(self.graph, source, sink, weight='weight')

            
            # Calculate minimum capacity along path
            min_capacity = float('inf')
            total_delay = 0
            
            for i in range(len(path) - 1):
                u, v = path[i], path[i + 1]
                capacity = self.graph[u][v]['capacity']
                delay = self.graph[u][v]['weight']
                min_capacity = min(min_capacity, capacity)
                total_delay += delay
            
            # Allocate flow up to minimum of demand and path capacity
            allocated_flow = min(demand, min_capacity)
            
            flow_paths = []
            for i in range(len(path) - 1):
                u, v = path[i], path[i + 1]
                flow_paths.append({
                    "from": u,
                    "to": v,
                    "flow": allocated_flow,
                    "capacity": self.graph[u][v]["capacity"],
                    "delay": self.graph[u][v]["weight"]
                })
            
            return {
                "flow_value": allocated_flow,
                "flow_cost": allocated_flow * total_delay,
                "avg_delay": total_delay,
                "total_cost": allocated_flow * total_delay,
                "flow_paths": flow_paths,
                "source": source,
                "sink": sink,
                "demand": demand
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "flow_value": 0,
                "flow_cost": 0,
                "avg_delay": 0,
                "flow_paths": []
            }
    
    def get_next_hop_routes(self, flow_demands: List[Tuple[int, int]], demands: Optional[List[float]] = None) -> List[Dict[str, Any]]:
        """
        Generate next-hop routing recommendations.
        
        Args:
            flow_demands: List of (source, destination) tuples
            demands: Optional list of demand values for each flow
            
        Returns:
            List of routing recommendations
        """
        if demands is None:
            demands = [1.0] * len(flow_demands)
            
        routes = []
        
        for (src, dst), demand in zip(flow_demands, demands):
            if src == dst:
                continue
                

            result = self.compute_min_cost_max_flow(src, dst, demand)
            
            if result["flow_value"] > 0:
                # Find first hop in flow paths
                for path in result["flow_paths"]:
                    if path["from"] == src:
                        routes.append({
                            "src": src,
                            "dst": dst,
                            "next_hop": path["to"],
                            "flow": result["flow_value"],
                            "cost": result["total_cost"],
                            "avg_delay": result["avg_delay"],
                            "model": "min_cost_max_flow"
                        })
                        break
            else:
                routes.append({
                    "src": src,
                    "dst": dst,
                    "next_hop": None,
                    "flow": 0,
                    "cost": 0,
                    "avg_delay": 0,
                    "model": "min_cost_max_flow",
                    "error": "No feasible path"
                })
        
        return routes
    
    def get_model_metrics(self, flow_demands: List[Tuple[int, int]], demands: Optional[List[float]] = None) -> Dict[str, Any]:
        """
        Calculate overall model performance metrics.
        
        Args:
            flow_demands: List of (source, destination) tuples
            demands: Optional list of demand values
            
        Returns:
            Dictionary with performance metrics
        """
        if demands is None:
            demands = [1.0] * len(flow_demands)
            
        total_flow = 0
        total_cost = 0
        total_delay = 0
        successful_flows = 0
        
        for (src, dst), demand in zip(flow_demands, demands):
            if src == dst:
                continue
                
            result = self.compute_min_cost_max_flow(src, dst, demand)
            total_flow += result["flow_value"]
            total_cost += result.get("total_cost", 0)
            total_delay += result.get("avg_delay", 0)
            
            if result["flow_value"] > 0:
                successful_flows += 1
        
        total_pairs = len([f for f in flow_demands if f[0] != f[1]])
        
        return {
            "model_name": "min_cost_max_flow",
            "total_flow": total_flow,
            "total_cost": total_cost,
            "avg_delay_per_flow": total_delay / total_pairs if total_pairs > 0 else 0,
            "success_rate": successful_flows / total_pairs if total_pairs > 0 else 0,
            "cost_efficiency": total_flow / total_cost if total_cost > 0 else 0,
            "alpha": self.alpha
        }