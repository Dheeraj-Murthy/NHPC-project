"""
Maximum Flow Model using Ford-Fulkerson algorithm.
Calculates maximum possible throughput between source-destination pairs.
"""

import networkx as nx
from typing import Dict, List, Tuple, Any
import json


class MaxFlowModel:
    """Maximum flow routing model using Ford-Fulkerson algorithm."""
    
    def __init__(self, topology: Dict[str, Any]):
        """
        Initialize with network topology.
        
        Args:
            topology: Dictionary containing nodes and links with bandwidth capacities
        """
        self.topology = topology
        self.graph = self._build_directed_graph()
        
    def _build_directed_graph(self) -> nx.DiGraph:
        """Build directed graph from topology with capacity constraints."""
        G = nx.DiGraph()
        nodes = self.topology.get("nodes", 0)
        G.add_nodes_from(range(nodes))
        
        for link in self.topology.get("links", []):
            src = link["src"]
            dst = link["dst"]
            # Parse bandwidth (e.g., "5Mbps" -> 5.0)
            bandwidth_str = link.get("bandwidth", "5Mbps")
            if "Gbps" in bandwidth_str:
                bandwidth = float(bandwidth_str.replace("Gbps", "").replace("Mbps", "")) * 1000
            else:
                bandwidth = float(bandwidth_str.replace("Mbps", "").replace("Gbps", ""))
            
            # Add both directions for undirected links
            G.add_edge(src, dst, capacity=bandwidth)
            G.add_edge(dst, src, capacity=bandwidth)
            
        return G
    
    def compute_max_flow(self, source: int, sink: int) -> Dict[str, Any]:
        """
        Compute maximum flow between source and sink.
        
        Args:
            source: Source node index
            sink: Sink node index
            
        Returns:
            Dictionary with max flow value and flow distribution
        """
        try:
            # Use networkx's maximum_flow algorithm
            flow_value, flow_dict = nx.maximum_flow(self.graph, source, sink, capacity='capacity')
            

            
            # Extract flow paths and bottlenecks
            flow_paths = []
            for u in flow_dict:
                for v, flow in flow_dict[u].items():
                    if flow > 0:
                        flow_paths.append({
                            "from": u,
                            "to": v,
                            "flow": flow,
                            "capacity": self.graph[u][v]["capacity"]
                        })
            
            # Identify bottleneck links (edges with high utilization)
            bottlenecks = []
            for u, v, data in self.graph.edges(data=True):
                capacity = data["capacity"]
                used_flow = flow_dict.get(u, {}).get(v, 0)
                utilization = used_flow / capacity if capacity > 0 else 0
                if utilization > 0.8:  # High utilization threshold
                    bottlenecks.append({
                        "link": f"{u}->{v}",
                        "utilization": utilization,
                        "capacity": capacity,
                        "used": used_flow
                    })
            
            return {
                "max_flow_value": flow_value,
                "flow_paths": flow_paths,
                "bottlenecks": bottlenecks,
                "source": source,
                "sink": sink
            }
            
            # Extract flow paths and bottlenecks
            flow_paths = []
            for u in flow_dict:
                for v, flow in flow_dict[u].items():
                    if flow > 0:
                        flow_paths.append({
                            "from": u,
                            "to": v,
                            "flow": flow,
                            "capacity": self.graph[u][v]["capacity"]
                        })
            
            # Identify bottleneck links (edges with high utilization)
            bottlenecks = []
            for u, v, data in self.graph.edges(data=True):
                capacity = data["capacity"]
                used_flow = flow_dict.get(u, {}).get(v, 0)
                utilization = used_flow / capacity if capacity > 0 else 0
                if utilization > 0.8:  # High utilization threshold
                    bottlenecks.append({
                        "link": f"{u}->{v}",
                        "utilization": utilization,
                        "capacity": capacity,
                        "used": used_flow
                    })
            
            return {
                "max_flow_value": flow_value,
                "flow_paths": flow_paths,
                "bottlenecks": bottlenecks,
                "source": source,
                "sink": sink
            }
            
        except nx.NetworkXError as e:
            return {
                "error": str(e),
                "max_flow_value": 0,
                "flow_paths": [],
                "bottlenecks": []
            }
    
    def get_next_hop_routes(self, flow_demands: List[Tuple[int, int]]) -> List[Dict[str, Any]]:
        """
        Generate next-hop routing recommendations based on max flow analysis.
        
        Args:
            flow_demands: List of (source, destination) tuples
            
        Returns:
            List of routing recommendations
        """
        routes = []
        
        for src, dst in flow_demands:
            if src == dst:
                continue
                
            # Compute max flow for this pair
            result = self.compute_max_flow(src, dst)
            
            if result["max_flow_value"] > 0:
                # Find first hop in flow paths
                for path in result["flow_paths"]:
                    if path["from"] == src:
                        routes.append({
                            "src": src,
                            "dst": dst,
                            "next_hop": path["to"],
                            "max_flow": result["max_flow_value"],
                            "model": "max_flow"
                        })
                        break
            else:
                # No path found
                routes.append({
                    "src": src,
                    "dst": dst,
                    "next_hop": None,
                    "max_flow": 0,
                    "model": "max_flow",
                    "error": "No path available"
                })
        
        return routes
    
    def get_model_metrics(self, flow_demands: List[Tuple[int, int]]) -> Dict[str, Any]:
        """
        Calculate overall model performance metrics.
        
        Args:
            flow_demands: List of (source, destination) tuples
            
        Returns:
            Dictionary with performance metrics
        """
        total_max_flow = 0
        successful_flows = 0
        all_bottlenecks = []
        
        for src, dst in flow_demands:
            if src == dst:
                continue
                
            result = self.compute_max_flow(src, dst)
            total_max_flow += result["max_flow_value"]
            
            if result["max_flow_value"] > 0:
                successful_flows += 1
                
            all_bottlenecks.extend(result.get("bottlenecks", []))
        
        total_flows = len([f for f in flow_demands if f[0] != f[1]])
        
        return {
            "model_name": "max_flow",
            "total_max_flow": total_max_flow,
            "success_rate": successful_flows / total_flows if total_flows > 0 else 0,
            "num_bottlenecks": len(all_bottlenecks),
            "bottleneck_links": all_bottlenecks[:5],  # Top 5 bottlenecks
            "avg_flow_per_pair": total_max_flow / total_flows if total_flows > 0 else 0
        }