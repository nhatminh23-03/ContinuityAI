"""Capability DTOs. docs/API_CONTRACT.md sections 6.4, 6.5 and 8.5."""

from datetime import date

from pydantic import BaseModel, Field

from .enums import (
    CapabilityExposure,
    ContinuityRiskClass,
    EvidenceConfidence,
    Freshness,
    OperationalCriticality,
    ReadinessLevel,
)


class EngineerRef(BaseModel):
    engineer_id: str
    name: str
    readiness: ReadinessLevel


class EngineerCoverage(BaseModel):
    """One engineer's demonstrated coverage of one capability.

    Carries no evidence ids by design: the evidence drawer queries
    GET /capabilities/{id}/evidence?engineer_id= instead. Contract decision CI-34.
    """

    engineer_id: str
    name: str
    readiness: ReadinessLevel
    freshness: Freshness
    evidence_confidence: EvidenceConfidence
    last_demonstrated_at: date | None = None


class IndexModifier(BaseModel):
    """One adjustment that contributed to the Continuity Risk Index.

    Added so the "Why this risk?" drawer can show *how* an index was reached rather than only which
    rules fired — the strongest available answer to "the risk score looks arbitrary" (PRD section
    30). The index is anchored on the risk class and clamped to its band, so these deltas explain
    position within a band and can never move a capability out of one.

    Optional and additive; contract decision DEC-11.
    """

    code: str
    delta: int


class CapabilityDetail(BaseModel):
    capability_id: str
    component_id: str
    system_id: str
    name: str
    description: str
    operational_criticality: OperationalCriticality
    exposure: CapabilityExposure
    continuity_risk_index: int | None = Field(default=None, ge=0, le=100)
    continuity_risk_class: ContinuityRiskClass | None = None
    evidence_confidence: EvidenceConfidence
    rules_triggered: list[str] = []
    index_modifiers: list[IndexModifier] = []
    primary_engineer: EngineerRef | None = None
    best_remaining_coverage: EngineerRef | None = None
    engineer_coverage: list[EngineerCoverage]


class CapabilityRef(BaseModel):
    capability_id: str
    name: str
