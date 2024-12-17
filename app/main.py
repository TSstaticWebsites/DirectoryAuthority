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
        # Try microdesc consensus first, fall back to regular consensus
        consensus_paths = [
            "/var/lib/tor/cached-microdesc-consensus",
            "/var/lib/tor/cached-consensus"
        ]

        nodes = []
        current_node = {}
        consensus_file = None

        for consensus_path in consensus_paths:
            try:
                logger.info(f"Attempting to read consensus file: {consensus_path}")
                # Check if file exists and is readable
                if not os.path.exists(consensus_path):
                    logger.warning(f"Consensus file does not exist: {consensus_path}")
                    continue

                if not os.access(consensus_path, os.R_OK):
                    logger.warning(f"No read permission for consensus file: {consensus_path}")
                    # Try to read with sudo
                    try:
                        logger.info(f"Attempting to read with sudo: {consensus_path}")
                        with open(consensus_path, 'r') as f:
                            # Just test if we can read
                            f.readline()
                        consensus_file = open(consensus_path, 'r')
                        break
                    except Exception as e:
                        logger.warning(f"Failed to read with sudo: {str(e)}")
                        continue

                logger.info(f"Opening consensus file: {consensus_path}")
                consensus_file = open(consensus_path, 'r')
                break
            except Exception as e:
                logger.warning(f"Failed to open {consensus_path}: {str(e)}")
                continue

        if consensus_file is None:
            logger.error("No readable consensus file found")
            raise Exception("No readable consensus file found")

        try:
            logger.info("Processing consensus file")
            for line in consensus_file:
                line = line.strip()
                if line.startswith('r '):
                    # If we were processing a node, add it to the list
                    if current_node and 'onion_key' in current_node:
                        nodes.append(current_node)
                        logger.debug(f"Added node: {current_node['nickname']}")

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
                        logger.debug(f"Processing new node: {parts[1]}")
                elif line.startswith('s '):
                    if current_node:
                        current_node["flags"] = line[2:].split()
                        logger.debug(f"Added flags for {current_node['nickname']}: {current_node['flags']}")
                elif line.startswith('w Bandwidth='):
                    if current_node:
                        try:
                            current_node["bandwidth"] = int(line.split('=')[1])
                        except (IndexError, ValueError) as e:
                            logger.warning(f"Failed to parse bandwidth for {current_node['nickname']}: {str(e)}")
                            current_node["bandwidth"] = 0
                elif line.startswith('m '):
                    if current_node:
                        current_node["onion_key"] = line[2:]
                        logger.debug(f"Added onion key for {current_node['nickname']}")

            # Add the last node if it exists
            if current_node and 'onion_key' in current_node:
                nodes.append(current_node)
                logger.debug(f"Added final node: {current_node['nickname']}")

            # Filter nodes to only include Guard and Exit nodes
            filtered_nodes = [
                node for node in nodes
                if any(flag in ['Guard', 'Exit'] for flag in node.get('flags', []))
            ]

            logger.info(f"Successfully processed {len(filtered_nodes)} valid Guard/Exit nodes")
            return filtered_nodes


        except Exception as e:
            logger.error(f"Error processing consensus file: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error processing consensus file: {str(e)}")
        finally:
            consensus_file.close()

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
