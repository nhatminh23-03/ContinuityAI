"""Endpoints 3 and 4. docs/API_CONTRACT.md sections 8.3 and 8.4."""

from fastapi import APIRouter

from app.core.errors import NotFoundError
from app.core.fixtures import load
from app.schemas.graph import GraphResponse
from app.schemas.system import SystemDetail

router = APIRouter(tags=["systems"])


@router.get("/systems/{system_id}", response_model=SystemDetail, response_model_exclude_unset=True)
async def get_system(system_id: str) -> dict:
    data = load("payment-gateway")
    if system_id != data["system_id"]:
        raise NotFoundError(f"System '{system_id}' not found.", {"system_id": system_id})
    return data


@router.get("/systems/{system_id}/graph", response_model=GraphResponse, response_model_exclude_unset=True)
async def get_system_graph(system_id: str, focus_capability_id: str | None = None) -> dict:
    data = load("payment-gateway-graph")
    if system_id != data["scope"]["id"]:
        raise NotFoundError(f"System '{system_id}' not found.", {"system_id": system_id})
    return data
