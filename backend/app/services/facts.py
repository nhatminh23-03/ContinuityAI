"""Build continuity facts from persistence.

One loader, used by the read endpoints, the simulator, the candidate engine, and the seed. The
alternative — each caller assembling its own view — is how a baseline and its counterfactual end
up disagreeing about the same graph.

The facts are plain frozen objects (`app/continuity/facts.py`) with no session attached, so once
loaded they can be recombined freely, including with one engineer filtered out.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.continuity.facts import CapabilityFacts, CoverageFact, SystemFacts
from app.core.errors import NotFoundError
from app.models.enums import RunbookState
from app.repositories import (
    CapabilityRepository,
    CoverageRepository,
    EngineerRepository,
    EvidenceRepository,
    SystemRepository,
)
from app.schemas.enums import (
    EvidenceConfidence,
    Freshness,
    OperationalCriticality,
    ReadinessLevel,
)


def _coverage_fact(row, engineer_names: dict[str, str]) -> CoverageFact:
    return CoverageFact(
        engineer_id=row.engineer_id,
        engineer_name=engineer_names.get(row.engineer_id, row.engineer_id),
        readiness=ReadinessLevel(row.readiness),
        freshness=Freshness(row.freshness),
        evidence_confidence=EvidenceConfidence(row.evidence_confidence),
        evidence_count=len(row.supporting_evidence_ids or []),
        last_demonstrated_at=row.last_demonstrated_at,
    )


def build_system_facts(session: Session, system_id: str) -> SystemFacts:
    system = SystemRepository(session).get(system_id)
    if system is None:
        raise NotFoundError(f"System '{system_id}' not found.", {"system_id": system_id})

    capabilities = CapabilityRepository(session).list_by_system(system_id)
    coverages = CoverageRepository(session).list_by_system(system_id)
    engineer_names = {e.engineer_id: e.name for e in EngineerRepository(session).list_all()}
    counts = EvidenceRepository(session).counts_by_capability(system_id)

    by_capability: dict[str, list[CoverageFact]] = {}
    for row in coverages:
        by_capability.setdefault(row.capability_id, []).append(_coverage_fact(row, engineer_names))

    capability_facts = tuple(
        CapabilityFacts(
            capability_id=capability.capability_id,
            name=capability.name,
            component_id=capability.component_id,
            system_id=capability.system_id,
            operational_criticality=OperationalCriticality(capability.operational_criticality),
            runbook_state=RunbookState(capability.runbook_state),
            coverages=tuple(by_capability.get(capability.capability_id, [])),
            total_evidence_count=counts.get(capability.capability_id, (0, 0))[0],
            conflicting_evidence_count=counts.get(capability.capability_id, (0, 0))[1],
        )
        for capability in capabilities
    )

    return SystemFacts(
        system_id=system.system_id,
        name=system.name,
        platform_id=system.platform_id,
        business_criticality=system.business_criticality,
        capabilities=capability_facts,
    )


def build_capability_facts(session: Session, capability_id: str) -> CapabilityFacts:
    capability = CapabilityRepository(session).get(capability_id)
    if capability is None:
        raise NotFoundError(
            f"Capability '{capability_id}' not found.", {"capability_id": capability_id}
        )

    coverages = CoverageRepository(session).list_by_capability(capability_id)
    engineer_names = {e.engineer_id: e.name for e in EngineerRepository(session).list_all()}
    total, conflicting = EvidenceRepository(session).counts_by_capability().get(capability_id, (0, 0))

    return CapabilityFacts(
        capability_id=capability.capability_id,
        name=capability.name,
        component_id=capability.component_id,
        system_id=capability.system_id,
        operational_criticality=OperationalCriticality(capability.operational_criticality),
        runbook_state=RunbookState(capability.runbook_state),
        coverages=tuple(_coverage_fact(row, engineer_names) for row in coverages),
        total_evidence_count=total,
        conflicting_evidence_count=conflicting,
    )
