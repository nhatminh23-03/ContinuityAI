"""Recompute coverage and assessments from evidence.

One implementation, used by three callers: the seed builds everything, the challenge workflow
rebuilds one capability after evidence changes, and the evaluator reads what they wrote. A second
implementation would eventually disagree with the first, and the disagreement would show up as a
number nobody could explain.

The direction of dependency is the important part:

    evidence  ──>  coverage (readiness)  ──>  capability assessment  ──>  system assessment

Nothing flows backwards. Readiness is always derived, never written directly, which is what makes
"managers cannot overwrite a score" (PRD section 21) structural rather than a matter of discipline:
there is no code path that accepts a readiness value.
"""

from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.continuity.aggregation import SystemAssessmentResult, aggregate_system
from app.continuity.exposure import CapabilityAssessmentResult, assess
from app.continuity.readiness import classify
from app.evidence.aggregation import EvidenceItem, aggregate
from app.models import (
    Capability,
    CapabilityAssessment,
    Coverage,
    Evidence,
    System,
    SystemAssessment,
)
from app.repositories import CapabilityRepository, SystemRepository
from app.services.facts import build_system_facts


def rebuild_coverage_for_capability(session: Session, capability_id: str) -> int:
    """Rebuild every coverage row for one capability from its evidence.

    Rows are deleted and rebuilt rather than patched, so an engineer whose last evidence record was
    moved elsewhere loses the coverage relationship entirely instead of keeping a stale readiness.
    """
    session.execute(delete(Coverage).where(Coverage.capability_id == capability_id))
    session.flush()

    rows = list(session.scalars(select(Evidence).where(Evidence.capability_id == capability_id)))
    buckets: dict[str, list[EvidenceItem]] = {}
    for row in rows:
        buckets.setdefault(row.engineer_id, []).append(EvidenceItem.from_row(row))

    for engineer_id, items in sorted(buckets.items()):
        session.add(_coverage_row(engineer_id, capability_id, items))
    session.flush()
    return len(buckets)


def rebuild_all_coverage(session: Session) -> int:
    """One pass over every evidence record. Used by the seed, where per-capability would be wasteful."""
    session.execute(delete(Coverage))
    session.flush()

    buckets: dict[tuple[str, str], list[EvidenceItem]] = {}
    for row in session.scalars(select(Evidence)):
        buckets.setdefault((row.engineer_id, row.capability_id), []).append(EvidenceItem.from_row(row))

    for (engineer_id, capability_id), items in sorted(buckets.items()):
        session.add(_coverage_row(engineer_id, capability_id, items))
    session.flush()
    return len(buckets)


def _coverage_row(engineer_id: str, capability_id: str, items: list[EvidenceItem]) -> Coverage:
    summary = aggregate(engineer_id, capability_id, items)
    readiness = classify(summary)
    return Coverage(
        engineer_id=engineer_id,
        capability_id=capability_id,
        readiness=readiness.readiness.value,
        freshness=summary.freshness.value,
        evidence_confidence=summary.evidence_confidence.value,
        last_demonstrated_at=summary.last_demonstrated_at,
        supporting_evidence_ids=summary.supporting_evidence_ids,
        readiness_reasons=readiness.reasons,
        aggregates=summary.as_dict(),
    )


def recompute_system(
    session: Session, system_id: str, rebuild_coverage: bool = False
) -> SystemAssessmentResult:
    """Reassess a whole system and persist the results.

    Capability assessments are written before the aggregate, because the aggregate reads them.
    """
    capabilities = CapabilityRepository(session).list_by_system(system_id)
    if rebuild_coverage:
        for capability in capabilities:
            rebuild_coverage_for_capability(session, capability.capability_id)

    facts = build_system_facts(session, system_id)
    results = {c.capability_id: assess(c) for c in facts.capabilities}

    for capability_id, result in results.items():
        _persist_capability(session, capability_id, result)

    aggregate_result = aggregate_system(facts, results)
    _persist_system(session, system_id, aggregate_result, results)
    session.flush()
    return aggregate_result


def recompute_capability(
    session: Session, capability_id: str, rebuild_coverage: bool = True
) -> tuple[CapabilityAssessmentResult, SystemAssessmentResult]:
    """Reassess one capability and roll the change up to its system.

    This is the path the challenge workflow takes. Rolling up matters: linking a missed incident to
    Incident Recovery can move the whole Payment Gateway index, and leaving the system row stale
    would make the dashboard disagree with the page the manager is looking at.
    """
    capability = session.get(Capability, capability_id)
    if capability is None:
        raise KeyError(capability_id)

    if rebuild_coverage:
        rebuild_coverage_for_capability(session, capability_id)

    system_result = recompute_system(session, capability.system_id, rebuild_coverage=False)
    capability_result = assess(
        next(
            c
            for c in build_system_facts(session, capability.system_id).capabilities
            if c.capability_id == capability_id
        )
    )
    return capability_result, system_result


def recompute_all(session: Session) -> None:
    """Everything, from evidence up. Used by the seed."""
    rebuild_all_coverage(session)
    for system in session.scalars(select(System)):
        recompute_system(session, system.system_id, rebuild_coverage=False)


def _persist_capability(
    session: Session, capability_id: str, result: CapabilityAssessmentResult
) -> None:
    row = session.get(CapabilityAssessment, capability_id) or CapabilityAssessment(
        capability_id=capability_id
    )
    row.exposure = result.exposure.value
    row.continuity_risk_index = result.continuity_risk_index
    row.continuity_risk_class = (
        result.continuity_risk_class.value if result.continuity_risk_class else None
    )
    row.evidence_confidence = result.evidence_confidence.value
    row.rules_triggered = result.rules_triggered
    row.index_modifiers = result.index_modifiers
    row.primary_engineer_id = result.primary_engineer_id
    row.best_remaining_engineer_id = result.best_remaining_engineer_id
    row.adequate_engineer_count = result.adequate_engineer_count
    session.add(row)


def _persist_system(
    session: Session,
    system_id: str,
    result: SystemAssessmentResult,
    capability_results: dict[str, CapabilityAssessmentResult],
) -> None:
    row = session.get(SystemAssessment, system_id) or SystemAssessment(system_id=system_id)
    row.exposure = result.exposure.value
    row.continuity_risk_index = result.continuity_risk_index
    row.continuity_risk_class = (
        result.continuity_risk_class.value if result.continuity_risk_class else None
    )
    row.evidence_confidence = result.evidence_confidence.value
    row.critical_gap_count = result.critical_gap_count
    row.degraded_capability_count = result.degraded_capability_count
    row.covered_capability_count = result.covered_capability_count
    row.insufficient_evidence_count = result.insufficient_evidence_count
    row.rules_triggered = result.rules_triggered

    # Declared-versus-demonstrated is judged on the capability that drives the system's risk.
    # Comparing against "whoever holds the most capabilities" would flag every system whose nominal
    # owner is not also its busiest engineer, which is a different finding entirely.
    driving = result.driving_capability_id
    strongest = (
        capability_results[driving].primary_engineer_id
        if driving and driving in capability_results
        else None
    )
    declared = SystemRepository(session).declared_owner(system_id)
    row.strongest_coverage_engineer_id = strongest
    row.declared_owner_mismatch = bool(
        declared and strongest and declared[0].engineer_id != strongest
    )
    session.add(row)
