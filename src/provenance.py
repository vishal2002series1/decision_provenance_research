import hashlib
import json
import time
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

class ProvenanceNode(BaseModel):
    """
    The Atomic Unit of Agent Accountability.
    This represents a single step in the agent's reasoning chain.
    """
    node_id: str = Field(default_factory=lambda: hashlib.sha256(str(time.time()).encode()).hexdigest()[:10])
    timestamp: float = Field(default_factory=time.time)
    parent_hash: Optional[str] = None
    
    # The "What Happened"
    action_type: str # e.g., "RETRIEVAL", "REASONING", "DECISION"
    input_data: Dict[str, Any]
    output_data: Dict[str, Any]
    
    # The Cryptographic Seal
    node_hash: Optional[str] = None

    def compute_hash(self) -> str:
        """
        Creates a SHA-256 hash of the ENTIRE state.
        If any bit of input/output changes, this hash changes.
        """
        payload = {
            "parent": self.parent_hash,
            "action": self.action_type,
            "input": self.sort_dict(self.input_data),  # Sort keys for consistency
            "output": self.sort_dict(self.output_data),
            "time": self.timestamp
        }
        # Serialize to JSON strictly
        payload_str = json.dumps(payload, sort_keys=True, default=str)
        return hashlib.sha256(payload_str.encode()).hexdigest()

    @staticmethod
    def sort_dict(d):
        """Recursively sorts dictionary keys to ensure deterministic hashing."""
        if isinstance(d, dict):
            return {k: ProvenanceNode.sort_dict(v) for k, v in sorted(d.items())}
        if isinstance(d, list):
            return [ProvenanceNode.sort_dict(i) for i in d]
        return d

class ProvenanceGraph:
    """
    The Manager that builds the chain.
    """
    def __init__(self):
        self.chain = []
        self.latest_hash = None

    def add_step(self, action_type: str, input_data: dict, output_data: dict):
        # 1. Create the node
        node = ProvenanceNode(
            parent_hash=self.latest_hash,
            action_type=action_type,
            input_data=input_data,
            output_data=output_data
        )
        
        # 2. Seal it (Compute Hash)
        node.node_hash = node.compute_hash()
        
        # 3. Add to chain
        self.chain.append(node)
        self.latest_hash = node.node_hash
        
        print(f"🔒 [Provenanced] Step '{action_type}' sealed. Hash: {node.node_hash[:8]}...")
        return node

    def verify_integrity(self) -> bool:
        """
        The 'Audit' function. Re-runs the math to check for tampering.
        """
        print("\n🕵️‍♂️ Starting Forensic Audit...")
        prev_hash = None
        for i, node in enumerate(self.chain):
            # Check 1: Chain Link
            if node.parent_hash != prev_hash:
                print(f"❌ TAMPERING DETECTED at Step {i}. Chain broken.")
                return False
            
            # Check 2: Data Integrity (Re-hash the content)
            recalculated = node.compute_hash()
            if recalculated != node.node_hash:
                print(f"❌ TAMPERING DETECTED at Step {i}. Data modified.")
                return False
            
            prev_hash = node.node_hash
            
        print("✅ Audit Passed. Graph is immutable.")
        return True
    # ... inside class ProvenanceGraph ...
    
    def visualize(self, filename="provenance_graph.png"):
        """
        Generates Figure 1 for the research paper.
        Visualizes the Merkle-DAG topology.
        """
        import networkx as nx
        import matplotlib.pyplot as plt

        G = nx.DiGraph()
        labels = {}
        colors = []
        
        print(f"📊 Generating Graph Visualization: {filename}")

        for i, node in enumerate(self.chain):
            # Use abbreviated hash as ID
            node_id = node.node_hash[:6]
            parent_id = node.parent_hash[:6] if node.parent_hash else "START"
            
            # Label: Action + Time
            label = f"{node.action_type}\n({node_id})"
            G.add_node(node_id, label=label)
            labels[node_id] = label
            
            # Color logic
            if node.action_type == "USER_INPUT": colors.append("#a8dadc")      # Light Blue
            elif node.action_type == "REASONING": colors.append("#f1faee")     # White
            elif node.action_type == "DECISION": colors.append("#e63946")      # Red
            else: colors.append("#dddddd")

            # Draw Edge from Parent
            if node.parent_hash:
                G.add_edge(parent_id, node_id)

        # Drawing settings for "Academic Style"
        plt.figure(figsize=(10, 6))
        pos = nx.spring_layout(G, seed=42) # Consistent layout
        
        nx.draw(G, pos, 
                labels=labels, 
                node_color=colors, 
                edge_color='gray',
                node_size=3000, 
                font_size=9, 
                font_weight='bold', 
                arrowsize=20,
                with_labels=True,
                edgecolors='black') # Node borders
        
        plt.title("Figure 1: Immutable Decision Provenance Graph", fontsize=14)
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"✅ Saved graph to {filename}")