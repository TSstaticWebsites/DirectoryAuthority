from typing import List, Dict, Optional
from datetime import datetime, timedelta
import uuid
from .models import TorNode, NodeRole

# In-memory storage for registered nodes
nodes: Dict[str, TorNode] = {}

def register_node(public_key: str, address: str, role: NodeRole, bandwidth: Optional[int] = None) -> TorNode:
    """Register a new Tor node or update existing one."""
    node_id = str(uuid.uuid4())
    node = TorNode(
        id=node_id,
        public_key=public_key,
        address=address,
        role=role,
        bandwidth=bandwidth
    )
    nodes[node_id] = node
    return node

def get_available_nodes(max_age_minutes: int = 5) -> List[TorNode]:
    """Get list of recently active nodes."""
    cutoff_time = datetime.utcnow() - timedelta(minutes=max_age_minutes)
    return [
        node for node in nodes.values()
        if node.last_seen >= cutoff_time
    ]

def update_node_status(node_id: str) -> None:
    """Update last_seen timestamp for a node."""
    if node_id in nodes:
        nodes[node_id].last_seen = datetime.utcnow()
