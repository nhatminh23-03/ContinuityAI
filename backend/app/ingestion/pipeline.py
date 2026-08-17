"""The ingestion pipeline. docs/ARCHITECTURE.md section 18.

    Source artifact -> adapter -> RawArtifact -> AI extraction -> validation -> Evidence

Every stage is observable. The report returned at the end records how many artifacts produced no
claims, how many claims were rejected and why, and how many strengths were corrected — the
numbers that tell you whether extraction is working, as opposed to whether it ran.

Evidence identifiers are derived, not allocated at random:

    first claim from an artifact   evidence_inc_184
    subsequent claims             evidence_inc_184_2, _3, ...

sorted by `(capability_id, engineer_id)`. That makes the identifier a stable function of the
corpus, which is what lets the frozen fixtures reference `evidence_inc_184` and keep referencing
it after a reseed.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from app.ai.provider import AIProvider, ExtractionContext
from app.ai.schemas import ArtifactInput, TaxonomyCapability
from app.ai.validation import validate_extraction
from app.core.errors import AIExtractionError
from app.evidence.freshness import freshness_for
from app.ingestion.adapters import normalise_reference
from app.models import Artifact, Evidence


@dataclass
class IngestionReport:
    artifacts_ingested: int = 0
    artifacts_without_claims: int = 0
    evidence_created: int = 0
    claims_rejected: list[str] = field(default_factory=list)
    strengths_corrected: list[str] = field(default_factory=list)
    ambiguities: list[str] = field(default_factory=list)

    def summary(self) -> str:
        return (
            f"{self.artifacts_ingested} artifacts -> {self.evidence_created} evidence records "
            f"({self.artifacts_without_claims} artifacts yielded nothing, "
            f"{len(self.claims_rejected)} claims rejected, "
            f"{len(self.strengths_corrected)} strengths corrected)"
        )


def ingest(
    session: Session,
    artifacts: list[ArtifactInput],
    taxonomy: list[TaxonomyCapability],
    engineer_names: dict[str, str],
    provider: AIProvider,
) -> IngestionReport:
    report = IngestionReport()
    context = ExtractionContext(capabilities=taxonomy, engineer_names=engineer_names)
    taxonomy_index = context.taxonomy_index()
    known_engineer_ids = set(engineer_names)

    for artifact in artifacts:
        session.add(
            Artifact(
                artifact_id=artifact.artifact_id,
                source_type=artifact.source_type.value,
                source_reference=artifact.source_reference,
                title=artifact.title,
                body=artifact.body,
                artifact_date=artifact.artifact_date,
                participants=[p.model_dump() for p in artifact.participants],
                system_hint=artifact.system_hint,
                file_paths=artifact.file_paths,
                provenance_source=artifact.provenance_source,
                source_url=artifact.source_url,
                extra={},
            )
        )
        report.artifacts_ingested += 1

        try:
            extraction = provider.extract_artifact_semantics(artifact, context)
        except Exception as exc:  # a provider failure must not corrupt the graph
            raise AIExtractionError(
                f"Extraction failed for {artifact.source_reference}.",
                {"artifact_id": artifact.artifact_id, "provider": getattr(provider, "name", "?")},
            ) from exc

        outcome = validate_extraction(extraction, artifact, taxonomy_index, known_engineer_ids)
        report.claims_rejected.extend(outcome.rejections)
        report.strengths_corrected.extend(outcome.corrections)
        report.ambiguities.extend(f"{artifact.source_reference}: {a}" for a in extraction.ambiguity)

        if not outcome.claims:
            report.artifacts_without_claims += 1
            continue

        base_id = f"evidence_{normalise_reference(artifact.source_reference)}"
        ordered = sorted(outcome.claims, key=lambda c: (c.capability_id, c.engineer_id))

        for index, claim in enumerate(ordered):
            capability = taxonomy_index[claim.capability_id]
            evidence_id = base_id if index == 0 else f"{base_id}_{index + 1}"
            session.add(
                Evidence(
                    evidence_id=evidence_id,
                    artifact_id=artifact.artifact_id,
                    source_type=artifact.source_type.value,
                    source_reference=artifact.source_reference,
                    source_title=artifact.title,
                    artifact_date=artifact.artifact_date,
                    engineer_id=claim.engineer_id,
                    system_id=capability.system_id,
                    component_id=capability.component_id,
                    capability_id=capability.capability_id,
                    evidence_role=claim.evidence_role.value,
                    evidence_strength=claim.evidence_strength.value,
                    summary=claim.summary,
                    freshness=freshness_for(artifact.artifact_date).value,
                    provenance_source=artifact.provenance_source,
                    provenance_record_id=artifact.source_reference,
                    provenance_url=artifact.source_url,
                    extraction_confidence=claim.extraction_confidence.value,
                    is_conflicting=claim.is_conflicting,
                    extraction_rationale=claim.rationale,
                )
            )
            report.evidence_created += 1

    session.flush()
    return report
