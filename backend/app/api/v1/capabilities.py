"""Endpoints 5 and 6. docs/API_CONTRACT.md sections 8.5 and 8.6."""

from fastapi import APIRouter

from app.core.errors import NotFoundError
from app.core.fixtures import load
from app.schemas.capability import CapabilityDetail
from app.schemas.evidence import EvidenceResponse

router = APIRouter(tags=["capabilities"])


@router.get("/capabilities/{capability_id}", response_model=CapabilityDetail, response_model_exclude_unset=True)
async def get_capability(capability_id: str) -> dict:
    data = load("incident-recovery")
    if capability_id != data["capability_id"]:
        raise NotFoundError(
            f"Capability '{capability_id}' not found.", {"capability_id": capability_id}
        )
    return data


@router.get("/capabilities/{capability_id}/evidence", response_model=EvidenceResponse, response_model_exclude_unset=True)
async def get_capability_evidence(
    capability_id: str, engineer_id: str | None = None
) -> dict:
    data = load("incident-recovery-evidence")
    if capability_id != data["capability"]["capability_id"]:
        raise NotFoundError(
            f"Capability '{capability_id}' not found.", {"capability_id": capability_id}
        )
    if engineer_id is None:
        return data
    filtered = dict(data)
    filtered["evidence"] = [e for e in data["evidence"] if e["engineer_id"] == engineer_id]
    filtered["missing_evidence"] = [
        m for m in data["missing_evidence"] if m["engineer_id"] == engineer_id
    ]
    return filtered
