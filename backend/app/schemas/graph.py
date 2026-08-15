"""Graph DTOs. docs/API_CONTRACT.md sections 6.8, 6.9, 6.10 and 8.4.

The frontend may choose layout but must not invent or infer relationships.
"""

from pydantic import BaseModel

from .enums import GraphEdgeType, GraphNodeType


class GraphScope(BaseModel):
    type: str
    id: str
    name: str


class GraphNode(BaseModel):
    id: str
    type: GraphNodeType
    label: str
    status: str | None = None
    metadata: dict = {}


class GraphEdge(BaseModel):
    source: str
    target: str
    type: GraphEdgeType
    metadata: dict = {}


class GraphResponse(BaseModel):
    scope: GraphScope
    nodes: list[GraphNode]
    edges: list[GraphEdge]
