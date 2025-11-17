"""
Multi-Commodity Flow Model for handling multiple flows simultaneously.
Uses linear programming formulation for fair bandwidth allocation.
"""

import networkx as nx
from typing import Dict, List, Tuple, Any, Optional
import json
from collections import defaultdict


class MultiCommodityFlowModel:
    """Multi-commodity flow routing model for fair bandwidth allocation."""

    def __init__(self, topology: Dict[str, Any]):
        """
        Initialize with network topology.

        Args:
            topology: Dictionary containing nodes and links
        """
        self.topology = topology
        self.graph = self._build_graph()

    def _build_graph(self) -> nx.Graph:
        """Build undirected graph with capacity constraints."""
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

    def _solve_multi_commodity_flow_simple(self, commodities: List[Tuple[int, int, float]]) -> Dict[str, Any]:
        """
        Simplified multi-commodity flow solver using proportional allocation.

        Args:
            commodities: List of (source, destination, demand) tuples

        Returns:
            Dictionary with flow allocation results
        """
        # Initialize flow allocation
        flow_allocation = defaultdict(lambda: defaultdict(float))
        edge_utilization = defaultdict(float)

        # Calculate total demand per edge
        edge_demands = defaultdict(float)
        for src, dst, demand in commodities:
            try:
                # Find shortest path for this commodity
                path = nx.shortest_path(self.graph, src, dst, weight='delay')

                # Add demand to each edge in the path
                for i in range(len(path) - 1):
                    u, v = path[i], path[i + 1]
                    edge = tuple(sorted([u, v]))
                    edge_demands[edge] += demand

            except nx.NetworkXNoPath:
                continue

        # Allocate flows proportionally to edge capacities
        for edge, total_demand in edge_demands.items():
            u, v = edge
            capacity = self.graph[u][v]['capacity']

            if total_demand <= capacity:
                # All demands can be satisfied
                allocation_ratio = 1.0
            else:
                # Proportional allocation
                allocation_ratio = capacity / total_demand

            # Distribute allocated flow back to commodities
            for src, dst, demand in commodities:
                try:
                    path = nx.shortest_path(self.graph, src, dst, weight='delay')

                    if edge in [(path[i], path[i+1]) for i in range(len(path)-1)] or \
                       edge in [(path[i+1], path[i]) for i in range(len(path)-1)]:
                        allocated_flow = demand * allocation_ratio
                        flow_allocation[(src, dst)][edge] = allocated_flow
                        edge_utilization[edge] += allocated_flow

                except nx.NetworkXNoPath:
                    continue

        # Calculate metrics
        total_allocated_flow = sum(sum(flows.values()) for flows in flow_allocation.values())
        fairness_index = self._calculate_fairness_index(commodities, flow_allocation)

        return {
            "flow_allocation": dict(flow_allocation),
            "edge_utilization": dict(edge_utilization),
            "total_allocated_flow": total_allocated_flow,
            "fairness_index": fairness_index,
            "edge_demands": dict(edge_demands)
        }

    def _calculate_fairness_index(self, commodities: List[Tuple[int, int, float]],
                                 flow_allocation: Dict) -> float:
        """
        Calculate Jain's fairness index for flow allocation.

        Args:
            commodities: List of (source, destination, demand) tuples
            flow_allocation: Flow allocation results

        Returns:
            Fairness index (0-1, higher is better)
        """
        allocated_flows = []
        for src, dst, demand in commodities:
            total_allocated = sum(flow_allocation.get((src, dst), {}).values())
            allocated_flows.append(total_allocated)

        if not allocated_flows:
            return 0.0

        # Jain's fairness index
        numerator = sum(allocated_flows) ** 2
        denominator = len(allocated_flows) * sum(flow ** 2 for flow in allocated_flows)

        return numerator / denominator if denominator > 0 else 0.0

    def compute_multi_commodity_flow(self, commodities: List[Tuple[int, int, float]]) -> Dict[str, Any]:
        """
        Compute multi-commodity flow allocation.

        Args:
            commodities: List of (source, destination, demand) tuples

        Returns:
            Dictionary with flow allocation and metrics
        """
        return self._solve_multi_commodity_flow_simple(commodities)

    def get_next_hop_routes(self, flow_demands: List[Tuple[int, int]],
                           demands: Optional[List[float]] = None) -> List[Dict[str, Any]]:
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

        # Create commodities list
        commodities = [(src, dst, demand) for (src, dst), demand in zip(flow_demands, demands)]

        # Solve multi-commodity flow
        result = self.compute_multi_commodity_flow(commodities)
        flow_allocation = result["flow_allocation"]

        routes = []

        for src, dst, demand in commodities:
            if src == dst:
                continue

            allocation = flow_allocation.get((src, dst), {})

            if allocation:
                # Find first hop in allocation
                for edge, flow in allocation.items():
                    if flow > 0:
                        u, v = edge
                        next_hop = v if u == src else u if v == src else None

                        if next_hop is not None:
                            routes.append({
                                "src": src,
                                "dst": dst,
                                "next_hop": next_hop,
                                "allocated_flow": flow,
                                "demand": demand,
                                "allocation_ratio": flow / demand if demand > 0 else 0,
                                "model": "multi_commodity_flow"
                            })
                            break
            else:
                routes.append({
                    "src": src,
                    "dst": dst,
                    "next_hop": None,
                    "allocated_flow": 0,
                    "demand": demand,
                    "allocation_ratio": 0,
                    "model": "multi_commodity_flow",
                    "error": "No allocation possible"
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

        commodities = [(src, dst, demand) for (src, dst), demand in zip(flow_demands, demands)]
        result = self.compute_multi_commodity_flow(commodities)

        total_demand = sum(demands)
        total_allocated = result["total_allocated_flow"]
        successful_flows = len([f for f in result["flow_allocation"].values() if sum(f.values()) > 0])

        # Calculate edge utilization statistics
        utilizations = []
        for edge, utilization in result["edge_utilization"].items():
            u, v = edge
            capacity = self.graph[u][v]['capacity']
            utilizations.append(utilization / capacity if capacity > 0 else 0)

        avg_utilization = sum(utilizations) / len(utilizations) if utilizations else 0
        max_utilization = max(utilizations) if utilizations else 0

        return {
            "model_name": "multi_commodity_flow",
            "total_demand": total_demand,
            "total_allocated": total_allocated,
            "allocation_ratio": total_allocated / total_demand if total_demand > 0 else 0,
            "fairness_index": result["fairness_index"],
            "success_rate": successful_flows / len(commodities) if commodities else 0,
            "avg_edge_utilization": avg_utilization,
            "max_edge_utilization": max_utilization,
            "num_active_flows": successful_flows
        }
