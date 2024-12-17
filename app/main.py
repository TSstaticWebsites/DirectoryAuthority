import logging
from typing import List, Dict
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from stem.control import Controller

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_consensus_nodes() -> List[Dict]:
    """
    Get a list of Tor nodes using the Tor controller interface.
    """
    nodes = []
    try:
        logger.debug("Attempting to connect to Tor controller")
        with Controller.from_port(port=9051) as controller:
            controller.authenticate()
            logger.debug("Successfully authenticated with Tor controller")

            # Get consensus data
            consensus = controller.get_network_statuses()
            logger.debug(f"Retrieved {len(consensus)} nodes from consensus")

            for router in consensus:
                if router.flags and ('Guard' in router.flags or 'Exit' in router.flags):
                    node = {
                        'nickname': router.nickname,
                        'fingerprint': router.fingerprint,
                        'address': router.address,
                        'or_port': router.or_port,
                        'dir_port': router.dir_port,
                        'flags': list(router.flags),
                        'bandwidth': router.bandwidth or 0
                    }
                    if node['bandwidth'] > 0:
                        nodes.append(node)

            logger.debug(f"Filtered to {len(nodes)} Guard/Exit nodes with bandwidth > 0")
            return nodes

    except Exception as e:
        logger.error(f"Error in get_consensus_nodes: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def root():
    """
    Root endpoint returning service information.
    """
    return {"message": "Directory Authority Proxy Service"}

@app.get("/nodes")
async def get_nodes() -> List[Dict]:
    """
    Get a list of available Tor nodes.
    """
    return get_consensus_nodes()

@app.get("/healthz")
async def healthz():
    """
    Health check endpoint.
    """
    return {"status": "healthy"}
