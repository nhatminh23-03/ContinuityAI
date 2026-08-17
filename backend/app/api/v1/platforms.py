"""Endpoints 1 and 2. docs/API_CONTRACT.md sections 8.1 and 8.2."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_session
from app.schemas.platform import PlatformListResponse
from app.schemas.system import SystemListResponse
from app.services import PlatformService, SystemService

router = APIRouter(tags=["platforms"])


@router.get("/platforms", response_model=PlatformListResponse, response_model_exclude_unset=True)
async def list_platforms(session: Session = Depends(get_session)) -> PlatformListResponse:
    return PlatformService(session).list_platforms()


@router.get(
    "/platforms/{platform_id}/systems",
    response_model=SystemListResponse,
    response_model_exclude_unset=True,
)
async def list_platform_systems(
    platform_id: str, session: Session = Depends(get_session)
) -> SystemListResponse:
    return SystemService(session).list_by_platform(platform_id)
