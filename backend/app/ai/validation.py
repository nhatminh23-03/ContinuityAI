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

The second half of the module applies the same discipline to the three narrative outputs of the
provider interface — the simulation sentence, the candidate strengths and gaps, and the mitigation
plan. Extraction validation protects the graph; narrative validation protects what a manager is
told about it, which is the part that is quoted back in a room. Neither raises: both report, and a
caller that receives a rejection uses the deterministic template instead.
"""

from __future__ import annotations

from app.ai.language_policy import (
    find_forbidden_phrases,
    find_inability_language,
    find_probability_language,
    find_unattested_names,
)
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
from app.schemas.enums import MitigationTaskType, ReadinessLevel


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


# ---------------------------------------------------------------------------------------
# Narrative gate
#
# Everything below validates prose rather than claims. It is what makes letting a language
# model write the manager-facing sentences defensible: the model may phrase the facts, and
# this decides whether what came back is still the facts. Like `validate_extraction`, these
# report and never raise — a caller that gets a rejection falls back to the deterministic
# template, so a bad generation costs the wording and nothing else.
# ---------------------------------------------------------------------------------------

# One sentence for a manager. The deterministic template lands around 250 characters; the cap
# exists to catch a model that starts writing an essay, not to trim a well-formed sentence.
MAX_SUMMARY_CHARS = 500

# AC-10 requires 3 to 5 actions. Checked here as well as in `MitigationPlanService.create`
# (MIN_TASKS/MAX_TASKS) on purpose: the service raises MitigationGenerationError, which is the
# right answer for a broken generator but the wrong one for a model that simply wrote six
# actions. Rejecting here means the template is used instead of the request failing.
MIN_PLAN_TASKS = 3
MAX_PLAN_TASKS = 5

_DRILL_READINESS_VALUES = frozenset({ReadinessLevel.NONE.value, ReadinessLevel.EXPOSED.value})


class NarrativeOutcome:
    """Whether generated prose may be used, and what was wrong with it if not."""

    def __init__(self) -> None:
        self.rejections: list[str] = []
        self.corrections: list[str] = []

    @property
    def accepted(self) -> bool:
        return not self.rejections

    def as_dict(self) -> dict:
        return {
            "accepted": self.accepted,
            "rejections": self.rejections,
            "corrections": self.corrections,
        }


class PlanValidationOutcome(NarrativeOutcome):
    """A narrative outcome that also carries the corrected draft.

    `draft` is populated only when the plan is accepted, mirroring `ValidationOutcome.claims`:
    a caller cannot reach for output that did not pass.
    """

    def __init__(self) -> None:
        super().__init__()
        self.draft: PlanDraft | None = None


def requires_recovery_drill(readiness: str | ReadinessLevel) -> bool:
    """Whether a candidate at this readiness must be given an unaided drill.

    AC-09: the plan reflects the chosen candidate's gap. Someone with no hands-on evidence needs
    the drill before the write-up; someone who has already assisted does not. This is the single
    definition of that rule — `DeterministicProvider.generate_mitigation_plan` branches on it and
    `validate_plan_draft` enforces it, so the template and the gate cannot drift apart.

    Tolerant of an unrecognised value, which it reports as "no drill required"; deciding whether
    an unknown readiness is itself a rejection belongs to the caller.
    """
    return str(getattr(readiness, "value", readiness)) in _DRILL_READINESS_VALUES


def _task_count_band(readiness: str | ReadinessLevel) -> tuple[int, int]:
    """Minimum and maximum actions for a candidate at this readiness.

    The AC-09 property asserted in tests/test_golden_path.py:208-218 is comparative — a candidate
    at EXPOSED gets strictly more actions than one at ASSISTED — but a validator only ever sees
    one plan. Expressing it as bands makes it checkable per call: the lower band's minimum sits
    above the upper band's maximum, so any two plans that both pass satisfy the comparison.
    """
    if requires_recovery_drill(readiness):
        return MAX_PLAN_TASKS, MAX_PLAN_TASKS
    return MIN_PLAN_TASKS, MAX_PLAN_TASKS - 1


def validate_simulation_summary(
    text: str | None, context: SimulationSummaryContext
) -> NarrativeOutcome:
    """The one sentence a manager reads under the simulation result.

    It may restate the facts the rule engine already decided and nothing else: no likelihood, no
    prediction that something breaks, no capability or person the simulation did not name.
    """
    outcome = NarrativeOutcome()

    if text is None or not text.strip():
        outcome.rejections.append("simulation summary is empty")
        return outcome

    if len(text) > MAX_SUMMARY_CHARS:
        outcome.rejections.append(
            f"simulation summary is {len(text)} characters; the limit is {MAX_SUMMARY_CHARS}"
        )

    for phrase in find_forbidden_phrases(text):
        outcome.rejections.append(f"simulation summary uses prohibited wording {phrase!r}")

    for marker in find_probability_language(text):
        # docs/DECISIONS.md CI-32: a simulation reports coverage loss, not the odds of an outage.
        outcome.rejections.append(
            f"simulation summary states a likelihood ({marker!r}); it may only describe coverage"
        )

    attested = [
        context.engineer_name,
        context.scope_name,
        *context.critical_gap_capabilities,
        *context.degraded_capabilities,
        *context.preserved_capabilities,
    ]
    for name in find_unattested_names(text, attested):
        outcome.rejections.append(
            f"simulation summary names '{name}', which is not among the simulated facts"
        )

    return outcome


def validate_candidate_narrative(
    narrative: CandidateNarrative, context: CandidateNarrativeContext
) -> NarrativeOutcome:
    """Strengths and gaps for one backup candidate.

    Both halves are required (tests/test_golden_path.py:133-136): strengths alone read as an
    endorsement and gaps alone read as a verdict, and the product's position is that a candidate
    is a set of evidence relationships, not either of those.

    FR-017 limits the content to evidence-backed graph facts, so every capability named has to
    come from the demonstrated, assisted, or missing lists, and the only person who may appear is
    the candidate.
    """
    outcome = NarrativeOutcome()

    strengths = [line for line in narrative.strengths if line.strip()]
    gaps = [line for line in narrative.gaps if line.strip()]

    if not strengths:
        outcome.rejections.append("candidate narrative states no strengths")
    if not gaps:
        outcome.rejections.append("candidate narrative states no gaps")

    attested = [
        context.candidate_name,
        context.capability_name,
        *context.demonstrated_capabilities,
        *context.assisted_capabilities,
        *context.missing_capabilities,
    ]

    for line in [*strengths, *gaps]:
        for phrase in find_forbidden_phrases(line):
            outcome.rejections.append(f"candidate narrative uses prohibited wording {phrase!r}")
        for name in find_unattested_names(line, attested):
            outcome.rejections.append(
                f"candidate narrative names '{name}', which is neither the candidate nor a "
                f"capability the evidence covers"
            )

    for gap in gaps:
        # PRD section 22.3. The gap is that the record holds no qualifying evidence, which is a
        # statement about the record. Phrasing it as a limit of the person is not the same claim.
        for marker in find_inability_language(gap):
            outcome.rejections.append(
                f"gap {gap!r} states inability ({marker!r}); a gap is absence of evidence"
            )

    return outcome


def validate_plan_draft(
    draft: PlanDraft, context: PlanContext, known_evidence_ids: set[str]
) -> PlanValidationOutcome:
    """A knowledge-transfer plan, before anyone is asked to approve it.

    The plan is the artifact a manager approves and someone then executes, so an invented step or
    an invented citation has a real cost. Four things are checked structurally — the action count,
    the task types, acceptance criteria (AC-10), and the citation on the opening review task
    (tests/test_golden_path.py:205) — plus the candidate-specificity invariant of AC-09.

    Unknown evidence ids are dropped rather than rejected, the same way `validate_extraction`
    corrects an evidence strength: a citation that does not resolve is noise, but the action it
    hangs off is still sound work, and losing the whole plan over it helps nobody.
    """
    outcome = PlanValidationOutcome()

    try:
        readiness = ReadinessLevel(context.candidate_readiness)
    except ValueError:
        # Without a readiness there is no candidate-specificity rule to apply, and a plan that
        # cited an unknown one was not built from this candidate's coverage.
        outcome.rejections.append(f"unknown candidate readiness '{context.candidate_readiness}'")
        return outcome

    if not MIN_PLAN_TASKS <= len(draft.tasks) <= MAX_PLAN_TASKS:
        outcome.rejections.append(
            f"plan has {len(draft.tasks)} actions; AC-10 requires between {MIN_PLAN_TASKS} and "
            f"{MAX_PLAN_TASKS}"
        )

    minimum, maximum = _task_count_band(readiness)
    if not minimum <= len(draft.tasks) <= maximum:
        expected = (
            f"exactly {minimum}" if minimum == maximum else f"between {minimum} and {maximum}"
        )
        outcome.rejections.append(
            f"plan has {len(draft.tasks)} actions; a candidate at {readiness.value} "
            f"takes {expected}"
        )

    attested = [
        context.source_engineer_name,
        context.candidate_name,
        context.capability_name,
        context.system_name,
        context.component_name,
        *context.missing_capabilities,
        *(str(e.get("source_reference", "")) for e in context.reference_evidence),
    ]

    tasks: list[PlanTaskDraft] = []
    task_types: list[str] = []

    for position, task in enumerate(draft.tasks, start=1):
        try:
            task_types.append(MitigationTaskType(task.task_type).value)
        except ValueError:
            outcome.rejections.append(
                f"action {position} has task type '{task.task_type}', which is not a mitigation "
                f"task type"
            )

        if not [c for c in task.acceptance_criteria if c.strip()]:
            outcome.rejections.append(
                f"action {position} has no acceptance criterion; AC-10 requires observable ones"
            )

        # Newline-joined, not space-joined: each field keeps its own opening position, so a
        # title that begins with an imperative verb is not read as part of a proper name.
        text = "\n".join([task.title, task.description, *task.acceptance_criteria])
        for phrase in find_forbidden_phrases(text):
            outcome.rejections.append(f"action {position} uses prohibited wording {phrase!r}")
        for name in find_unattested_names(text, attested):
            outcome.rejections.append(
                f"action {position} names '{name}', which is neither the source engineer, the "
                f"candidate, nor anything the plan context supplied"
            )

        kept = [e for e in task.linked_evidence_ids if e in known_evidence_ids]
        dropped = [e for e in task.linked_evidence_ids if e not in known_evidence_ids]
        if dropped:
            outcome.corrections.append(
                f"action {position}: dropped unresolvable evidence {', '.join(dropped)}"
            )
        tasks.append(task.model_copy(update={"linked_evidence_ids": kept}))

    # After filtering, so an id that does not resolve cannot stand in for a citation.
    if not tasks or not tasks[0].linked_evidence_ids:
        outcome.rejections.append("the opening action cites no evidence for the candidate to study")

    drill = MitigationTaskType.RECOVERY_DRILL.value
    if requires_recovery_drill(readiness) and drill not in task_types:
        outcome.rejections.append(
            f"a candidate at {readiness.value} has no hands-on evidence and must be given a "
            f"{drill}"
        )
    if not requires_recovery_drill(readiness) and drill in task_types:
        outcome.rejections.append(
            f"a candidate at {readiness.value} has already assisted; a {drill} belongs to the "
            f"band below, and including it erases the difference between the two plans"
        )

    if outcome.accepted:
        outcome.draft = draft.model_copy(update={"tasks": tasks})
    return outcome
