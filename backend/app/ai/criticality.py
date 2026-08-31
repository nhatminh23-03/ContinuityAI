"""AI-suggested system business criticality. FR-010.

The requirement is unusually careful about its own limits: "AI **may** suggest system criticality; a
human-confirmed value is **authoritative**." Both halves are implemented here, and the second is the
one worth being strict about — a suggestion that can quietly overwrite a human's answer is not a
suggestion.

So the resolution rule is small and blunt: a suggestion is *recorded* for every system, and it is only
ever *used* where no human has confirmed a value. On the seeded organisation all five systems are
`HUMAN_CONFIRMED`, which means every number in the demo is unchanged by this module and the suggestions
sit alongside as a comparison. That is not the feature being inert — being overridable is the feature.

The comparison is worth more than the suggestion. Agreement between a model and five human-confirmed
values says something checkable about whether the model understands the estate; a disagreement is a
question for a manager rather than an error. `scripts/suggest_criticality.py` reports it.

Why criticality and not readiness. Business criticality is a judgement about a *system* from its stated
purpose, so a model reading a description is doing the same kind of work a person would. Readiness is a
judgement about a person, computed from evidence by rules, and no model touches it — see
`docs/DECISIONS.md` and the PRD's "AI extracts; deterministic logic scores".
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from app.ai.extraction import parse_json_block
from app.schemas.enums import BusinessCriticality, CriticalitySource, EvidenceConfidence

logger = logging.getLogger(__name__)

PROMPT_FILE = Path(__file__).parent / "prompts" / "criticality_system.txt"
CRITICALITY_MAX_TOKENS = 250


@dataclass(frozen=True)
class CriticalitySuggestion:
    system_id: str
    business_criticality: BusinessCriticality
    rationale: str
    confidence: EvidenceConfidence
    suggested_by: str


@dataclass(frozen=True)
class SystemDescription:
    """What the model is given. Deliberately no engineer, no headcount, no activity volume.

    Those are the inputs that would turn "how important is this system" into "how busy is this team",
    which is the inference this product exists to argue against.
    """

    system_id: str
    name: str
    description: str
    platform_name: str
    component_names: list[str]
    capability_names: list[str]


def system_prompt() -> str:
    return PROMPT_FILE.read_text()


def build_user_prompt(system: SystemDescription) -> str:
    return (
        f"PLATFORM\n{system.platform_name}\n\n"
        f"SYSTEM\nname: {system.name}\ndescription: {system.description or '(none recorded)'}\n\n"
        f"COMPONENTS\n" + ("\n".join(f"- {c}" for c in system.component_names) or "- none") + "\n\n"
        f"OPERATIONAL CAPABILITIES\n"
        + ("\n".join(f"- {c}" for c in system.capability_names) or "- none")
        + "\n"
    )


def suggest(system: SystemDescription, *, chat, provider_label: str) -> CriticalitySuggestion | None:
    """One suggestion, or None if the model could not produce a usable one.

    Returns None rather than raising, and rather than guessing. This is an optional enrichment — the
    PRD says "may" — so a failure here must not stop a seed or a script. A missing suggestion is a
    correct outcome; a fabricated one would be a wrong answer wearing the same clothes.
    """
    try:
        raw = chat(system_prompt(), build_user_prompt(system), CRITICALITY_MAX_TOKENS)
        payload = parse_json_block(raw)
        criticality = BusinessCriticality(
            str(payload.get("business_criticality", "")).strip().upper()
        )
        rationale = str(payload.get("rationale") or "").strip()
        if not rationale:
            logger.warning("criticality suggestion for %s had no rationale; discarded", system.system_id)
            return None
        try:
            confidence = EvidenceConfidence(str(payload.get("confidence", "LOW")).strip().upper())
        except ValueError:
            confidence = EvidenceConfidence.LOW
        return CriticalitySuggestion(
            system_id=system.system_id,
            business_criticality=criticality,
            rationale=rationale,
            confidence=confidence,
            suggested_by=provider_label,
        )
    except Exception as exc:  # noqa: BLE001 — an optional enrichment never breaks the caller
        logger.warning("criticality suggestion for %s failed (%s)", system.system_id, exc)
        return None


def resolve(
    *,
    human_value: BusinessCriticality | None,
    human_confirmed: bool,
    suggestion: CriticalitySuggestion | None,
) -> tuple[BusinessCriticality | None, CriticalitySource]:
    """The FR-010 precedence rule, in one place so it cannot be applied inconsistently.

    A human-confirmed value wins outright, and it wins *even when the model disagrees* — the
    disagreement is worth surfacing to a manager, and is not grounds for the system to change its own
    mind. Only an unconfirmed system takes the model's answer, and it is then labelled `AI_SUGGESTED`
    so the interface can say where the value came from rather than presenting all criticality as
    equally settled.
    """
    if human_confirmed and human_value is not None:
        return human_value, CriticalitySource.HUMAN_CONFIRMED
    if suggestion is not None:
        return suggestion.business_criticality, CriticalitySource.AI_SUGGESTED
    return human_value, CriticalitySource.HUMAN_CONFIRMED


def agreement(
    human_value: BusinessCriticality, suggestion: CriticalitySuggestion | None
) -> str:
    """How the model's answer compares to the human one, for the comparison report."""
    if suggestion is None:
        return "no suggestion"
    if suggestion.business_criticality is human_value:
        return "agrees"
    return f"differs ({human_value.value} -> {suggestion.business_criticality.value})"
