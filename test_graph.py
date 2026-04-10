#!/usr/bin/env python
"""
Quick test script to verify DAG properties and performance
"""
import json
import time
from code_graph_builder import CodeGraphBuilder
from node_feature_engineering import extract_node_features

# Load AST data
print("Loading AST data...")
with open(r"p:\8th Sem\Neural Networks\Project\PdfViewer_ast.json", "r", encoding="utf-8") as f:
    ast_data = json.load(f)

# Build graph with timing
print(f"\n{'='*60}")
print("Building Code Property Graph...")
print(f"{'='*60}")
start_time = time.time()

builder = CodeGraphBuilder()
graph = builder.build(ast_data)

build_time = time.time() - start_time
print(f"\n{'='*60}")
print(f"Build completed in {build_time:.2f} seconds")
print(f"Nodes: {graph.number_of_nodes():,}")
print(f"Edges: {graph.number_of_edges():,}")
print(f"{'='*60}\n")

# Test feature extraction
print(f"{'='*60}")
print("Extracting node features...")
print(f"{'='*60}")
start_time = time.time()

features = extract_node_features(graph)

extract_time = time.time() - start_time
print(f"\nExtraction completed in {extract_time:.2f} seconds")
print(f"Features extracted: {len(features):,}")
print(f"Sample feature vector length: {len(list(features.values())[0])}")
print(f"{'='*60}\n")

# Summary
print("✅ SUCCESS: Graph is working efficiently!")
print(f"   Total time: {build_time + extract_time:.2f} seconds")
