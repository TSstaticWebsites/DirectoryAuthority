import asyncio
import logging
from typing import List, Dict
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from stem import Signal
from stem.control import Controller
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
    Fetch and process Tor consensus nodes using microdescriptors.
    """
    try:
        logger.info("Initializing Tor controller on port 9051")
        controller = Controller.from_port(port=9051)

        logger.info("Authenticating with Tor controller using cookie file")
        cookie_path = "/var/run/tor/control.authcookie"
        try:
            with open(cookie_path, 'rb') as f:
                cookie = f.read()
                logger.debug(f"Read auth cookie of length: {len(cookie)}")
        except Exception as e:
            logger.error(f"Failed to read auth cookie: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to read auth cookie")

        auth_task = asyncio.create_task(asyncio.to_thread(lambda: controller.authenticate(cookie)))
        try:
            await asyncio.wait_for(auth_task, timeout=10.0)
            logger.info("Successfully authenticated with Tor controller")
        except asyncio.TimeoutError:
            logger.error("Tor controller authentication timeout")
            raise HTTPException(status_code=500, detail="Tor controller authentication timeout")
        except Exception as e:
            logger.error(f"Authentication failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Authentication failed: {str(e)}")

        logger.info("Fetching consensus data")
        consensus_task = asyncio.create_task(
            asyncio.to_thread(lambda: list(controller.get_network_statuses()))
        )
        try:
            consensus = await asyncio.wait_for(consensus_task, timeout=30.0)
            logger.info(f"Successfully fetched {len(consensus)} nodes from consensus")
        except asyncio.TimeoutError:
            logger.error("Consensus fetch timeout")
            raise HTTPException(status_code=500, detail="Consensus fetch timeout")
        except Exception as e:
            logger.error(f"Failed to fetch consensus: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to fetch consensus: {str(e)}")

        nodes = []
        for router in consensus:
            try:
                # Only include nodes that can be used as Guard or Exit nodes
                if 'Guard' in router.flags or 'Exit' in router.flags:
                    logger.debug(f"Processing node {router.fingerprint} with flags: {router.flags}")
                    # Use the correct GETINFO command format for microdescriptors
                    micro_desc_cmd = f"GETINFO md/desc/id/{router.fingerprint}"
                    micro_desc_task = asyncio.create_task(
                        asyncio.to_thread(
                            lambda r=router, cmd=micro_desc_cmd: controller._msg(cmd)
                        )
                    )
                    try:
                        response = await asyncio.wait_for(micro_desc_task, timeout=5.0)
                        if response and response.raw_content():
                            # Extract the onion key from the microdescriptor
                            micro_desc_lines = response.raw_content().decode().split('\n')
                            onion_key = None
                            for line in micro_desc_lines:
                                if line.startswith('onion-key'):
                                    onion_key = '\n'.join(micro_desc_lines[
                                        micro_desc_lines.index(line):
                                        micro_desc_lines.index(line) + 4
                                    ])
                                    break

                            if onion_key:
                                # Convert onion key to base64 for transmission
                                onion_key_base64 = base64.b64encode(
                                    onion_key.encode()
                                ).decode()

                                node_info = {
                                    "nickname": router.nickname,
                                    "fingerprint": router.fingerprint,
                                    "address": router.address,
                                    "or_port": router.or_port,
                                    "dir_port": router.dir_port,
                                    "flags": list(router.flags),
                                    "onion_key": onion_key_base64,
                                    "bandwidth": router.bandwidth
                                }
                                nodes.append(node_info)
                                logger.debug(f"Successfully added node {router.fingerprint}")

                    except asyncio.TimeoutError:
                        logger.warning(
                            f"Timeout fetching microdescriptor for {router.fingerprint}"
                        )
                        continue
                    except Exception as e:
                        logger.warning(
                            f"Error fetching microdescriptor for {router.fingerprint}: {str(e)}"
                        )
                        continue

            except Exception as e:
                logger.warning(f"Error processing node {router.fingerprint}: {str(e)}")
                continue

        logger.info(f"Successfully processed {len(nodes)} valid nodes")
        return nodes

    except Exception as e:
        logger.error(f"Error in get_consensus_nodes: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if 'controller' in locals():
            controller.close()

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
