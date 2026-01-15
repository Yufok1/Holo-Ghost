"""
HOLO-GHOST Cascade Lattice
Core structures for causal lineage and structural evolution.
"""

import time
import uuid
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field

@dataclass
class LatticeNode:
    """A semantic entity in the causal lattice."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: str = "generic"
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    
    # Structural survival metrics
    strength: float = 1.0
    energy: float = 1.0
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.type,
            "data": self.data,
            "timestamp": self.timestamp,
            "strength": self.strength
        }

@dataclass
class LatticeEdge:
    """A causal relationship between nodes."""
    source_id: str
    target_id: str
    type: str = "causes"
    weight: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)

class CausalLattice:
    """
    A multi-dimensional causality graph.
    Supports emergence, dominance, and structural culling.
    """
    def __init__(self):
        self.nodes: Dict[str, LatticeNode] = {}
        self.edges: List[LatticeEdge] = []
        
    def add_node(self, node_type: str, data: Dict[str, Any], parents: Optional[List[str]] = None) -> LatticeNode:
        """Add a node and link it to its causal parents."""
        node = LatticeNode(type=node_type, data=data)
        self.nodes[node.id] = node
        
        if parents:
            for parent_id in parents:
                if parent_id in self.nodes:
                    self.add_edge(parent_id, node.id, "leads_to")
        
        return node

    def add_edge(self, source_id: str, target_id: str, edge_type: str = "causes", weight: float = 1.0):
        """Add a causal edge between nodes."""
        edge = LatticeEdge(source_id, target_id, edge_type, weight)
        self.edges.append(edge)

    def prune(self, threshold: float = 0.1):
        """Cull weak structures that haven't persisted."""
        # This is where the 'battle / absorption' metaphor lives
        # Nodes with low strength are removed, their energy might be absorbed by stronger neighbors
        surviving_nodes = {}
        for node_id, node in self.nodes.items():
            if node.strength >= threshold:
                surviving_nodes[node_id] = node
        
        self.nodes = surviving_nodes
        self.edges = [e for e in self.edges if e.source_id in self.nodes and e.target_id in self.nodes]

    def get_lineage(self, node_id: str, depth: int = 10) -> List[LatticeNode]:
        """Trace the causal ancestry of a node."""
        lineage = []
        current_id = node_id
        
        visited = set()
        
        def trace(nid, current_depth):
            if nid in visited or current_depth <= 0:
                return
            visited.add(nid)
            if nid in self.nodes:
                lineage.append(self.nodes[nid])
                # Find parents (edges where nid is target)
                parents = [e.source_id for e in self.edges if e.target_id == nid]
                for p_id in parents:
                    trace(p_id, current_depth - 1)
                    
        trace(node_id, depth)
        return lineage
