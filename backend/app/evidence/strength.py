"""Evidence strength, derived from evidence role. PRD section 16.1.

Strength is a deterministic function of role, not an independent judgement. A provider that
returns a disagreeing strength is corrected by `app/ai/validation.py`. Keeping the mapping in
one place is what stops "how strong is this?" from becoming a second, competing opinion.

    WEAK      exposure only: reviewed, commented, observed. Establishes no execution.
    MODERATE  hands-on but supported or partial: assisted a recovery, authored a change.
    STRONG    independent execution, or authoring the operational knowledge itself.
"""

from __future__ import annotations

from app.schemas.enums import EvidenceRole, EvidenceStrength, ReadinessLevel

_ROLE_STRENGTH: dict[EvidenceRole, EvidenceStrength] = {
    EvidenceRole.EXPOSURE: EvidenceStrength.WEAK,
    EvidenceRole.CONTRIBUTION: EvidenceStrength.MODERATE,
    EvidenceRole.ASSISTED_EXECUTION: EvidenceStrength.MODERATE,
    EvidenceRole.INDEPENDENT_EXECUTION: EvidenceStrength.STRONG,
    EvidenceRole.KNOWLEDGE_CAPTURE: EvidenceStrength.STRONG,
}

READINESS_RANK: dict[ReadinessLevel, int] = {
    ReadinessLevel.NONE: 0,
    ReadinessLevel.EXPOSED: 1,
    ReadinessLevel.ASSISTED: 2,
    ReadinessLevel.PRACTICED: 3,
    ReadinessLevel.VALIDATED: 4,
}

STRENGTH_RANK: dict[EvidenceStrength, int] = {
    EvidenceStrength.WEAK: 0,
    EvidenceStrength.MODERATE: 1,
    EvidenceStrength.STRONG: 2,
}

# Readiness at or above this level counts as adequate coverage of a capability. This single
# threshold is what separates "somebody has done this" from "somebody has watched this happen",
# and it drives every exposure rule downstream.
ADEQUATE_READINESS = {ReadinessLevel.PRACTICED, ReadinessLevel.VALIDATED}

# Display order for a provenance drawer: the record that most directly demonstrates the capability
# first. Sorting by date instead would routinely bury an independent production recovery under a
# more recent document, which is the opposite of what someone asking "why?" needs to see.
EVIDENCE_ROLE_PRIORITY: dict[EvidenceRole, int] = {
    EvidenceRole.INDEPENDENT_EXECUTION: 0,
    EvidenceRole.KNOWLEDGE_CAPTURE: 1,
    EvidenceRole.ASSISTED_EXECUTION: 2,
    EvidenceRole.CONTRIBUTION: 3,
    EvidenceRole.EXPOSURE: 4,
}


def role_priority(role: EvidenceRole | str) -> int:
    value = EvidenceRole(role) if isinstance(role, str) else role
    return EVIDENCE_ROLE_PRIORITY[value]


def strength_for_role(role: EvidenceRole) -> EvidenceStrength:
    return _ROLE_STRENGTH[role]


def is_adequate(readiness: ReadinessLevel | str) -> bool:
    value = ReadinessLevel(readiness) if isinstance(readiness, str) else readiness
    return value in ADEQUATE_READINESS


def readiness_rank(readiness: ReadinessLevel | str) -> int:
    value = ReadinessLevel(readiness) if isinstance(readiness, str) else readiness
    return READINESS_RANK[value]


def best_readiness(levels: list[ReadinessLevel | str]) -> ReadinessLevel:
    if not levels:
        return ReadinessLevel.NONE
    return max((ReadinessLevel(v) if isinstance(v, str) else v for v in levels), key=readiness_rank)
