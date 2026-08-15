"""Backup-candidate DTOs. docs/API_CONTRACT.md section 8.8.

Technical overlap only. No employee value, ranking, or match percentage exists here
or anywhere else in the contract.
"""

from pydantic import BaseModel, Field

from .capability import CapabilityRef
from .enums import EvidenceConfidence, TechnicalOverlap


class BackupCandidateRequest(BaseModel):
    simulation_id: str | None = None
    capability_id: str
    limit: int = Field(default=3, ge=1, le=3)


class BackupCandidate(BaseModel):
    engineer_id: str
    name: str
    technical_overlap: TechnicalOverlap
    strengths: list[str]
    gaps: list[str]
    evidence_confidence: EvidenceConfidence
    supporting_evidence_ids: list[str] = []


class BackupCandidateResponse(BaseModel):
    capability: CapabilityRef
    candidates: list[BackupCandidate]
    message: str | None = None
    disclaimer: str
