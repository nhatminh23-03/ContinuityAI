"""FR-005 taxonomy discovery, and FR-010 AI-suggested criticality.

Both requirements let a model name something it was not given, which sits in obvious tension with the
closed world that keeps invented capabilities out of the graph. These tests pin how that tension is
resolved, because getting it wrong is the difference between a useful suggestion and a hallucinated
risk number.

FR-005: "AI shall propose components/capabilities using existing metadata first and flag
low-confidence concepts for review."
FR-010: "AI may suggest system criticality; a human-confirmed value is authoritative."
"""

from __future__ import annotations

import json
from datetime import date

from app.ai.extraction import parse_extraction
from app.ai.provider import ExtractionContext
from app.ai.schemas import ArtifactInput, ArtifactParticipant, TaxonomyCapability
from app.schemas.enums import (
    BusinessCriticality,
    CriticalitySource,
    EvidenceConfidence,
    EvidenceSourceType,
    TaxonomyProposalKind,
)


def artifact() -> ArtifactInput:
    return ArtifactInput(
        artifact_id="artifact_inc_900",
        source_type=EvidenceSourceType.INCIDENT,
        source_reference="INC-900",
        title="Webhook backlog after provider outage",
        body="Replayed the webhook backlog by hand to recover merchant notifications.",
        artifact_date=date(2026, 5, 14),
        participants=[
            ArtifactParticipant(engineer_id="eng_alex_chen", participant_role="RESOLVER")
        ],
        system_hint="system_payment_gateway",
        provenance_source="synthetic_incident_dataset",
    )


def context() -> ExtractionContext:
    return ExtractionContext(
        capabilities=[
            TaxonomyCapability(
                capability_id="cap_incident_recovery",
                name="Incident Recovery",
                aliases=["gateway recovery"],
                system_id="system_payment_gateway",
                component_id="component_gateway_integration",
            )
        ],
        engineer_names={"eng_alex_chen": "Alex Chen"},
    )


def parse(payload: dict):
    return parse_extraction(
        json.dumps(payload),
        artifact(),
        context(),
        provider_label="test/model",
        is_conflicting=False,
    )


# ---------------------------------------------------------------------------------------
# FR-005 — proposals are suggestions, never evidence
# ---------------------------------------------------------------------------------------


def test_a_concept_absent_from_the_taxonomy_is_proposed() -> None:
    extraction = parse(
        {
            "claims": [],
            "taxonomy_proposals": [
                {
                    "kind": "CAPABILITY",
                    "name": "Webhook Replay",
                    "rationale": "'replayed the webhook backlog by hand'",
                    "confidence": "MEDIUM",
                }
            ],
        }
    )

    assert len(extraction.taxonomy_proposals) == 1
    proposal = extraction.taxonomy_proposals[0]
    assert proposal.name == "Webhook Replay"
    assert proposal.kind is TaxonomyProposalKind.CAPABILITY
    assert proposal.confidence is EvidenceConfidence.MEDIUM
    # Provenance, on the same terms as any claim: a reviewer reads the artifact, not the proposal.
    assert proposal.source_reference == "INC-900"
    assert proposal.system_id == "system_payment_gateway"


def test_a_proposal_never_becomes_a_claim() -> None:
    """The property the whole design rests on.

    Claims move risk numbers. Proposals must not, so a proposal cannot be attributed to an engineer and
    cannot arrive as evidence — even when the model tries to supply one alongside no claims at all.
    """
    extraction = parse(
        {
            "claims": [],
            "taxonomy_proposals": [
                {
                    "kind": "CAPABILITY",
                    "name": "Webhook Replay",
                    "rationale": "'replayed the webhook backlog'",
                    "confidence": "HIGH",
                }
            ],
        }
    )

    assert extraction.claims == []
    assert len(extraction.taxonomy_proposals) == 1
    # There is no field on a proposal that could carry an attribution.
    assert not hasattr(extraction.taxonomy_proposals[0], "engineer_id")


def test_low_confidence_proposals_are_kept_because_that_is_the_flag() -> None:
    """FR-005 says low-confidence concepts are *flagged for review*, not discarded.

    Filtering them would satisfy the closed world and defeat the requirement — a half-recognised
    concept is frequently the interesting one, and the confidence value is how it is triaged.
    """
    extraction = parse(
        {
            "claims": [],
            "taxonomy_proposals": [
                {
                    "kind": "CAPABILITY",
                    "name": "Merchant Notification Recovery",
                    "rationale": "'merchant notifications' recovered, unclear if a distinct capability",
                    "confidence": "LOW",
                }
            ],
        }
    )

    assert len(extraction.taxonomy_proposals) == 1
    assert extraction.taxonomy_proposals[0].confidence is EvidenceConfidence.LOW


def test_a_proposal_that_duplicates_existing_metadata_is_dropped_and_noted() -> None:
    """"Using existing metadata first" — a rewording of a known capability is not a discovery.

    Matched against aliases as well as names, since the taxonomy carries aliases precisely because one
    capability has several surface forms. The near-miss is recorded rather than silently swallowed.
    """
    extraction = parse(
        {
            "claims": [],
            "taxonomy_proposals": [
                {
                    "kind": "CAPABILITY",
                    "name": "Incident Recovery",
                    "rationale": "duplicate by name",
                    "confidence": "HIGH",
                },
                {
                    "kind": "CAPABILITY",
                    "name": "Gateway Recovery",
                    "rationale": "duplicate by alias",
                    "confidence": "HIGH",
                },
            ],
        }
    )

    assert extraction.taxonomy_proposals == []
    assert len(extraction.ambiguity) == 2
    assert all("already covers" in note for note in extraction.ambiguity)


def test_an_unjustified_proposal_is_dropped() -> None:
    """Same rule every claim obeys: nothing enters the record that cannot say why."""
    extraction = parse(
        {
            "claims": [],
            "taxonomy_proposals": [
                {"kind": "CAPABILITY", "name": "Mystery Capability", "rationale": "  "},
                {"kind": "CAPABILITY", "name": "  ", "rationale": "has a reason but no name"},
            ],
        }
    )
    assert extraction.taxonomy_proposals == []


def test_repeated_proposals_are_merged_with_a_count(session) -> None:
    """A concept named once is a guess; named repeatedly it is a gap in the taxonomy.

    The count is what makes a review list sortable by something more useful than recency, so repeats
    must merge rather than accumulate rows.
    """
    from app.ai.schemas import ArtifactExtraction, TaxonomyProposal
    from app.ingestion.pipeline import IngestionReport, _record_proposals, proposals_for_review
    from app.models import Artifact

    session.add(
        Artifact(
            artifact_id="artifact_inc_900",
            source_type="INCIDENT",
            source_reference="INC-900",
            title="t",
            body="b",
            artifact_date=date(2026, 5, 14),
            participants=[],
            system_hint="system_payment_gateway",
            file_paths=[],
            provenance_source="test",
            extra={},
        )
    )
    session.flush()

    report = IngestionReport()
    for confidence in (EvidenceConfidence.LOW, EvidenceConfidence.HIGH):
        _record_proposals(
            session,
            artifact(),
            ArtifactExtraction(
                artifact_id="artifact_inc_900",
                system_id="system_payment_gateway",
                taxonomy_proposals=[
                    TaxonomyProposal(
                        kind=TaxonomyProposalKind.CAPABILITY,
                        name="Webhook Replay",
                        system_id="system_payment_gateway",
                        rationale="seen again",
                        confidence=confidence,
                        source_reference="INC-900",
                    )
                ],
            ),
            report,
            provider_label="test",
        )
    session.flush()

    rows = [p for p in proposals_for_review(session) if p.name == "Webhook Replay"]
    assert len(rows) == 1, "the same concept must not produce two review items"
    assert rows[0].occurrences == 2
    # The clearer of the two readings wins.
    assert rows[0].confidence == EvidenceConfidence.HIGH.value
    # Counted once as a distinct concept, not twice.
    assert report.taxonomy_proposals == 1

    session.rollback()


def test_nothing_in_the_continuity_engine_reads_the_proposals_table() -> None:
    """Structural guarantee, checked rather than trusted.

    If a scoring module ever imported this table, a hallucinated concept could reach a risk number. The
    separation is the entire reason proposals are allowed to exist, so it is asserted here rather than
    left to review.
    """
    from pathlib import Path

    engine_dirs = [
        Path("app/continuity"),
        Path("app/evidence"),
        Path("app/simulation"),
        Path("app/graph"),
    ]
    offenders = [
        path
        for directory in engine_dirs
        for path in directory.rglob("*.py")
        if "TaxonomyProposal" in path.read_text()
    ]
    assert not offenders, f"scoring code must not read taxonomy proposals: {offenders}"


# ---------------------------------------------------------------------------------------
# FR-010 — a human-confirmed value is authoritative
# ---------------------------------------------------------------------------------------


def _suggestion(value: BusinessCriticality):
    from app.ai.criticality import CriticalitySuggestion

    return CriticalitySuggestion(
        system_id="system_refund_engine",
        business_criticality=value,
        rationale="handles refunds",
        confidence=EvidenceConfidence.MEDIUM,
        suggested_by="test/model",
    )


def test_a_human_confirmed_value_wins_even_when_the_model_disagrees() -> None:
    """The half of FR-010 worth being strict about.

    Live, the model rated three of five systems higher than the humans did. If disagreement moved the
    value, a demo's criticality — and therefore its risk classes — would drift every time the model was
    re-run. It is a suggestion; the human answer stands and the disagreement is a question for them.
    """
    from app.ai.criticality import resolve

    value, source = resolve(
        human_value=BusinessCriticality.HIGH,
        human_confirmed=True,
        suggestion=_suggestion(BusinessCriticality.CRITICAL),
    )
    assert value is BusinessCriticality.HIGH
    assert source is CriticalitySource.HUMAN_CONFIRMED


def test_an_unconfirmed_system_takes_the_suggestion_and_is_labelled_as_such() -> None:
    from app.ai.criticality import resolve

    value, source = resolve(
        human_value=None,
        human_confirmed=False,
        suggestion=_suggestion(BusinessCriticality.CRITICAL),
    )
    assert value is BusinessCriticality.CRITICAL
    assert source is CriticalitySource.AI_SUGGESTED


def test_no_suggestion_leaves_the_value_alone() -> None:
    """FR-010 says "may". A model that cannot answer must not blank an existing value."""
    from app.ai.criticality import resolve

    value, source = resolve(
        human_value=BusinessCriticality.MEDIUM, human_confirmed=False, suggestion=None
    )
    assert value is BusinessCriticality.MEDIUM
    assert source is CriticalitySource.HUMAN_CONFIRMED


def test_a_failed_suggestion_returns_none_rather_than_guessing() -> None:
    """An optional enrichment must not invent an answer, and must not break its caller."""
    from app.ai.criticality import SystemDescription, suggest

    def broken(system, user, max_tokens):
        raise RuntimeError("gateway down")

    result = suggest(
        SystemDescription(
            system_id="system_refund_engine",
            name="Refund Engine",
            description="Processes refunds",
            platform_name="Payments Platform",
            component_names=["Refund Orchestration"],
            capability_names=["Refund Reversal"],
        ),
        chat=broken,
        provider_label="test/model",
    )
    assert result is None


def test_the_criticality_prompt_is_given_no_person_and_no_headcount() -> None:
    """The input that would turn "how important is this system" into "how busy is this team".

    Team size is not importance, and this product's entire argument is that the two must not be
    confused. So the prompt is built from purpose, components and capabilities — and the absence of
    everything else is asserted, because it would be an easy and plausible-looking thing to add.
    """
    from app.ai.criticality import SystemDescription, build_user_prompt

    prompt = build_user_prompt(
        SystemDescription(
            system_id="system_refund_engine",
            name="Refund Engine",
            description="Processes customer refunds",
            platform_name="Payments Platform",
            component_names=["Refund Orchestration"],
            capability_names=["Refund Reversal"],
        )
    )

    lowered = prompt.lower()
    for forbidden in ("engineer", "headcount", "alex", "commits", "activity", "readiness"):
        assert forbidden not in lowered, f"criticality must not be judged from {forbidden!r}"
    assert "Refund Orchestration" in prompt and "Refund Reversal" in prompt


def test_the_criticality_prompt_forbids_judging_people() -> None:
    from app.ai.criticality import system_prompt

    text = system_prompt().lower()
    assert "never judge a person" in text
    assert "team size is not importance" in text
