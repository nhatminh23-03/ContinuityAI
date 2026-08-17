"""Validate provider output before anything reaches the database.

docs/ARCHITECTURE.md section 22: LLM JSON -> schema validation -> entity resolution ->
capability/system mapping -> persist. Malformed or unsupported output is rejected, never
silently accepted.

Rejection rules, in order of how much damage they prevent:

1. **Unknown capability.** A capability not in the taxonomy given to the provider is a
   hallucination. Dropped, and recorded as ambiguity.
2. **Cross-system attribution.** A capability that belongs to a different system than the
   artifact is a mis-mapping. Dropped.
3. **Unknown engineer.** An engineer not among the artifact's recorded participants is an
   invented attribution — the most damaging failure this product could have, because it would
   put a claim against a named person with nothing behind it. Dropped.
4. **Role/strength disagreement.** `evidence_role` is authoritative and `evidence_strength` is
   derived from it (PRD section 16.1). A provider that disagrees is corrected, not trusted.
"""

from __future__ import annotations

from app.ai.schemas import ArtifactExtraction, ArtifactInput, CapabilityClaim, TaxonomyCapability
from app.evidence.strength import strength_for_role


class ValidationOutcome:
    """Accepted claims plus a record of what was thrown away and why."""

    def __init__(self) -> None:
        self.claims: list[CapabilityClaim] = []
        self.rejections: list[str] = []
        self.corrections: list[str] = []

    def as_dict(self) -> dict:
        return {
            "accepted": len(self.claims),
            "rejections": self.rejections,
            "corrections": self.corrections,
        }


def validate_extraction(
    extraction: ArtifactExtraction,
    artifact: ArtifactInput,
    taxonomy: dict[str, TaxonomyCapability],
    known_engineer_ids: set[str],
) -> ValidationOutcome:
    outcome = ValidationOutcome()
    participant_ids = {p.engineer_id for p in artifact.participants}
    seen: set[tuple[str, str]] = set()

    for claim in extraction.claims:
        capability = taxonomy.get(claim.capability_id)
        if capability is None:
            outcome.rejections.append(
                f"unknown capability '{claim.capability_id}' on {artifact.source_reference}"
            )
            continue

        if artifact.system_hint and capability.system_id != artifact.system_hint:
            outcome.rejections.append(
                f"capability '{claim.capability_id}' belongs to {capability.system_id}, "
                f"artifact {artifact.source_reference} belongs to {artifact.system_hint}"
            )
            continue

        if claim.engineer_id not in known_engineer_ids:
            outcome.rejections.append(
                f"unknown engineer '{claim.engineer_id}' on {artifact.source_reference}"
            )
            continue

        if claim.engineer_id not in participant_ids:
            # An engineer who does not appear in the artifact cannot have demonstrated
            # anything through it, whatever the text implies.
            outcome.rejections.append(
                f"engineer '{claim.engineer_id}' is not a recorded participant of "
                f"{artifact.source_reference}"
            )
            continue

        key = (claim.capability_id, claim.engineer_id)
        if key in seen:
            outcome.rejections.append(
                f"duplicate claim for {key} on {artifact.source_reference}"
            )
            continue
        seen.add(key)

        expected_strength = strength_for_role(claim.evidence_role)
        if claim.evidence_strength != expected_strength:
            outcome.corrections.append(
                f"{artifact.source_reference}: strength {claim.evidence_strength.value} -> "
                f"{expected_strength.value} for role {claim.evidence_role.value}"
            )
            claim = claim.model_copy(update={"evidence_strength": expected_strength})

        outcome.claims.append(claim)

    return outcome
