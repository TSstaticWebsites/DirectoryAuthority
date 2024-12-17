import asyncio
import logging
from typing import List, Dict
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import base64

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

async def get_consensus_nodes() -> List[Dict]:
    """
    Fetch and process Tor consensus nodes using the cached consensus file.
    """
    try:
        logger.info("Reading cached consensus file")
        consensus_path = "/var/lib/tor/cached-microdesc-consensus"
        nodes = []
        current_node = {}

        try:
            with open(consensus_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('r '):
                        # If we were processing a node, add it to the list
                        if current_node and 'onion_key' in current_node:
                            nodes.append(current_node)

                        # Start a new node
                        parts = line.split()
                        if len(parts) >= 9:
                            current_node = {
                                "nickname": parts[1],
                                "fingerprint": parts[2],
                                "address": parts[6],
                                "or_port": int(parts[7]),
                                "dir_port": int(parts[8]),
                                "flags": [],
                                "bandwidth": 0
                            }
                    elif line.startswith('s '):
                        if current_node:
                            current_node["flags"] = line[2:].split()
                    elif line.startswith('w Bandwidth='):
                        if current_node:
                            try:
                                current_node["bandwidth"] = int(line.split('=')[1])
                            except (IndexError, ValueError):
                                current_node["bandwidth"] = 0
                    elif line.startswith('m '):
                        if current_node:
                            # Base64 encoded key is directly in the microdescriptor line
                            current_node["onion_key"] = line[2:]

                # Add the last node if it exists
                if current_node and 'onion_key' in current_node:
                    nodes.append(current_node)

            # Filter nodes to only include Guard and Exit nodes
            filtered_nodes = [
                node for node in nodes
                if any(flag in ['Guard', 'Exit'] for flag in node.get('flags', []))
            ]

            logger.info(f"Successfully processed {len(filtered_nodes)} valid Guard/Exit nodes")
            return filtered_nodes

        except Exception as e:
            logger.error(f"Failed to read consensus file: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to read consensus file")

    except Exception as e:
        logger.error(f"Error in get_consensus_nodes: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def root():
    return {"message": "Directory Authority Proxy"}

@app.get("/nodes")
async def get_nodes() -> List[Dict]:
    """
    Get a list of available Tor nodes.
    """
    return await get_consensus_nodes()

@app.get("/healthz")
def healthz():
    """
    Health check endpoint.
    """
    return {"status": "healthy"}
