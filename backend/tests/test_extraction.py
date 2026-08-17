"""AI extraction and its validation gate.

Per docs/ARCHITECTURE.md section 60, these do not test prose. They test that output parses, that
enum values are valid, that a known artifact maps to the expected capability family, and — most
importantly — that unsupported output is rejected rather than partially accepted.
"""

from __future__ import annotations

from datetime import date

import pytest

from app.ai.deterministic import DeterministicProvider
from app.ai.provider import ExtractionContext, get_provider
from app.ai.schemas import (
    ArtifactExtraction,
    ArtifactInput,
    ArtifactParticipant,
    CapabilityClaim,
    TaxonomyCapability,
)
from app.ai.validation import validate_extraction
from app.schemas.enums import (
    EvidenceRole,
    EvidenceSourceType,
    EvidenceStrength,
)

GATEWAY = TaxonomyCapability(
    capability_id="cap_incident_recovery",
    name="Incident Recovery",
    aliases=["incident recovery", "gateway recovery", "transaction routing"],
    system_id="system_payment_gateway",
    component_id="component_gateway_integration",
)
REFUNDS = TaxonomyCapability(
    capability_id="cap_refund_reversal",
    name="Refund Reversal",
    aliases=["refund reversal"],
    system_id="system_refund_engine",
    component_id="component_refund_orchestration",
)

CONTEXT = ExtractionContext(
    capabilities=[GATEWAY, REFUNDS],
    engineer_names={"eng_alex_chen": "Alex Chen", "eng_maria_gomez": "Maria Gomez"},
)


def artifact(
    body: str,
    participants: list[tuple[str, str]],
    source_type: EvidenceSourceType = EvidenceSourceType.INCIDENT,
    system_hint: str | None = "system_payment_gateway",
) -> ArtifactInput:
    return ArtifactInput(
        artifact_id="artifact_inc_184",
        source_type=source_type,
        source_reference="INC-184",
        title="P1 Payment Gateway Provider Failure",
        body=body,
        artifact_date=date(2026, 5, 14),
        participants=[ArtifactParticipant(engineer_id=e, participant_role=r) for e, r in participants],
        system_hint=system_hint,
        provenance_source="synthetic_incident_dataset",
    )


@pytest.fixture()
def provider() -> DeterministicProvider:
    return DeterministicProvider()


# ---------------------------------------------------------------------------------------
# Extraction
# ---------------------------------------------------------------------------------------


def test_the_configured_provider_satisfies_the_interface() -> None:
    resolved = get_provider()
    assert resolved.name == "deterministic"
    for method in (
        "extract_artifact_semantics",
        "summarize_simulation",
        "explain_candidate",
        "generate_mitigation_plan",
    ):
        assert callable(getattr(resolved, method))


def test_a_resolver_on_an_incident_becomes_independent_execution(provider) -> None:
    extraction = provider.extract_artifact_semantics(
        artifact("Alex restored transaction routing without escalation.", [("eng_alex_chen", "RESOLVER")]),
        CONTEXT,
    )
    assert len(extraction.claims) == 1
    claim = extraction.claims[0]
    assert claim.capability_id == "cap_incident_recovery"
    assert claim.evidence_role is EvidenceRole.INDEPENDENT_EXECUTION
    assert claim.evidence_strength is EvidenceStrength.STRONG
    assert claim.rationale, "every claim must cite what produced it"


def test_one_artifact_can_carry_different_roles_for_different_people(provider) -> None:
    """This is why the per-claim extraction shape was chosen over the flat one in the API contract
    (DEC-06): one incident shows Alex resolving and Maria assisting, and a single role per artifact
    would have to discard one of them."""
    extraction = provider.extract_artifact_semantics(
        artifact(
            "Alex led gateway recovery; Maria assisted.",
            [("eng_alex_chen", "RESOLVER"), ("eng_maria_gomez", "ASSISTING_RESPONDER")],
        ),
        CONTEXT,
    )
    roles = {c.engineer_id: c.evidence_role for c in extraction.claims}
    assert roles["eng_alex_chen"] is EvidenceRole.INDEPENDENT_EXECUTION
    assert roles["eng_maria_gomez"] is EvidenceRole.ASSISTED_EXECUTION


def test_an_artifact_naming_no_capability_yields_nothing(provider) -> None:
    """Returning nothing is a correct answer. Most repository activity demonstrates no operational
    capability at all, and a provider that always finds something is worse than useless."""
    extraction = provider.extract_artifact_semantics(
        artifact("Bumped a dependency version.", [("eng_alex_chen", "AUTHOR")],
                 source_type=EvidenceSourceType.PULL_REQUEST),
        CONTEXT,
    )
    assert extraction.claims == []
    assert extraction.ambiguity


def test_capability_matching_is_scoped_to_the_artifacts_system(provider) -> None:
    """Without scoping, "Monitoring" in a gateway incident would also match "Refund Monitoring"."""
    extraction = provider.extract_artifact_semantics(
        artifact("A refund reversal was required.", [("eng_alex_chen", "RESOLVER")]),
        CONTEXT,
    )
    assert extraction.claims == [], "a refund capability must not attach to a gateway artifact"


def test_an_unmapped_participant_role_produces_no_claim(provider) -> None:
    extraction = provider.extract_artifact_semantics(
        artifact("Alex restored transaction routing.", [("eng_alex_chen", "NOT_A_ROLE")]),
        CONTEXT,
    )
    assert extraction.claims == []
    assert any("unrecognised participant role" in a for a in extraction.ambiguity)


# ---------------------------------------------------------------------------------------
# Validation: the gate between a provider and the graph
# ---------------------------------------------------------------------------------------


def claim(capability_id: str, engineer_id: str, role: EvidenceRole = EvidenceRole.INDEPENDENT_EXECUTION,
          strength: EvidenceStrength = EvidenceStrength.STRONG) -> CapabilityClaim:
    return CapabilityClaim(
        capability_id=capability_id,
        engineer_id=engineer_id,
        evidence_role=role,
        evidence_strength=strength,
        summary="summary",
        rationale="rationale",
    )


def validate(claims: list[CapabilityClaim], participants: list[tuple[str, str]]):
    return validate_extraction(
        ArtifactExtraction(artifact_id="artifact_inc_184", claims=claims),
        artifact("body", participants),
        {c.capability_id: c for c in CONTEXT.capabilities},
        set(CONTEXT.engineer_names),
    )


def test_an_invented_capability_is_rejected() -> None:
    outcome = validate([claim("cap_does_not_exist", "eng_alex_chen")], [("eng_alex_chen", "RESOLVER")])
    assert outcome.claims == []
    assert any("unknown capability" in r for r in outcome.rejections)


def test_a_claim_against_a_non_participant_is_rejected() -> None:
    """The most damaging failure available to this product would be attributing work to someone who
    does not appear in the artifact at all."""
    outcome = validate([claim("cap_incident_recovery", "eng_maria_gomez")], [("eng_alex_chen", "RESOLVER")])
    assert outcome.claims == []
    assert any("not a recorded participant" in r for r in outcome.rejections)


def test_a_cross_system_attribution_is_rejected() -> None:
    outcome = validate([claim("cap_refund_reversal", "eng_alex_chen")], [("eng_alex_chen", "RESOLVER")])
    assert outcome.claims == []
    assert any("belongs to" in r for r in outcome.rejections)


def test_a_disagreeing_strength_is_corrected_rather_than_trusted() -> None:
    outcome = validate(
        [claim("cap_incident_recovery", "eng_alex_chen", EvidenceRole.EXPOSURE, EvidenceStrength.STRONG)],
        [("eng_alex_chen", "RESOLVER")],
    )
    assert len(outcome.claims) == 1
    assert outcome.claims[0].evidence_strength is EvidenceStrength.WEAK
    assert outcome.corrections


def test_duplicate_claims_for_the_same_pair_are_rejected() -> None:
    outcome = validate(
        [claim("cap_incident_recovery", "eng_alex_chen"), claim("cap_incident_recovery", "eng_alex_chen")],
        [("eng_alex_chen", "RESOLVER")],
    )
    assert len(outcome.claims) == 1
    assert any("duplicate claim" in r for r in outcome.rejections)


def test_a_claim_without_a_rationale_cannot_be_constructed() -> None:
    with pytest.raises(ValueError):
        CapabilityClaim(
            capability_id="cap_incident_recovery",
            engineer_id="eng_alex_chen",
            evidence_role=EvidenceRole.INDEPENDENT_EXECUTION,
            evidence_strength=EvidenceStrength.STRONG,
            summary="summary",
            rationale="   ",
        )
