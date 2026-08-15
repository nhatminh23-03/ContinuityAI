"""Build the demo database from scratch. docs/ARCHITECTURE.md section 88.

    python -m scripts.seed_demo            # from backend/
    python backend/scripts/seed_demo.py    # from the repository root

One command, deterministic, idempotent: it drops and rebuilds every table, so a clean clone and a
twentieth reseed produce identical output (PRD AC-15).

The pipeline, in order — each stage consuming only the stage above it:

    data/org/            structure: platforms, systems, components, capabilities, engineers
    data/synthetic/      artifacts + CODEOWNERS
         │
         ├─ ingestion ──────────> Artifact rows
         ├─ AI extraction ──────> Evidence rows          (app/ai/, validated)
         ├─ aggregation ────────> Coverage rows          (app/evidence/ + app/continuity/readiness)
         ├─ exposure rules ─────> CapabilityAssessment   (app/continuity/exposure)
         └─ aggregation ────────> SystemAssessment       (app/continuity/aggregation)

Readiness is recomputed here from evidence every time. It is never loaded from a file, and the
hidden ground truth is not read at any point in this script — only the artifacts the generator
produced from it.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT / "backend") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "backend"))

from sqlalchemy.orm import Session  # noqa: E402

from app.ai.provider import get_provider  # noqa: E402
from app.ai.schemas import TaxonomyCapability  # noqa: E402
from app.continuity.aggregation import aggregate_system  # noqa: E402
from app.continuity.exposure import assess  # noqa: E402
from app.continuity.readiness import classify  # noqa: E402
from app.core.config import settings  # noqa: E402
from app.db.session import create_all, drop_all, session_scope  # noqa: E402
from app.evidence.aggregation import EvidenceItem, aggregate  # noqa: E402
from app.ingestion import ingest, load_declared_ownership, load_synthetic_corpus  # noqa: E402
from app.models import (  # noqa: E402
    Capability,
    CapabilityAssessment,
    Component,
    Coverage,
    DeclaredOwnership,
    Engineer,
    Evidence,
    Platform,
    System,
    SystemAssessment,
)
from app.repositories import CapabilityRepository, SystemRepository  # noqa: E402
from app.services.facts import build_system_facts  # noqa: E402


@dataclass
class SeedReport:
    platforms: int = 0
    systems: int = 0
    components: int = 0
    capabilities: int = 0
    engineers: int = 0
    declared_owners: int = 0
    artifacts: int = 0
    evidence: int = 0
    coverage: int = 0
    ingestion_summary: str = ""

    def render(self) -> str:
        return "\n".join(
            [
                "seed complete",
                f"  platforms        {self.platforms}",
                f"  systems          {self.systems}",
                f"  components       {self.components}",
                f"  capabilities     {self.capabilities}",
                f"  engineers        {self.engineers}",
                f"  declared owners  {self.declared_owners}",
                f"  artifacts        {self.artifacts}",
                f"  evidence         {self.evidence}",
                f"  coverage edges   {self.coverage}",
                f"  {self.ingestion_summary}",
            ]
        )


def _load_org() -> dict:
    path = settings.data_path / "org" / "novapay.json"
    if not path.exists():
        raise FileNotFoundError(f"{path} is missing.")
    return json.loads(path.read_text())


def _persist_structure(session: Session, org: dict, report: SeedReport) -> list[TaxonomyCapability]:
    taxonomy: list[TaxonomyCapability] = []

    for engineer in org["engineers"]:
        session.add(
            Engineer(
                engineer_id=engineer["engineer_id"],
                name=engineer["name"],
                role=engineer.get("role"),
                team=engineer.get("team"),
            )
        )
        report.engineers += 1

    for platform_position, platform in enumerate(org["platforms"]):
        session.add(
            Platform(
                platform_id=platform["platform_id"],
                name=platform["name"],
                description=platform.get("description"),
                drift_status=platform.get("drift_status", "STABLE"),
                position=platform_position,
            )
        )
        report.platforms += 1

        for system_position, system in enumerate(platform["systems"]):
            session.add(
                System(
                    system_id=system["system_id"],
                    platform_id=platform["platform_id"],
                    name=system["name"],
                    description=system.get("description"),
                    business_criticality=system["business_criticality"],
                    criticality_source=system.get("criticality_source", "HUMAN_CONFIRMED"),
                    drift_status=system.get("drift_status", "STABLE"),
                    position=system_position,
                )
            )
            report.systems += 1

            for component_position, component in enumerate(system["components"]):
                session.add(
                    Component(
                        component_id=component["component_id"],
                        system_id=system["system_id"],
                        name=component["name"],
                        description=component.get("description"),
                        position=component_position,
                    )
                )
                report.components += 1

                for capability_position, capability in enumerate(component["capabilities"]):
                    session.add(
                        Capability(
                            capability_id=capability["capability_id"],
                            component_id=component["component_id"],
                            system_id=system["system_id"],
                            name=capability["name"],
                            description=capability.get("description", ""),
                            operational_criticality=capability["operational_criticality"],
                            runbook_state=capability.get("runbook_state", "NOT_ASSESSED"),
                            aliases=capability.get("aliases", []),
                            position=capability_position,
                        )
                    )
                    report.capabilities += 1
                    taxonomy.append(
                        TaxonomyCapability(
                            capability_id=capability["capability_id"],
                            name=capability["name"],
                            aliases=capability.get("aliases", []),
                            system_id=system["system_id"],
                            component_id=component["component_id"],
                        )
                    )

    session.flush()
    return taxonomy


def _persist_declared_ownership(session: Session, report: SeedReport) -> None:
    for entry in load_declared_ownership(settings.data_path):
        session.add(
            DeclaredOwnership(
                system_id=entry["system_id"],
                engineer_id=entry["engineer_id"],
                source_reference=entry.get("source_reference", "CODEOWNERS"),
            )
        )
        report.declared_owners += 1
    session.flush()


def _build_coverage(session: Session, report: SeedReport) -> None:
    """Aggregate evidence into coverage, then classify readiness from the aggregate.

    Readiness is derived here and only here. Nothing writes a readiness value directly, which is
    what makes DOMAIN_MODEL.md invariant 4 ("users cannot edit readiness") structural rather than
    a convention.
    """
    buckets: dict[tuple[str, str], list[EvidenceItem]] = {}
    for row in session.query(Evidence).all():
        buckets.setdefault((row.engineer_id, row.capability_id), []).append(EvidenceItem.from_row(row))

    for (engineer_id, capability_id), items in sorted(buckets.items()):
        summary = aggregate(engineer_id, capability_id, items)
        readiness = classify(summary)
        session.add(
            Coverage(
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
        )
        report.coverage += 1
    session.flush()


def _assess(session: Session) -> None:
    """Run the continuity rules and persist the results.

    Precomputed rather than evaluated per request (ARCHITECTURE.md section 86). The simulator
    recomputes in memory from the same facts, so a precomputed baseline and a live counterfactual
    cannot disagree.
    """
    systems = SystemRepository(session)
    capabilities = CapabilityRepository(session)

    for system in systems.list_all():
        facts = build_system_facts(session, system.system_id)
        results = {c.capability_id: assess(c) for c in facts.capabilities}

        for capability_id, result in results.items():
            session.add(
                CapabilityAssessment(
                    capability_id=capability_id,
                    exposure=result.exposure.value,
                    continuity_risk_index=result.continuity_risk_index,
                    continuity_risk_class=(
                        result.continuity_risk_class.value if result.continuity_risk_class else None
                    ),
                    evidence_confidence=result.evidence_confidence.value,
                    rules_triggered=result.rules_triggered,
                    index_modifiers=result.index_modifiers,
                    primary_engineer_id=result.primary_engineer_id,
                    best_remaining_engineer_id=result.best_remaining_engineer_id,
                    adequate_engineer_count=result.adequate_engineer_count,
                )
            )

        aggregate_result = aggregate_system(facts, results)

        # Declared-versus-demonstrated is judged on the capability that drives the system's risk.
        # Comparing against "whoever holds the most capabilities" would flag every system where the
        # nominal owner is not also the busiest engineer, which is not the same finding at all.
        driving = aggregate_result.driving_capability_id
        strongest = results[driving].primary_engineer_id if driving in results else None
        declared = systems.declared_owner(system.system_id)
        mismatch = bool(declared and strongest and declared[0].engineer_id != strongest)

        session.add(
            SystemAssessment(
                system_id=system.system_id,
                exposure=aggregate_result.exposure.value,
                continuity_risk_index=aggregate_result.continuity_risk_index,
                continuity_risk_class=(
                    aggregate_result.continuity_risk_class.value
                    if aggregate_result.continuity_risk_class
                    else None
                ),
                evidence_confidence=aggregate_result.evidence_confidence.value,
                critical_gap_count=aggregate_result.critical_gap_count,
                degraded_capability_count=aggregate_result.degraded_capability_count,
                covered_capability_count=aggregate_result.covered_capability_count,
                insufficient_evidence_count=aggregate_result.insufficient_evidence_count,
                rules_triggered=aggregate_result.rules_triggered,
                declared_owner_mismatch=mismatch,
                strongest_coverage_engineer_id=strongest,
            )
        )
    session.flush()
    _ = capabilities  # repository retained for symmetry with the read path


def seed(verbose: bool = True) -> SeedReport:
    report = SeedReport()
    drop_all()
    create_all()

    org = _load_org()
    artifacts = load_synthetic_corpus(settings.data_path)
    provider = get_provider()

    with session_scope() as session:
        taxonomy = _persist_structure(session, org, report)
        _persist_declared_ownership(session, report)

        engineer_names = {e["engineer_id"]: e["name"] for e in org["engineers"]}
        ingestion = ingest(session, artifacts, taxonomy, engineer_names, provider)
        report.artifacts = ingestion.artifacts_ingested
        report.evidence = ingestion.evidence_created
        report.ingestion_summary = ingestion.summary()

        _build_coverage(session, report)
        _assess(session)

    if verbose:
        print(report.render())
        print(f"  provider         {provider.name}")
        print(f"  database         {settings.database_url}")
    return report


def main() -> None:
    seed()


if __name__ == "__main__":
    main()
