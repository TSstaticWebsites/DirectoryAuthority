import asyncio
import logging
import os
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
        # Since UseMicrodescriptors=0, we use the regular consensus file
        consensus_path = "/var/lib/tor/cached-consensus"

        # Debug information about file and permissions
        logger.debug(f"Current working directory: {os.getcwd()}")
        logger.debug(f"Process UID: {os.getuid()}")
        logger.debug(f"Process GID: {os.getgid()}")
        logger.debug(f"Process groups: {os.getgroups()}")

        # Check if file exists
        if not os.path.exists(consensus_path):
            logger.error(f"Consensus file does not exist at path: {consensus_path}")
            raise Exception(f"Consensus file not found at {consensus_path}")

        # Get file stats
        file_stat = os.stat(consensus_path)
        logger.debug(f"File permissions: {oct(file_stat.st_mode)}")
        logger.debug(f"File owner: {file_stat.st_uid}")
        logger.debug(f"File group: {file_stat.st_gid}")

        if not os.access(consensus_path, os.R_OK):
            logger.error(f"No read permission for consensus file: {consensus_path}")
            raise Exception(f"Cannot read consensus file at {consensus_path}")

        nodes = []
        current_node = {}
        in_router_section = False

        try:
            logger.info("Processing consensus file")
            with open(consensus_path, 'r') as f:
                for line in f:
                    line = line.strip()

                    # Router entry starts with "r " line
                    if line.startswith('r '):
                        # Save previous node if it exists and has required fields
                        if current_node and all(k in current_node for k in ['fingerprint', 'address']):
                            nodes.append(current_node)
                            logger.debug(f"Added node: {current_node.get('nickname', 'unknown')}")

                        # Parse router line
                        # Format: r nickname identity address OR_port SOC_port
                        parts = line.split()
                        if len(parts) >= 8:
                            current_node = {
                                "nickname": parts[1],
                                "fingerprint": parts[2],
                                "address": parts[6],
                                "or_port": int(parts[7]),
                                "flags": [],
                                "bandwidth": 0
                            }
                            in_router_section = True
                            logger.debug(f"Processing new node: {parts[1]}")

                    # Only process these lines if we're in a router section
                    elif in_router_section:
                        if line.startswith('s '):
                            # Parse flags
                            current_node["flags"] = line[2:].split()
                            logger.debug(f"Added flags for {current_node.get('nickname', 'unknown')}: {current_node['flags']}")

                        elif line.startswith('w Bandwidth='):
                            # Parse bandwidth
                            try:
                                bw_parts = line.split('=')[1].split()
                                if bw_parts:
                                    current_node["bandwidth"] = int(bw_parts[0])
                            except (IndexError, ValueError) as e:
                                logger.warning(f"Failed to parse bandwidth: {str(e)}")
                                current_node["bandwidth"] = 0

                        elif line.startswith('p '):
                            # Parse exit policy summary (indicates this is likely an exit node)
                            current_node["exit_policy"] = line[2:]

                    # Empty line indicates end of router section
                    elif line == "" and in_router_section:
                        in_router_section = False
                        if current_node and all(k in current_node for k in ['fingerprint', 'address']):
                            nodes.append(current_node)
                            logger.debug(f"Added final node in section: {current_node.get('nickname', 'unknown')}")
                        current_node = {}

            # Add the last node if we have one
            if current_node and all(k in current_node for k in ['fingerprint', 'address']):
                nodes.append(current_node)
                logger.debug(f"Added final node: {current_node.get('nickname', 'unknown')}")

            # Filter nodes to only include Guard and Exit nodes with sufficient bandwidth
            filtered_nodes = [
                node for node in nodes
                if (
                    any(flag in ['Guard', 'Exit'] for flag in node.get('flags', []))
                    and node.get('bandwidth', 0) > 0
                )
            ]

            logger.info(f"Successfully processed {len(filtered_nodes)} valid Guard/Exit nodes")
            return filtered_nodes

        except Exception as e:
            logger.error(f"Error processing consensus file: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error processing consensus file: {str(e)}")

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
