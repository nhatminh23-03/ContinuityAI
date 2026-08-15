"""Endpoints 3 and 4. docs/API_CONTRACT.md sections 8.3 and 8.4."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_session
from app.graph import GraphService
from app.schemas.graph import GraphResponse
from app.schemas.system import SystemDetail
from app.services import SystemService

router = APIRouter(tags=["systems"])


@router.get("/systems/{system_id}", response_model=SystemDetail, response_model_exclude_unset=True)
async def get_system(system_id: str, session: Session = Depends(get_session)) -> SystemDetail:
    return SystemService(session).detail(system_id)


@router.get(
    "/systems/{system_id}/graph", response_model=GraphResponse, response_model_exclude_unset=True
)
async def get_system_graph(
    system_id: str,
    focus_capability_id: str | None = Query(
        default=None,
        description=(
            "Narrow the graph to one capability's neighbourhood and include its evidence nodes."
        ),
    ),
    session: Session = Depends(get_session),
) -> GraphResponse:
    return GraphService(session).system_graph(system_id, focus_capability_id)
