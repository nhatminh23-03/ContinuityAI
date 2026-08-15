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


@pytest.fixture(scope="module")
def report(session):
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
