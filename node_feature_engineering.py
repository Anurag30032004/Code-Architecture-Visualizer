import networkx as nx
from typing import Dict, List
from collections import deque

NODE_TYPES = ["FILE", "CLASS", "FUNCTION", "MODULE"]

def one_hot_node_type(node_type: str) -> List[int]:
    return [1 if node_type == t else 0 for t in NODE_TYPES]

def estimate_loc(node_attrs: Dict) -> int:
    return node_attrs.get("loc", 0)

def fan_in(graph: nx.DiGraph, node) -> int:
    return graph.in_degree(node)

def fan_out(graph: nx.DiGraph, node) -> int:
    return graph.out_degree(node)

def compute_all_depths(graph: nx.DiGraph) -> Dict:
    """
    Compute depths for all nodes efficiently using multi-source BFS.
    Much faster than computing depth individually for each node.
    """
    depths = {}
    queue = deque()

    # Initialize FILE nodes with depth 0
    for node, data in graph.nodes(data=True):
        if data.get("type") == "FILE":
            depths[node] = 0
            queue.append(node)

    # Multi-source BFS traversal
    while queue:
        current = queue.popleft()
        current_depth = depths[current]

        # Process all successors
        for neighbor in graph.successors(current):
            if neighbor not in depths:
                depths[neighbor] = current_depth + 1
                queue.append(neighbor)

    # Assign depth 0 to any unvisited nodes (orphaned nodes)
    for node in graph.nodes():
        if node not in depths:
            depths[node] = 0

    return depths

def extract_node_features(graph: nx.DiGraph) -> Dict:
    """Extract features for all nodes efficiently"""
    print(f"Computing features for {graph.number_of_nodes()} nodes...")
    
    depths = compute_all_depths(graph)
    print(f"✅ Depths computed for all nodes")
    
    feature_map = {}
    
    for idx, (node, attrs) in enumerate(graph.nodes(data=True)):
        if idx % 5000 == 0:
            print(f"   Processing node {idx}/{graph.number_of_nodes()}...")
            
        node_type = attrs.get("type", "MODULE")

        features = []
        features.extend(one_hot_node_type(node_type))
        features.append(attrs.get("loc", 0))
        features.append(graph.in_degree(node))
        features.append(graph.out_degree(node))
        features.append(depths.get(node, 0))

        feature_map[node] = features

    print(f"✅ Features extracted successfully")
    return feature_map
