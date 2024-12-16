from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from stem import Signal
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
        # Initialize Tor controller with explicit port and timeout
        controller = Controller.from_port(port=9051)

        print("Connecting to Tor controller...")
        # Set timeout for authentication
        auth_task = asyncio.create_task(asyncio.to_thread(controller.authenticate))
        try:
            await asyncio.wait_for(auth_task, timeout=10.0)
            print("Successfully authenticated with Tor controller")
        except asyncio.TimeoutError:
            raise HTTPException(
                status_code=500,
                detail="Timeout while authenticating with Tor controller"
            )

        print("Fetching consensus data...")
        # Set timeout for consensus fetch
        consensus_task = asyncio.create_task(
            asyncio.to_thread(controller.get_network_statuses)
        )
        try:
            consensus = await asyncio.wait_for(consensus_task, timeout=30.0)
            print(f"Retrieved {len(consensus)} nodes from consensus")
        except asyncio.TimeoutError:
            raise HTTPException(
                status_code=500,
                detail="Timeout while fetching consensus data"
            )

        nodes = []
        for router in consensus:
            # Only include nodes with Guard or Exit flags
            if 'Guard' in router.flags or 'Exit' in router.flags:
                role = NodeRole.ENTRY if 'Guard' in router.flags else \
                       NodeRole.EXIT if 'Exit' in router.flags else \
                       NodeRole.MIDDLE

                print(f"Fetching descriptor for node {router.fingerprint}...")
                # Set timeout for descriptor fetch
                desc_task = asyncio.create_task(
                    asyncio.to_thread(
                        controller.get_server_descriptor, router.fingerprint
                    )
                )
                try:
                    desc = await asyncio.wait_for(desc_task, timeout=10.0)
                    if not desc or not desc.onion_key:
                        print(f"Warning: Missing onion key for node {router.fingerprint}")
                        continue

                    node = Node(
                        id=router.fingerprint,
                        public_key=base64.b64encode(
                            desc.onion_key.encode('utf-8') if isinstance(desc.onion_key, str)
                            else desc.onion_key
                        ).decode('utf-8'),
                        role=role,
                        address=f"{router.address}:{router.or_port}"
                    )
                    nodes.append(node)
                except asyncio.TimeoutError:
                    print(f"Timeout fetching descriptor for node {router.fingerprint}")
                    continue
                except Exception as e:
                    print(f"Error fetching descriptor for node {router.fingerprint}: {str(e)}")
                    continue

        await asyncio.to_thread(controller.close)
        print(f"Successfully fetched {len(nodes)} valid nodes")
        return nodes
    except Exception as e:
        print(f"Error in get_consensus_nodes: {str(e)}")
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
