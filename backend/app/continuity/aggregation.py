"""Roll capability assessments up to systems and platforms. PRD section 17.3.

The governing constraint is *do not average severe gaps away*. A system with one critical gap and
nine healthy capabilities is not ninety percent healthy — the gap is the thing that will hurt.
So the system index is the **maximum** across its capabilities, and the class is the class of the
capability that produced it. Breadth is communicated through the counts and the fired rules, not
by diluting the number.

Platforms get no index of their own (contract decision CI-10). A platform row shows the highest
system index, the total critical gaps, and drift. Inventing a second aggregation formula is
exactly what that freeze exists to prevent, and "where do I look first?" is already answered by
the highest system plus a gap count.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.continuity.exposure import CapabilityAssessmentResult
from app.continuity.facts import SystemFacts
from app.continuity.reason_codes import SystemReason
from app.schemas.enums import (
    CapabilityExposure,
    ContinuityRiskClass,
    EvidenceConfidence,
    OperationalCriticality,
)

# Worst first. INSUFFICIENT_EVIDENCE sits below DEGRADED deliberately: it is a data problem, and
# it should not outrank a coverage problem the evidence does support.
EXPOSURE_SEVERITY: dict[CapabilityExposure, int] = {
    CapabilityExposure.CRITICAL_GAP: 3,
    CapabilityExposure.DEGRADED: 2,
    CapabilityExposure.INSUFFICIENT_EVIDENCE: 1,
    CapabilityExposure.COVERED: 0,
}

CONFIDENCE_RANK: dict[EvidenceConfidence, int] = {
    EvidenceConfidence.LOW: 0,
    EvidenceConfidence.MEDIUM: 1,
    EvidenceConfidence.HIGH: 2,
}


@dataclass(frozen=True)
class SystemAssessmentResult:
    system_id: str
    exposure: CapabilityExposure
    continuity_risk_class: ContinuityRiskClass | None
    continuity_risk_index: int | None
    evidence_confidence: EvidenceConfidence
    critical_gap_count: int = 0
    degraded_capability_count: int = 0
    covered_capability_count: int = 0
    insufficient_evidence_count: int = 0
    rules_triggered: list[str] = field(default_factory=list)
    driving_capability_id: str | None = None


@dataclass(frozen=True)
class PlatformAssessmentResult:
    platform_id: str
    system_count: int
    critical_gap_count: int
    highest_system_risk_index: int | None


def aggregate_system(
    facts: SystemFacts, results: dict[str, CapabilityAssessmentResult]
) -> SystemAssessmentResult:
    assessments = [results[c.capability_id] for c in facts.capabilities if c.capability_id in results]

    if not assessments:
        return SystemAssessmentResult(
            system_id=facts.system_id,
            exposure=CapabilityExposure.INSUFFICIENT_EVIDENCE,
            continuity_risk_class=None,
            continuity_risk_index=None,
            evidence_confidence=EvidenceConfidence.LOW,
            rules_triggered=[SystemReason.INSUFFICIENT_EVIDENCE_PRESENT.value],
        )

    counts = {exposure: 0 for exposure in CapabilityExposure}
    for assessment in assessments:
        counts[assessment.exposure] += 1

    worst = max(assessments, key=lambda a: EXPOSURE_SEVERITY[a.exposure])
    scored = [a for a in assessments if a.continuity_risk_index is not None]
    driver = (
        max(
            scored,
            key=lambda a: (
                a.continuity_risk_index,
                EXPOSURE_SEVERITY[a.exposure],
                a.capability_id,
            ),
        )
        if scored
        else None
    )

    return SystemAssessmentResult(
        system_id=facts.system_id,
        exposure=worst.exposure,
        continuity_risk_class=driver.continuity_risk_class if driver else None,
        continuity_risk_index=driver.continuity_risk_index if driver else None,
        evidence_confidence=_system_confidence(assessments),
        critical_gap_count=counts[CapabilityExposure.CRITICAL_GAP],
        degraded_capability_count=counts[CapabilityExposure.DEGRADED],
        covered_capability_count=counts[CapabilityExposure.COVERED],
        insufficient_evidence_count=counts[CapabilityExposure.INSUFFICIENT_EVIDENCE],
        rules_triggered=_system_reasons(facts, results),
        driving_capability_id=driver.capability_id if driver else None,
    )


def _system_confidence(assessments: list[CapabilityAssessmentResult]) -> EvidenceConfidence:
    """Confidence of the capabilities that are actually driving concern.

    Averaging across a whole system would let twenty well-evidenced healthy capabilities mask
    thin evidence on the one that is exposed.
    """
    exposed = [
        a
        for a in assessments
        if a.exposure in {CapabilityExposure.CRITICAL_GAP, CapabilityExposure.DEGRADED}
    ]
    considered = exposed or assessments
    return min(
        (a.evidence_confidence for a in considered),
        key=lambda c: CONFIDENCE_RANK[c],
        default=EvidenceConfidence.LOW,
    )


def _system_reasons(
    facts: SystemFacts, results: dict[str, CapabilityAssessmentResult]
) -> list[str]:
    reasons: list[str] = []
    critical_gap = high_gap = critical_degraded = high_degraded = False
    sole_expert = 0
    insufficient = False
    low_confidence = False

    for capability in facts.capabilities:
        assessment = results.get(capability.capability_id)
        if assessment is None:
            continue
        is_critical = capability.operational_criticality is OperationalCriticality.CRITICAL
        is_high = capability.operational_criticality is OperationalCriticality.HIGH

        if assessment.exposure is CapabilityExposure.CRITICAL_GAP:
            critical_gap = critical_gap or is_critical
            high_gap = high_gap or is_high
        elif assessment.exposure is CapabilityExposure.DEGRADED:
            critical_degraded = critical_degraded or is_critical
            high_degraded = high_degraded or is_high
        elif assessment.exposure is CapabilityExposure.INSUFFICIENT_EVIDENCE:
            insufficient = True

        if assessment.adequate_engineer_count == 1:
            sole_expert += 1
        if assessment.evidence_confidence is EvidenceConfidence.LOW:
            low_confidence = True

    if critical_gap:
        reasons.append(SystemReason.CRITICAL_CAPABILITY_GAP.value)
    if high_gap:
        reasons.append(SystemReason.HIGH_CAPABILITY_GAP.value)
    if critical_degraded:
        reasons.append(SystemReason.CRITICAL_CAPABILITY_DEGRADED.value)
    if high_degraded:
        reasons.append(SystemReason.HIGH_CAPABILITY_DEGRADED.value)
    if sole_expert > 1:
        reasons.append(SystemReason.MULTIPLE_SOLE_EXPERT_CAPABILITIES.value)
    elif sole_expert == 1:
        reasons.append(SystemReason.SOLE_EXPERT_CAPABILITY.value)
    if insufficient:
        reasons.append(SystemReason.INSUFFICIENT_EVIDENCE_PRESENT.value)
    if low_confidence:
        reasons.append(SystemReason.LOW_EVIDENCE_CONFIDENCE.value)

    return reasons


def aggregate_platform(
    platform_id: str, system_results: list[SystemAssessmentResult]
) -> PlatformAssessmentResult:
    indexes = [r.continuity_risk_index for r in system_results if r.continuity_risk_index is not None]
    return PlatformAssessmentResult(
        platform_id=platform_id,
        system_count=len(system_results),
        critical_gap_count=sum(r.critical_gap_count for r in system_results),
        highest_system_risk_index=max(indexes) if indexes else None,
    )
