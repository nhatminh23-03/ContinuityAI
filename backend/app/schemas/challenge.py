"""Challenge DTOs. PRD section 21, closing FR-020 and AC-11.

The governing rule: *scores change because evidence changes, not because a manager overwrote a
score.* There is deliberately no field anywhere in this module that accepts a readiness level, an
exposure state, or a risk index. The request describes an evidence operation; the response reports
what the rules then concluded.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from .enums import (
    CapabilityExposure,
    ChallengeType,
    ContinuityRiskClass,
    EvidenceConfidence,
    EvidenceRole,
    ReadinessLevel,
)


class ChallengeRequest(BaseModel):
    challenge_type: ChallengeType
    submitted_by: str
    comment: str

    # LINK_EVIDENCE and MANAGER_ATTESTATION concern one engineer's coverage.
    engineer_id: str | None = None

    # LINK_EVIDENCE: the artifact the extraction step missed or mis-mapped, by source reference
    # (for example "INC-221"). The engineer must be a recorded participant of it — a manager may
    # point at evidence, not invent it.
    source_reference: str | None = None

    # MANAGER_ATTESTATION: what the manager states the engineer did. Capped at MODERATE strength
    # whatever is claimed, so an attestation can never alone manufacture VALIDATED.
    evidence_role: EvidenceRole | None = None

    # CORRECT_CAPABILITY_MAPPING: move one evidence record to the capability it belongs to.
    evidence_id: str | None = None
    target_capability_id: str | None = None

    @field_validator("comment")
    @classmethod
    def _reason_required(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("a challenge must state why: the reason is part of the audit trail")
        return value


class AssessmentSnapshot(BaseModel):
    """A capability assessment at a point in time, for the before/after of a recomputation."""

    exposure: CapabilityExposure
    continuity_risk_index: int | None = None
    continuity_risk_class: ContinuityRiskClass | None = None
    evidence_confidence: EvidenceConfidence
    readiness: ReadinessLevel | None = None
    rules_triggered: list[str] = Field(default_factory=list)


class SystemSnapshot(BaseModel):
    continuity_risk_index: int | None = None
    continuity_risk_class: ContinuityRiskClass | None = None
    exposure: CapabilityExposure
    critical_gap_count: int = Field(ge=0)
    degraded_capability_count: int = Field(ge=0)
    covered_capability_count: int = Field(ge=0)


class ChallengeResponse(BaseModel):
    challenge_id: str
    challenge_type: ChallengeType
    capability_id: str
    engineer_id: str | None = None
    submitted_by: str
    submitted_at: datetime

    # What actually changed in the evidence layer, named so the audit trail is readable.
    evidence_created: str | None = None
    evidence_moved: str | None = None

    # The recomputation, reported rather than requested.
    capability_before: AssessmentSnapshot
    capability_after: AssessmentSnapshot
    system_before: SystemSnapshot
    system_after: SystemSnapshot
    recomputed: bool
