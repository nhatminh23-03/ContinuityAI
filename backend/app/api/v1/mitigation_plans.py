"""Endpoints 9 and 10. docs/API_CONTRACT.md sections 8.9 and 8.10."""

from fastapi import APIRouter

from app.core.errors import NotFoundError, ValidationError
from app.core.fixtures import load
from app.schemas.mitigation import (
    ApprovePlanRequest,
    ApprovePlanResponse,
    MitigationPlanRequest,
    MitigationPlanResponse,
)

router = APIRouter(tags=["mitigation-plans"])


@router.post("/mitigation-plans", response_model=MitigationPlanResponse, response_model_exclude_unset=True, status_code=201)
async def create_mitigation_plan(request: MitigationPlanRequest) -> dict:
    # Generating a plan does not change readiness or continuity risk.
    return load("mitigation-plan")


@router.post("/mitigation-plans/{plan_id}/approve", response_model=ApprovePlanResponse, response_model_exclude_unset=True)
async def approve_mitigation_plan(plan_id: str, request: ApprovePlanRequest) -> dict:
    draft = load("mitigation-plan")
    if plan_id != draft["plan_id"]:
        raise NotFoundError(f"Plan '{plan_id}' not found.", {"plan_id": plan_id})
    if draft["status"] != "DRAFT":
        raise ValidationError(
            "Only a DRAFT plan can be approved.", {"plan_id": plan_id}
        )
    # request.tasks carries manager edits when present. Contract decision CI-12.
    return load("mitigation-plan-approved")
