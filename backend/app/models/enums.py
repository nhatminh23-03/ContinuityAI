"""Internal enums that are NOT part of the wire contract.

Everything in `app/schemas/enums.py` crosses the API boundary and is frozen. The values
below never leave the backend, so they can change without a Category C decision.
"""

from enum import Enum


class StrEnum(str, Enum):
    """String enum so values persist as their literal text."""


class RunbookState(StrEnum):
    """Documentation adequacy for a capability.

    Feeds the documentation modifiers in the Continuity Risk Index (PRD section 17.2).

    This is seeded, not derived. Nothing in the evidence schema expresses whether a
    runbook actually covers a failure path — `KNOWLEDGE_CAPTURE` evidence proves a
    document was written, not that it is complete. `NOT_ASSESSED` contributes nothing
    and is the honest default. See RECOMMENDATIONS.md R-06.
    """

    CURRENT = "CURRENT"
    INCOMPLETE = "INCOMPLETE"
    MISSING = "MISSING"
    NOT_ASSESSED = "NOT_ASSESSED"


class ParticipantRole(StrEnum):
    """How an engineer appears in a raw artifact, before interpretation.

    These come from the source system, not from inference: incident platforms record who
    resolved versus who assisted, review systems record author versus reviewer. The AI
    layer maps (source_type, participant_role, text) onto an `EvidenceRole`.
    """

    RESOLVER = "RESOLVER"
    ASSISTING_RESPONDER = "ASSISTING_RESPONDER"
    COMMENTER = "COMMENTER"
    AUTHOR = "AUTHOR"
    REVIEWER = "REVIEWER"
    ASSIGNEE = "ASSIGNEE"
    REPORTER = "REPORTER"
    ATTESTING_MANAGER = "ATTESTING_MANAGER"
