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

import re

from sqlalchemy import select

from app.ai.provider import AIProvider, ExtractionContext
from app.ai.schemas import ArtifactExtraction, ArtifactInput, TaxonomyCapability
from app.ai.validation import validate_extraction
from app.core.errors import AIExtractionError
from app.evidence.freshness import freshness_for
from app.ingestion.adapters import normalise_reference
from app.models import Artifact, Evidence, TaxonomyProposalRow
from app.schemas.enums import EvidenceConfidence, TaxonomyProposalStatus


@dataclass
class IngestionReport:
    artifacts_ingested: int = 0
    artifacts_without_claims: int = 0
    # FR-005: distinct concepts proposed, and how many of those the model itself marked LOW.
    taxonomy_proposals: int = 0
    low_confidence_proposals: int = 0
    evidence_created: int = 0
    claims_rejected: list[str] = field(default_factory=list)
    strengths_corrected: list[str] = field(default_factory=list)
    ambiguities: list[str] = field(default_factory=list)

    def proposal_summary(self) -> str:
        """FR-005, reported separately from evidence because it is a different kind of output.

        Proposals are suggestions for a human and carry no evidence, so folding them into the evidence
        line would overstate what the run produced.
        """
        if not self.taxonomy_proposals:
            return "no taxonomy concepts proposed"
        return (
            f"{self.taxonomy_proposals} taxonomy concept(s) proposed for review "
            f"({self.low_confidence_proposals} low confidence)"
        )

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

        # FR-005. Recorded before the `no claims` early return below, deliberately: an artifact that
        # produced no claim *because the taxonomy has no name for what it describes* is the single most
        # informative case for a proposal, and returning early would throw exactly those away.
        _record_proposals(
            session, artifact, extraction, report, provider_label=getattr(provider, "name", "?")
        )

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


def _proposal_slug(kind: str, name: str, system_id: str | None) -> str:
    """A stable id, so the same concept proposed by two artifacts is one row with a count of two.

    Derived rather than allocated, for the same reason evidence ids are: a reseed must not renumber
    things a reviewer has already looked at.
    """
    stem = re.sub(r"[^a-z0-9]+", "_", name.strip().lower()).strip("_")
    scope = system_id or "unscoped"
    return f"proposal_{kind.lower()}_{scope}_{stem}"


def _record_proposals(
    session: Session,
    artifact: ArtifactInput,
    extraction: ArtifactExtraction,
    report: IngestionReport,
    *,
    provider_label: str,
) -> None:
    """Persist FR-005 proposals, merging repeats rather than duplicating them.

    Nothing here touches `capabilities`, `evidence`, or any assessment. A proposal is a note to a human;
    the closed-world guarantee for the graph is only worth having if this function cannot weaken it, so
    the only table it writes is its own.

    Repeats increment `occurrences` instead of adding rows. A concept named by one artifact is a guess;
    the same concept named by nine is a gap in the taxonomy, and that count is what makes a review list
    sortable by something more useful than recency.
    """
    for proposal in extraction.taxonomy_proposals:
        proposal_id = _proposal_slug(proposal.kind.value, proposal.name, proposal.system_id)
        existing = session.get(TaxonomyProposalRow, proposal_id)
        if existing is not None:
            existing.occurrences += 1
            # Keep the highest confidence seen. A concept one artifact was unsure about and another
            # stated plainly is better described by the plain one.
            if _confidence_rank(proposal.confidence) > _confidence_rank(
                EvidenceConfidence(existing.confidence)
            ):
                existing.confidence = proposal.confidence.value
                existing.rationale = proposal.rationale
                existing.source_reference = proposal.source_reference
            continue

        session.add(
            TaxonomyProposalRow(
                proposal_id=proposal_id,
                kind=proposal.kind.value,
                name=proposal.name,
                system_id=proposal.system_id,
                component_id=proposal.component_id,
                rationale=proposal.rationale,
                confidence=proposal.confidence.value,
                status=TaxonomyProposalStatus.PROPOSED.value,
                source_reference=proposal.source_reference,
                artifact_id=artifact.artifact_id,
                proposed_by=provider_label,
                occurrences=1,
            )
        )
        # Flushed immediately so the next artifact's `session.get` above can see it.
        #
        # Without this the merge silently does not work: `session.get` resolves persistent rows, not
        # ones still pending in the session, so two artifacts proposing the same concept before a flush
        # both insert and the unique constraint aborts the whole seed. Found by
        # `test_repeated_proposals_are_merged_with_a_count`, which is exactly the shape a real corpus
        # produces — the same missing concept is usually described by several artifacts.
        #
        # Proposals are rare next to artifacts, so the cost of flushing each one is nothing.
        session.flush()
        report.taxonomy_proposals += 1
        if proposal.confidence is EvidenceConfidence.LOW:
            report.low_confidence_proposals += 1


def _confidence_rank(confidence: EvidenceConfidence) -> int:
    return {
        EvidenceConfidence.LOW: 0,
        EvidenceConfidence.MEDIUM: 1,
        EvidenceConfidence.HIGH: 2,
    }[confidence]


def proposals_for_review(session: Session) -> list[TaxonomyProposalRow]:
    """Everything still awaiting a human, most-corroborated first.

    Ordered by occurrences before confidence on purpose: a concept nine artifacts mention is a stronger
    signal about the taxonomy than one the model happened to feel confident about once.
    """
    stmt = (
        select(TaxonomyProposalRow)
        .where(TaxonomyProposalRow.status == TaxonomyProposalStatus.PROPOSED.value)
        .order_by(TaxonomyProposalRow.occurrences.desc(), TaxonomyProposalRow.name)
    )
    return list(session.scalars(stmt))
