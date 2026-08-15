"""A deterministic, offline implementation of the AI provider interface.

Why this exists as the default rather than a model call:

* **The demo cannot depend on a network.** docs/ARCHITECTURE.md section 85 says the live demo
  must not gamble on provider latency or availability.
* **Reproducibility.** The evaluation in `app/evaluation/` compares inferred readiness against
  hidden labels. That comparison is only meaningful if extraction is repeatable.
* **The interface is the important part.** Swapping in a model changes extraction quality; it
  changes no conclusion path, because readiness, exposure, risk, and candidate selection are all
  downstream and deterministic either way.

How extraction works here:

1. **Capability resolution** — match the capability name or one of its aliases in the artifact
   text, scoped to the artifact's system. Scoping is what stops "Monitoring" in a Payment
   Gateway incident from also matching "Refund Monitoring" in another service.
2. **Role interpretation** — map `(source_type, participant_role)` onto an `EvidenceRole`. The
   participant role comes from the source system, so this step interprets rather than invents:
   an incident platform already knows who resolved and who assisted.
3. **Strength** — derived from role, never asserted independently.

Be clear about the ceiling. This resolves capabilities by string match, so it finds what the
text names and nothing more. It cannot read "restarted the workers and traffic recovered" and
infer incident recovery without the phrase present. That is exactly the gap a language model
closes, and it is the single highest-value upgrade available — RECOMMENDATIONS.md R-01.
"""

from __future__ import annotations

from app.ai.provider import ExtractionContext
from app.ai.schemas import (
    ArtifactExtraction,
    ArtifactInput,
    CandidateNarrative,
    CandidateNarrativeContext,
    CapabilityClaim,
    PlanContext,
    PlanDraft,
    PlanTaskDraft,
    SimulationSummaryContext,
    TaxonomyCapability,
)
from app.evidence.strength import strength_for_role
from app.models.enums import ParticipantRole
from app.schemas.enums import (
    EvidenceConfidence,
    EvidenceRole,
    EvidenceSourceType,
    MitigationTaskType,
    ReadinessLevel,
)

# (source_type, participant_role) -> evidence role. Anything unmapped yields no claim, which is
# the correct answer far more often than a guess would be.
_ROLE_MAP: dict[tuple[EvidenceSourceType, ParticipantRole], EvidenceRole] = {
    (EvidenceSourceType.INCIDENT, ParticipantRole.RESOLVER): EvidenceRole.INDEPENDENT_EXECUTION,
    (EvidenceSourceType.INCIDENT, ParticipantRole.ASSISTING_RESPONDER): EvidenceRole.ASSISTED_EXECUTION,
    (EvidenceSourceType.INCIDENT, ParticipantRole.COMMENTER): EvidenceRole.EXPOSURE,
    (EvidenceSourceType.PULL_REQUEST, ParticipantRole.AUTHOR): EvidenceRole.CONTRIBUTION,
    (EvidenceSourceType.PULL_REQUEST, ParticipantRole.REVIEWER): EvidenceRole.EXPOSURE,
    (EvidenceSourceType.CODE_REVIEW, ParticipantRole.REVIEWER): EvidenceRole.EXPOSURE,
    (EvidenceSourceType.CODE_REVIEW, ParticipantRole.AUTHOR): EvidenceRole.CONTRIBUTION,
    (EvidenceSourceType.COMMIT, ParticipantRole.AUTHOR): EvidenceRole.CONTRIBUTION,
    (EvidenceSourceType.ISSUE, ParticipantRole.COMMENTER): EvidenceRole.EXPOSURE,
    (EvidenceSourceType.ISSUE, ParticipantRole.REPORTER): EvidenceRole.EXPOSURE,
    (EvidenceSourceType.ISSUE, ParticipantRole.ASSIGNEE): EvidenceRole.CONTRIBUTION,
    (EvidenceSourceType.TICKET, ParticipantRole.ASSIGNEE): EvidenceRole.CONTRIBUTION,
    (EvidenceSourceType.TICKET, ParticipantRole.REPORTER): EvidenceRole.EXPOSURE,
    (EvidenceSourceType.TICKET, ParticipantRole.COMMENTER): EvidenceRole.EXPOSURE,
    (EvidenceSourceType.DOCUMENT, ParticipantRole.AUTHOR): EvidenceRole.KNOWLEDGE_CAPTURE,
    (EvidenceSourceType.DOCUMENT, ParticipantRole.REVIEWER): EvidenceRole.EXPOSURE,
    (EvidenceSourceType.TECHNICAL_DISCUSSION, ParticipantRole.COMMENTER): EvidenceRole.EXPOSURE,
    (EvidenceSourceType.TECHNICAL_DISCUSSION, ParticipantRole.AUTHOR): EvidenceRole.EXPOSURE,
    (EvidenceSourceType.MANAGER_ATTESTATION, ParticipantRole.ATTESTING_MANAGER): EvidenceRole.CONTRIBUTION,
}

# Phrases indicating an attempt that did not hold. Such a record is retained but marked
# conflicting: it never supports a claim, it shows in the provenance drawer, and it lowers
# Evidence Confidence. DOMAIN_MODEL.md section 12.
_CONFLICT_MARKERS = (
    "recovery attempt was reverted",
    "did not restore",
    "handed off unresolved",
    "change was rolled back after",
    "failed to recover",
)

_SUMMARY_TEMPLATES: dict[EvidenceRole, str] = {
    EvidenceRole.INDEPENDENT_EXECUTION: "{engineer} independently carried out {capability} in {reference}.",
    EvidenceRole.ASSISTED_EXECUTION: "{engineer} assisted with {capability} in {reference}, with another responder leading.",
    EvidenceRole.CONTRIBUTION: "{engineer} authored a change affecting {capability} in {reference}.",
    EvidenceRole.KNOWLEDGE_CAPTURE: "{engineer} authored operational documentation for {capability} in {reference}.",
    EvidenceRole.EXPOSURE: "{engineer} reviewed or discussed {capability} in {reference}; no execution is evidenced.",
}


class DeterministicProvider:
    name = "deterministic"

    # -- extraction ---------------------------------------------------------------------

    def extract_artifact_semantics(
        self, artifact: ArtifactInput, context: ExtractionContext
    ) -> ArtifactExtraction:
        candidates = context.by_system(artifact.system_hint)
        matches = self._match_capabilities(artifact, candidates)
        ambiguity: list[str] = []

        if not matches:
            return ArtifactExtraction(
                artifact_id=artifact.artifact_id,
                system_id=artifact.system_hint,
                ambiguity=["no capability named in the artifact text"],
            )

        if len(matches) > 1:
            # Recorded rather than resolved. Guessing between two capabilities would put an
            # unfalsifiable claim in the graph; naming the ambiguity keeps it reviewable.
            ambiguity.append(
                "artifact text names more than one capability: "
                + ", ".join(sorted(c.capability_id for c, _ in matches))
            )

        is_conflicting = self._looks_conflicting(artifact)
        claims: list[CapabilityClaim] = []

        for capability, needle in matches:
            for participant in artifact.participants:
                try:
                    participant_role = ParticipantRole(participant.participant_role)
                except ValueError:
                    ambiguity.append(f"unrecognised participant role '{participant.participant_role}'")
                    continue

                evidence_role = _ROLE_MAP.get((artifact.source_type, participant_role))
                if evidence_role is None:
                    continue

                engineer_name = context.engineer_names.get(participant.engineer_id, participant.engineer_id)
                claims.append(
                    CapabilityClaim(
                        capability_id=capability.capability_id,
                        engineer_id=participant.engineer_id,
                        evidence_role=evidence_role,
                        evidence_strength=strength_for_role(evidence_role),
                        summary=_SUMMARY_TEMPLATES[evidence_role].format(
                            engineer=engineer_name,
                            capability=capability.name,
                            reference=artifact.source_reference,
                        ),
                        rationale=(
                            f"{artifact.source_type.value} {artifact.source_reference}: participant "
                            f"role {participant_role.value} on text matching '{needle}'"
                        ),
                        extraction_confidence=(
                            EvidenceConfidence.LOW if len(matches) > 1 else EvidenceConfidence.HIGH
                        ),
                        is_conflicting=is_conflicting,
                    )
                )

        return ArtifactExtraction(
            artifact_id=artifact.artifact_id,
            system_id=artifact.system_hint,
            component_id=matches[0][0].component_id if len(matches) == 1 else None,
            claims=claims,
            ambiguity=ambiguity,
        )

    @staticmethod
    def _match_capabilities(
        artifact: ArtifactInput, candidates: list[TaxonomyCapability]
    ) -> list[tuple[TaxonomyCapability, str]]:
        text = f"{artifact.title or ''}\n{artifact.body}".lower()
        matched: list[tuple[TaxonomyCapability, str]] = []
        for capability in candidates:
            needles = [capability.name.lower(), *(a.lower() for a in capability.aliases)]
            hit = next((n for n in needles if n in text), None)
            if hit is not None:
                matched.append((capability, hit))
        return sorted(matched, key=lambda m: m[0].capability_id)

    @staticmethod
    def _looks_conflicting(artifact: ArtifactInput) -> bool:
        text = f"{artifact.title or ''}\n{artifact.body}".lower()
        return any(marker in text for marker in _CONFLICT_MARKERS)

    # -- narration ----------------------------------------------------------------------

    def summarize_simulation(self, context: SimulationSummaryContext) -> str | None:
        """One sentence over facts the rules already decided.

        Deliberately never says the system will fail. The simulation identifies coverage loss;
        the disclaimer that it is not an outage prediction is frontend copy (decision CI-32).
        """
        gaps = context.critical_gap_capabilities
        preserved = context.preserved_capabilities

        if not gaps and not context.degraded_capabilities:
            return (
                f"{context.engineer_name}'s unavailability leaves every assessed capability in "
                f"{context.scope_name} with adequate demonstrated coverage."
            )

        parts: list[str] = []
        if gaps:
            parts.append(
                f"{len(gaps)} capability gap{'s' if len(gaps) != 1 else ''} "
                f"({self._join(gaps)}) would have no adequate demonstrated coverage"
            )
        if context.degraded_capabilities:
            parts.append(f"{self._join(context.degraded_capabilities)} would lose redundancy")
        sentence = (
            f"Without {context.engineer_name}, {context.scope_name} moves from "
            f"{context.risk_class_before} to {context.risk_class_after}: " + "; ".join(parts) + "."
        )
        if preserved:
            sentence += f" {self._join(preserved)} remain covered."
        return sentence

    def explain_candidate(self, context: CandidateNarrativeContext) -> CandidateNarrative:
        """Strengths and gaps, phrased to the strength of the evidence and no further.

        A gap is always "no qualifying evidence was found", never "cannot do this"
        (PRD section 22.3). Absence of evidence is absence of evidence.
        """
        strengths = [f"Demonstrated {name}" for name in context.demonstrated_capabilities]
        strengths += [f"Assisted {name}" for name in context.assisted_capabilities]
        gaps = [
            f"No qualifying independent evidence for {name}" for name in context.missing_capabilities
        ]
        return CandidateNarrative(strengths=strengths, gaps=gaps)

    # -- planning -----------------------------------------------------------------------

    def generate_mitigation_plan(self, context: PlanContext) -> PlanDraft:
        """Target the exposed capability, not the whole person.

        docs/ARCHITECTURE.md section 38: "Teach Maria everything Alex knows" is the failure
        mode. Every task below names the specific capability and states observable acceptance
        criteria, and the sequence follows the PRD section 11.7 progression
        understand -> observe -> practise -> drill -> document.
        """
        capability = context.capability_name
        system = context.system_name
        references = [e.get("source_reference") for e in context.reference_evidence if e.get("source_reference")]
        reference_phrase = " and ".join(references[:2]) if references else "the recorded incidents"
        evidence_ids = [e["evidence_id"] for e in context.reference_evidence if e.get("evidence_id")]

        tasks: list[PlanTaskDraft] = [
            PlanTaskDraft(
                title=f"Review {system} {capability} architecture",
                description=(
                    f"Review the {capability} path in {context.component_name}, the current runbook, "
                    f"and the historical records {reference_phrase}."
                ),
                task_type=MitigationTaskType.KNOWLEDGE_REVIEW.value,
                acceptance_criteria=[
                    f"Walk the current {capability} path end to end",
                    f"Review the recorded {system} incidents that exercised it",
                    "Record the questions the existing material does not answer",
                ],
                linked_evidence_ids=evidence_ids[:2],
            ),
            PlanTaskDraft(
                title=f"Shadow {capability} with {context.source_engineer_name}",
                description=(
                    f"Observe {context.source_engineer_name} working through {capability} and capture "
                    f"the decision points that are not written down."
                ),
                task_type=MitigationTaskType.SHADOWING.value,
                acceptance_criteria=[
                    "Attend a guided exercise end to end",
                    "Write down each decision point and what drove it",
                ],
            ),
            PlanTaskDraft(
                title=f"Execute {capability} in staging",
                description=(
                    f"Perform {capability} in staging without step-by-step prompting and confirm "
                    f"normal operation is restored."
                ),
                task_type=MitigationTaskType.PRACTICE.value,
                acceptance_criteria=[
                    f"Complete {capability} unaided in staging",
                    "Verify the system returns to normal operation",
                    "Note any step the runbook is missing",
                ],
            ),
        ]

        # Someone with no hands-on evidence at all needs the drill before the write-up; someone
        # who has already assisted does not. The plan reflects the gap, not a fixed template.
        if context.candidate_readiness in {ReadinessLevel.NONE.value, ReadinessLevel.EXPOSED.value}:
            tasks.append(
                PlanTaskDraft(
                    title=f"Run an unaided {capability} drill",
                    description=(
                        f"Run a scheduled drill covering {capability} with the source engineer "
                        f"observing only."
                    ),
                    task_type=MitigationTaskType.RECOVERY_DRILL.value,
                    acceptance_criteria=[
                        "Complete the drill without intervention",
                        "Pass the post-drill verification checks",
                    ],
                )
            )

        tasks.append(
            PlanTaskDraft(
                title=f"Update the {system} {capability} runbook",
                description=(
                    "Fold the gaps found during the exercise back into the runbook so the next "
                    "person does not rediscover them."
                ),
                task_type=MitigationTaskType.DOCUMENTATION.value,
                acceptance_criteria=[
                    "Add the missing steps identified during practice",
                    "Add rollback guidance",
                    "Submit the runbook for review",
                ],
            )
        )

        return PlanDraft(target_readiness=context.target_readiness, tasks=tasks)

    @staticmethod
    def _join(names: list[str]) -> str:
        if len(names) == 1:
            return names[0]
        if len(names) == 2:
            return f"{names[0]} and {names[1]}"
        return ", ".join(names[:-1]) + f", and {names[-1]}"
