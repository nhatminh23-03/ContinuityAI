"""Persistence models. docs/DOMAIN_MODEL.md sections 38-39.

Two groups of tables:

* **Structure and evidence** — platforms, systems, components, capabilities, engineers,
  declared ownership, raw artifacts, evidence, coverage. This is the knowledge graph,
  stored relationally and assembled into typed nodes/edges in `app/graph/`.
* **Precomputed assessments** — capability and system assessments. These are derived,
  written by the seed and by any recomputation, and read by the API. Precomputing is
  what keeps read endpoints inside the AC-14 latency target, and it is sanctioned by
  docs/ARCHITECTURE.md section 86.

Assessment rows carry more than the contract exposes: fired reason codes, the index
modifier breakdown, and evidence aggregates. That surplus is what makes a conclusion
explainable after the fact rather than merely reproducible.
"""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

# --------------------------------------------------------------------------------------
# Structure
# --------------------------------------------------------------------------------------


class Platform(Base):
    __tablename__ = "platforms"

    platform_id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(String)
    # Seeded, not computed: the MVP has no assessment history to diff against.
    # RECOMMENDATIONS.md R-04.
    drift_status: Mapped[str] = mapped_column(String, nullable=False, default="STABLE")
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    systems: Mapped[list[System]] = relationship(back_populates="platform", order_by="System.position")


class System(Base):
    __tablename__ = "systems"

    system_id: Mapped[str] = mapped_column(String, primary_key=True)
    platform_id: Mapped[str] = mapped_column(ForeignKey("platforms.platform_id"), nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(String)
    business_criticality: Mapped[str] = mapped_column(String, nullable=False)
    criticality_source: Mapped[str] = mapped_column(String, nullable=False, default="HUMAN_CONFIRMED")
    drift_status: Mapped[str] = mapped_column(String, nullable=False, default="STABLE")
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    platform: Mapped[Platform] = relationship(back_populates="systems")
    components: Mapped[list[Component]] = relationship(
        back_populates="system", order_by="Component.position"
    )


class Component(Base):
    __tablename__ = "components"

    component_id: Mapped[str] = mapped_column(String, primary_key=True)
    system_id: Mapped[str] = mapped_column(ForeignKey("systems.system_id"), nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(String)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    system: Mapped[System] = relationship(back_populates="components")
    capabilities: Mapped[list[Capability]] = relationship(
        back_populates="component", order_by="Capability.position"
    )


class Capability(Base):
    __tablename__ = "capabilities"

    capability_id: Mapped[str] = mapped_column(String, primary_key=True)
    component_id: Mapped[str] = mapped_column(ForeignKey("components.component_id"), nullable=False)
    # Denormalised. Every capability belongs to exactly one system through its component
    # (DOMAIN_MODEL.md section 9.2), and carrying it here avoids a join on the hottest
    # query in the product.
    system_id: Mapped[str] = mapped_column(ForeignKey("systems.system_id"), nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    operational_criticality: Mapped[str] = mapped_column(String, nullable=False)
    runbook_state: Mapped[str] = mapped_column(String, nullable=False, default="NOT_ASSESSED")
    # Surface forms the extraction layer matches artifact text against.
    aliases: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    component: Mapped[Component] = relationship(back_populates="capabilities")


class Engineer(Base):
    __tablename__ = "engineers"

    engineer_id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[str | None] = mapped_column(String)
    team: Mapped[str | None] = mapped_column(String)

    # There is deliberately no score, rating, ranking, or value column here, and adding
    # one is prohibited by DOMAIN_MODEL.md section 10.2. `tests/test_responsible_ai.py`
    # asserts this table's columns against an allowlist.


class DeclaredOwnership(Base):
    """Formal ownership from CODEOWNERS or a service catalogue.

    Kept separate from demonstrated coverage and never merged into it
    (DOMAIN_MODEL.md section 35). The gap between the two is the demo's opening beat.
    """

    __tablename__ = "declared_ownership"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    system_id: Mapped[str] = mapped_column(ForeignKey("systems.system_id"), nullable=False)
    engineer_id: Mapped[str] = mapped_column(ForeignKey("engineers.engineer_id"), nullable=False)
    source_reference: Mapped[str] = mapped_column(String, nullable=False, default="CODEOWNERS")

    __table_args__ = (UniqueConstraint("system_id", "engineer_id", name="uq_declared_owner"),)


# --------------------------------------------------------------------------------------
# Evidence pipeline
# --------------------------------------------------------------------------------------


class Artifact(Base):
    """A normalised source record, before interpretation. DOMAIN_MODEL.md section 13.

    Retained after extraction so a provenance card can quote the original and so
    extraction can be re-run without re-ingesting.
    """

    __tablename__ = "artifacts"

    artifact_id: Mapped[str] = mapped_column(String, primary_key=True)
    source_type: Mapped[str] = mapped_column(String, nullable=False)
    source_reference: Mapped[str] = mapped_column(String, nullable=False)
    title: Mapped[str | None] = mapped_column(String)
    body: Mapped[str] = mapped_column(Text, nullable=False, default="")
    artifact_date: Mapped[date] = mapped_column(Date, nullable=False)
    # [{"engineer_id": ..., "participant_role": ...}] — from the source system, not inferred.
    participants: Mapped[list[dict]] = mapped_column(JSON, nullable=False, default=list)
    system_hint: Mapped[str | None] = mapped_column(String)
    file_paths: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    provenance_source: Mapped[str] = mapped_column(String, nullable=False)
    source_url: Mapped[str | None] = mapped_column(String)
    extra: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)


class Evidence(Base):
    """One interpreted claim: this engineer, this capability, this role, this strength."""

    __tablename__ = "evidence"

    evidence_id: Mapped[str] = mapped_column(String, primary_key=True)
    artifact_id: Mapped[str] = mapped_column(ForeignKey("artifacts.artifact_id"), nullable=False)
    source_type: Mapped[str] = mapped_column(String, nullable=False)
    source_reference: Mapped[str] = mapped_column(String, nullable=False)
    source_title: Mapped[str | None] = mapped_column(String)
    artifact_date: Mapped[date] = mapped_column(Date, nullable=False)
    engineer_id: Mapped[str] = mapped_column(ForeignKey("engineers.engineer_id"), nullable=False)
    system_id: Mapped[str] = mapped_column(ForeignKey("systems.system_id"), nullable=False)
    component_id: Mapped[str | None] = mapped_column(ForeignKey("components.component_id"))
    capability_id: Mapped[str] = mapped_column(ForeignKey("capabilities.capability_id"), nullable=False)
    evidence_role: Mapped[str] = mapped_column(String, nullable=False)
    evidence_strength: Mapped[str] = mapped_column(String, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    freshness: Mapped[str] = mapped_column(String, nullable=False)
    provenance_source: Mapped[str] = mapped_column(String, nullable=False)
    provenance_record_id: Mapped[str] = mapped_column(String, nullable=False)
    provenance_url: Mapped[str | None] = mapped_column(String)
    # How confident the extraction step was in this record. Separate from the aggregate
    # Evidence Confidence on a coverage relationship.
    extraction_confidence: Mapped[str] = mapped_column(String, nullable=False, default="MEDIUM")
    # Marks evidence that materially contradicts the rest, e.g. a reverted recovery
    # attempt. Surfaces as `conflicting_evidence` and depresses evidence confidence.
    is_conflicting: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    extraction_rationale: Mapped[str] = mapped_column(Text, nullable=False, default="")


class Coverage(Base):
    """`Engineer --DEMONSTRATES--> Capability`. DOMAIN_MODEL.md section 11.

    Readiness here is always computed from the evidence rows referenced by
    `supporting_evidence_ids`. It is never written directly by a user and never by the
    AI layer (invariants 3 and 4, DOMAIN_MODEL.md section 47).
    """

    __tablename__ = "engineer_capability_coverage"

    engineer_id: Mapped[str] = mapped_column(ForeignKey("engineers.engineer_id"), primary_key=True)
    capability_id: Mapped[str] = mapped_column(
        ForeignKey("capabilities.capability_id"), primary_key=True
    )
    readiness: Mapped[str] = mapped_column(String, nullable=False)
    freshness: Mapped[str] = mapped_column(String, nullable=False)
    evidence_confidence: Mapped[str] = mapped_column(String, nullable=False)
    last_demonstrated_at: Mapped[date | None] = mapped_column(Date)
    supporting_evidence_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    # Why this readiness, in machine-readable form, for the "Why?" drawer.
    readiness_reasons: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    # strong/moderate/weak counts, source-type count, per-role counts.
    aggregates: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)


# --------------------------------------------------------------------------------------
# Precomputed assessments
# --------------------------------------------------------------------------------------


class CapabilityAssessment(Base):
    __tablename__ = "capability_assessments"

    capability_id: Mapped[str] = mapped_column(
        ForeignKey("capabilities.capability_id"), primary_key=True
    )
    exposure: Mapped[str] = mapped_column(String, nullable=False)
    continuity_risk_index: Mapped[int | None] = mapped_column(Integer)
    continuity_risk_class: Mapped[str | None] = mapped_column(String)
    evidence_confidence: Mapped[str] = mapped_column(String, nullable=False)
    rules_triggered: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    # [{"code": ..., "delta": ...}] — the arithmetic behind the index, so the number is
    # inspectable rather than merely asserted. Not currently on the wire; see
    # RECOMMENDATIONS.md R-03.
    index_modifiers: Mapped[list[dict]] = mapped_column(JSON, nullable=False, default=list)
    primary_engineer_id: Mapped[str | None] = mapped_column(String)
    best_remaining_engineer_id: Mapped[str | None] = mapped_column(String)
    adequate_engineer_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class TaxonomyProposalRow(Base):
    """A concept a model proposed that the taxonomy does not contain. FR-005.

    Its own table, and pointedly not a row in `capabilities`. A proposal has no evidence, no engineer,
    and no assessment; nothing in `app/continuity/` reads this table. That is what lets the product ask
    a model to name concepts it was not given while keeping extraction closed-world — the two would
    otherwise contradict each other.

    Promotion into `capabilities` is a human act. `status` exists so "flagged for review" is a state a
    proposal can be in and move out of, rather than a label with nothing behind it.
    """

    __tablename__ = "taxonomy_proposals"

    proposal_id: Mapped[str] = mapped_column(String, primary_key=True)
    kind: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    system_id: Mapped[str | None] = mapped_column(String)
    component_id: Mapped[str | None] = mapped_column(String)
    rationale: Mapped[str] = mapped_column(Text, nullable=False, default="")
    # The model's own confidence. LOW is the FR-005 review flag, not a reason to discard.
    confidence: Mapped[str] = mapped_column(String, nullable=False, default="LOW")
    status: Mapped[str] = mapped_column(String, nullable=False, default="PROPOSED")
    # Provenance, on the same terms as any claim (FR-006): a reviewer reads the artifact, not the
    # proposal's word for it.
    source_reference: Mapped[str | None] = mapped_column(String)
    artifact_id: Mapped[str | None] = mapped_column(ForeignKey("artifacts.artifact_id"))
    # Which provider proposed it, so a bad run can be traced to a model rather than to the taxonomy.
    proposed_by: Mapped[str] = mapped_column(String, nullable=False, default="")
    # How many artifacts independently suggested the same concept. A concept seen once is a guess;
    # seen repeatedly it is a gap in the taxonomy, and that is the signal worth sorting a review by.
    occurrences: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    __table_args__ = (UniqueConstraint("kind", "name", "system_id", name="uq_taxonomy_proposal"),)


class SystemAssessment(Base):
    __tablename__ = "system_assessments"

    system_id: Mapped[str] = mapped_column(ForeignKey("systems.system_id"), primary_key=True)
    exposure: Mapped[str] = mapped_column(String, nullable=False)
    continuity_risk_index: Mapped[int | None] = mapped_column(Integer)
    continuity_risk_class: Mapped[str | None] = mapped_column(String)
    evidence_confidence: Mapped[str] = mapped_column(String, nullable=False)
    critical_gap_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    degraded_capability_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    covered_capability_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    insufficient_evidence_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    rules_triggered: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    declared_owner_mismatch: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    strongest_coverage_engineer_id: Mapped[str | None] = mapped_column(String)


# --------------------------------------------------------------------------------------
# Workflow objects
# --------------------------------------------------------------------------------------


class Simulation(Base):
    __tablename__ = "simulations"

    simulation_id: Mapped[str] = mapped_column(String, primary_key=True)
    simulation_type: Mapped[str] = mapped_column(String, nullable=False)
    engineer_id: Mapped[str] = mapped_column(ForeignKey("engineers.engineer_id"), nullable=False)
    scope_type: Mapped[str] = mapped_column(String, nullable=False)
    scope_id: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    # The full response DTO. A simulation is a point-in-time answer; storing the result
    # verbatim means a later evidence change cannot silently rewrite history.
    result_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)


class MitigationPlan(Base):
    __tablename__ = "mitigation_plans"

    plan_id: Mapped[str] = mapped_column(String, primary_key=True)
    capability_id: Mapped[str] = mapped_column(ForeignKey("capabilities.capability_id"), nullable=False)
    system_id: Mapped[str] = mapped_column(ForeignKey("systems.system_id"), nullable=False)
    source_engineer_id: Mapped[str] = mapped_column(ForeignKey("engineers.engineer_id"), nullable=False)
    selected_backup_engineer_id: Mapped[str] = mapped_column(
        ForeignKey("engineers.engineer_id"), nullable=False
    )
    simulation_id: Mapped[str | None] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, nullable=False, default="DRAFT")
    target_readiness: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime)
    approved_by: Mapped[str | None] = mapped_column(String)

    tasks: Mapped[list[MitigationTask]] = relationship(
        back_populates="plan", order_by="MitigationTask.sequence", cascade="all, delete-orphan"
    )


class AssessmentChallenge(Base):
    """Audit trail for a manager disputing an assessment. PRD section 21, DOMAIN_MODEL section 33.

    Stores the previous assessment, the stated reason, what changed in the evidence layer, and the
    new result. That record is the point: an assessment that can be corrected but not audited is
    worse than one that cannot be corrected at all, because nobody can later ask why it moved.

    There is deliberately no column here for a readiness level or a risk index. A manager changes
    evidence; the rules recompute the rest.
    """

    __tablename__ = "assessment_challenges"

    challenge_id: Mapped[str] = mapped_column(String, primary_key=True)
    capability_id: Mapped[str] = mapped_column(
        ForeignKey("capabilities.capability_id"), nullable=False
    )
    engineer_id: Mapped[str | None] = mapped_column(ForeignKey("engineers.engineer_id"))
    challenge_type: Mapped[str] = mapped_column(String, nullable=False)
    comment: Mapped[str] = mapped_column(Text, nullable=False)
    submitted_by: Mapped[str] = mapped_column(String, nullable=False)
    submitted_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    evidence_created_id: Mapped[str | None] = mapped_column(String)
    evidence_moved_id: Mapped[str | None] = mapped_column(String)
    moved_from_capability_id: Mapped[str | None] = mapped_column(String)

    # Full before/after snapshots, so the trail survives later recomputations.
    previous_assessment: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    new_assessment: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)


class MitigationTask(Base):
    """A task identifier is scoped to its plan, not globally unique.

    The contract's task ids are `task_001`, `task_002`, ... within a plan (section 8.9), so the
    primary key is composite. A globally unique id would either force `plan_001_task_001` onto the
    wire or make the second plan collide with the first.
    """

    __tablename__ = "mitigation_tasks"

    plan_id: Mapped[str] = mapped_column(
        ForeignKey("mitigation_plans.plan_id"), primary_key=True, nullable=False
    )
    task_id: Mapped[str] = mapped_column(String, primary_key=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[str] = mapped_column(String, nullable=False)
    # Wire ordering is array order; `sequence` keeps it stable across a round-trip.
    # Contract decision CI-23.
    sequence: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    acceptance_criteria: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    linked_evidence_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)

    plan: Mapped[MitigationPlan] = relationship(back_populates="tasks")
