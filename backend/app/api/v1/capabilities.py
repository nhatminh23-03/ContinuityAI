"""Endpoints 5 and 6. docs/API_CONTRACT.md sections 8.5 and 8.6."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_session
from app.schemas.capability import CapabilityDetail
from app.schemas.evidence import EvidenceResponse
from app.services import CapabilityService, EvidenceService

router = APIRouter(tags=["capabilities"])


@router.get(
    "/capabilities/{capability_id}",
    response_model=CapabilityDetail,
    response_model_exclude_unset=True,
)
async def get_capability(
    capability_id: str, session: Session = Depends(get_session)
) -> CapabilityDetail:
    return CapabilityService(session).detail(capability_id)


@router.get(
    "/capabilities/{capability_id}/evidence",
    response_model=EvidenceResponse,
    response_model_exclude_unset=True,
)
async def get_capability_evidence(
    capability_id: str,
    engineer_id: str | None = Query(
        default=None, description="Filter the provenance view to one engineer."
    ),
    session: Session = Depends(get_session),
) -> EvidenceResponse:
    return EvidenceService(session).for_capability(capability_id, engineer_id)
