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

from app.ai.provider import extraction_provenance, get_provider  # noqa: E402
from app.ai.schemas import TaxonomyCapability  # noqa: E402
from app.core.config import settings  # noqa: E402
from app.db.session import create_all, drop_all, session_scope  # noqa: E402
from app.ingestion import (  # noqa: E402
    ingest,
    load_declared_ownership,
    load_public_github_corpus,
    load_synthetic_corpus,
)
from app.models import (  # noqa: E402
    Capability,
    Component,
    DeclaredOwnership,
    Engineer,
    Platform,
    System,
)
from app.repositories import SystemRepository  # noqa: E402
from app.services.recompute import rebuild_all_coverage, recompute_system  # noqa: E402


@dataclass
class SeedReport:
    platforms: int = 0
    systems: int = 0
    components: int = 0
    capabilities: int = 0
    engineers: int = 0
    declared_owners: int = 0
    artifacts: int = 0
    public_artifacts: int = 0
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
                f"  artifacts        {self.artifacts} "
                f"({self.artifacts - self.public_artifacts} synthetic, "
                f"{self.public_artifacts} real public GitHub)",
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


def _derive(session: Session, report: SeedReport) -> None:
    """Aggregate evidence into coverage, classify readiness, then run the continuity rules.

    Delegates to `app/services/recompute.py`, which is the same code path the challenge workflow
    uses when a manager adds evidence. One implementation means a freshly seeded baseline and a
    recomputed capability cannot disagree.

    Assessments are precomputed rather than evaluated per request (ARCHITECTURE.md section 86).
    """
    report.coverage = rebuild_all_coverage(session)
    for system in SystemRepository(session).list_all():
        recompute_system(session, system.system_id, rebuild_coverage=False)
    session.flush()


def seed(verbose: bool = True) -> SeedReport:
    report = SeedReport()
    drop_all()
    create_all()

    org = _load_org()
    # Both evidence classes the PRD calls for (section 14.1): real public GitHub activity where it
    # exists, and synthetic private enterprise records for the operational context that is never
    # public. They normalise to the same artifact shape and share one extraction path.
    synthetic = load_synthetic_corpus(settings.data_path)
    public = load_public_github_corpus(settings.data_path)
    provider = get_provider()

    with session_scope() as session:
        taxonomy = _persist_structure(session, org, report)
        _persist_declared_ownership(session, report)

        engineer_names = {e["engineer_id"]: e["name"] for e in org["engineers"]}
        ingestion = ingest(session, [*synthetic, *public], taxonomy, engineer_names, provider)
        report.artifacts = ingestion.artifacts_ingested
        report.public_artifacts = len(public)
        report.evidence = ingestion.evidence_created
        report.ingestion_summary = ingestion.summary()

        _derive(session, report)

    if verbose:
        print(report.render())
        # What produced the graph, not what AI_PROVIDER is set to. The two are not always the same
        # thing, and this line is the record of where the evidence in the database came from.
        # Extraction provenance is the one thing here that must not be quietly wrong.
        print(f"  extraction       {extraction_provenance(provider)}")

        # Under a chain the configured name is a list of candidates, not an answer: what matters is
        # which one actually extracted, per artifact. Printed as a tally so a run that started on
        # watsonx and finished on OpenRouter says exactly that, and so a run that quietly used the
        # templates cannot look like a model run.
        provenance = getattr(provider, "provenance", None)
        if provenance is not None:
            counted = provenance.extraction_providers()
            for label, count in sorted(counted.items(), key=lambda kv: -kv[1]):
                print(f"    {label:<28} {count} artifact(s)")
            if not provenance.used_a_model_for_extraction():
                print(
                    "  WARNING          no artifact was extracted by a model. This graph is "
                    "rule-derived; do not describe it as model-derived."
                )
        print(f"  database         {settings.database_url}")
    return report


def main() -> None:
    seed()


if __name__ == "__main__":
    main()
