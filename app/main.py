from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from stem.descriptor.remote import DescriptorDownloader
from stem.control import Controller
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
        consensus = await asyncio.to_thread(
            downloader.get_consensus
        )
        nodes = []
        for router in consensus.routers:
            # Only include nodes with Guard or Exit flags
            if 'Guard' in router.flags or 'Exit' in router.flags:
                role = NodeRole.ENTRY if 'Guard' in router.flags else \
                       NodeRole.EXIT if 'Exit' in router.flags else \
                       NodeRole.MIDDLE

                # Get node's public key
                controller = Controller.from_port()
                await asyncio.to_thread(controller.authenticate)
                key_material = await asyncio.to_thread(
                    controller.get_server_descriptor, router.fingerprint
                )

                node = Node(
                    id=router.fingerprint,
                    public_key=base64.b64encode(key_material.onion_key).decode(),
                    role=role,
                    address=f"{router.address}:{router.or_port}"
                )
                nodes.append(node)

                await asyncio.to_thread(controller.close)

        return nodes
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    return {"message": "Directory Authority Proxy"}

@app.get("/nodes", response_model=NodeList)
async def get_nodes():
    """Return list of available Tor nodes from network consensus."""
    nodes = await get_consensus_nodes()
    return NodeList(nodes=nodes)

@app.get("/healthz")
async def healthz():
    return {"status": "ok"}
