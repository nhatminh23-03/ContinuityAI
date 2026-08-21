"""The safety gate a generated narrative must pass before a manager sees it.

Task 2 of .superpowers/sdd/superpowers-brainstorming-continuityai-merry-heron/task-2-brief.md.
Nothing calls these validators yet; they exist so that letting a language model write the
manager-facing sentences is defensible rather than hopeful.

Every rejection path gets a test, and so does the accepting case beside it — a gate that rejects
everything is as useless as one that accepts everything, and only the pair proves neither.
"""

from __future__ import annotations

import logging

import pytest

from app.ai.deterministic import DeterministicProvider
from app.ai.language_policy import FORBIDDEN_PHRASES
from app.ai.schemas import (
    CandidateNarrative,
    CandidateNarrativeContext,
    PlanContext,
    PlanDraft,
    PlanTaskDraft,
    SimulationSummaryContext,
)
from app.ai.validation import (
    MAX_SUMMARY_CHARS,
    validate_candidate_narrative,
    validate_plan_draft,
    validate_simulation_summary,
)

# The list moved out of tests/test_responsible_ai.py. Pinned here as a literal rather than
# imported from that module, so the later task that swaps the test over to the shared constant
# cannot make this assertion vacuous.
EXPECTED_FORBIDDEN_PHRASES = (
    "best employee",
    "cannot recover",
    "chance of failure",
    "probability of outage",
    "irreplaceable",
    "critical employee",
    "weak engineer",
    "low-value engineer",
)


def test_the_canonical_phrase_list_is_unchanged_by_the_move() -> None:
    assert FORBIDDEN_PHRASES == EXPECTED_FORBIDDEN_PHRASES


# ---------------------------------------------------------------------------------------
# Simulation summary
# ---------------------------------------------------------------------------------------


def sim_context(**overrides) -> SimulationSummaryContext:
    base = dict(
        engineer_name="Alex Chen",
        scope_name="Payment Gateway",
        critical_gap_capabilities=["Incident Recovery"],
        degraded_capabilities=["Refund Processing"],
        preserved_capabilities=["Ledger Reconciliation"],
        risk_class_before="MODERATE",
        risk_class_after="HIGH",
    )
    base.update(overrides)
    return SimulationSummaryContext(**base)


GOOD_SUMMARY = (
    "Without Alex Chen, Payment Gateway moves from MODERATE to HIGH: Incident Recovery would "
    "have no adequate demonstrated coverage and Refund Processing would lose redundancy. "
    "Ledger Reconciliation remains covered."
)


def test_a_grounded_summary_is_accepted() -> None:
    outcome = validate_simulation_summary(GOOD_SUMMARY, sim_context())
    assert outcome.accepted, outcome.rejections


def test_the_deterministic_summary_passes_its_own_gate() -> None:
    """The template is the fallback. If it failed the gate, the fallback would be unusable."""
    context = sim_context()
    text = DeterministicProvider().summarize_simulation(context)
    outcome = validate_simulation_summary(text, context)
    assert outcome.accepted, outcome.rejections


@pytest.mark.parametrize("text", [None, "", "   \n  "])
def test_an_empty_summary_is_rejected(text) -> None:
    outcome = validate_simulation_summary(text, sim_context())
    assert not outcome.accepted


def test_an_over_long_summary_is_rejected() -> None:
    assert validate_simulation_summary("x" * MAX_SUMMARY_CHARS, sim_context()).accepted
    assert not validate_simulation_summary("x" * (MAX_SUMMARY_CHARS + 1), sim_context()).accepted


def test_a_forbidden_phrase_in_a_summary_is_rejected() -> None:
    outcome = validate_simulation_summary(
        "Without Alex Chen, Payment Gateway is irreplaceable.", sim_context()
    )
    assert not outcome.accepted


@pytest.mark.parametrize(
    "text",
    [
        "There is a 60% coverage shortfall on Incident Recovery.",
        "The probability of losing Incident Recovery rises without Alex Chen.",
        "There is a real chance of losing Incident Recovery.",
        "Incident Recovery will fail without Alex Chen.",
    ],
)
def test_probability_language_in_a_summary_is_rejected(text) -> None:
    """A simulation identifies coverage loss. It does not forecast an outage (PRD 22.3)."""
    outcome = validate_simulation_summary(text, sim_context())
    assert not outcome.accepted


def test_a_capability_outside_the_context_lists_is_rejected() -> None:
    outcome = validate_simulation_summary(
        "Without Alex Chen, Payment Gateway loses Settlement Batching coverage.", sim_context()
    )
    assert not outcome.accepted
    assert any("Settlement Batching" in r for r in outcome.rejections)


def test_capabilities_from_every_context_list_are_accepted() -> None:
    """Degraded and preserved capabilities are given facts too, not only the gaps."""
    outcome = validate_simulation_summary(
        "Refund Processing would lose redundancy and Ledger Reconciliation remains covered.",
        sim_context(),
    )
    assert outcome.accepted, outcome.rejections


def test_a_second_engineer_named_in_a_summary_is_rejected() -> None:
    outcome = validate_simulation_summary(
        "Without Alex Chen, Priya Raman would carry Incident Recovery.", sim_context()
    )
    assert not outcome.accepted


# ---------------------------------------------------------------------------------------
# Candidate narrative
# ---------------------------------------------------------------------------------------


def candidate_context(**overrides) -> CandidateNarrativeContext:
    base = dict(
        capability_name="Incident Recovery",
        candidate_name="Maria Gomez",
        technical_overlap="HIGH",
        demonstrated_capabilities=["Queue Draining"],
        assisted_capabilities=["Incident Recovery"],
        missing_capabilities=["Ledger Reconciliation"],
    )
    base.update(overrides)
    return CandidateNarrativeContext(**base)


GOOD_NARRATIVE = CandidateNarrative(
    strengths=["Demonstrated Queue Draining", "Assisted Incident Recovery"],
    gaps=["No qualifying independent evidence for Ledger Reconciliation"],
)


def test_a_grounded_candidate_narrative_is_accepted() -> None:
    outcome = validate_candidate_narrative(GOOD_NARRATIVE, candidate_context())
    assert outcome.accepted, outcome.rejections


def test_the_deterministic_narrative_passes_its_own_gate() -> None:
    context = candidate_context()
    narrative = DeterministicProvider().explain_candidate(context)
    outcome = validate_candidate_narrative(narrative, context)
    assert outcome.accepted, outcome.rejections


def test_a_narrative_with_no_strengths_is_rejected() -> None:
    """test_golden_path.py:133-136 requires both halves on every candidate."""
    outcome = validate_candidate_narrative(
        CandidateNarrative(strengths=[], gaps=list(GOOD_NARRATIVE.gaps)), candidate_context()
    )
    assert not outcome.accepted


def test_a_narrative_whose_strengths_are_blank_strings_is_rejected() -> None:
    outcome = validate_candidate_narrative(
        CandidateNarrative(strengths=["  "], gaps=list(GOOD_NARRATIVE.gaps)), candidate_context()
    )
    assert not outcome.accepted


def test_a_narrative_with_no_gaps_is_rejected() -> None:
    outcome = validate_candidate_narrative(
        CandidateNarrative(strengths=list(GOOD_NARRATIVE.strengths), gaps=[]), candidate_context()
    )
    assert not outcome.accepted


@pytest.mark.parametrize(
    "strength",
    [
        "Demonstrated Incident Recovery independently",
        "Has demonstrated Incident Recovery end to end",
        "Handled Incident Recovery unaided during the last outage",
        "Ran Ledger Reconciliation on their own",
        "Solo Ledger Reconciliation work in the last quarter",
    ],
)
def test_a_strength_overstating_assisted_or_missing_work_is_rejected(strength) -> None:
    """The failure mode the product exists to avoid, and the one the name check cannot see.

    Both capabilities are attested, so the flattened list `find_unattested_names` receives has no
    objection: only the buckets know that Incident Recovery is assisted-only here and that Ledger
    Reconciliation is absent from the record entirely.
    """
    outcome = validate_candidate_narrative(
        CandidateNarrative(strengths=[strength], gaps=list(GOOD_NARRATIVE.gaps)),
        candidate_context(),
    )
    assert not outcome.accepted
    assert any("assisted or absent" in r for r in outcome.rejections), outcome.rejections


@pytest.mark.parametrize(
    "strength",
    [
        "Maria Gomez has independently handled that recovery work end to end, unaided.",
        "Maria Gomez has run the same kind of work solo before.",
    ],
)
def test_known_blind_spot_of_the_independence_check(strength) -> None:
    """The fifth documented blind spot, and the one that does not belong to the name check.

    The rule above pairs an independence marker with an unproven capability *name*, so it fires
    only where the strength lexically contains that name. Referring to the same capability
    obliquely — "that recovery work", "the same kind of work" — carries the identical
    overstatement past it, because deciding that a pronoun phrase means Incident Recovery needs a
    lexicon this module does not have, exactly as with the lower-case invention the name check
    cannot see.

    Documented here rather than patched: HARD RULE 2 of `prompts/candidate_narrative_system.txt`
    is what keeps assisted work from being written up as demonstrated, and this gate is the net
    under that instruction, not a replacement for it.
    """
    outcome = validate_candidate_narrative(
        CandidateNarrative(strengths=[strength], gaps=list(GOOD_NARRATIVE.gaps)),
        candidate_context(),
    )
    assert outcome.accepted, outcome.rejections


def test_the_same_wording_is_accepted_for_a_capability_the_record_demonstrates() -> None:
    """The pair that proves the rule reads the bucket rather than the word."""
    outcome = validate_candidate_narrative(
        CandidateNarrative(
            strengths=["Demonstrated Queue Draining independently"],
            gaps=list(GOOD_NARRATIVE.gaps),
        ),
        candidate_context(),
    )
    assert outcome.accepted, outcome.rejections


def test_assisted_participation_may_still_be_stated_as_assisted() -> None:
    outcome = validate_candidate_narrative(
        CandidateNarrative(
            strengths=["Assisted Incident Recovery alongside the incident lead"],
            gaps=list(GOOD_NARRATIVE.gaps),
        ),
        candidate_context(),
    )
    assert outcome.accepted, outcome.rejections


def test_a_capability_outside_the_graph_facts_is_rejected() -> None:
    outcome = validate_candidate_narrative(
        CandidateNarrative(
            strengths=["Has demonstrated Settlement Batching end to end"],
            gaps=list(GOOD_NARRATIVE.gaps),
        ),
        candidate_context(),
    )
    assert not outcome.accepted
    assert any("Settlement Batching" in r for r in outcome.rejections)


def test_a_capability_the_context_names_differently_is_rejected() -> None:
    """The likeliest invention is a near miss, not a wholesale fabrication: the model paraphrases
    Incident Recovery into Incident Response and the sentence still reads correctly."""
    outcome = validate_candidate_narrative(
        CandidateNarrative(
            strengths=["Assisted with Incident Response during the outage"],
            gaps=list(GOOD_NARRATIVE.gaps),
        ),
        candidate_context(),
    )
    assert not outcome.accepted


def test_another_person_named_in_a_narrative_is_rejected() -> None:
    outcome = validate_candidate_narrative(
        CandidateNarrative(
            strengths=["Assisted Incident Recovery alongside Alex Chen"],
            gaps=list(GOOD_NARRATIVE.gaps),
        ),
        candidate_context(),
    )
    assert not outcome.accepted


def test_a_forbidden_phrase_in_a_narrative_is_rejected() -> None:
    outcome = validate_candidate_narrative(
        CandidateNarrative(
            strengths=["Demonstrated Queue Draining"],
            gaps=["A weak engineer on Ledger Reconciliation"],
        ),
        candidate_context(),
    )
    assert not outcome.accepted


@pytest.mark.parametrize(
    "gap",
    [
        "Cannot run Ledger Reconciliation",
        "Is unable to run Ledger Reconciliation",
        "Incapable of running Ledger Reconciliation",
    ],
)
def test_a_gap_phrased_as_inability_is_rejected(gap) -> None:
    """PRD 22.3: a gap is absence of evidence, never inability."""
    outcome = validate_candidate_narrative(
        CandidateNarrative(strengths=list(GOOD_NARRATIVE.strengths), gaps=[gap]),
        candidate_context(),
    )
    assert not outcome.accepted


def test_a_gap_phrased_as_absence_of_evidence_is_accepted() -> None:
    outcome = validate_candidate_narrative(
        CandidateNarrative(
            strengths=list(GOOD_NARRATIVE.strengths),
            gaps=["No qualifying independent evidence for Ledger Reconciliation"],
        ),
        candidate_context(),
    )
    assert outcome.accepted, outcome.rejections


# ---------------------------------------------------------------------------------------
# Mitigation plan draft
# ---------------------------------------------------------------------------------------

KNOWN_EVIDENCE = {"ev_001", "ev_002"}


def plan_context(readiness: str = "ASSISTED", **overrides) -> PlanContext:
    base = dict(
        capability_name="Incident Recovery",
        system_name="Payment Gateway",
        component_name="Recovery Orchestrator",
        source_engineer_name="Alex Chen",
        candidate_name="Maria Gomez",
        candidate_readiness=readiness,
        target_readiness="PRACTICED",
        missing_capabilities=["Incident Recovery"],
        reference_evidence=[{"evidence_id": "ev_001", "source_reference": "INC-2481"}],
    )
    base.update(overrides)
    return PlanContext(**base)


def task(
    title: str,
    task_type: str,
    criteria: list[str] | None = None,
    evidence: list[str] | None = None,
) -> PlanTaskDraft:
    return PlanTaskDraft(
        title=title,
        description=f"{title} with Alex Chen observing.",
        task_type=task_type,
        acceptance_criteria=["Complete the step unaided"] if criteria is None else criteria,
        linked_evidence_ids=evidence or [],
    )


def base_tasks() -> list[PlanTaskDraft]:
    """Four actions, matching the shape the template produces for a candidate at ASSISTED."""
    return [
        task("Review the Incident Recovery runbook", "KNOWLEDGE_REVIEW", evidence=["ev_001"]),
        task("Shadow Incident Recovery", "SHADOWING"),
        task("Execute Incident Recovery in staging", "PRACTICE"),
        task("Update the Payment Gateway runbook", "DOCUMENTATION"),
    ]


def drill_tasks() -> list[PlanTaskDraft]:
    """Five, with the unaided drill a candidate at NONE or EXPOSED must receive (AC-09)."""
    tasks = base_tasks()
    tasks.insert(3, task("Run an unaided Incident Recovery drill", "RECOVERY_DRILL"))
    return tasks


def draft(tasks: list[PlanTaskDraft], target: str = "PRACTICED") -> PlanDraft:
    return PlanDraft(target_readiness=target, tasks=tasks)


def test_a_plan_matching_the_template_shape_is_accepted() -> None:
    outcome = validate_plan_draft(draft(base_tasks()), plan_context("ASSISTED"), KNOWN_EVIDENCE)
    assert outcome.accepted, outcome.rejections
    assert outcome.draft is not None


@pytest.mark.parametrize("readiness", ["NONE", "EXPOSED", "ASSISTED", "PRACTICED", "VALIDATED"])
def test_the_deterministic_plan_template_passes_its_own_gate(readiness) -> None:
    """The AC-09 invariant is stated in the validator and honoured by deterministic.py:295.
    This is the test that fails first if the two ever drift apart."""
    context = plan_context(readiness)
    outcome = validate_plan_draft(
        DeterministicProvider().generate_mitigation_plan(context), context, KNOWN_EVIDENCE
    )
    assert outcome.accepted, (readiness, outcome.rejections)


@pytest.mark.parametrize("count", [2, 6])
def test_a_plan_outside_three_to_five_actions_is_rejected_not_raised(count) -> None:
    """AC-10, checked here so a bad count falls back to the template instead of surfacing as
    MitigationGenerationError mid-demo."""
    tasks = [
        task(f"Review step {i}", "KNOWLEDGE_REVIEW", evidence=["ev_001"])
        for i in range(count)
    ]
    outcome = validate_plan_draft(draft(tasks), plan_context("ASSISTED"), KNOWN_EVIDENCE)
    assert not outcome.accepted
    assert outcome.draft is None


def test_an_unknown_task_type_is_rejected() -> None:
    tasks = base_tasks()
    tasks[1] = task("Shadow Incident Recovery", "URGENT_REPLACEMENT")
    outcome = validate_plan_draft(draft(tasks), plan_context("ASSISTED"), KNOWN_EVIDENCE)
    assert not outcome.accepted
    assert any("URGENT_REPLACEMENT" in r for r in outcome.rejections)


def test_a_task_without_acceptance_criteria_is_rejected() -> None:
    tasks = base_tasks()
    tasks[2] = task("Execute Incident Recovery in staging", "PRACTICE", criteria=[])
    outcome = validate_plan_draft(draft(tasks), plan_context("ASSISTED"), KNOWN_EVIDENCE)
    assert not outcome.accepted


def test_a_task_whose_acceptance_criteria_are_blank_is_rejected() -> None:
    tasks = base_tasks()
    tasks[2] = task("Execute Incident Recovery in staging", "PRACTICE", criteria=["   "])
    outcome = validate_plan_draft(draft(tasks), plan_context("ASSISTED"), KNOWN_EVIDENCE)
    assert not outcome.accepted


def test_an_unknown_evidence_id_is_dropped_with_a_correction_not_a_rejection() -> None:
    """Mirrors how validate_extraction corrects evidence strength rather than rejecting."""
    tasks = base_tasks()
    tasks[0] = task(
        "Review the Incident Recovery runbook",
        "KNOWLEDGE_REVIEW",
        evidence=["ev_001", "ev_invented"],
    )
    outcome = validate_plan_draft(draft(tasks), plan_context("ASSISTED"), KNOWN_EVIDENCE)
    assert outcome.accepted, outcome.rejections
    assert outcome.draft.tasks[0].linked_evidence_ids == ["ev_001"]
    assert any("ev_invented" in c for c in outcome.corrections)


def test_the_first_task_must_link_the_evidence_it_rests_on() -> None:
    """test_golden_path.py:205."""
    tasks = base_tasks()
    tasks[0] = task("Review the Incident Recovery runbook", "KNOWLEDGE_REVIEW", evidence=[])
    outcome = validate_plan_draft(draft(tasks), plan_context("ASSISTED"), KNOWN_EVIDENCE)
    assert not outcome.accepted


def test_the_first_task_is_rejected_when_dropping_unknown_ids_leaves_it_bare() -> None:
    """Filtering runs first, so an unknown id cannot masquerade as a citation."""
    tasks = base_tasks()
    tasks[0] = task(
        "Review the Incident Recovery runbook", "KNOWLEDGE_REVIEW", evidence=["ev_invented"]
    )
    outcome = validate_plan_draft(draft(tasks), plan_context("ASSISTED"), KNOWN_EVIDENCE)
    assert not outcome.accepted


@pytest.mark.parametrize("readiness", ["NONE", "EXPOSED"])
def test_a_candidate_with_no_hands_on_evidence_must_receive_a_drill(readiness) -> None:
    """AC-09, the half that keeps test_golden_path.py:208-218 honest."""
    outcome = validate_plan_draft(draft(base_tasks()), plan_context(readiness), KNOWN_EVIDENCE)
    assert not outcome.accepted
    assert any("RECOVERY_DRILL" in r for r in outcome.rejections)

    accepted = validate_plan_draft(draft(drill_tasks()), plan_context(readiness), KNOWN_EVIDENCE)
    assert accepted.accepted, accepted.rejections


@pytest.mark.parametrize("readiness", ["NONE", "EXPOSED"])
def test_a_candidate_with_no_hands_on_evidence_gets_more_actions_than_one_who_assisted(
    readiness,
) -> None:
    """The strict inequality has to hold from a single draft, so it is encoded as a band: the
    lower readiness band takes five actions, the higher band at most four."""
    thin = drill_tasks()[:4]
    outcome = validate_plan_draft(draft(thin), plan_context(readiness), KNOWN_EVIDENCE)
    assert not outcome.accepted

    fat = validate_plan_draft(draft(drill_tasks()), plan_context("ASSISTED"), KNOWN_EVIDENCE)
    assert not fat.accepted, "five actions and a drill is the shape reserved for NONE/EXPOSED"


def test_an_unknown_readiness_value_is_rejected() -> None:
    outcome = validate_plan_draft(
        draft(base_tasks()), plan_context("SEMI_PRACTICED"), KNOWN_EVIDENCE
    )
    assert not outcome.accepted


def test_a_forbidden_phrase_in_a_plan_is_rejected() -> None:
    tasks = base_tasks()
    tasks[1] = task(
        "Shadow the critical employee", "SHADOWING", criteria=["Attend one exercise end to end"]
    )
    outcome = validate_plan_draft(draft(tasks), plan_context("ASSISTED"), KNOWN_EVIDENCE)
    assert not outcome.accepted


def test_a_third_person_named_in_a_plan_is_rejected() -> None:
    tasks = base_tasks()
    tasks[2] = task(
        "Execute Incident Recovery in staging",
        "PRACTICE",
        criteria=["Have Priya Raman confirm the result"],
    )
    outcome = validate_plan_draft(draft(tasks), plan_context("ASSISTED"), KNOWN_EVIDENCE)
    assert not outcome.accepted
    assert any("Priya Raman" in r for r in outcome.rejections)


def test_both_named_people_in_the_context_are_allowed() -> None:
    tasks = base_tasks()
    tasks[1] = task(
        "Shadow Incident Recovery with Alex Chen",
        "SHADOWING",
        criteria=["Maria Gomez records each decision point"],
    )
    outcome = validate_plan_draft(draft(tasks), plan_context("ASSISTED"), KNOWN_EVIDENCE)
    assert outcome.accepted, outcome.rejections


def test_validation_reports_rather_than_raises() -> None:
    """The whole point of the gate: bad output degrades the prose, never the request."""
    nonsense = PlanDraft(target_readiness="", tasks=[])
    outcome = validate_plan_draft(nonsense, plan_context("NONE"), set())
    assert not outcome.accepted
    assert outcome.rejections


# ---------------------------------------------------------------------------------------
# The name check: what it accepts, what it catches, and what it cannot see
#
# A gate that rejects everything is indistinguishable from a gate that works, because both
# produce the deterministic template. The first test here is the one that catches that.
# ---------------------------------------------------------------------------------------

TITLE_CASED_TASKS = [
    "Review Incident Recovery Architecture",
    "Shadow Alex Chen During Incident Recovery",
    "Execute Incident Recovery In Staging",
    "Update The Payment Gateway Runbook",
]


def test_ordinary_title_cased_output_is_accepted() -> None:
    """Title case is a formatting choice, not a semantic property. A model that capitalises its
    task titles must not have every plan silently replaced by the template."""
    tasks = [
        task(title, task_type, evidence=["ev_001"] if index == 0 else None)
        for index, (title, task_type) in enumerate(
            zip(TITLE_CASED_TASKS, ["KNOWLEDGE_REVIEW", "SHADOWING", "PRACTICE", "DOCUMENTATION"])
        )
    ]
    outcome = validate_plan_draft(draft(tasks), plan_context("ASSISTED"), KNOWN_EVIDENCE)
    assert outcome.accepted, outcome.rejections


@pytest.mark.parametrize(
    "line",
    [
        "Sarah Chen would carry Incident Recovery.",
        "Shadow Sarah Chen During Incident Recovery",
    ],
)
def test_a_name_recombined_from_an_attested_one_is_caught_in_any_casing(line) -> None:
    """The sharpest failure: an invented colleague wearing a real surname. Caught whether the
    line is written as prose or as a title, because the full attested name is never present."""
    outcome = validate_plan_draft(
        draft([task(line, "SHADOWING", evidence=["ev_001"]), *base_tasks()[1:]]),
        plan_context("ASSISTED"),
        KNOWN_EVIDENCE,
    )
    assert not outcome.accepted


@pytest.mark.parametrize(
    "line",
    [
        "Please ask Priya to confirm the result",
        "Coordinate with Stripe during the drill",
        "The settlement batching path is uncovered",
    ],
)
def test_known_blind_spots_of_the_name_check(line) -> None:
    """Documented, not hidden. These pass, and the module docstring says why: one capitalised word
    is structurally identical to any capitalised noun, and a lower-case invention offers no signal
    at all. Separating either needs a lexicon this module does not have.

    Closing the lower-case case needs the capability taxonomy passed into the validator, the way
    `validate_extraction` receives it. Until then the prompt carries that weight, and this test
    exists so nobody reads the gate as closed-world grounding it is not.
    """
    outcome = validate_plan_draft(
        draft([task(line, "SHADOWING", evidence=["ev_001"]), *base_tasks()[1:]]),
        plan_context("ASSISTED"),
        KNOWN_EVIDENCE,
    )
    assert outcome.accepted, outcome.rejections


@pytest.mark.parametrize(
    "line",
    [
        "Loop in Sarah Kim And Priya Raman before the drill.",
        "Ask Priya And Marcus to review the runbook.",
        "Contact Sarah From Payments about the drill.",
        "Escalate to The Settlement Batching owner if needed.",
        "Coverage of Refund Processing In Europe would drop.",
        "Review The Settlement Batching Runbook",
    ],
)
def test_a_capitalised_function_word_does_not_buy_a_run_an_exemption(line) -> None:
    """The title exemption is bounded to two-word runs, and this is why.

    Unbounded, one capitalised "And", "From" or "The" exempted the whole run, which let two
    invented colleagues through in ordinary prose — the case the module docstring calls the most
    damaging thing this product could print. A stripped title leaves a two-word tail ("In
    Staging", "Update The"); an invented name needs more room than that.
    """
    outcome = validate_plan_draft(
        draft([task(line, "SHADOWING", evidence=["ev_001"]), *base_tasks()[1:]]),
        plan_context("ASSISTED"),
        KNOWN_EVIDENCE,
    )
    assert not outcome.accepted


def test_a_drill_at_assisted_is_rejected_at_a_legal_action_count() -> None:
    """The rejection that keeps test_golden_path.py:213 ("RECOVERY_DRILL" not in maria_types)
    passing once a model writes the plan. Four actions is inside the ASSISTED band, so the count
    rule cannot catch this shape and only the drill rule can."""
    tasks = base_tasks()
    tasks[2] = task("Run an unaided Incident Recovery drill", "RECOVERY_DRILL")
    outcome = validate_plan_draft(draft(tasks), plan_context("ASSISTED"), KNOWN_EVIDENCE)

    assert len(tasks) == 4, "inside the ASSISTED band, so the count rule is not what rejects this"
    assert not outcome.accepted
    assert any("RECOVERY_DRILL" in r for r in outcome.rejections)


# ---------------------------------------------------------------------------------------
# Visibility
# ---------------------------------------------------------------------------------------


def test_a_rejection_is_logged_at_warning(caplog) -> None:
    """Rejections are silent by construction — the caller falls back to the template and the
    response looks normal. Without this the gate could reject every generation for a week."""
    with caplog.at_level(logging.WARNING, logger="app.ai.validation"):
        validate_simulation_summary("Alex Chen is irreplaceable.", sim_context())
    assert [r for r in caplog.records if r.levelno == logging.WARNING]
    assert "irreplaceable" in caplog.text


def test_every_validator_logs_its_rejections(caplog) -> None:
    with caplog.at_level(logging.WARNING, logger="app.ai.validation"):
        validate_candidate_narrative(CandidateNarrative(strengths=[], gaps=[]), candidate_context())
        validate_plan_draft(PlanDraft(target_readiness="", tasks=[]), plan_context("NONE"), set())
    subjects = {record.getMessage().split(" rejected")[0] for record in caplog.records}
    assert subjects == {"candidate narrative", "mitigation plan"}


def test_a_dropped_evidence_id_is_logged(caplog) -> None:
    """Quiet data loss otherwise: the plan is accepted and a citation has vanished."""
    tasks = base_tasks()
    tasks[0] = task(
        "Review the Incident Recovery runbook",
        "KNOWLEDGE_REVIEW",
        evidence=["ev_001", "ev_invented"],
    )
    with caplog.at_level(logging.INFO, logger="app.ai.validation"):
        outcome = validate_plan_draft(draft(tasks), plan_context("ASSISTED"), KNOWN_EVIDENCE)
    assert outcome.accepted, outcome.rejections
    assert "ev_invented" in caplog.text
