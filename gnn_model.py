"""
Section 6.4: Graph Neural Network (GraphSAGE)
----------------------------------------------
Learns latent architectural representations from the Code Property Graph.
Uses a 2-layer GraphSAGE model trained via unsupervised link prediction.

Usage:
    from gnn_model import prepare_pyg_data, train_gnn, get_embeddings

    data, node_mapping = prepare_pyg_data(graph, node_features)
    model, losses = train_gnn(data, epochs=100, lr=0.01)
    embeddings = get_embeddings(model, data, node_mapping)
"""

import torch
import torch.nn.functional as F
from torch_geometric.nn import SAGEConv
from torch_geometric.data import Data
import networkx as nx
import numpy as np
from typing import Dict, List, Tuple


# ======================== MODEL ========================

class CodeGraphSAGE(torch.nn.Module):
    """
    2-layer GraphSAGE model for learning node embeddings
    from the Code Property Graph.

    Architecture:
        Input (8) → SAGEConv(64) → ReLU → Dropout → SAGEConv(32) → Output
    """

    def __init__(self, in_channels: int, hidden_channels: int = 64,
                 out_channels: int = 32, dropout: float = 0.3):
        super().__init__()
        self.conv1 = SAGEConv(in_channels, hidden_channels)
        self.conv2 = SAGEConv(hidden_channels, out_channels)
        self.dropout = dropout

    def forward(self, x, edge_index):
        """Forward pass — returns node embeddings."""
        x = self.conv1(x, edge_index)
        x = F.relu(x)
        x = F.dropout(x, p=self.dropout, training=self.training)
        x = self.conv2(x, edge_index)
        return x

    def embed(self, x, edge_index):
        """Get L2-normalized embeddings for downstream tasks."""
        self.eval()
        with torch.no_grad():
            z = self.forward(x, edge_index)
            return F.normalize(z, p=2, dim=1)


# =================== DATA PREPARATION ===================

def prepare_pyg_data(graph: nx.DiGraph,
                     node_features: Dict[str, List]) -> Tuple[Data, Dict]:
    """
    Convert NetworkX graph + feature dict → PyTorch Geometric Data object.

    Args:
        graph: NetworkX DiGraph from CodeGraphBuilder
        node_features: Dict mapping node names to feature vectors (from Section 6.3)

    Returns:
        data: PyG Data object with x (features) and edge_index
        node_mapping: Dict mapping node names to integer indices
    """
    # Build node-to-index mapping (only for nodes that have features)
    nodes_with_features = [n for n in graph.nodes() if n in node_features]
    node_mapping = {node: idx for idx, node in enumerate(nodes_with_features)}

    print(f"Preparing PyG data...")
    print(f"  Nodes with features: {len(node_mapping)}")

    # Build feature matrix
    feature_dim = len(next(iter(node_features.values())))
    x = torch.zeros((len(node_mapping), feature_dim), dtype=torch.float)

    for node, idx in node_mapping.items():
        x[idx] = torch.tensor(node_features[node], dtype=torch.float)

    # Build edge index (only edges between nodes that exist in our mapping)
    src_list, dst_list = [], []
    edge_type_list = []
    for u, v, edata in graph.edges(data=True):
        if u in node_mapping and v in node_mapping:
            src_list.append(node_mapping[u])
            dst_list.append(node_mapping[v])
            edge_type_list.append(edata.get("type", "UNKNOWN"))

    edge_index = torch.tensor([src_list, dst_list], dtype=torch.long)

    # Make undirected by adding reverse edges (GraphSAGE works best undirected)
    edge_index_rev = torch.stack([edge_index[1], edge_index[0]], dim=0)
    edge_index_full = torch.cat([edge_index, edge_index_rev], dim=1)

    # Remove duplicate edges
    edge_index_full = torch.unique(edge_index_full, dim=1)

    data = Data(x=x, edge_index=edge_index_full)

    print(f"  Edges (undirected): {data.edge_index.size(1)}")
    print(f"  Feature dimension: {feature_dim}")
    print(f"✅ PyG Data object created")

    return data, node_mapping


# =================== TRAINING ===================

def _negative_sampling(edge_index: torch.Tensor,
                       num_nodes: int,
                       num_neg: int) -> torch.Tensor:
    """Generate random negative edges (pairs of nodes without an edge)."""
    neg_src = torch.randint(0, num_nodes, (num_neg,))
    neg_dst = torch.randint(0, num_nodes, (num_neg,))
    return torch.stack([neg_src, neg_dst], dim=0)


def train_gnn(data: Data,
              epochs: int = 100,
              lr: float = 0.01,
              hidden_channels: int = 64,
              out_channels: int = 32) -> Tuple:
    """
    Train the GraphSAGE model using unsupervised link prediction.

    The model learns to predict whether an edge exists between two nodes.
    Positive examples = actual edges; Negative examples = random node pairs.

    Args:
        data: PyG Data object from prepare_pyg_data()
        epochs: Number of training epochs
        lr: Learning rate
        hidden_channels: Hidden layer size
        out_channels: Embedding dimension

    Returns:
        model: Trained CodeGraphSAGE model
        losses: List of training losses per epoch
    """
    in_channels = data.num_node_features

    model = CodeGraphSAGE(
        in_channels=in_channels,
        hidden_channels=hidden_channels,
        out_channels=out_channels
    )
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)

    # Use all edges for training (unsupervised setting)
    pos_edge_index = data.edge_index
    num_pos = pos_edge_index.size(1)

    print(f"\nTraining GraphSAGE model...")
    print(f"  Architecture: {in_channels} → {hidden_channels} → {out_channels}")
    print(f"  Positive edges: {num_pos}")
    print(f"  Epochs: {epochs}, LR: {lr}")
    print()

    losses = []
    model.train()

    for epoch in range(1, epochs + 1):
        optimizer.zero_grad()

        # Forward pass — get node embeddings
        z = model(data.x, data.edge_index)

        # Positive edge scores (dot product of connected node pairs)
        pos_src, pos_dst = pos_edge_index
        pos_score = (z[pos_src] * z[pos_dst]).sum(dim=1)
        pos_loss = F.binary_cross_entropy_with_logits(
            pos_score, torch.ones_like(pos_score)
        )

        # Negative edge scores (random non-edges)
        neg_edge_index = _negative_sampling(
            pos_edge_index, data.num_nodes, num_pos
        )
        neg_src, neg_dst = neg_edge_index
        neg_score = (z[neg_src] * z[neg_dst]).sum(dim=1)
        neg_loss = F.binary_cross_entropy_with_logits(
            neg_score, torch.zeros_like(neg_score)
        )

        # Total loss
        loss = pos_loss + neg_loss
        loss.backward()
        optimizer.step()

        losses.append(loss.item())

        if epoch % 10 == 0 or epoch == 1:
            print(f"  Epoch {epoch:3d}/{epochs} | Loss: {loss.item():.4f}")

    print(f"\n✅ Training complete! Final loss: {losses[-1]:.4f}")
    return model, losses


# =================== INFERENCE ===================

def get_embeddings(model: CodeGraphSAGE,
                   data: Data,
                   node_mapping: Dict[str, int]) -> Dict[str, List[float]]:
    """
    Extract final node embeddings from the trained model.

    Args:
        model: Trained CodeGraphSAGE model
        data: PyG Data object
        node_mapping: Dict mapping node names to indices

    Returns:
        Dict mapping node names to embedding vectors (list of floats)
    """
    z = model.embed(data.x, data.edge_index)

    # Reverse mapping: index → node name
    idx_to_node = {idx: node for node, idx in node_mapping.items()}

    embeddings = {}
    for idx in range(z.size(0)):
        node_name = idx_to_node[idx]
        embeddings[node_name] = z[idx].tolist()

    print(f"✅ Extracted embeddings for {len(embeddings)} nodes")
    print(f"   Embedding dimension: {z.size(1)}")

    return embeddings
