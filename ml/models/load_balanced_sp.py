"""
Load-Balanced Shortest Path Model.
Modified Dijkstra algorithm that considers current link utilization.
"""

import networkx as nx
from typing import Dict, List, Tuple, Any, Optional
import json
from collections import defaultdict


class LoadBalancedShortestPathModel:
    """Load-balanced shortest path routing model."""

    def __init__(self, topology: Dict[str, Any], beta: float = 0.3):
        """
        Initialize with network topology.

        Args:
            topology: Dictionary containing nodes and links
            beta: Weight factor for utilization in path cost (0-1)
        """
        self.topology = topology
        self.beta = beta  # Weight for utilization in path cost
        self.graph = self._build_graph()
        self.current_utilization = defaultdict(float)  # Track current link utilization

    def _build_graph(self) -> nx.Graph:
        """Build graph with capacity and delay attributes."""
        G = nx.Graph()
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

            G.add_edge(src, dst, capacity=bandwidth, delay=delay)

        return G

    def _calculate_edge_cost(self, u: int, v: int, flow_demand: float = 1.0) -> float:
        """
        Calculate edge cost considering delay and current utilization.

        Args:
            u, v: Edge endpoints
            flow_demand: Additional flow to consider

        Returns:
            Combined cost value
        """
        base_delay = self.graph[u][v]["delay"]
        capacity = self.graph[u][v]["capacity"]

        # Current utilization + new demand
        current_util = self.current_utilization.get(tuple(sorted([u, v])), 0.0)
        new_utilization = (current_util + flow_demand) / capacity

        # Cost = delay * (1 + beta * utilization_penalty)
        utilization_penalty = new_utilization ** 2  # Quadratic penalty for congestion

        return base_delay * (1 + self.beta * utilization_penalty)

    def find_load_balanced_path(self, source: int, sink: int, flow_demand: float = 1.0) -> Dict[str, Any]:
        """
        Find load-balanced shortest path using modified Dijkstra.

        Args:
            source: Source node
            sink: Destination node
            flow_demand: Flow demand to route

        Returns:
            Dictionary with path and cost information
        """
        try:
            # Create a temporary graph with dynamic edge weights
            temp_graph = nx.Graph()
            temp_graph.add_nodes_from(self.graph.nodes())

            for u, v, data in self.graph.edges(data=True):
                cost = self._calculate_edge_cost(u, v, flow_demand)
                temp_graph.add_edge(u, v, weight=cost, capacity=data['capacity'], delay=data['delay'])

            # Find shortest path
            path = nx.shortest_path(temp_graph, source, sink, weight='weight')
            path_length = nx.shortest_path_length(temp_graph, source, sink, weight='weight')

            # Calculate path metrics
            total_delay = 0
            max_utilization = 0
            edge_costs = []

            for i in range(len(path) - 1):
                u, v = path[i], path[i + 1]
                edge = tuple(sorted([u, v]))

                # Original delay
                total_delay += self.graph[u][v]['delay']

                # Current utilization
                current_util = self.current_utilization.get(edge, 0.0)
                capacity = self.graph[u][v]['capacity']
                utilization = (current_util + flow_demand) / capacity
                max_utilization = max(max_utilization, utilization)

                # Edge cost
                edge_cost = self._calculate_edge_cost(u, v, flow_demand)
                edge_costs.append(edge_cost)

            return {
                "path": path,
                "path_length": path_length,
                "total_delay": total_delay,
                "max_utilization": max_utilization,
                "edge_costs": edge_costs,
                "hop_count": len(path) - 1,
                "source": source,
                "sink": sink,
                "flow_demand": flow_demand
            }

        except nx.NetworkXNoPath:
            return {
                "error": "No path found",
                "path": [],
                "path_length": float('inf'),
                "total_delay": float('inf'),
                "max_utilization": 1.0
            }

    def update_utilization(self, path: List[int], flow_demand: float):
        """
        Update current utilization after routing a flow.

        Args:
            path: Path taken by the flow
            flow_demand: Amount of flow routed
        """
        for i in range(len(path) - 1):
            u, v = path[i], path[i + 1]
            edge = tuple(sorted([u, v]))
            self.current_utilization[edge] += flow_demand

    def reset_utilization(self):
        """Reset all utilization tracking."""
        self.current_utilization.clear()

    def get_next_hop_routes(self, flow_demands: List[Tuple[int, int]],
                           demands: Optional[List[float]] = None,
                           update_util: bool = True) -> List[Dict[str, Any]]:
        """
        Generate next-hop routing recommendations.

        Args:
            flow_demands: List of (source, destination) tuples
            demands: Optional list of demand values for each flow
            update_util: Whether to update utilization after each route

        Returns:
            List of routing recommendations
        """
        if demands is None:
            demands = [1.0] * len(flow_demands)

        if update_util:
            self.reset_utilization()

        routes = []

        # Sort flows by demand (larger flows first for better load balancing)
        sorted_flows = sorted(zip(flow_demands, demands), key=lambda x: x[1], reverse=True)

        for (src, dst), demand in sorted_flows:
            if src == dst:
                continue

            result = self.find_load_balanced_path(src, dst, demand)

            if "error" not in result and result["path"]:
                next_hop = result["path"][1] if len(result["path"]) > 1 else None

                routes.append({
                    "src": src,
                    "dst": dst,
                    "next_hop": next_hop,
                    "path": result["path"],
                    "path_cost": result["path_length"],
                    "total_delay": result["total_delay"],
                    "max_utilization": result["max_utilization"],
                    "hop_count": result["hop_count"],
                    "demand": demand,
                    "model": "load_balanced_sp"
                })

                if update_util:
                    self.update_utilization(result["path"], demand)
            else:
                routes.append({
                    "src": src,
                    "dst": dst,
                    "next_hop": None,
                    "path": [],
                    "path_cost": float('inf'),
                    "total_delay": float('inf'),
                    "max_utilization": 1.0,
                    "hop_count": 0,
                    "demand": demand,
                    "model": "load_balanced_sp",
                    "error": "No path available"
                })

        return routes

    def get_model_metrics(self, flow_demands: List[Tuple[int, int]],
                         demands: Optional[List[float]] = None) -> Dict[str, Any]:
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

        # Get routes with utilization tracking
        routes = self.get_next_hop_routes(flow_demands, demands, update_util=True)

        # Calculate metrics
        total_delay = sum(route.get("total_delay", 0) for route in routes)
        total_cost = sum(route.get("path_cost", 0) for route in routes)
        total_hops = sum(route.get("hop_count", 0) for route in routes)
        max_utilization = max(route.get("max_utilization", 0) for route in routes)

        successful_flows = len([r for r in routes if r.get("next_hop") is not None])
        total_flows = len(routes)

        # Calculate edge utilization statistics
        edge_utils = []
        for edge, util in self.current_utilization.items():
            u, v = edge
            capacity = self.graph[u][v]['capacity']
            edge_utils.append(util / capacity if capacity > 0 else 0)

        avg_utilization = sum(edge_utils) / len(edge_utils) if edge_utils else 0

        return {
            "model_name": "load_balanced_sp",
            "avg_delay_per_flow": total_delay / total_flows if total_flows > 0 else 0,
            "avg_cost_per_flow": total_cost / total_flows if total_flows > 0 else 0,
            "avg_hops_per_flow": total_hops / total_flows if total_flows > 0 else 0,
            "max_utilization": max_utilization,
            "avg_edge_utilization": avg_utilization,
            "success_rate": successful_flows / total_flows if total_flows > 0 else 0,
            "total_flows_routed": successful_flows,
            "beta": self.beta
        }
