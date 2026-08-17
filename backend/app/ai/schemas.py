"""The AI extraction contract. docs/ARCHITECTURE.md sections 19-22.

The boundary this file enforces is the product's central architectural rule: AI interprets
what an artifact *demonstrates*; it never emits readiness, exposure, continuity risk, a chosen
candidate, or anything about a person's worth. Those are downstream deterministic decisions.

Two output shapes for extraction exist in the specifications and they are not compatible:

* `ARCHITECTURE.md` section 21 returns a list of per-capability records, each carrying its own
  engineer and evidence role.
* `API_CONTRACT.md` section 10.2 returns a flat array of capability strings with a single
  `engineer_id` and a single `evidence_role` for the whole artifact.

This module implements the section 21 shape. The section 10.2 shape cannot express the hero
artifact, where one incident shows Alex resolving independently and Maria assisting — a single
role per artifact would have to discard one of them. Logged as a contract amendment in
docs/DECISIONS.md (DEC-06). Nothing on the wire changes: extraction output is internal.
"""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field, field_validator

from app.schemas.enums import (
    EvidenceConfidence,
    EvidenceRole,
    EvidenceSourceType,
    EvidenceStrength,
)


class ArtifactParticipant(BaseModel):
    """A participant as the *source system* recorded them.

    This is metadata, not inference. Incident platforms record who resolved and who assisted;
    review systems record author and reviewer. Interpreting those into an `EvidenceRole` is the
    extraction step's job.
    """

    engineer_id: str
    participant_role: str


class ArtifactInput(BaseModel):
    """One normalised artifact, ready for interpretation. DOMAIN_MODEL.md section 13."""

    artifact_id: str
    source_type: EvidenceSourceType
    source_reference: str
    title: str | None = None
    body: str = ""
    artifact_date: date
    participants: list[ArtifactParticipant] = Field(default_factory=list)
    system_hint: str | None = None
    file_paths: list[str] = Field(default_factory=list)
    provenance_source: str
    source_url: str | None = None


class TaxonomyCapability(BaseModel):
    """What a provider is allowed to attribute evidence to.

    Extraction is closed-world by design: a provider may only return capabilities present in
    the taxonomy it was given. That is what stops a language model from inventing a plausible
    capability, which FR-005 and section 15.4 of the PRD both prohibit.
    """

    capability_id: str
    name: str
    aliases: list[str] = Field(default_factory=list)
    system_id: str
    component_id: str


class CapabilityClaim(BaseModel):
    """One claim: this engineer, this capability, this role, this strength."""

    capability_id: str
    engineer_id: str
    evidence_role: EvidenceRole
    evidence_strength: EvidenceStrength
    summary: str
    rationale: str
    extraction_confidence: EvidenceConfidence = EvidenceConfidence.MEDIUM
    is_conflicting: bool = False

    @field_validator("summary", "rationale")
    @classmethod
    def _non_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("summary and rationale must be non-empty: every claim is cited")
        return value


class ArtifactExtraction(BaseModel):
    """Structured result for one artifact. May legitimately contain zero claims.

    Returning nothing is a valid, expected answer — most artifacts in a real repository
    demonstrate no operational capability at all.
    """

    artifact_id: str
    system_id: str | None = None
    component_id: str | None = None
    claims: list[CapabilityClaim] = Field(default_factory=list)
    ambiguity: list[str] = Field(default_factory=list)
    possible_taxonomy_duplicates: list[str] = Field(default_factory=list)


class SimulationSummaryContext(BaseModel):
    """Deterministic facts a provider may narrate. It receives no free rein."""

    engineer_name: str
    scope_name: str
    critical_gap_capabilities: list[str] = Field(default_factory=list)
    degraded_capabilities: list[str] = Field(default_factory=list)
    preserved_capabilities: list[str] = Field(default_factory=list)
    risk_class_before: str
    risk_class_after: str


class CandidateNarrativeContext(BaseModel):
    capability_name: str
    candidate_name: str
    technical_overlap: str
    # Kept apart on purpose. Phrasing assisted participation as "demonstrated" would overstate
    # it, and overstating is the failure mode the whole product is built to avoid.
    demonstrated_capabilities: list[str] = Field(default_factory=list)
    assisted_capabilities: list[str] = Field(default_factory=list)
    missing_capabilities: list[str] = Field(default_factory=list)


class CandidateNarrative(BaseModel):
    strengths: list[str] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)


class PlanTaskDraft(BaseModel):
    title: str
    description: str
    task_type: str
    acceptance_criteria: list[str] = Field(default_factory=list)
    linked_evidence_ids: list[str] = Field(default_factory=list)


class PlanContext(BaseModel):
    capability_name: str
    system_name: str
    component_name: str
    source_engineer_name: str
    candidate_name: str
    candidate_readiness: str
    target_readiness: str
    missing_capabilities: list[str] = Field(default_factory=list)
    reference_evidence: list[dict] = Field(default_factory=list)


class PlanDraft(BaseModel):
    target_readiness: str
    tasks: list[PlanTaskDraft] = Field(default_factory=list)
