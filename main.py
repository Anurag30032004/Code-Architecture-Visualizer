"""
main.py — Contains the notebook code for Section 6.5 Component Inference
Copy the cell below into your main.ipynb notebook.
"""

# ============================================================
# CELL 9 (Markdown): ### Component Inference
# ============================================================

# ============================================================
# CELL 10 (Code): Component Inference — COPY THIS INTO NOTEBOOK
# ============================================================
import importlib
import sys

# Reload module to get latest version
if 'component_inference' in sys.modules:
    del sys.modules['component_inference']

from component_inference import infer_components_kmeans, evaluate_clusters, assign_components_to_graph

print("="*60)
print("Section 6.5: Component Inference")
print("="*60)

# Run K-Means Clustering on the embeddings
# (Assuming 'embeddings', 'graph', and 'node_mapping' exist from Section 6.4)
n_components = 15  # Choose number of expected architectural components
labels = infer_components_kmeans(embeddings, n_clusters=n_components)

# Evaluate the clusters
score = evaluate_clusters(embeddings, labels)

# Assign the component IDs back to the original graph attributes
assign_components_to_graph(graph, labels, node_mapping)

# Print distribution of nodes across components
from collections import Counter
counts = Counter(labels.values())

print(f"\nComponent Distribution (Top 10):")
for comp_id, count in counts.most_common(10):
    print(f"  Component {comp_id:2d}: {count:5d} nodes")

print(f"\n✅ Section 6.5 complete!")

# ============================================================
# CELL 11 (Markdown): ### Component Graph Construction & Visualization
# ============================================================

# ============================================================
# CELL 12 (Code): Component Graph Construction — COPY THIS INTO NOTEBOOK
# ============================================================
import importlib
import sys
import os

# Reload module to get latest version
if 'component_graph' in sys.modules:
    del sys.modules['component_graph']

from component_graph import build_component_graph, visualize_architecture, visualize_tree_diagram

print("="*60)
print("Section 6.6: Component Graph Construction")
print("="*60)

# Build high-level component graph
comp_graph = build_component_graph(graph)

# Visualize the standard graph
html_path_standard = visualize_architecture(comp_graph, "architecture.html")

# Visualize the hierarchical tree/block diagram
html_path_tree = visualize_tree_diagram(comp_graph, "architecture_tree.html")

# Provide IPython display links
from IPython.display import IFrame, display, HTML

display(HTML(f"<h3>Standard Architecture Diagram</h3>"))
display(HTML(f"<a href='architecture.html' target='_blank'>Open in new tab</a>"))
display(IFrame(src='./architecture.html', width='100%', height='500px'))

display(HTML(f"<h3>Hierarchical Tree (Block) Diagram</h3>"))
display(HTML(f"<a href='architecture_tree.html' target='_blank'>Open in new tab</a>"))
display(IFrame(src='./architecture_tree.html', width='100%', height='500px'))

print(f"\n✅ Section 6.6 complete!")

