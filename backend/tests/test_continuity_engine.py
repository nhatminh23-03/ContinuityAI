"""Unit tests for the deterministic continuity rules.

No database. These build facts directly so each rule can be pinned in isolation, and they encode
the numbers the frozen fixtures depend on. If one of these fails, the demo's headline figures have
moved and `fixtures/` needs a coordinated update — not a quiet re-baseline.
"""

from __future__ import annotations

import pytest

from app.continuity.aggregation import aggregate_system
from app.continuity.exposure import CLASS_BANDS, assess
from app.continuity.facts import CapabilityFacts, CoverageFact, SystemFacts
from app.continuity.reason_codes import CapabilityReason, SystemReason
from app.models.enums import RunbookState
from app.schemas.enums import (
    CapabilityExposure,
    ContinuityRiskClass,
    EvidenceConfidence,
    Freshness,
    OperationalCriticality,
    ReadinessLevel,
)

R, F, C, OC = ReadinessLevel, Freshness, EvidenceConfidence, OperationalCriticality


def coverage(engineer_id: str, readiness: R, freshness: F = F.FRESH, confidence: C = C.HIGH, count: int = 3) -> CoverageFact:
    return CoverageFact(engineer_id, engineer_id.title(), readiness, freshness, confidence, count)


def capability(
    capability_id: str,
    criticality: OC,
    coverages: list[CoverageFact],
    runbook: RunbookState = RunbookState.NOT_ASSESSED,
    total_evidence: int = 6,
) -> CapabilityFacts:
    return CapabilityFacts(
        capability_id=capability_id,
        name=capability_id.replace("cap_", "").replace("_", " ").title(),
        component_id="component_x",
        system_id="system_x",
        operational_criticality=criticality,
        runbook_state=runbook,
        coverages=tuple(coverages),
        total_evidence_count=total_evidence,
    )


# ---------------------------------------------------------------------------------------
# Exposure: the distinction between no redundancy and no coverage (contract decision CI-03)
# ---------------------------------------------------------------------------------------


def test_sole_expert_on_a_critical_capability_is_degraded_not_a_gap() -> None:
    """Coverage exists, resilience does not. This is what makes the simulation able to change
    something: if a sole-expert capability were already CRITICAL_GAP, removing the expert could
    not make it worse."""
    result = assess(capability("cap_a", OC.CRITICAL, [coverage("alex", R.VALIDATED), coverage("maria", R.ASSISTED)]))
    assert result.exposure is CapabilityExposure.DEGRADED
    assert result.continuity_risk_class is ContinuityRiskClass.HIGH


def test_no_adequate_coverage_on_a_critical_capability_is_a_critical_gap() -> None:
    result = assess(capability("cap_a", OC.CRITICAL, [coverage("maria", R.ASSISTED), coverage("jordan", R.EXPOSED)]))
    assert result.exposure is CapabilityExposure.CRITICAL_GAP
    assert result.continuity_risk_class is ContinuityRiskClass.CRITICAL


def test_two_adequate_engineers_is_covered() -> None:
    result = assess(capability("cap_a", OC.CRITICAL, [coverage("alex", R.VALIDATED), coverage("maria", R.VALIDATED)]))
    assert result.exposure is CapabilityExposure.COVERED
    assert result.continuity_risk_class is ContinuityRiskClass.LOW


def test_risk_class_scales_with_operational_criticality() -> None:
    """DEC-07. A HIGH capability with no coverage is a real gap, but calling it CRITICAL risk
    collapses the criticality dimension — every uncovered capability would read the same."""
    critical = assess(capability("cap_a", OC.CRITICAL, [coverage("maria", R.EXPOSED)]))
    high = assess(capability("cap_b", OC.HIGH, [coverage("maria", R.EXPOSED)]))

    assert critical.exposure is high.exposure is CapabilityExposure.CRITICAL_GAP
    assert critical.continuity_risk_class is ContinuityRiskClass.CRITICAL
    assert high.continuity_risk_class is ContinuityRiskClass.HIGH


def test_medium_capability_without_adequate_coverage_is_degraded_not_critical() -> None:
    result = assess(capability("cap_a", OC.MEDIUM, [coverage("maria", R.EXPOSED)]))
    assert result.exposure is CapabilityExposure.DEGRADED
    assert result.continuity_risk_class is ContinuityRiskClass.MODERATE


def test_stale_evidence_does_not_count_as_adequate_coverage() -> None:
    """PRD rule R6. Someone who last did this three years ago is not current coverage."""
    result = assess(
        capability("cap_a", OC.CRITICAL, [coverage("alex", R.VALIDATED, F.STALE), coverage("maria", R.EXPOSED)])
    )
    assert result.exposure is CapabilityExposure.CRITICAL_GAP
    assert CapabilityReason.STALE_ADEQUATE_COVERAGE.value in result.rules_triggered


def test_sparse_evidence_returns_insufficient_evidence_with_no_number() -> None:
    """AC-12. A fabricated index would be worse than admitting the data cannot support one."""
    result = assess(capability("cap_a", OC.MEDIUM, [coverage("grace", R.EXPOSED, count=1)], total_evidence=1))
    assert result.exposure is CapabilityExposure.INSUFFICIENT_EVIDENCE
    assert result.continuity_risk_index is None
    assert result.continuity_risk_class is None
    assert result.rules_triggered == [CapabilityReason.INSUFFICIENT_EVIDENCE.value]


# ---------------------------------------------------------------------------------------
# The index
# ---------------------------------------------------------------------------------------


def test_index_is_clamped_to_the_band_of_its_class() -> None:
    """PRD section 17.2. Modifiers adjust for comparison; they must never reclassify."""
    result = assess(
        capability(
            "cap_a",
            OC.CRITICAL,
            [coverage("alex", R.VALIDATED), coverage("maria", R.EXPOSED)],
            runbook=RunbookState.MISSING,
        )
    )
    low, high = CLASS_BANDS[result.continuity_risk_class][:2]
    assert low <= result.continuity_risk_index <= high


@pytest.mark.parametrize(
    ("runbook", "expected"),
    [(RunbookState.NOT_ASSESSED, 72), (RunbookState.CURRENT, 69), (RunbookState.INCOMPLETE, 75)],
)
def test_documentation_state_moves_the_index_within_the_band(runbook: RunbookState, expected: int) -> None:
    result = assess(
        capability(
            "cap_a",
            OC.CRITICAL,
            [coverage("alex", R.VALIDATED), coverage("maria", R.ASSISTED), coverage("jordan", R.EXPOSED)],
            runbook=runbook,
        )
    )
    assert result.continuity_risk_index == expected


def test_reason_codes_describe_the_classification_not_the_modifiers() -> None:
    """`rules_triggered` answers "which rules decided this". Modifiers only nudge the number and
    are reported separately, so the list stays short enough to read."""
    result = assess(
        capability("cap_a", OC.CRITICAL, [coverage("alex", R.VALIDATED), coverage("maria", R.ASSISTED)])
    )
    assert result.rules_triggered == [
        CapabilityReason.CRITICAL_CAPABILITY.value,
        CapabilityReason.SINGLE_VALIDATED_ENGINEER.value,
        CapabilityReason.NO_PRACTICED_OR_VALIDATED_BACKUP.value,
    ]
    assert [m["code"] for m in result.index_modifiers] == [
        "SOLE_ADEQUATE_ENGINEER",
        "BEST_ALTERNATIVE_ASSISTED",
    ]


# ---------------------------------------------------------------------------------------
# The hero scenario, end to end through the rules
# ---------------------------------------------------------------------------------------


def payment_gateway() -> SystemFacts:
    """The seeded Payment Gateway coverage, per PRD appendix A.2 plus the wider team."""
    return SystemFacts(
        system_id="system_payment_gateway",
        name="Payment Gateway",
        platform_id="platform_payments",
        business_criticality="CRITICAL",
        capabilities=(
            capability("cap_incident_recovery", OC.CRITICAL, [
                coverage("alex", R.VALIDATED),
                coverage("maria", R.ASSISTED, confidence=C.MEDIUM, count=2),
                coverage("jordan", R.EXPOSED, F.AGING, C.MEDIUM, 2),
            ]),
            capability("cap_provider_failover", OC.HIGH, [
                coverage("alex", R.PRACTICED), coverage("maria", R.PRACTICED), coverage("jordan", R.EXPOSED),
            ]),
            capability("cap_certificate_management", OC.CRITICAL, [
                coverage("alex", R.VALIDATED), coverage("maria", R.EXPOSED),
            ]),
            capability("cap_retry_logic", OC.HIGH, [
                coverage("alex", R.VALIDATED), coverage("jordan", R.VALIDATED),
                coverage("omar", R.PRACTICED), coverage("maria", R.EXPOSED),
            ]),
            capability("cap_monitoring", OC.MEDIUM, [
                coverage("maria", R.VALIDATED), coverage("lena", R.VALIDATED),
                coverage("alex", R.PRACTICED), coverage("jordan", R.ASSISTED),
            ]),
        ),
    )


def evaluate(facts: SystemFacts):
    results = {c.capability_id: assess(c) for c in facts.capabilities}
    return results, aggregate_system(facts, results)


def test_seeded_baseline_reproduces_the_frozen_fixture_values() -> None:
    results, system = evaluate(payment_gateway())

    assert results["cap_incident_recovery"].continuity_risk_index == 72
    assert system.continuity_risk_index == 74
    assert system.continuity_risk_class is ContinuityRiskClass.HIGH
    assert system.exposure is CapabilityExposure.DEGRADED
    assert system.evidence_confidence is EvidenceConfidence.HIGH
    assert (system.critical_gap_count, system.degraded_capability_count, system.covered_capability_count) == (0, 2, 3)
    assert system.rules_triggered == [
        SystemReason.CRITICAL_CAPABILITY_DEGRADED.value,
        SystemReason.MULTIPLE_SOLE_EXPERT_CAPABILITIES.value,
    ]


def test_removing_the_sole_expert_creates_two_critical_gaps_and_preserves_retry_logic() -> None:
    """AC-06 in rule form: the result must be specific about which capabilities move and which
    do not. "Alex is important" is what the product exists to replace."""
    baseline = payment_gateway()
    _, before = evaluate(baseline)
    after_results, after = evaluate(baseline.without("alex"))

    assert after.continuity_risk_index == 93
    assert after.continuity_risk_class is ContinuityRiskClass.CRITICAL
    assert (after.critical_gap_count, after.degraded_capability_count, after.covered_capability_count) == (2, 1, 2)

    assert after_results["cap_incident_recovery"].exposure is CapabilityExposure.CRITICAL_GAP
    assert after_results["cap_certificate_management"].exposure is CapabilityExposure.CRITICAL_GAP
    assert after_results["cap_provider_failover"].exposure is CapabilityExposure.DEGRADED
    assert after_results["cap_retry_logic"].exposure is CapabilityExposure.COVERED
    assert after_results["cap_retry_logic"].best_readiness is R.VALIDATED
    assert before.continuity_risk_index == 74, "baseline must not be mutated by the counterfactual"


def test_counterfactual_does_not_mutate_the_baseline_facts() -> None:
    """ARCHITECTURE.md quality bar E. Frozen facts make this structural, not a matter of care."""
    baseline = payment_gateway()
    original = baseline.capabilities[0].coverages
    baseline.without("alex")
    assert baseline.capabilities[0].coverages == original


def test_system_risk_does_not_average_severe_gaps_away() -> None:
    """PRD section 17.3. Nine healthy capabilities must not dilute one critical gap."""
    facts = SystemFacts(
        system_id="system_x", name="X", platform_id="platform_x", business_criticality="HIGH",
        capabilities=(
            capability("cap_gap", OC.CRITICAL, [coverage("a", R.EXPOSED)]),
            *[
                capability(f"cap_ok_{i}", OC.LOW, [coverage("b", R.VALIDATED), coverage("c", R.VALIDATED)])
                for i in range(9)
            ],
        ),
    )
    _, system = evaluate(facts)
    assert system.continuity_risk_class is ContinuityRiskClass.CRITICAL
    assert system.exposure is CapabilityExposure.CRITICAL_GAP
