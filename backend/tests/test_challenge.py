"""The challenge / correct / learn workflow. PRD section 21, closing FR-020 and AC-11.

These are the only tests that mutate seeded state, so the module reseeds on the way in and on the
way out. Without that, every later test asserting the frozen numbers would fail for a reason that
has nothing to do with the code under test.

The property being defended throughout: a manager changes **evidence**, and the rules recompute the
rest. No request in this file sets a readiness level, an exposure state, or a risk index, because no
such field exists.
"""

from __future__ import annotations

import pytest
from sqlalchemy import select

CAPABILITY = "cap_incident_recovery"
ALEX = "eng_alex_chen"
MARIA = "eng_maria_gomez"
JORDAN = "eng_jordan_lee"
MANAGER = "eng_manager_sarah"


@pytest.fixture(scope="module", autouse=True)
def restore_after_module(seeded_database):
    """Leave the database as this module found it, so later modules see the frozen numbers."""
    yield
    from scripts.seed_demo import seed

    seed(verbose=False)


@pytest.fixture(autouse=True)
def fresh_seed(seeded_database):
    """Each test starts from the seeded baseline.

    Several of these assert an initial readiness before challenging it, so they cannot inherit a
    previous test's mutation. Reseeding before rather than around each test halves the cost.
    """
    from scripts.seed_demo import seed

    seed(verbose=False)
    yield


def challenge(client, payload: dict, capability_id: str = CAPABILITY):
    return client.post(f"/api/v1/capabilities/{capability_id}/challenge", json=payload)


def readiness_of(client, engineer_id: str, capability_id: str = CAPABILITY) -> str:
    body = client.get(f"/api/v1/capabilities/{capability_id}").json()
    return next(
        (c["readiness"] for c in body["engineer_coverage"] if c["engineer_id"] == engineer_id),
        "NONE",
    )


# ---------------------------------------------------------------------------------------
# AC-11 — readiness and risk are recomputed after a challenge
# ---------------------------------------------------------------------------------------


def test_manager_attestation_recomputes_readiness_and_closes_the_gap(client) -> None:
    """The hero correction. Jordan's only recorded evidence is two years of reviews, so he reads
    EXPOSED. The manager attests that he did once recover the gateway unaided; readiness is
    recomputed from the new evidence and Incident Recovery gains a second adequate engineer.

    Nothing sets a readiness value — the request states what happened and the rules conclude.
    """
    assert readiness_of(client, JORDAN) == "EXPOSED"

    response = challenge(
        client,
        {
            "challenge_type": "MANAGER_ATTESTATION",
            "engineer_id": JORDAN,
            "submitted_by": MANAGER,
            "evidence_role": "INDEPENDENT_EXECUTION",
            "comment": "Jordan restored the gateway alone during the March incident; never written up.",
        },
    )
    assert response.status_code == 201
    body = response.json()

    assert body["recomputed"] is True
    assert body["capability_before"]["readiness"] == "EXPOSED"
    assert body["capability_after"]["readiness"] in {"ASSISTED", "PRACTICED"}
    assert body["evidence_created"]

    # The capability itself improves: a second adequate engineer removes the sole-expert condition.
    assert body["capability_before"]["exposure"] == "DEGRADED"
    assert body["capability_after"]["exposure"] == "COVERED"
    assert body["capability_after"]["continuity_risk_index"] < body["capability_before"]["continuity_risk_index"]

    # And the change rolls up, so the dashboard cannot disagree with the page.
    assert body["system_after"]["degraded_capability_count"] < body["system_before"]["degraded_capability_count"]
    assert readiness_of(client, JORDAN) == "PRACTICED"


def test_the_attested_evidence_is_visible_and_labelled_as_an_attestation(client) -> None:
    """DOMAIN_MODEL.md section 34: attestation must remain distinguishable from artifact-derived
    proof. A manager's word appearing as an incident record would be indistinguishable from one."""
    challenge(
        client,
        {
            "challenge_type": "MANAGER_ATTESTATION",
            "engineer_id": JORDAN,
            "submitted_by": MANAGER,
            "evidence_role": "ASSISTED_EXECUTION",
            "comment": "Jordan assisted the March recovery.",
        },
    )
    body = client.get(f"/api/v1/capabilities/{CAPABILITY}/evidence", params={"engineer_id": JORDAN}).json()
    attestations = [e for e in body["evidence"] if e["source_type"] == "MANAGER_ATTESTATION"]

    assert len(attestations) == 1
    record = attestations[0]
    assert record["provenance"]["source"] == "manager_attestation"
    assert record["provenance"]["record_id"] == MANAGER
    assert MANAGER in record["summary"]
    # Capped, so an attestation can never carry the weight of a production recovery.
    assert record["evidence_strength"] in {"WEAK", "MODERATE"}


def test_attestations_alone_cannot_manufacture_a_validated_expert(client) -> None:
    """The abuse case. If a manager could assert their way to VALIDATED, the whole evidence model
    would be decorative. Attested records are capped at MODERATE and so never contribute to the
    strong-source diversity VALIDATED requires."""
    for index in range(3):
        response = challenge(
            client,
            {
                "challenge_type": "MANAGER_ATTESTATION",
                "engineer_id": MARIA,
                "submitted_by": MANAGER,
                "evidence_role": "INDEPENDENT_EXECUTION",
                "comment": f"Maria recovered the gateway unaided, occasion {index + 1}.",
            },
        )
        assert response.status_code == 201

    assert readiness_of(client, MARIA) != "VALIDATED"


# ---------------------------------------------------------------------------------------
# Linking evidence the extraction step missed
# ---------------------------------------------------------------------------------------


def test_linking_an_artifact_the_engineer_participated_in_creates_evidence(client, session) -> None:
    from app.models import Artifact, Evidence

    linked = {
        row.artifact_id
        for row in session.scalars(
            select(Evidence).where(
                Evidence.capability_id == CAPABILITY, Evidence.engineer_id == JORDAN
            )
        )
    }
    candidate = next(
        artifact
        for artifact in session.scalars(select(Artifact))
        if artifact.artifact_id not in linked
        and any(p["engineer_id"] == JORDAN for p in artifact.participants)
    )

    response = challenge(
        client,
        {
            "challenge_type": "LINK_EVIDENCE",
            "engineer_id": JORDAN,
            "submitted_by": MANAGER,
            "source_reference": candidate.source_reference,
            "comment": "This work covered gateway recovery and was mapped elsewhere.",
        },
    )
    assert response.status_code == 201
    assert response.json()["evidence_created"]


def test_a_manager_cannot_link_an_artifact_the_engineer_did_not_take_part_in(client) -> None:
    """The same invariant the AI validation layer enforces, for the same reason: a claim against
    someone who does not appear in the artifact is unsupported however it arrives."""
    response = challenge(
        client,
        {
            "challenge_type": "LINK_EVIDENCE",
            "engineer_id": MARIA,
            "submitted_by": MANAGER,
            "source_reference": "INC-184",
            "comment": "Crediting Maria for Alex's recovery.",
        },
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    assert "not a recorded participant" in response.json()["error"]["message"]


def test_a_manager_cannot_invent_an_artifact(client) -> None:
    response = challenge(
        client,
        {
            "challenge_type": "LINK_EVIDENCE",
            "engineer_id": JORDAN,
            "submitted_by": MANAGER,
            "source_reference": "INC-999999",
            "comment": "There was definitely an incident.",
        },
    )
    assert response.status_code == 404


def test_linking_the_same_artifact_twice_is_rejected(client) -> None:
    response = challenge(
        client,
        {
            "challenge_type": "LINK_EVIDENCE",
            "engineer_id": ALEX,
            "submitted_by": MANAGER,
            "source_reference": "INC-184",
            "comment": "Already counted.",
        },
    )
    assert response.status_code == 422
    assert "already evidences" in response.json()["error"]["message"]


# ---------------------------------------------------------------------------------------
# Correcting a mis-mapped record
# ---------------------------------------------------------------------------------------


def test_correcting_a_mapping_moves_evidence_and_recomputes_both_capabilities(client, session) -> None:
    from app.models import Evidence

    record = session.scalar(
        select(Evidence).where(Evidence.capability_id == "cap_monitoring")
    )
    origin = client.get("/api/v1/capabilities/cap_monitoring").json()

    response = challenge(
        client,
        {
            "challenge_type": "CORRECT_CAPABILITY_MAPPING",
            "submitted_by": MANAGER,
            "evidence_id": record.evidence_id,
            "comment": "This change was about retry behaviour, not monitoring.",
        },
        capability_id="cap_retry_logic",
    )
    assert response.status_code == 201
    assert response.json()["evidence_moved"] == record.evidence_id

    moved = client.get("/api/v1/capabilities/cap_retry_logic/evidence").json()
    assert record.evidence_id in {e["evidence_id"] for e in moved["evidence"]}

    # The capability it left is recomputed too, otherwise it would keep evidence it no longer has.
    after_origin = client.get("/api/v1/capabilities/cap_monitoring").json()
    assert after_origin != origin


def test_evidence_cannot_be_moved_between_systems(client, session) -> None:
    from app.models import Evidence

    record = session.scalar(select(Evidence).where(Evidence.capability_id == CAPABILITY))
    response = challenge(
        client,
        {
            "challenge_type": "CORRECT_CAPABILITY_MAPPING",
            "submitted_by": MANAGER,
            "evidence_id": record.evidence_id,
            "comment": "Wrong service entirely.",
        },
        capability_id="cap_refund_reversal",
    )
    assert response.status_code == 422
    assert "between systems" in response.json()["error"]["message"]


# ---------------------------------------------------------------------------------------
# Audit trail and guardrails
# ---------------------------------------------------------------------------------------


def test_every_challenge_is_recorded_with_its_reason_and_both_assessments(client, session) -> None:
    """PRD section 21: store the previous assessment, the reason, what changed, and the new result.
    A correctable assessment that cannot be audited is worse than one that cannot be corrected,
    because nobody can later ask why it moved."""
    from app.models import AssessmentChallenge

    challenge(
        client,
        {
            "challenge_type": "MANAGER_ATTESTATION",
            "engineer_id": JORDAN,
            "submitted_by": MANAGER,
            "evidence_role": "ASSISTED_EXECUTION",
            "comment": "Observed during the March incident review.",
        },
    )
    session.expire_all()
    record = session.scalar(select(AssessmentChallenge))

    assert record is not None
    assert record.submitted_by == MANAGER
    assert "March incident review" in record.comment
    assert record.previous_assessment["exposure"]
    assert record.new_assessment["exposure"]
    assert record.evidence_created_id


def test_a_challenge_must_state_a_reason(client) -> None:
    response = challenge(
        client,
        {
            "challenge_type": "MANAGER_ATTESTATION",
            "engineer_id": JORDAN,
            "submitted_by": MANAGER,
            "comment": "   ",
        },
    )
    assert response.status_code == 422


def test_the_request_offers_no_way_to_set_a_score() -> None:
    """The structural guarantee behind "scores change because evidence changes"."""
    from app.schemas.challenge import ChallengeRequest

    fields = set(ChallengeRequest.model_fields)
    for forbidden in (
        "readiness",
        "exposure",
        "continuity_risk_index",
        "continuity_risk_class",
        "evidence_confidence",
        "technical_overlap",
    ):
        assert forbidden not in fields, forbidden


def test_unknown_capability_and_engineer_are_rejected(client) -> None:
    assert challenge(
        client,
        {
            "challenge_type": "MANAGER_ATTESTATION",
            "engineer_id": JORDAN,
            "submitted_by": MANAGER,
            "comment": "x",
        },
        capability_id="cap_nope",
    ).status_code == 404

    assert challenge(
        client,
        {
            "challenge_type": "MANAGER_ATTESTATION",
            "engineer_id": "eng_nobody",
            "submitted_by": MANAGER,
            "comment": "x",
        },
    ).status_code == 404
