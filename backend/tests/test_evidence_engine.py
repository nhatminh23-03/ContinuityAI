"""Unit tests for evidence strength, freshness, aggregation, and readiness classification.

The readiness boundaries are the product's most consequential judgement, so they are pinned
directly rather than only through the API.
"""

from __future__ import annotations

from datetime import date

import pytest

from app.continuity.readiness import classify
from app.evidence.aggregation import EvidenceItem, aggregate
from app.evidence.freshness import freshness_for
from app.evidence.strength import strength_for_role
from app.schemas.enums import (
    EvidenceConfidence,
    EvidenceRole,
    EvidenceSourceType,
    EvidenceStrength,
    Freshness,
    ReadinessLevel,
)

REFERENCE = date(2026, 8, 15)


def item(
    evidence_id: str,
    role: EvidenceRole,
    source: EvidenceSourceType,
    freshness: Freshness = Freshness.FRESH,
    artifact_date: date = date(2026, 5, 14),
    conflicting: bool = False,
) -> EvidenceItem:
    return EvidenceItem(
        evidence_id=evidence_id,
        source_type=source,
        evidence_role=role,
        evidence_strength=strength_for_role(role),
        freshness=freshness,
        artifact_date=artifact_date,
        is_conflicting=conflicting,
    )


def readiness_of(items: list[EvidenceItem]) -> ReadinessLevel:
    return classify(aggregate("eng_x", "cap_x", items)).readiness


# ---------------------------------------------------------------------------------------
# Strength and freshness
# ---------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("role", "expected"),
    [
        (EvidenceRole.EXPOSURE, EvidenceStrength.WEAK),
        (EvidenceRole.CONTRIBUTION, EvidenceStrength.MODERATE),
        (EvidenceRole.ASSISTED_EXECUTION, EvidenceStrength.MODERATE),
        (EvidenceRole.INDEPENDENT_EXECUTION, EvidenceStrength.STRONG),
        (EvidenceRole.KNOWLEDGE_CAPTURE, EvidenceStrength.STRONG),
    ],
)
def test_strength_is_derived_from_role(role: EvidenceRole, expected: EvidenceStrength) -> None:
    assert strength_for_role(role) is expected


@pytest.mark.parametrize(
    ("artifact_date", "expected"),
    [
        (date(2026, 5, 14), Freshness.FRESH),
        (date(2025, 3, 1), Freshness.FRESH),
        (date(2024, 6, 12), Freshness.AGING),
        (date(2022, 1, 1), Freshness.STALE),
    ],
)
def test_freshness_thresholds(artifact_date: date, expected: Freshness) -> None:
    assert freshness_for(artifact_date, REFERENCE) is expected


# ---------------------------------------------------------------------------------------
# Readiness: independence, not volume
# ---------------------------------------------------------------------------------------


def test_many_weak_interactions_never_reach_adequate_readiness() -> None:
    """The "artifact, not activity" principle. Twenty reviews are still twenty reviews."""
    reviews = [
        item(f"e{i}", EvidenceRole.EXPOSURE, EvidenceSourceType.CODE_REVIEW) for i in range(20)
    ]
    assert readiness_of(reviews) is ReadinessLevel.EXPOSED


def test_no_evidence_is_none() -> None:
    assert readiness_of([]) is ReadinessLevel.NONE


def test_assisted_execution_plus_a_contribution_is_assisted() -> None:
    assert readiness_of([
        item("e1", EvidenceRole.ASSISTED_EXECUTION, EvidenceSourceType.INCIDENT),
        item("e2", EvidenceRole.CONTRIBUTION, EvidenceSourceType.TICKET),
    ]) is ReadinessLevel.ASSISTED


def test_one_independent_execution_with_support_is_practiced_not_validated() -> None:
    assert readiness_of([
        item("e1", EvidenceRole.INDEPENDENT_EXECUTION, EvidenceSourceType.INCIDENT),
        item("e2", EvidenceRole.CONTRIBUTION, EvidenceSourceType.PULL_REQUEST),
    ]) is ReadinessLevel.PRACTICED


def test_two_independent_executions_from_one_source_type_are_not_validated() -> None:
    """The PRACTICED to VALIDATED boundary is repetition *and* diversity. Two incidents from the
    same pager rotation are one kind of proof."""
    assert readiness_of([
        item("e1", EvidenceRole.INDEPENDENT_EXECUTION, EvidenceSourceType.INCIDENT),
        item("e2", EvidenceRole.INDEPENDENT_EXECUTION, EvidenceSourceType.INCIDENT),
    ]) is ReadinessLevel.PRACTICED


def test_repeated_independent_execution_across_source_types_is_validated() -> None:
    assert readiness_of([
        item("e1", EvidenceRole.INDEPENDENT_EXECUTION, EvidenceSourceType.INCIDENT),
        item("e2", EvidenceRole.INDEPENDENT_EXECUTION, EvidenceSourceType.INCIDENT),
        item("e3", EvidenceRole.KNOWLEDGE_CAPTURE, EvidenceSourceType.DOCUMENT),
    ]) is ReadinessLevel.VALIDATED


def test_stale_independent_execution_does_not_carry_forward() -> None:
    assert readiness_of([
        item("e1", EvidenceRole.INDEPENDENT_EXECUTION, EvidenceSourceType.INCIDENT,
             Freshness.STALE, date(2021, 1, 1)),
    ]) is ReadinessLevel.ASSISTED


def test_conflicting_evidence_blocks_validated_and_lowers_confidence() -> None:
    items = [
        item("e1", EvidenceRole.INDEPENDENT_EXECUTION, EvidenceSourceType.INCIDENT),
        item("e2", EvidenceRole.INDEPENDENT_EXECUTION, EvidenceSourceType.INCIDENT),
        item("e3", EvidenceRole.KNOWLEDGE_CAPTURE, EvidenceSourceType.DOCUMENT),
        item("e4", EvidenceRole.INDEPENDENT_EXECUTION, EvidenceSourceType.INCIDENT, conflicting=True),
    ]
    summary = aggregate("eng_x", "cap_x", items)
    assert summary.evidence_confidence is EvidenceConfidence.LOW
    assert classify(summary).readiness is not ReadinessLevel.VALIDATED


# ---------------------------------------------------------------------------------------
# Evidence confidence, which is orthogonal to risk
# ---------------------------------------------------------------------------------------


def test_confidence_requires_volume_diversity_and_recency() -> None:
    high = aggregate("eng_x", "cap_x", [
        item("e1", EvidenceRole.INDEPENDENT_EXECUTION, EvidenceSourceType.INCIDENT),
        item("e2", EvidenceRole.CONTRIBUTION, EvidenceSourceType.PULL_REQUEST),
        item("e3", EvidenceRole.KNOWLEDGE_CAPTURE, EvidenceSourceType.DOCUMENT),
    ])
    assert high.evidence_confidence is EvidenceConfidence.HIGH

    medium = aggregate("eng_x", "cap_x", [
        item("e1", EvidenceRole.ASSISTED_EXECUTION, EvidenceSourceType.INCIDENT),
        item("e2", EvidenceRole.CONTRIBUTION, EvidenceSourceType.TICKET),
    ])
    assert medium.evidence_confidence is EvidenceConfidence.MEDIUM

    low = aggregate("eng_x", "cap_x", [
        item("e1", EvidenceRole.EXPOSURE, EvidenceSourceType.CODE_REVIEW),
    ])
    assert low.evidence_confidence is EvidenceConfidence.LOW


def test_last_demonstrated_at_is_the_most_recent_qualifying_artifact() -> None:
    summary = aggregate("eng_x", "cap_x", [
        item("e1", EvidenceRole.INDEPENDENT_EXECUTION, EvidenceSourceType.INCIDENT,
             artifact_date=date(2026, 3, 2)),
        item("e2", EvidenceRole.KNOWLEDGE_CAPTURE, EvidenceSourceType.DOCUMENT,
             artifact_date=date(2026, 6, 1)),
    ])
    assert summary.last_demonstrated_at == date(2026, 6, 1)
