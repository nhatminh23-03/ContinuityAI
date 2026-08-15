"""Readiness classification. PRD section 16.2, DOMAIN_MODEL.md section 16.

Deterministic, and the AI layer cannot reach it: extraction produces evidence records, and this
module reads counts off them. DOMAIN_MODEL.md invariants 3 and 4.

    NONE       no qualifying evidence
    EXPOSED    reviewed, discussed, observed — no execution evidenced
    ASSISTED   participated in execution, with support or without independence
    PRACTICED  one current independent execution, plus a supporting item
    VALIDATED  repeated independent execution across more than one kind of artifact

The distinction that matters most is EXPOSED -> ASSISTED -> PRACTICED. It is about
*independence*, never about volume. Twenty reviews stay EXPOSED, because the rules below read
`independent_execution_count`, not `total`. That is the "artifact, not activity" principle
(PRD section 7) expressed as code.

The PRACTICED -> VALIDATED boundary is repetition plus source diversity: two incidents from the
same pager rotation are one kind of proof, an incident plus an authored runbook are two.

These are prototype heuristics for transparent demo logic, not validated competency standards.
Real use would need customer calibration (PRD section 16.2).
"""

from __future__ import annotations

from dataclasses import dataclass

from app.continuity.reason_codes import ReadinessReason
from app.evidence.aggregation import EvidenceAggregate
from app.schemas.enums import Freshness, ReadinessLevel


@dataclass(frozen=True)
class ReadinessResult:
    readiness: ReadinessLevel
    reasons: list[str]


def classify(aggregate: EvidenceAggregate) -> ReadinessResult:
    reasons: list[str] = []

    if aggregate.total == 0:
        if aggregate.conflicting:
            # Every record for this pair contradicts itself. Not "no evidence" — evidence that
            # cannot be relied on, which is a different thing and worth saying.
            return ReadinessResult(ReadinessLevel.NONE, [ReadinessReason.CONFLICTING_EVIDENCE.value])
        return ReadinessResult(ReadinessLevel.NONE, [ReadinessReason.NO_QUALIFYING_EVIDENCE.value])

    if aggregate.conflicting:
        reasons.append(ReadinessReason.CONFLICTING_EVIDENCE.value)

    # VALIDATED — repeated independent execution, more than one kind of artifact, still current.
    if (
        aggregate.independent_execution_count >= 2
        and aggregate.strong_source_type_count >= 2
        and aggregate.has_fresh_strong
        and not aggregate.conflicting
    ):
        return ReadinessResult(
            ReadinessLevel.VALIDATED,
            [
                ReadinessReason.REPEATED_INDEPENDENT_EXECUTION.value,
                ReadinessReason.DIVERSE_STRONG_SOURCES.value,
                ReadinessReason.CURRENT_STRONG_EVIDENCE.value,
            ],
        )

    # PRACTICED — has done it unaided at least once, recently enough to count, with corroboration.
    if (
        aggregate.independent_execution_count >= 1
        and aggregate.has_current_independent
        and aggregate.total >= 2
    ):
        reasons.append(ReadinessReason.SINGLE_INDEPENDENT_EXECUTION.value)
        return ReadinessResult(ReadinessLevel.PRACTICED, reasons)

    # An independent execution that has gone stale, with nothing since, does not carry forward.
    if aggregate.independent_execution_count >= 1 and aggregate.freshness is Freshness.STALE:
        reasons.append(ReadinessReason.STALE_EVIDENCE_ONLY.value)
        return ReadinessResult(ReadinessLevel.ASSISTED, reasons)

    # ASSISTED — meaningful hands-on participation without evidence of independence.
    if aggregate.total >= 2 and (
        aggregate.assisted_execution_count >= 1
        or aggregate.contribution_count >= 1
        or aggregate.knowledge_capture_count >= 1
    ):
        if aggregate.assisted_execution_count >= 1:
            reasons.append(ReadinessReason.ASSISTED_EXECUTION_ONLY.value)
        elif aggregate.knowledge_capture_count >= 1:
            reasons.append(ReadinessReason.KNOWLEDGE_CAPTURE_ONLY.value)
        else:
            reasons.append(ReadinessReason.CONTRIBUTION_ONLY.value)
        return ReadinessResult(ReadinessLevel.ASSISTED, reasons)

    # EXPOSED — has interacted with the capability. Says nothing about ability either way.
    reasons.append(ReadinessReason.EXPOSURE_ONLY.value)
    return ReadinessResult(ReadinessLevel.EXPOSED, reasons)
