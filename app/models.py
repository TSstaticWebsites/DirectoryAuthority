from pydantic import BaseModel
from typing import List
from enum import Enum

class NodeRole(str, Enum):
    ENTRY = "entry"
    MIDDLE = "middle"
    EXIT = "exit"

class Node(BaseModel):
    id: str
    public_key: str
    role: NodeRole
    address: str

class NodeList(BaseModel):
    nodes: List[Node]
