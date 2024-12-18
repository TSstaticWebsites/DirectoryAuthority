from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from stem.descriptor.remote import DescriptorDownloader
from .models import Node, NodeList, NodeRole
import asyncio
import base64

app = FastAPI()

# Enable CORS for browser access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def get_consensus_nodes():
    """Fetch nodes from Tor network consensus."""
    try:
        downloader = DescriptorDownloader()
        consensus_iterator = await asyncio.to_thread(lambda: downloader.get_consensus().run())
        nodes = []

        # Collect all routers from the consensus
        routers = await asyncio.to_thread(lambda: list(consensus_iterator))

        for router in routers:
            # Only include nodes with Guard or Exit flags
            if 'Guard' in router.flags or 'Exit' in router.flags:
                role = NodeRole.ENTRY if 'Guard' in router.flags else \
                       NodeRole.EXIT if 'Exit' in router.flags else \
                       NodeRole.MIDDLE

                # Use the router's key material directly
                try:
                    node = Node(
                        id=router.fingerprint,
                        public_key=base64.b64encode(router.onion_key).decode(),
                        role=role,
                        address=f"{router.address}:{router.or_port}"
                    )
                    nodes.append(node)
                except AttributeError:
                    # Skip nodes that don't have all required attributes
                    continue

        return nodes
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    return {"message": "Directory Authority Proxy"}

@app.get("/api/v1/nodes", response_model=NodeList)
async def get_nodes():
    """Return list of available Tor nodes from network consensus."""
    nodes = await get_consensus_nodes()
    return NodeList(nodes=nodes)

@app.get("/healthz")
async def healthz():
    return {"status": "ok"}
