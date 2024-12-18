from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from stem.descriptor.remote import DescriptorDownloader
from .models import Node, NodeList, NodeRole
import asyncio
import base64
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
        logger.info("Starting consensus fetch...")
        downloader = DescriptorDownloader()
        logger.info("Created DescriptorDownloader")

        try:
            logger.info("Fetching consensus...")
            consensus_iterator = await asyncio.to_thread(lambda: downloader.get_consensus().run())
            logger.info("Got consensus iterator")

            logger.info("Converting iterator to list...")
            routers = await asyncio.to_thread(lambda: list(consensus_iterator))
            logger.info(f"Found {len(routers)} routers in consensus")

            nodes = []
            for router in routers:
                try:
                    # Only include nodes with Guard or Exit flags
                    if 'Guard' in router.flags or 'Exit' in router.flags:
                        role = NodeRole.ENTRY if 'Guard' in router.flags else \
                               NodeRole.EXIT if 'Exit' in router.flags else \
                               NodeRole.MIDDLE

                        # Use the router's key material directly
                        node = Node(
                            id=router.fingerprint,
                            public_key=base64.b64encode(router.onion_key).decode(),
                            role=role,
                            address=f"{router.address}:{router.or_port}"
                        )
                        nodes.append(node)
                except AttributeError as e:
                    logger.warning(f"Skipping router due to missing attribute: {str(e)}")
                    continue
                except Exception as e:
                    logger.error(f"Error processing router: {str(e)}")
                    continue

            logger.info(f"Successfully processed {len(nodes)} valid nodes")
            return nodes

        except Exception as e:
            logger.error(f"Error fetching consensus: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error fetching consensus: {str(e)}")

    except Exception as e:
        logger.error(f"Unexpected error in get_consensus_nodes: {str(e)}")
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
