"""Model extraction that is shared by every model-backed provider.

FR-004 says "AI shall convert each artifact into structured evidence records using the schema in
Section 15". Nothing about that job is vendor-specific: the prompt, the permitted-id lists, the
discard rules, and the derived evidence strength are all properties of *the task*, not of whichever
gateway carries the request. Only the transport differs.

This module holds the task. `watsonx.py` and `openrouter.py` supply a `chat` callable and a label,
and both then produce byte-comparable extraction from the same prompt and the same rules — which is
what makes the provider comparison in `scripts/extract_with_provider.py` a measurement of the models
rather than a measurement of two hand-written parsers that happen to disagree.

It was originally written once inside `watsonx.py`. Moving it here rather than copying it into the
second provider is the difference between one extraction contract and two that drift.

Three properties are enforced here rather than trusted to the prompt, because a prompt is a request
and this is a guarantee:

* **Closed world.** A `capability_id` outside the supplied list, or an `engineer_id` outside the
  artifact's participants, is discarded and recorded as ambiguity. A model cannot introduce a
  capability or attribute work to someone who was not there.
* **Strength is derived, never accepted.** `evidence_strength` comes from `strength_for_role`
  (PRD 16.1). A model that returns a strength has it overwritten, so it cannot promote its own claim.
* **No uncited claims.** A claim with no summary or no rationale is discarded. Every surviving claim
  can answer "why do you say that?" with words from the artifact.

The real gate is still `app/ai/validation.py`, which every provider's output passes through. The
checks here are the cheap local ones that stop obvious rubbish from getting that far.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Callable

from app.ai.provider import ExtractionContext
from app.ai.schemas import ArtifactExtraction, ArtifactInput, CapabilityClaim
from app.core.errors import AIExtractionError
from app.evidence.strength import strength_for_role
from app.schemas.enums import EvidenceConfidence, EvidenceRole

PROMPT_DIR = Path(__file__).parent / "prompts"
EXTRACTION_SYSTEM_PROMPT_FILE = PROMPT_DIR / "extraction_system.txt"

# Extraction is a classification task, so sampling buys nothing and costs reproducibility, which the
# evaluation in app/evaluation/ depends on.
EXTRACTION_TEMPERATURE = 0.0
EXTRACTION_MAX_TOKENS = 900

_JSON_BLOCK = re.compile(r"\{.*\}", re.DOTALL)


def system_prompt() -> str:
    return EXTRACTION_SYSTEM_PROMPT_FILE.read_text()


def parse_json_block(raw: str) -> dict:
    """Models wrap JSON in prose or fences often enough that this has to be tolerant."""
    text = raw.strip()
    if text.startswith("```"):
        text = text.strip("`")
        text = text[text.find("\n") + 1 :] if "\n" in text else text
        text = text.replace("json\n", "", 1)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = _JSON_BLOCK.search(text)
        if not match:
            raise
        return json.loads(match.group(0))


def nothing_to_extract(artifact: ArtifactInput, context: ExtractionContext) -> ArtifactExtraction | None:
    """The cases where a model call would buy nothing, so it is not made.

    No capability in scope means there is nothing to attribute to; no participants means there is
    nobody to attribute it to. Both are common — most of the corpus is routine work — and paying a
    model call to confirm it would be the single largest waste in a 640-artifact run.
    """
    capabilities = context.by_system(artifact.system_hint)
    if capabilities and artifact.participants:
        return None
    return ArtifactExtraction(
        artifact_id=artifact.artifact_id,
        system_id=artifact.system_hint,
        ambiguity=["no capabilities in scope" if not capabilities else "no participants"],
    )


def build_user_prompt(artifact: ArtifactInput, context: ExtractionContext) -> str:
    """The artifact, plus the two lists the model is allowed to choose from.

    The lists are the closed world. They are given explicitly on every call rather than assumed from
    the system prompt, because the permitted values differ per artifact — they are scoped to the
    artifact's own system.
    """
    capabilities = context.by_system(artifact.system_hint)
    capability_lines = "\n".join(
        f"- {c.capability_id} — {c.name}" + (f" (also called: {', '.join(c.aliases)})" if c.aliases else "")
        for c in capabilities
    )
    participant_lines = "\n".join(
        f"- {p.engineer_id} — {context.engineer_names.get(p.engineer_id, p.engineer_id)} "
        f"— PARTICIPANT_ROLE: {p.participant_role}"
        for p in artifact.participants
    )
    paths = ", ".join(artifact.file_paths) if artifact.file_paths else "none recorded"

    return (
        f"CAPABILITIES (the only permitted capability_id values)\n{capability_lines}\n\n"
        f"PARTICIPANTS (the only permitted engineer_id values)\n{participant_lines}\n\n"
        f"ARTIFACT\n"
        f"type: {artifact.source_type.value}\n"
        f"reference: {artifact.source_reference}\n"
        f"date: {artifact.artifact_date.isoformat()}\n"
        f"files: {paths}\n"
        f"title: {artifact.title or '(none)'}\n"
        f"body:\n{artifact.body or '(empty)'}\n"
    )


def parse_extraction(
    raw: str,
    artifact: ArtifactInput,
    context: ExtractionContext,
    *,
    provider_label: str,
    is_conflicting: bool,
) -> ArtifactExtraction:
    """Turn one model reply into an `ArtifactExtraction`, discarding anything ungrounded.

    `provider_label` is written into each claim's rationale, so a record in the database says which
    model produced it. That is the difference between believing the graph is model-derived and being
    able to show it.
    """
    try:
        payload = parse_json_block(raw)
    except json.JSONDecodeError as exc:
        raise AIExtractionError(
            f"{provider_label} returned output that is not JSON for {artifact.source_reference}.",
            {"artifact_id": artifact.artifact_id, "snippet": raw[:200]},
        ) from exc

    capabilities = context.by_system(artifact.system_hint)
    taxonomy = {c.capability_id for c in capabilities}
    participants = {p.engineer_id for p in artifact.participants}

    claims: list[CapabilityClaim] = []
    ambiguity = [str(a) for a in payload.get("ambiguity", []) if a]

    for entry in payload.get("claims", []) or []:
        if not isinstance(entry, dict):
            continue
        try:
            role = EvidenceRole(str(entry.get("evidence_role", "")).strip().upper())
        except ValueError:
            ambiguity.append(f"unrecognised evidence_role {entry.get('evidence_role')!r}")
            continue

        capability_id = str(entry.get("capability_id", "")).strip()
        engineer_id = str(entry.get("engineer_id", "")).strip()
        summary = str(entry.get("summary") or "").strip()
        rationale = str(entry.get("rationale") or "").strip()

        if capability_id not in taxonomy or engineer_id not in participants:
            ambiguity.append(
                f"discarded claim outside the supplied lists: {capability_id!r}/{engineer_id!r}"
            )
            continue
        if not summary or not rationale:
            ambiguity.append(f"discarded uncited claim for {capability_id}/{engineer_id}")
            continue

        claims.append(
            CapabilityClaim(
                capability_id=capability_id,
                engineer_id=engineer_id,
                evidence_role=role,
                # Derived, never taken from the model. PRD section 16.1.
                evidence_strength=strength_for_role(role),
                summary=summary,
                rationale=f"{provider_label}: {rationale}",
                extraction_confidence=EvidenceConfidence.MEDIUM,
                is_conflicting=is_conflicting,
            )
        )

    component_id = None
    if len({c.capability_id for c in claims}) == 1:
        claimed = next(iter({c.capability_id for c in claims}))
        component_id = next((c.component_id for c in capabilities if c.capability_id == claimed), None)

    return ArtifactExtraction(
        artifact_id=artifact.artifact_id,
        system_id=artifact.system_hint,
        component_id=component_id,
        claims=claims,
        ambiguity=ambiguity,
    )


def extract_with(
    artifact: ArtifactInput,
    context: ExtractionContext,
    *,
    chat: Callable[[str, str, int], str],
    provider_label: str,
    is_conflicting: bool,
) -> ArtifactExtraction:
    """The whole extraction for one artifact, given a transport.

    `chat(system, user, max_tokens) -> str` is the only thing a provider has to supply.
    """
    skipped = nothing_to_extract(artifact, context)
    if skipped is not None:
        return skipped

    raw = chat(system_prompt(), build_user_prompt(artifact, context), EXTRACTION_MAX_TOKENS)
    return parse_extraction(
        raw,
        artifact,
        context,
        provider_label=provider_label,
        is_conflicting=is_conflicting,
    )
