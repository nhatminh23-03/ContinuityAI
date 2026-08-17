"""Endpoint 8. docs/API_CONTRACT.md section 8.8."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_session
from app.recommendation import BackupCandidateService
from app.schemas.recommendation import BackupCandidateRequest, BackupCandidateResponse

router = APIRouter(tags=["recommendations"])


@router.post(
    "/recommendations/backup-candidates",
    response_model=BackupCandidateResponse,
    response_model_exclude_unset=True,
)
async def compare_backup_candidates(
    request: BackupCandidateRequest, session: Session = Depends(get_session)
) -> BackupCandidateResponse:
    return BackupCandidateService(session).compare(request)
