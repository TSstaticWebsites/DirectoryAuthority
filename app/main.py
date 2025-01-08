from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from .models import TorNode, NodeRole
from .services import register_node, get_available_nodes, update_node_status

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/nodes", response_model=List[TorNode])
async def list_nodes():
    """Get list of available Tor nodes."""
    return get_available_nodes()

@app.post("/nodes", response_model=TorNode)
async def create_node(public_key: str, address: str, role: NodeRole, bandwidth: Optional[int] = None):
    """Register a new Tor node."""
    return register_node(public_key, address, role, bandwidth)

@app.put("/nodes/{node_id}/heartbeat")
async def node_heartbeat(node_id: str):
    """Update node's last_seen timestamp."""
    try:
        update_node_status(node_id)
        return {"status": "updated"}
    except KeyError:
        raise HTTPException(status_code=404, detail="Node not found")
