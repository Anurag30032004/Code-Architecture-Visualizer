"""
Section 6.5: Component Inference
--------------------------------
Groups low-level code entities into higher-level logical architectural
components using K-Means clustering or DBSCAN on node embeddings.

Usage:
    from component_inference import infer_components_kmeans, evaluate_clusters
    
    # Run clustering
    labels = infer_components_kmeans(embeddings, n_clusters=20)
    
    # Evaluate with Silhouette Score
    score = evaluate_clusters(embeddings, labels)
"""

import numpy as np
from sklearn.cluster import KMeans, DBSCAN
from sklearn.metrics import silhouette_score
from typing import Dict, List, Set, Tuple
import networkx as nx

def _get_embedding_matrix(embeddings: Dict[str, List[float]]) -> Tuple[np.ndarray, List[str]]:
    """Convert embedding dict to numpy matrix and node list."""
    nodes = list(embeddings.keys())
    matrix = np.array([embeddings[node] for node in nodes])
    return matrix, nodes

def infer_components_kmeans(embeddings: Dict[str, List[float]], 
                            n_clusters: int = 10) -> Dict[str, int]:
    """
    Cluster node embeddings using K-Means.
    
    Args:
        embeddings: Dict mapping node names to their embedding vectors
        n_clusters: Number of components to find
        
    Returns:
        Dict mapping node names to their cluster component ID
    """
    print(f"Running K-Means clustering (K={n_clusters})...")
    matrix, nodes = _get_embedding_matrix(embeddings)
    
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init='auto')
    labels = kmeans.fit_predict(matrix)
    
    component_labels = {node: int(label) for node, label in zip(nodes, labels)}
    print(f"✅ Grouped {len(nodes)} nodes into {n_clusters} components")
    
    return component_labels

def infer_components_dbscan(embeddings: Dict[str, List[float]], 
                            eps: float = 0.5, 
                            min_samples: int = 5) -> Dict[str, int]:
    """
    Cluster node embeddings using DBSCAN (density-based).
    Good for finding components of arbitrary shape/size without specifying K.
    
    Args:
        embeddings: Dict mapping node names to embedding vectors
        eps: Maximum distance between two samples for one to be considered as in the neighborhood of the other
        min_samples: The number of samples in a neighborhood for a point to be considered as a core point
        
    Returns:
        Dict mapping node names to their cluster component ID (-1 is noise)
    """
    print(f"Running DBSCAN clustering (eps={eps}, min_samples={min_samples})...")
    matrix, nodes = _get_embedding_matrix(embeddings)
    
    dbscan = DBSCAN(eps=eps, min_samples=min_samples)
    labels = dbscan.fit_predict(matrix)
    
    # Print noise statistics if any
    noise_count = sum(1 for l in labels if l == -1)
    if noise_count > 0:
        print(f"  Note: Found {noise_count} noise nodes (-1)")
        
    n_components = len(set(labels)) - (1 if -1 in labels else 0)
    
    component_labels = {node: int(label) for node, label in zip(nodes, labels)}
    print(f"✅ Found {n_components} components")
    
    return component_labels

def evaluate_clusters(embeddings: Dict[str, List[float]], 
                      component_labels: Dict[str, int]) -> float:
    """
    Evaluate the quality of the clustering using Silhouette Score.
    
    Args:
        embeddings: Dict mapping node names to embedding vectors
        component_labels: Dict mapping node names to component IDs
        
    Returns:
        Silhouette score (float between -1 and 1, higher is better)
    """
    # Filter out noise points (-1) if using DBSCAN
    nodes = [n for n, l in component_labels.items() if l != -1]
    
    if len(nodes) < 2 or len(set(component_labels[n] for n in nodes)) < 2:
        print("  Not enough valid clusters for evaluation")
        return -1.0
        
    matrix = np.array([embeddings[n] for n in nodes])
    labels = np.array([component_labels[n] for n in nodes])
    
    score = silhouette_score(matrix, labels)
    print(f"✅ Silhouette Score: {score:.4f} (range: -1 to 1, >0.5 is good)")
    
    return float(score)

def assign_components_to_graph(graph: nx.DiGraph, 
                               component_labels: Dict[str, int], 
                               node_mapping: dict = None) -> None:
    """
    Update the NetworkX graph with the inferred component labels.
    Adds a 'component_id' attribute to each clustered node.
    """
    assigned = 0
    for node, label in component_labels.items():
        if graph.has_node(node):
            graph.nodes[node]['component_id'] = label
            assigned += 1
            
    print(f"✅ Assigned component IDs to {assigned}/{graph.number_of_nodes()} graph nodes")
