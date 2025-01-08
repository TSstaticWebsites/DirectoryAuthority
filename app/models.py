from pydantic import BaseModel
from enum import Enum
from typing import List, Optional
from datetime import datetime

class NodeRole(str, Enum):
    ENTRY = "ENTRY"
    MIDDLE = "MIDDLE"
    EXIT = "EXIT"

class TorNode(BaseModel):
    id: str
    public_key: str
    address: str
    role: NodeRole
    last_seen: datetime = datetime.utcnow()
    bandwidth: Optional[int] = None
