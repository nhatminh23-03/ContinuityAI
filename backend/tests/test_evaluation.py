"""Hidden-ground-truth evaluation, run as a test. PRD section 25 and phase 8.

The application receives only generated artifacts and must re-derive readiness from them. This
asserts it does — that the inferred graph matches the hidden model the artifacts were generated
from, and that the whole loop (extraction, aggregation, readiness, exposure, risk, simulation,
candidates) is self-consistent.

Read the caveat in `app/evaluation/report.py` before quoting any figure from here. It is controlled
prototype validation against synthetic data, not evidence of real-world accuracy.
"""

from __future__ import annotations

import pytest

from app.evaluation import evaluate, load_ground_truth
from app.repositories import CapabilityRepository, EvidenceRepository


@pytest.fixture()
def report(session):
    """Function-scoped to match the `session` fixture, which cannot outlive a reseed."""
    return evaluate(session, load_ground_truth())


def test_every_check_passes(report) -> None:
    failures = [
        f"{check.name}: {check.passed}/{check.total}\n    " + "\n    ".join(check.failures)
        for check in report.checks
        if not check.ok
    ]
    assert not failures, "\n".join(failures)


def test_readiness_is_reconstructed_from_artifacts_alone(report) -> None:
    """The central claim of the product, measured. The seed never writes a readiness value; every
    one is derived from the evidence the generator produced."""
    check = next(c for c in report.checks if c.name.startswith("Knowledge reconstruction"))
    assert check.total >= 50, "the labelled set should cover the whole organisation"
    assert check.rate == 1.0, check.failures


def test_critical_gaps_are_found_without_false_positives(report) -> None:
    check = next(c for c in report.checks if c.name.startswith("Critical gap detection"))
    assert check.rate == 1.0, check.failures


def test_the_counterfactual_matches_the_expected_coverage_change(report) -> None:
    check = next(c for c in report.checks if c.name.startswith("Counterfactual simulation"))
    assert check.rate == 1.0, check.failures


def test_every_coverage_claim_is_grounded_in_a_source(report) -> None:
    """AC-04 and FR-024, expressed as a rate rather than a spot check."""
    check = next(c for c in report.checks if c.name.startswith("Evidence grounding"))
    assert check.rate == 1.0, check.failures


def test_most_ingested_artifacts_produce_no_evidence(session) -> None:
    """A corpus where everything is significant would be a corpus that proves nothing. The noise
    exists so extraction has to decline, and the ratio is worth watching: if it collapses, the
    matcher has become too eager."""
    from app.models import Artifact

    artifacts = session.query(Artifact).count()
    evidence = EvidenceRepository(session).count()
    assert artifacts > 500, "PRD section 14.3 targets 500-2,000 normalised records"
    assert evidence < artifacts / 2, (
        f"{evidence} evidence records from {artifacts} artifacts is suspiciously high"
    )


def test_the_dataset_reaches_the_scale_the_prd_asks_for(session) -> None:
    from app.models import Capability, Component, Engineer, Platform, System

    assert 2 <= session.query(Platform).count() <= 3
    assert 5 <= session.query(System).count() <= 7
    assert 12 <= session.query(Component).count() <= 20
    assert 25 <= session.query(Capability).count() <= 40
    assert 8 <= session.query(Engineer).count() <= 15


def test_every_capability_has_been_assessed(session) -> None:
    capabilities = CapabilityRepository(session)
    unassessed = [
        capability.capability_id
        for capability in capabilities.list_all()
        if capabilities.assessment(capability.capability_id) is None
    ]
    assert not unassessed, unassessed


def test_at_least_one_capability_reports_insufficient_evidence(session) -> None:
    """AC-12 requires the seed to exercise the uncertainty path, not just permit it."""
    capabilities = CapabilityRepository(session)
    states = [
        capabilities.assessment(c.capability_id).exposure
        for c in capabilities.list_all()
        if capabilities.assessment(c.capability_id)
    ]
    assert "INSUFFICIENT_EVIDENCE" in states


def test_conflicting_evidence_is_seeded_and_lowers_confidence_without_erasing_coverage(
    client, session
) -> None:
    """PRD section 16.5 and R-11. `Risk: MODERATE` with `Confidence: LOW` is a legitimate state, and
    the seed now exercises it: a Policy Rollback attempt that was itself rolled back.

    The record is retained and surfaced separately rather than discarded. It never supports a claim,
    so Daniel keeps PRACTICED on the strength of his two qualifying records — the conflict changes
    how much the assessment can be trusted, not what the other evidence shows.
    """
    from app.models import Evidence

    conflicting = [e for e in session.query(Evidence).all() if e.is_conflicting]
    assert conflicting, "the seed should exercise the conflicting-evidence path, not merely allow it"

    body = client.get("/api/v1/capabilities/cap_policy_rollback").json()
    assert body["exposure"] == "DEGRADED"
    assert body["evidence_confidence"] == "LOW"
    assert "CONFLICTING_EVIDENCE" in body["rules_triggered"]
    assert "LOW_EVIDENCE_CONFIDENCE" in body["rules_triggered"]

    readiness = {c["engineer_id"]: c["readiness"] for c in body["engineer_coverage"]}
    assert readiness["eng_daniel_kim"] == "PRACTICED"

    evidence = client.get("/api/v1/capabilities/cap_policy_rollback/evidence").json()
    assert evidence["conflicting_evidence"], "a conflicting record must be visible in the drawer"
    supporting = {e["evidence_id"] for e in evidence["evidence"]}
    conflicted = {e["evidence_id"] for e in evidence["conflicting_evidence"]}
    assert not supporting & conflicted, "a conflicting record must never also support the claim"


def test_the_hero_scenario_is_unaffected_by_the_conflicting_record(client) -> None:
    """The conflict was placed on Authorization precisely so it exercises the path without moving a
    number the frozen fixtures pin."""
    gateway = client.get("/api/v1/systems/system_payment_gateway").json()
    assert gateway["continuity_risk_index"] == 74
    assert gateway["continuity_risk_class"] == "HIGH"
    assert gateway["evidence_confidence"] == "HIGH"

    platforms = {p["platform_id"]: p for p in client.get("/api/v1/platforms").json()["platforms"]}
    assert platforms["platform_payments"]["highest_system_risk_index"] == 74
    assert platforms["platform_identity"]["highest_system_risk_index"] == 68


# ---------------------------------------------------------------------------------------
# R-02 — the adversarial artifacts, and whether the check that guards them has teeth
# ---------------------------------------------------------------------------------------


def test_the_adversarial_traps_are_in_the_corpus_and_all_declined(report) -> None:
    """R-02. The answer to "100% only proves the pipeline agrees with its own generator".

    Seven artifacts written to fool the rules — activity mistaken for capability, attribution read out
    of prose instead of the participant record, seniority language mistaken for evidence. Declining
    them is a different kind of claim from reconstructing a label, because each is a specific way a
    plausible implementation gets this wrong while still scoring perfectly on cooperative data.
    """
    check = next(c for c in report.checks if c.name.startswith("Adversarial artifacts"))
    assert check.total >= 7, "the trap set should not silently shrink"
    assert check.rate == 1.0, check.failures
    # All three trap families must be exercised, not just the easy one.
    note = " ".join(check.notes)
    for trap in ("volume_without_execution", "attribution_by_name", "authority_language"):
        assert trap in note, f"{trap} was not exercised"


def test_volume_of_review_activity_does_not_become_capability(client) -> None:
    """"Artifact, not activity" is a stated PRD principle, and this is what tests it.

    Grace has eight review and comment records on Token Rotation and no execution. A system that
    counted activity would promote her; readiness must stay EXPOSED.
    """
    body = client.get("/api/v1/capabilities/cap_token_rotation").json()
    readiness = {c["engineer_id"]: c["readiness"] for c in body["engineer_coverage"]}
    assert readiness["eng_grace_liu"] == "EXPOSED", (
        f"Grace read as {readiness['eng_grace_liu']} on the strength of review volume alone"
    )
    # And the capability is still assessed on real coverage, not on the noise around it.
    assert body["exposure"] == "DEGRADED"


def test_a_name_in_the_prose_does_not_create_coverage(client) -> None:
    """INC-9001 says Tom Becker did the work single-handedly. The participant record says otherwise.

    Tom is a Payments engineer with no Identity coverage, so attribution by narrative would hand him a
    capability in a platform he has never worked in. This is the exact mistake the measured model
    extraction made, so it is worth a test rather than an assumption.
    """
    body = client.get("/api/v1/capabilities/cap_token_rotation").json()
    covered = {c["engineer_id"] for c in body["engineer_coverage"]}
    assert "eng_tom_becker" not in covered, "coverage was created from a name in prose"


def test_the_adversarial_check_fails_when_a_trap_actually_works(session) -> None:
    """The check must be able to fail, or its passing means nothing.

    Verified by lowering a ceiling below what the corpus legitimately produces, rather than by
    corrupting the database: Grace really is EXPOSED on Token Rotation, so a ceiling of NONE is a
    breach the check has to report. If this test ever passes silently, the check has stopped looking.
    """
    from app.evaluation.evaluator import _adversarial
    from app.evaluation.ground_truth import GroundTruth

    rigged = GroundTruth(
        adversarial_artifacts=[
            {
                "reference": "REV-9001",
                "trap": "volume_without_execution",
                "ceiling": {
                    "engineer_id": "eng_grace_liu",
                    "capability_id": "cap_token_rotation",
                    "readiness": "NONE",
                },
            }
        ]
    )
    check = _adversarial(session, rigged)
    assert check.passed == 0 and check.total == 1
    assert any("above the NONE ceiling" in f for f in check.failures), check.failures


def test_a_trap_missing_from_the_corpus_fails_rather_than_passes(session) -> None:
    """The blind spot R-26 was about, closed here before it can open.

    If a trap's artifact is absent, nothing was tested — and a check that returns green in that state
    would go quiet the moment someone regenerated the corpus without the traps. Absence is a failure.
    """
    from app.evaluation.evaluator import _adversarial
    from app.evaluation.ground_truth import GroundTruth

    rigged = GroundTruth(
        adversarial_artifacts=[
            {"reference": "REV-DOES-NOT-EXIST", "trap": "volume_without_execution"}
        ]
    )
    check = _adversarial(session, rigged)
    assert check.passed == 0
    assert any("not in the corpus" in f for f in check.failures), check.failures
