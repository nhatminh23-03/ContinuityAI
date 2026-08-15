"""Capability exposure, risk class, and the Continuity Risk Index. PRD sections 17.1 and 17.2.

The rule class is the authoritative output. The index is a derived comparison number, clamped to
the band of its class so a modifier can never silently reclassify anything. It is **not** a
probability of outage, of departure, or of anything else (PRD section 12 of the API contract).

Exposure separates two conditions the specifications originally collapsed (contract decision
CI-03):

* `DEGRADED` — coverage exists but resilience does not. One person can do this today.
* `CRITICAL_GAP` — no adequate coverage would remain at all.

That separation is what makes the counterfactual able to *create* a new critical gap. Under the
original rule R1, a capability could only lose adequate coverage if it already had no adequate
backup, which was R1's own trigger — so the simulation could never change anything, and the
frozen `before.critical_gap_count: 0` state was unreachable.

Risk class scales with operational criticality
----------------------------------------------
PRD rule R1 as written assigns CRITICAL class to any CRITICAL-or-HIGH capability with no
adequate coverage. Implemented literally, every uncovered capability in the portfolio reads
CRITICAL, the criticality dimension collapses, and a HIGH capability with a gap becomes
indistinguishable from a CRITICAL one. The class therefore scales:

    no adequate coverage    CRITICAL criticality -> CRITICAL      HIGH -> HIGH
    one adequate engineer   CRITICAL criticality -> HIGH          HIGH -> MODERATE

Exposure is unchanged — both still reach `CRITICAL_GAP` and `DEGRADED` respectively, so the
gap counts and the demo beats are unaffected. Logged as DEC-07.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.continuity.facts import CapabilityFacts
from app.continuity.reason_codes import MODIFIER_DELTAS, CapabilityReason, IndexModifier
from app.models.enums import RunbookState
from app.schemas.enums import (
    CapabilityExposure,
    ContinuityRiskClass,
    EvidenceConfidence,
    OperationalCriticality,
    ReadinessLevel,
)

# PRD section 17.2. (low, high, anchor)
CLASS_BANDS: dict[ContinuityRiskClass, tuple[int, int, int]] = {
    ContinuityRiskClass.LOW: (0, 39, 20),
    ContinuityRiskClass.MODERATE: (40, 59, 50),
    ContinuityRiskClass.HIGH: (60, 79, 70),
    ContinuityRiskClass.CRITICAL: (80, 100, 90),
}

# Below this, the honest answer is that the data cannot support a responsible assessment.
# PRD rule R5 and AC-12.
MIN_EVIDENCE_FOR_ASSESSMENT = 2

_ELEVATED_CRITICALITY = {OperationalCriticality.CRITICAL, OperationalCriticality.HIGH}


@dataclass(frozen=True)
class CapabilityAssessmentResult:
    capability_id: str
    exposure: CapabilityExposure
    continuity_risk_class: ContinuityRiskClass | None
    continuity_risk_index: int | None
    evidence_confidence: EvidenceConfidence
    rules_triggered: list[str] = field(default_factory=list)
    index_modifiers: list[dict] = field(default_factory=list)
    primary_engineer_id: str | None = None
    best_remaining_engineer_id: str | None = None
    adequate_engineer_count: int = 0
    best_readiness: ReadinessLevel = ReadinessLevel.NONE


def assess(facts: CapabilityFacts) -> CapabilityAssessmentResult:
    primary = facts.primary
    alternative = facts.best_alternative
    confidence = primary.evidence_confidence if primary else EvidenceConfidence.LOW

    if _is_insufficient(facts):
        # No class and no index. A number here would be a fabrication dressed as an assessment,
        # and PRD section 11.2 of the API contract explicitly permits a null index in this state.
        return CapabilityAssessmentResult(
            capability_id=facts.capability_id,
            exposure=CapabilityExposure.INSUFFICIENT_EVIDENCE,
            continuity_risk_class=None,
            continuity_risk_index=None,
            evidence_confidence=EvidenceConfidence.LOW,
            rules_triggered=[CapabilityReason.INSUFFICIENT_EVIDENCE.value],
            primary_engineer_id=primary.engineer_id if primary else None,
            best_remaining_engineer_id=alternative.engineer_id if alternative else None,
            adequate_engineer_count=facts.adequate_count,
            best_readiness=primary.readiness if primary else ReadinessLevel.NONE,
        )

    exposure, risk_class, reasons = _classify(facts)
    modifiers = _modifiers(facts)
    index = _index(risk_class, modifiers)
    reasons.extend(_evidence_reasons(facts, confidence))

    return CapabilityAssessmentResult(
        capability_id=facts.capability_id,
        exposure=exposure,
        continuity_risk_class=risk_class,
        continuity_risk_index=index,
        evidence_confidence=confidence,
        rules_triggered=reasons,
        index_modifiers=[{"code": code.value, "delta": delta} for code, delta in modifiers],
        primary_engineer_id=primary.engineer_id if primary else None,
        best_remaining_engineer_id=alternative.engineer_id if alternative else None,
        adequate_engineer_count=facts.adequate_count,
        best_readiness=primary.readiness if primary else ReadinessLevel.NONE,
    )


def _is_insufficient(facts: CapabilityFacts) -> bool:
    if facts.total_evidence_count < MIN_EVIDENCE_FOR_ASSESSMENT:
        return True
    # Evidence exists but none of it supports a coverage claim and none of it is trustworthy.
    if not facts.coverages:
        return True
    if facts.adequate_count == 0 and all(
        c.evidence_confidence is EvidenceConfidence.LOW for c in facts.coverages
    ):
        primary = facts.primary
        if primary is None or primary.rank < 2:  # below ASSISTED
            return True
    return False


def _classify(
    facts: CapabilityFacts,
) -> tuple[CapabilityExposure, ContinuityRiskClass, list[str]]:
    criticality = facts.operational_criticality
    elevated = criticality in _ELEVATED_CRITICALITY
    adequate = facts.adequate_count
    reasons: list[str] = []

    if criticality is OperationalCriticality.CRITICAL:
        reasons.append(CapabilityReason.CRITICAL_CAPABILITY.value)
    elif criticality is OperationalCriticality.HIGH:
        reasons.append(CapabilityReason.HIGH_CAPABILITY.value)

    if adequate == 0:
        reasons.append(CapabilityReason.NO_PRACTICED_OR_VALIDATED_COVERAGE.value)
        if not elevated:
            # A medium or low capability with nobody practised is worth surfacing, but calling
            # it a critical gap would devalue the term where it matters.
            return CapabilityExposure.DEGRADED, ContinuityRiskClass.MODERATE, reasons
        risk_class = (
            ContinuityRiskClass.CRITICAL
            if criticality is OperationalCriticality.CRITICAL
            else ContinuityRiskClass.HIGH
        )
        return CapabilityExposure.CRITICAL_GAP, risk_class, reasons

    if adequate == 1:
        sole = facts.adequate[0]
        reasons.append(
            CapabilityReason.SINGLE_VALIDATED_ENGINEER.value
            if sole.readiness is ReadinessLevel.VALIDATED
            else CapabilityReason.SINGLE_PRACTICED_ENGINEER.value
        )
        reasons.append(CapabilityReason.NO_PRACTICED_OR_VALIDATED_BACKUP.value)
        if not elevated:
            return CapabilityExposure.COVERED, ContinuityRiskClass.MODERATE, reasons
        risk_class = (
            ContinuityRiskClass.HIGH
            if criticality is OperationalCriticality.CRITICAL
            else ContinuityRiskClass.MODERATE
        )
        return CapabilityExposure.DEGRADED, risk_class, reasons

    reasons.append(CapabilityReason.ADEQUATE_BACKUP_PRESENT.value)
    has_validated = any(c.readiness is ReadinessLevel.VALIDATED for c in facts.adequate)
    risk_class = ContinuityRiskClass.LOW if has_validated else ContinuityRiskClass.MODERATE
    return CapabilityExposure.COVERED, risk_class, reasons


def _evidence_reasons(facts: CapabilityFacts, confidence: EvidenceConfidence) -> list[str]:
    reasons: list[str] = []
    if confidence is EvidenceConfidence.LOW:
        reasons.append(CapabilityReason.LOW_EVIDENCE_CONFIDENCE.value)
    if facts.conflicting_evidence_count:
        reasons.append(CapabilityReason.CONFLICTING_EVIDENCE.value)
    if facts.has_stale_adequate:
        reasons.append(CapabilityReason.STALE_ADEQUATE_COVERAGE.value)
    if facts.runbook_state is RunbookState.MISSING:
        reasons.append(CapabilityReason.MISSING_RUNBOOK.value)
    elif facts.runbook_state is RunbookState.INCOMPLETE:
        reasons.append(CapabilityReason.INCOMPLETE_RUNBOOK.value)
    elif facts.runbook_state is RunbookState.CURRENT:
        reasons.append(CapabilityReason.CURRENT_RUNBOOK.value)
    return reasons


def _modifiers(facts: CapabilityFacts) -> list[tuple[IndexModifier, int]]:
    """Small, inspectable adjustments. PRD section 17.2.

    Coverage modifiers are mutually exclusive by construction: when two or more engineers are
    adequate, the second one *is* the backup, so `SECOND_*` applies and `BEST_ALTERNATIVE_*`
    does not. Applying both would count one fact twice.
    """
    applied: list[IndexModifier] = []
    adequate = facts.adequate

    if len(adequate) >= 2:
        second = adequate[1]
        applied.append(
            IndexModifier.SECOND_VALIDATED_ENGINEER
            if second.readiness is ReadinessLevel.VALIDATED
            else IndexModifier.SECOND_PRACTICED_ENGINEER
        )
    else:
        if len(adequate) == 1:
            applied.append(IndexModifier.SOLE_ADEQUATE_ENGINEER)
        # With at most one adequate engineer, what matters is how close the next person is.
        fallback = facts.best_alternative if len(adequate) == 1 else facts.primary
        if fallback is None:
            applied.append(IndexModifier.BEST_ALTERNATIVE_EXPOSED_OR_NONE)
        elif fallback.readiness is ReadinessLevel.ASSISTED:
            applied.append(IndexModifier.BEST_ALTERNATIVE_ASSISTED)
        else:
            applied.append(IndexModifier.BEST_ALTERNATIVE_EXPOSED_OR_NONE)

    if facts.runbook_state is RunbookState.MISSING:
        applied.append(IndexModifier.RUNBOOK_MISSING)
    elif facts.runbook_state is RunbookState.INCOMPLETE:
        applied.append(IndexModifier.RUNBOOK_INCOMPLETE)
    elif facts.runbook_state is RunbookState.CURRENT:
        applied.append(IndexModifier.RUNBOOK_CURRENT)

    return [(code, MODIFIER_DELTAS[code]) for code in applied]


def _index(risk_class: ContinuityRiskClass, modifiers: list[tuple[IndexModifier, int]]) -> int:
    low, high, anchor = CLASS_BANDS[risk_class]
    raw = anchor + sum(delta for _, delta in modifiers)
    return max(low, min(high, raw))


def band_for(risk_class: ContinuityRiskClass) -> tuple[int, int]:
    low, high, _ = CLASS_BANDS[risk_class]
    return low, high
