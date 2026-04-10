"""
Section 6.6: Component Graph Construction
-----------------------------------------
Transforms a low-level code graph into a high-level component architecture graph.
Visualizes the final architecture as an interactive HTML diagram using PyVis.

Usage:
    from component_graph import build_component_graph, visualize_architecture
    
    comp_graph = build_component_graph(graph)
    visualize_architecture(comp_graph, "architecture.html")
"""

import networkx as nx
from typing import Dict, Any
from pyvis.network import Network
import os
import math

def build_component_graph(original_graph: nx.DiGraph) -> nx.DiGraph:
    """
    Collapse the original low-level node graph into a high-level 
    component graph based on inferred `component_id`s.
    
    Args:
        original_graph: The original Code Property Graph equipped with 'component_id'
        
    Returns:
        A new NetworkX DiGraph where nodes are components and edges are weighted dependencies.
    """
    print("Building high-level Component Graph...")
    comp_graph = nx.DiGraph()
    
    # Track node counts for each component to set their size in visualization
    comp_sizes = {}
    
    for node, data in original_graph.nodes(data=True):
        comp_id = data.get('component_id')
        if comp_id is None or comp_id == -1:
            continue  # Skip unassigned or noise nodes
            
        comp_name = f"Component_{comp_id}"
        comp_sizes[comp_name] = comp_sizes.get(comp_name, 0) + 1
        
        if not comp_graph.has_node(comp_name):
            comp_graph.add_node(comp_name, size=0, title=f"Architecture Module {comp_id}")
            
    # Update sizes in the graph
    for comp_name, size in comp_sizes.items():
        comp_graph.nodes[comp_name]['size'] = size
        
    # Aggregate edges
    edge_weights = {}
    
    for u, v, data in original_graph.edges(data=True):
        u_comp = original_graph.nodes[u].get('component_id')
        v_comp = original_graph.nodes[v].get('component_id')
        
        # Only aggregate if both nodes belong to a valid component AND it's not a self-loop
        if (u_comp is not None and u_comp != -1 and 
            v_comp is not None and v_comp != -1 and 
            u_comp != v_comp):
            
            u_name = f"Component_{u_comp}"
            v_name = f"Component_{v_comp}"
            
            edge_pair = (u_name, v_name)
            edge_weights[edge_pair] = edge_weights.get(edge_pair, 0) + 1

    # Add edges to the component graph
    for (u, v), weight in edge_weights.items():
        comp_graph.add_edge(u, v, value=weight, title=f"Dependencies: {weight}")
        
    print(f"✅ Collapsed {original_graph.number_of_nodes()} low-level nodes into "
          f"{comp_graph.number_of_nodes()} architectural components.")
    print(f"✅ Found {comp_graph.number_of_edges()} interactions between components.")
    
    return comp_graph

def visualize_architecture(comp_graph: nx.DiGraph, output_file: str = "architecture.html") -> str:
    """
    Generate an interactive HTML diagram of the component graph using PyVis.
    
    Args:
        comp_graph: The high-level component graph.
        output_file: Path to save the interactive HTML file.
        
    Returns:
        Absolute path to the generated HTML file.
    """
    print(f"Visualizing architecture components...")
    
    # Initialize PyVis network
    net = Network(height="750px", width="100%", directed=True, bgcolor="#222222", font_color="white")
    
    # Enable Physics for force-directed layout
    net.barnes_hut(gravity=-8000, central_gravity=0.3, spring_length=200, spring_strength=0.05, damping=0.09)
    
    # Import NetworkX graph data
    net.from_nx(comp_graph)
    
    # Customize node sizes based on their weight relative to max size
    if comp_graph.number_of_nodes() > 0:
        max_size = max([data.get('size', 1) for _, data in comp_graph.nodes(data=True)])
        
        for node in net.nodes:
            # Scale sizes for better visibility: minimum 15, maximum 50
            original_size = next((data.get('size', 1) for n, data in comp_graph.nodes(data=True) if n == node['id']), 1)
            scaled_size = max(15, min(50, int((original_size / max_size) * 50)))
            
            node['size'] = scaled_size
            node['color'] = "#4CAF50" # Green nodes for modules
            node['borderWidth'] = 2
            
        # Customize edge thickness based on weight
        max_weight = max([data.get('value', 1) for _, _, data in comp_graph.edges(data=True)]) if comp_graph.number_of_edges() > 0 else 1
        
        for edge in net.edges:
            original_weight = edge.get('value', 1)
            ratio = original_weight / max_weight
            
            # Scale edge width: min 1, max 10
            edge['width'] = max(1, min(10, int(ratio * 10)))
            
            # Color edge based on interaction strength: >50% Red, >10% Orange, else Gray
            if ratio > 0.5:
                edge_color = "#ff4d4d"  # Red for high interaction
            elif ratio > 0.1:
                edge_color = "#ffbd45"  # Orange for medium
            else:
                edge_color = "#888888"  # Gray for low
                
            edge['color'] = edge_color
            edge['arrows'] = 'to'

    # Save to file
    # Ensure it's an absolute path within current working directory if not specified
    output_path = os.path.abspath(output_file)
    net.save_graph(output_path)
    
    print(f"✅ Interactive architecture diagram saved to: {output_path}")
    return output_path

def visualize_tree_diagram(comp_graph: nx.DiGraph, output_file: str = "architecture_tree.html") -> str:
    """
    Generate a hierarchical tree (block) interactive diagram using PyVis.
    """
    print(f"Visualizing hierarchical tree diagram...")
    
    net = Network(height="750px", width="100%", directed=True, bgcolor="#222222", font_color="white")
    
    # Enable Hierarchical layout
    net.set_options("""
    var options = {
      "layout": {
        "hierarchical": {
          "enabled": true,
          "direction": "UD",
          "sortMethod": "directed",
          "nodeSpacing": 250,
          "levelSeparation": 250,
          "parentCentralization": true
        }
      },
      "physics": {
        "enabled": false
      }
    }
    """)
    
    net.from_nx(comp_graph)
    
    if comp_graph.number_of_nodes() > 0:
        max_size = max([data.get('size', 1) for _, data in comp_graph.nodes(data=True)])
        
        for node in net.nodes:
            original_size = next((data.get('size', 1) for n, data in comp_graph.nodes(data=True) if n == node['id']), 1)
            scaled_size = max(15, min(40, int((original_size / max_size) * 40)))
            
            node['size'] = scaled_size
            node['color'] = "#00bcd4" # Cyan for tree nodes
            node['shape'] = 'box'     # Box shape for block diagram
            node['borderWidth'] = 2
            
            # Add detail: Node label showing size
            node['label'] = f"{node['id']}\n({original_size} items)"
            node['font'] = {'size': 20, 'color': 'black'}
            node['color'] = {
                'background': '#00bcd4',
                'border': '#008ba3',
                'highlight': {'background': '#4dd0e1', 'border': '#008ba3'}
            }
            
        max_weight = max([data.get('value', 1) for _, _, data in comp_graph.edges(data=True)]) if comp_graph.number_of_edges() > 0 else 1
        
        for edge in net.edges:
            original_weight = edge.get('value', 1)
            ratio = original_weight / max_weight
            edge['width'] = max(1, min(5, int(ratio * 5)))
            
            # Add detail: Edge label showing dependency count
            edge['label'] = f" {original_weight} "
            edge['font'] = {'size': 14, 'align': 'horizontal', 'color': '#ffffff', 'background': '#333333'}
            
            if ratio > 0.5:
                edge['color'] = "#ff4d4d"
            elif ratio > 0.1:
                edge['color'] = "#ffbd45"
            else:
                edge['color'] = "#888888"
                
            edge['arrows'] = 'to'

    output_path = os.path.abspath(output_file)
    net.save_graph(output_path)
    
    print(f"✅ Hierarchical tree diagram saved to: {output_path}")
    return output_path
