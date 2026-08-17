"""The closed reason-code vocabulary.

`API_CONTRACT.md` section 12.1: "Person A owns the closed list of codes." This module is that
list. The frontend writes display copy per code, which keeps responsible-AI wording under joint
review instead of generating prose in the backend, and renders an unrecognised code as its raw
value rather than hiding it.

Two spellings existed in the specifications for the same three concepts —
`SINGLE_VALIDATED_ENGINEER` / `NO_PRACTICED_OR_VALIDATED_BACKUP` / `INCOMPLETE_DOCUMENTATION` in
`API_CONTRACT.md`, versus `SINGLE_VALIDATED_EXPERT` / `NO_READY_BACKUP` / `AGING_DOCUMENTATION`
in `ARCHITECTURE.md` section 29. The contract spelling wins, because the frozen fixtures already
use it and the frontend will already have written copy against it. Logged as DEC-05.

Two separate vocabularies, deliberately:

* **Capability codes** explain why one capability reached its exposure and risk class.
* **System codes** explain the aggregation — why the system reads the way it does given its
  capabilities.

Index modifiers are **not** reason codes. `rules_triggered` answers "which rules decided the
classification"; a modifier only nudges the comparison number inside a band it cannot leave.
Mixing them would make the list longer and less meaningful. Modifiers are persisted separately
on the assessment row.
"""

from __future__ import annotations

from enum import Enum


class StrEnum(str, Enum):
    pass


class CapabilityReason(StrEnum):
    # Criticality context
    CRITICAL_CAPABILITY = "CRITICAL_CAPABILITY"
    HIGH_CAPABILITY = "HIGH_CAPABILITY"

    # Coverage shape
    NO_PRACTICED_OR_VALIDATED_COVERAGE = "NO_PRACTICED_OR_VALIDATED_COVERAGE"
    SINGLE_VALIDATED_ENGINEER = "SINGLE_VALIDATED_ENGINEER"
    SINGLE_PRACTICED_ENGINEER = "SINGLE_PRACTICED_ENGINEER"
    NO_PRACTICED_OR_VALIDATED_BACKUP = "NO_PRACTICED_OR_VALIDATED_BACKUP"
    ADEQUATE_BACKUP_PRESENT = "ADEQUATE_BACKUP_PRESENT"

    # Evidence quality
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    LOW_EVIDENCE_CONFIDENCE = "LOW_EVIDENCE_CONFIDENCE"
    CONFLICTING_EVIDENCE = "CONFLICTING_EVIDENCE"
    STALE_ADEQUATE_COVERAGE = "STALE_ADEQUATE_COVERAGE"

    # Documentation
    MISSING_RUNBOOK = "MISSING_RUNBOOK"
    INCOMPLETE_RUNBOOK = "INCOMPLETE_RUNBOOK"
    CURRENT_RUNBOOK = "CURRENT_RUNBOOK"


class SystemReason(StrEnum):
    CRITICAL_CAPABILITY_GAP = "CRITICAL_CAPABILITY_GAP"
    HIGH_CAPABILITY_GAP = "HIGH_CAPABILITY_GAP"
    CRITICAL_CAPABILITY_DEGRADED = "CRITICAL_CAPABILITY_DEGRADED"
    HIGH_CAPABILITY_DEGRADED = "HIGH_CAPABILITY_DEGRADED"
    SOLE_EXPERT_CAPABILITY = "SOLE_EXPERT_CAPABILITY"
    MULTIPLE_SOLE_EXPERT_CAPABILITIES = "MULTIPLE_SOLE_EXPERT_CAPABILITIES"
    INSUFFICIENT_EVIDENCE_PRESENT = "INSUFFICIENT_EVIDENCE_PRESENT"
    LOW_EVIDENCE_CONFIDENCE = "LOW_EVIDENCE_CONFIDENCE"


class ReadinessReason(StrEnum):
    """Why one engineer reached one readiness level. Feeds the coverage row, not the API."""

    REPEATED_INDEPENDENT_EXECUTION = "REPEATED_INDEPENDENT_EXECUTION"
    DIVERSE_STRONG_SOURCES = "DIVERSE_STRONG_SOURCES"
    CURRENT_STRONG_EVIDENCE = "CURRENT_STRONG_EVIDENCE"
    SINGLE_INDEPENDENT_EXECUTION = "SINGLE_INDEPENDENT_EXECUTION"
    ASSISTED_EXECUTION_ONLY = "ASSISTED_EXECUTION_ONLY"
    CONTRIBUTION_ONLY = "CONTRIBUTION_ONLY"
    KNOWLEDGE_CAPTURE_ONLY = "KNOWLEDGE_CAPTURE_ONLY"
    EXPOSURE_ONLY = "EXPOSURE_ONLY"
    NO_QUALIFYING_EVIDENCE = "NO_QUALIFYING_EVIDENCE"
    CONFLICTING_EVIDENCE = "CONFLICTING_EVIDENCE"
    STALE_EVIDENCE_ONLY = "STALE_EVIDENCE_ONLY"


class IndexModifier(StrEnum):
    """Index adjustments. PRD section 17.2.

    `HIGH_OPERATIONAL_DEPENDENCY` from the PRD table is deliberately **not** implemented. It
    fires when "the majority of recent P1 recovery evidence is concentrated" in one engineer,
    which is true of nearly every sole-expert capability in the seed — so it would add a constant
    to exactly the capabilities the sole-expert modifier already penalises, double-counting one
    signal. RECOMMENDATIONS.md R-08.
    """

    SOLE_ADEQUATE_ENGINEER = "SOLE_ADEQUATE_ENGINEER"
    BEST_ALTERNATIVE_ASSISTED = "BEST_ALTERNATIVE_ASSISTED"
    BEST_ALTERNATIVE_EXPOSED_OR_NONE = "BEST_ALTERNATIVE_EXPOSED_OR_NONE"
    SECOND_PRACTICED_ENGINEER = "SECOND_PRACTICED_ENGINEER"
    SECOND_VALIDATED_ENGINEER = "SECOND_VALIDATED_ENGINEER"
    RUNBOOK_MISSING = "RUNBOOK_MISSING"
    RUNBOOK_INCOMPLETE = "RUNBOOK_INCOMPLETE"
    RUNBOOK_CURRENT = "RUNBOOK_CURRENT"


MODIFIER_DELTAS: dict[IndexModifier, int] = {
    IndexModifier.SOLE_ADEQUATE_ENGINEER: +1,
    IndexModifier.BEST_ALTERNATIVE_ASSISTED: +1,
    IndexModifier.BEST_ALTERNATIVE_EXPOSED_OR_NONE: +3,
    IndexModifier.SECOND_PRACTICED_ENGINEER: -5,
    IndexModifier.SECOND_VALIDATED_ENGINEER: -8,
    IndexModifier.RUNBOOK_MISSING: +5,
    IndexModifier.RUNBOOK_INCOMPLETE: +3,
    IndexModifier.RUNBOOK_CURRENT: -3,
}

ALL_CAPABILITY_REASONS = frozenset(c.value for c in CapabilityReason)
ALL_SYSTEM_REASONS = frozenset(c.value for c in SystemReason)
