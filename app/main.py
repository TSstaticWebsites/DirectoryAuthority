from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uuid
from .models import Node, NodeList, NodeRole

app = FastAPI()

# Enable CORS for browser access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mock data for testing
MOCK_NODES = [
    Node(
        id=str(uuid.uuid4()),
        public_key="mock_key_entry_1",
        role=NodeRole.ENTRY,
        address="entry1.onion:9001"
    ),
    Node(
        id=str(uuid.uuid4()),
        public_key="mock_key_middle_1",
        role=NodeRole.MIDDLE,
        address="middle1.onion:9001"
    ),
    Node(
        id=str(uuid.uuid4()),
        public_key="mock_key_exit_1",
        role=NodeRole.EXIT,
        address="exit1.onion:9001"
    ),
    # Additional nodes for better circuit building
    Node(
        id=str(uuid.uuid4()),
        public_key="mock_key_entry_2",
        role=NodeRole.ENTRY,
        address="entry2.onion:9001"
    ),
    Node(
        id=str(uuid.uuid4()),
        public_key="mock_key_middle_2",
        role=NodeRole.MIDDLE,
        address="middle2.onion:9001"
    ),
    Node(
        id=str(uuid.uuid4()),
        public_key="mock_key_exit_2",
        role=NodeRole.EXIT,
        address="exit2.onion:9001"
    ),
]

@app.get("/")
async def root():
    return {"message": "Directory Authority Proxy"}

@app.get("/nodes", response_model=NodeList)
async def get_nodes():
    """Return list of available Tor nodes."""
    return NodeList(nodes=MOCK_NODES)

@app.get("/healthz")
async def healthz():
    return {"status": "ok"}
