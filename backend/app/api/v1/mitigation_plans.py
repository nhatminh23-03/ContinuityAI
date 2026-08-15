"""Endpoints 9 and 10. docs/API_CONTRACT.md sections 8.9 and 8.10."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_session
from app.mitigation import MitigationPlanService
from app.schemas.mitigation import (
    ApprovePlanRequest,
    ApprovePlanResponse,
    MitigationPlanRequest,
    MitigationPlanResponse,
)

router = APIRouter(tags=["mitigation-plans"])


@router.post(
    "/mitigation-plans",
    response_model=MitigationPlanResponse,
    response_model_exclude_unset=True,
    status_code=201,
)
async def create_mitigation_plan(
    request: MitigationPlanRequest, session: Session = Depends(get_session)
) -> MitigationPlanResponse:
    # Generating a plan does not change readiness or continuity risk. Nobody becomes more capable
    # because work was scheduled.
    return MitigationPlanService(session).create(request)


@router.post(
    "/mitigation-plans/{plan_id}/approve",
    response_model=ApprovePlanResponse,
    response_model_exclude_unset=True,
)
async def approve_mitigation_plan(
    plan_id: str, request: ApprovePlanRequest, session: Session = Depends(get_session)
) -> ApprovePlanResponse:
    # `request.tasks` carries manager edits when present, replacing the stored task list before
    # the status transition. Contract decision CI-12.
    return MitigationPlanService(session).approve(plan_id, request)
