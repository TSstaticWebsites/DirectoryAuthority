from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx
from stem.descriptor.remote import DescriptorDownloader
from typing import List, Dict
import asyncio

app = FastAPI()

# Disable CORS. Do not remove this for full-stack development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

@app.get("/healthz")
async def healthz():
    return {"status": "ok"}

@app.get("/nodes", response_model=List[Dict])
async def get_nodes():
    try:
        downloader = DescriptorDownloader()
        consensus = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: list(downloader.get_consensus().run())
        )

        nodes = []
        for router in consensus:
            nodes.append({
                "nickname": router.nickname,
                "fingerprint": router.fingerprint,
                "address": router.address,
                "or_port": router.or_port,
                "dir_port": router.dir_port,
                "flags": list(router.flags),
                "bandwidth": router.bandwidth,
            })

        return nodes
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
