"""Endpoint 8. docs/API_CONTRACT.md section 8.8."""

from fastapi import APIRouter

from app.core.fixtures import load
from app.schemas.recommendation import BackupCandidateRequest, BackupCandidateResponse

router = APIRouter(tags=["recommendations"])


@router.post("/recommendations/backup-candidates", response_model=BackupCandidateResponse, response_model_exclude_unset=True)
async def compare_backup_candidates(request: BackupCandidateRequest) -> dict:
    data = load("backup-candidates")
    return {**data, "candidates": data["candidates"][: request.limit]}
