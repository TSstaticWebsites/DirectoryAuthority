import logging
from typing import List, Dict
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from stem.control import Controller
import base64
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend

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

def generate_key_pair() -> str:
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )
    public_key = private_key.public_key()

    pem = public_key.public_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

    return base64.b64encode(pem).decode('utf-8')

def get_consensus_nodes() -> List[Dict]:
    nodes = []
    try:
        logger.debug("Attempting to connect to Tor controller")
        with Controller.from_port(port=9051) as controller:
            controller.authenticate()
            logger.debug("Successfully authenticated with Tor controller")

            try:
                consensus = list(controller.get_network_statuses())
                logger.debug(f"Retrieved {len(consensus)} nodes from consensus")

                # Limit to first 100 valid nodes to prevent response size issues
                node_count = 0
                for router in consensus:
                    if node_count >= 100:
                        break

                    if router.flags and ('Guard' in router.flags or 'Exit' in router.flags):
                        try:
                            node = {
                                'nickname': router.nickname,
                                'fingerprint': router.fingerprint,
                                'address': router.address,
                                'or_port': router.or_port,
                                'dir_port': router.dir_port,
                                'flags': list(router.flags),
                                'bandwidth': router.bandwidth or 0,
                                'public_key': generate_key_pair()
                            }
                            if node['bandwidth'] > 0:
                                nodes.append(node)
                                node_count += 1
                        except Exception as node_error:
                            logger.error(f"Error processing node {router.nickname}: {str(node_error)}")
                            continue

                logger.debug(f"Filtered to {len(nodes)} Guard/Exit nodes with bandwidth > 0")
                if not nodes:
                    logger.error("No valid nodes found after filtering")
                    raise HTTPException(status_code=500, detail="No valid nodes available")

                # Log sample node for debugging
                if nodes:
                    sample_node = {**nodes[0]}
                    sample_node['public_key'] = sample_node['public_key'][:32] + '...'  # Truncate key in logs
                    logger.debug(f"Sample node data: {sample_node}")

                return nodes

            except Exception as consensus_error:
                logger.error(f"Error fetching consensus: {str(consensus_error)}")
                raise HTTPException(status_code=500, detail="Failed to fetch consensus data")

    except Exception as controller_error:
        logger.error(f"Error in get_consensus_nodes: {str(controller_error)}")
        raise HTTPException(status_code=500, detail=str(controller_error))

@app.get("/")
def root():
    return {"message": "Directory Authority Proxy Service"}

@app.get("/nodes")
async def get_nodes() -> List[Dict]:
    try:
        nodes = get_consensus_nodes()
        # Verify response data
        logger.debug(f"Returning {len(nodes)} nodes")
        return nodes
    except Exception as e:
        logger.error(f"Error in get_nodes endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/healthz")
async def healthz():
    return {"status": "healthy"}
