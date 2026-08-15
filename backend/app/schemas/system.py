"""System DTOs. docs/API_CONTRACT.md sections 6.2, 6.3, 8.2 and 8.3."""

from pydantic import BaseModel, Field

from .enums import (
    BusinessCriticality,
    CapabilityExposure,
    ContinuityRiskClass,
    CriticalitySource,
    EvidenceConfidence,
    KnowledgeDriftStatus,
)
from .platform import PlatformRef


class SystemSummary(BaseModel):
    system_id: str
    platform_id: str
    name: str
    description: str | None = None
    business_criticality: BusinessCriticality
    continuity_risk_index: int | None = Field(default=None, ge=0, le=100)
    continuity_risk_class: ContinuityRiskClass | None = None
    exposure: CapabilityExposure
    evidence_confidence: EvidenceConfidence
    critical_gap_count: int = Field(ge=0)
    degraded_capability_count: int = Field(ge=0)
    covered_capability_count: int = Field(ge=0)
    insufficient_evidence_count: int = Field(ge=0)
    drift_status: KnowledgeDriftStatus


class SystemListResponse(BaseModel):
    platform: PlatformRef
    systems: list[SystemSummary]


class ComponentSummary(BaseModel):
    component_id: str
    name: str
    description: str | None = None
    capability_ids: list[str]


class DeclaredOwnership(BaseModel):
    """Declared ownership is not demonstrated coverage. Contract decision CI-07."""

    engineer_id: str
    name: str
    source: str
    mismatch_detected: bool


class SystemDetail(SystemSummary):
    criticality_source: CriticalitySource | None = None
    rules_triggered: list[str] = []
    declared_ownership: DeclaredOwnership | None = None
    components: list[ComponentSummary]
