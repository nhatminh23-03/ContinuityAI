"""Endpoints 1 and 2. docs/API_CONTRACT.md sections 8.1 and 8.2."""

from fastapi import APIRouter

from app.core.errors import NotFoundError
from app.core.fixtures import load
from app.schemas.platform import PlatformListResponse
from app.schemas.system import SystemListResponse

router = APIRouter(tags=["platforms"])


@router.get("/platforms", response_model=PlatformListResponse, response_model_exclude_unset=True)
async def list_platforms() -> dict:
    return load("platforms")


@router.get("/platforms/{platform_id}/systems", response_model=SystemListResponse, response_model_exclude_unset=True)
async def list_platform_systems(platform_id: str) -> dict:
    data = load("payments-systems")
    if platform_id != data["platform"]["platform_id"]:
        raise NotFoundError(
            f"Platform '{platform_id}' not found.", {"platform_id": platform_id}
        )
    return data
