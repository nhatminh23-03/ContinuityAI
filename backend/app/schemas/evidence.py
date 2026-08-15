"""Evidence DTOs. docs/API_CONTRACT.md sections 6.7 and 8.6.

Absence of evidence is reported as absence of evidence, never as inability.
"""

from datetime import date

from pydantic import BaseModel

from .capability import CapabilityRef
from .enums import (
    CapabilityExposure,
    EvidenceConfidence,
    EvidenceRole,
    EvidenceSourceType,
    EvidenceStrength,
    Freshness,
)


class Provenance(BaseModel):
    source: str
    record_id: str
    source_url: str | None = None


class EvidenceRecord(BaseModel):
    evidence_id: str
    source_type: EvidenceSourceType
    source_reference: str
    source_title: str | None = None
    artifact_date: date
    engineer_id: str
    system_id: str
    component_id: str | None = None
    capability_id: str
    evidence_role: EvidenceRole
    evidence_strength: EvidenceStrength
    summary: str
    freshness: Freshness
    provenance: Provenance


class MissingEvidence(BaseModel):
    engineer_id: str
    engineer_name: str
    description: str


class EngineerNameRef(BaseModel):
    engineer_id: str
    name: str


class DeclaredOwnerRef(EngineerNameRef):
    source: str


class DeclaredVsDemonstrated(BaseModel):
    declared_owner: DeclaredOwnerRef | None = None
    strongest_demonstrated_coverage: EngineerNameRef | None = None
    mismatch_detected: bool


class CapabilityAssessment(BaseModel):
    exposure: CapabilityExposure
    evidence_confidence: EvidenceConfidence
    rules_triggered: list[str] = []


class EvidenceResponse(BaseModel):
    capability: CapabilityRef
    assessment: CapabilityAssessment
    evidence: list[EvidenceRecord]
    missing_evidence: list[MissingEvidence] = []
    conflicting_evidence: list[EvidenceRecord] = []
    declared_vs_demonstrated: DeclaredVsDemonstrated | None = None
