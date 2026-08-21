"""The OpenRouter provider, without touching the network.

The mirror image of tests/test_watsonx_provider.py, because the provider is the mirror image of
that one: extraction here is deterministic and the *narratives* are model-written. So these do not
test whether a model writes good prose. They test the property that makes letting it write prose
defensible at all — that every generation goes through `app/ai/validation.py` before it is
returned, and that anything the gate rejects, anything malformed, and anything that never arrived
comes back as the deterministic template instead.

`_chat` is replaced throughout, so no credential and no network are needed. The handful of tests
that exercise the transport itself replace the httpx client instead, which is still offline.
"""

from __future__ import annotations

from datetime import date

import pytest

from app.ai.deterministic import DeterministicProvider
from app.ai.provider import ExtractionContext
from app.ai.schemas import (
    ArtifactInput,
    ArtifactParticipant,
    CandidateNarrativeContext,
    PlanContext,
    SimulationSummaryContext,
    TaxonomyCapability,
)
from app.core.config import settings
from app.core.errors import AIExtractionError
from app.schemas.enums import EvidenceSourceType

RULES = DeterministicProvider()

# ---------------------------------------------------------------------------------------
# Fixtures and helpers
# ---------------------------------------------------------------------------------------


@pytest.fixture()
def provider(monkeypatch):
    """A provider with a credential present but every network call stubbed."""
    monkeypatch.setattr(settings, "openrouter_api_key", "test-key")
    from app.ai.openrouter import OpenRouterProvider

    return OpenRouterProvider()


def reply(provider, payload: str):
    """Answer the next model call with `payload`, whatever was asked."""
    provider._chat = lambda system, user, max_tokens, timeout=None: payload  # type: ignore[assignment]
    return provider


def fail(provider, exc: Exception | None = None):
    """Make the model call fail the way a timeout or a 500 does."""

    def explode(*args, **kwargs):
        raise exc or AIExtractionError("model unavailable")

    provider._chat = explode  # type: ignore[assignment]
    return provider


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


def candidate_context(**overrides) -> CandidateNarrativeContext:
    base = dict(
        capability_name="Incident Recovery",
        candidate_name="Maria Gomez",
        technical_overlap="HIGH",
        demonstrated_capabilities=["Provider Failover"],
        assisted_capabilities=["Incident Recovery"],
        missing_capabilities=["Ledger Reconciliation"],
    )
    base.update(overrides)
    return CandidateNarrativeContext(**base)


def plan_context(readiness: str = "ASSISTED", **overrides) -> PlanContext:
    base = dict(
        capability_name="Incident Recovery",
        system_name="Payment Gateway",
        component_name="Gateway Integration",
        source_engineer_name="Alex Chen",
        candidate_name="Maria Gomez",
        candidate_readiness=readiness,
        target_readiness="PRACTICED",
        missing_capabilities=["Provider Failover"],
        reference_evidence=[
            {"evidence_id": "ev_001", "source_reference": "INC-184"},
            {"evidence_id": "ev_002", "source_reference": "INC-207"},
        ],
    )
    base.update(overrides)
    return PlanContext(**base)


GOOD_SUMMARY = (
    "Without Alex Chen, Payment Gateway moves from MODERATE to HIGH: Incident Recovery would "
    "have no adequate demonstrated coverage and Refund Processing would lose redundancy."
)

GOOD_CANDIDATE_JSON = (
    '{"strengths": ["Demonstrated Provider Failover on the gateway path", '
    '"Assisted on Incident Recovery"], '
    '"gaps": ["No qualifying independent evidence for Incident Recovery", '
    '"No qualifying evidence for Ledger Reconciliation"]}'
)


def plan_task(
    title: str,
    task_type: str,
    description: str = "Work through the Incident Recovery path in Gateway Integration.",
    criteria: list[str] | None = None,
    evidence: list[str] | None = None,
) -> dict:
    return {
        "title": title,
        "description": description,
        "task_type": task_type,
        "acceptance_criteria": criteria or ["Complete the step and record what was missing"],
        "linked_evidence_ids": evidence or [],
    }


def plan_payload(tasks: list[dict]) -> str:
    import json

    return json.dumps({"tasks": tasks})


def good_plan_tasks() -> list[dict]:
    """Three actions, which is what a candidate who has already assisted takes."""
    return [
        plan_task(
            "Review the Incident Recovery path",
            "KNOWLEDGE_REVIEW",
            description="Review the Incident Recovery path in Gateway Integration and INC-184.",
            evidence=["ev_001"],
        ),
        plan_task("Shadow Incident Recovery with Alex Chen", "SHADOWING"),
        plan_task("Execute Incident Recovery in staging", "PRACTICE"),
    ]


# ---------------------------------------------------------------------------------------
# Wiring: configuration, registration, and the deterministic extraction half
# ---------------------------------------------------------------------------------------


def test_a_missing_credential_fails_at_construction(monkeypatch) -> None:
    monkeypatch.setattr(settings, "openrouter_api_key", "")
    from app.ai.openrouter import OpenRouterProvider

    with pytest.raises(ValueError, match="OPENROUTER_API_KEY"):
        OpenRouterProvider()


def test_the_provider_is_registered_and_selectable(monkeypatch) -> None:
    monkeypatch.setattr(settings, "openrouter_api_key", "test-key")
    from app.ai.provider import get_provider

    assert get_provider("openrouter").name == "openrouter"
    assert get_provider("deterministic").name == "deterministic"


def test_extraction_is_the_deterministic_one_and_calls_no_model(provider) -> None:
    """This provider buys narratives, not extraction. Every risk number in the product is
    computed from the extracted graph, so that half stays rule-based and reproducible."""
    artifact = ArtifactInput(
        artifact_id="artifact_inc_184",
        source_type=EvidenceSourceType.INCIDENT,
        source_reference="INC-184",
        title="P1 Payment Gateway Provider Failure",
        body="Incident Recovery was performed without escalation.",
        artifact_date=date(2026, 5, 14),
        participants=[
            ArtifactParticipant(engineer_id="eng_alex_chen", participant_role="RESOLVER")
        ],
        system_hint="system_payment_gateway",
        provenance_source="synthetic_incident_dataset",
    )
    context = ExtractionContext(
        capabilities=[
            TaxonomyCapability(
                capability_id="cap_incident_recovery",
                name="Incident Recovery",
                system_id="system_payment_gateway",
                component_id="component_gateway_integration",
            )
        ],
        engineer_names={"eng_alex_chen": "Alex Chen"},
    )
    fail(provider, AssertionError("the model must not be called for extraction"))

    extraction = provider.extract_artifact_semantics(artifact, context)
    expected = RULES.extract_artifact_semantics(artifact, context)
    assert [c.model_dump() for c in extraction.claims] == [c.model_dump() for c in expected.claims]


def test_the_provider_refuses_to_build_an_extraction_cache(monkeypatch) -> None:
    """`--provider openrouter` would write an openrouter_cache.json full of deterministic output,
    which is the one artifact in this repo that must not be misleading about its own provenance."""
    monkeypatch.setattr(settings, "openrouter_api_key", "test-key")
    monkeypatch.setattr(
        "sys.argv", ["/repo/backend/scripts/extract_with_provider.py", "--provider", "openrouter"]
    )
    from app.ai.openrouter import CacheBuildRefusedError, OpenRouterProvider

    with pytest.raises(CacheBuildRefusedError, match="deterministic"):
        OpenRouterProvider()


# ---------------------------------------------------------------------------------------
# The simulation sentence
# ---------------------------------------------------------------------------------------


def test_a_grounded_summary_is_returned(provider) -> None:
    reply(provider, f'  "{GOOD_SUMMARY}"  ')
    assert provider.summarize_simulation(sim_context()) == GOOD_SUMMARY


def test_a_summary_that_states_a_likelihood_falls_back(provider) -> None:
    """CI-32: a simulation reports coverage loss, never the odds of an outage."""
    reply(provider, "There is a 70% chance the gateway fails without Alex Chen.")
    assert provider.summarize_simulation(sim_context()) == RULES.summarize_simulation(sim_context())


def test_a_summary_naming_someone_the_simulation_did_not_falls_back(provider) -> None:
    reply(
        provider,
        "Without Alex Chen, Sarah Kim would carry Incident Recovery in Payment Gateway alone.",
    )
    assert provider.summarize_simulation(sim_context()) == RULES.summarize_simulation(sim_context())


def test_an_empty_summary_falls_back(provider) -> None:
    reply(provider, "   ")
    assert provider.summarize_simulation(sim_context()) == RULES.summarize_simulation(sim_context())


def test_a_transport_failure_on_the_summary_falls_back(provider) -> None:
    fail(provider)
    assert provider.summarize_simulation(sim_context()) == RULES.summarize_simulation(sim_context())


# ---------------------------------------------------------------------------------------
# Candidate strengths and gaps
# ---------------------------------------------------------------------------------------


def test_a_grounded_candidate_narrative_is_returned(provider) -> None:
    reply(provider, GOOD_CANDIDATE_JSON)
    narrative = provider.explain_candidate(candidate_context())
    # The model's wording, not the template's — the deterministic lines name the same capabilities,
    # so only the phrasing distinguishes them.
    assert "Demonstrated Provider Failover on the gateway path" in narrative.strengths
    assert any("Ledger Reconciliation" in g for g in narrative.gaps)


def test_candidate_json_wrapped_in_fences_is_recovered(provider) -> None:
    """Models add fences often enough that failing on them would be a self-inflicted outage."""
    reply(provider, f"```json\n{GOOD_CANDIDATE_JSON}\n```")
    narrative = provider.explain_candidate(candidate_context())
    assert narrative.strengths and narrative.gaps
    assert narrative != RULES.explain_candidate(candidate_context())


def test_a_gap_phrased_as_inability_falls_back(provider) -> None:
    """PRD section 22.3. A gap is absence of evidence, never a statement about the person."""
    reply(
        provider,
        """{"strengths": ["Assisted on Incident Recovery"],
        "gaps": ["Maria Gomez cannot recover the gateway unaided"]}""",
    )
    context = candidate_context()
    assert provider.explain_candidate(context) == RULES.explain_candidate(context)


def test_a_narrative_with_no_gaps_falls_back(provider) -> None:
    """Strengths alone read as an endorsement, which is not what a candidate view is."""
    reply(provider, '{"strengths": ["Assisted on Incident Recovery"], "gaps": []}')
    context = candidate_context()
    assert provider.explain_candidate(context) == RULES.explain_candidate(context)


def test_a_candidate_narrative_naming_an_invented_colleague_falls_back(provider) -> None:
    reply(
        provider,
        """{"strengths": ["Worked alongside Sarah Kim on Provider Failover"],
        "gaps": ["No qualifying evidence for Ledger Reconciliation"]}""",
    )
    context = candidate_context()
    assert provider.explain_candidate(context) == RULES.explain_candidate(context)


def test_a_candidate_reply_that_is_not_json_falls_back(provider) -> None:
    reply(provider, "Maria looks like a strong choice to me.")
    context = candidate_context()
    assert provider.explain_candidate(context) == RULES.explain_candidate(context)


def test_a_transport_failure_on_the_candidate_narrative_falls_back(provider) -> None:
    fail(provider)
    context = candidate_context()
    assert provider.explain_candidate(context) == RULES.explain_candidate(context)


# ---------------------------------------------------------------------------------------
# The mitigation plan
# ---------------------------------------------------------------------------------------


def test_a_valid_plan_is_returned(provider) -> None:
    reply(provider, plan_payload(good_plan_tasks()))
    draft = provider.generate_mitigation_plan(plan_context())

    assert [t.task_type for t in draft.tasks] == ["KNOWLEDGE_REVIEW", "SHADOWING", "PRACTICE"]
    assert draft.tasks[0].title == "Review the Incident Recovery path", "the model's own wording"
    # Never taken from the model: the target is a deterministic decision made upstream.
    assert draft.target_readiness == "PRACTICED"


def test_plan_json_wrapped_in_fences_is_recovered(provider) -> None:
    reply(provider, f"```json\n{plan_payload(good_plan_tasks())}\n```")
    draft = provider.generate_mitigation_plan(plan_context())
    assert len(draft.tasks) == 3


def test_the_returned_plan_is_the_filtered_one_not_the_raw_draft(provider) -> None:
    """`validate_plan_draft` drops citations that do not resolve. Returning the draft that was
    passed in would put an unresolvable evidence id in front of a manager."""
    tasks = good_plan_tasks()
    tasks[0]["linked_evidence_ids"] = ["ev_001", "ev_invented"]
    reply(provider, plan_payload(tasks))

    draft = provider.generate_mitigation_plan(plan_context())
    assert draft.tasks[0].linked_evidence_ids == ["ev_001"]


def test_a_plan_with_too_many_actions_falls_back(provider) -> None:
    tasks = good_plan_tasks() + [
        plan_task("Write the runbook", "DOCUMENTATION"),
        plan_task("Review the architecture", "ARCHITECTURE_REVIEW"),
        plan_task("Practise again", "PRACTICE"),
    ]
    reply(provider, plan_payload(tasks))
    context = plan_context()
    assert provider.generate_mitigation_plan(context) == RULES.generate_mitigation_plan(context)


def test_a_plan_with_an_invented_task_type_falls_back(provider) -> None:
    tasks = good_plan_tasks()
    tasks[1]["task_type"] = "PAIR_PROGRAMMING"
    reply(provider, plan_payload(tasks))
    context = plan_context()
    assert provider.generate_mitigation_plan(context) == RULES.generate_mitigation_plan(context)


def test_a_plan_without_the_drill_the_candidate_needs_falls_back(provider) -> None:
    """AC-09: a candidate with no hands-on evidence is given the unaided drill, and a plan that
    omits it is the wrong plan for that candidate however well it reads."""
    reply(provider, plan_payload(good_plan_tasks()))
    context = plan_context("EXPOSED")
    assert provider.generate_mitigation_plan(context) == RULES.generate_mitigation_plan(context)


def test_a_plan_whose_opening_action_cites_nothing_falls_back(provider) -> None:
    tasks = good_plan_tasks()
    tasks[0]["linked_evidence_ids"] = []
    reply(provider, plan_payload(tasks))
    context = plan_context()
    assert provider.generate_mitigation_plan(context) == RULES.generate_mitigation_plan(context)


def test_a_plan_reply_that_is_not_json_falls_back(provider) -> None:
    reply(provider, "Sure! Here is a plan: first, review the runbook.")
    context = plan_context()
    assert provider.generate_mitigation_plan(context) == RULES.generate_mitigation_plan(context)


def test_a_plan_missing_required_task_fields_falls_back(provider) -> None:
    reply(provider, '{"tasks": [{"title": "Review the runbook"}]}')
    context = plan_context()
    assert provider.generate_mitigation_plan(context) == RULES.generate_mitigation_plan(context)


def test_a_transport_failure_on_the_plan_falls_back(provider) -> None:
    fail(provider)
    context = plan_context()
    assert provider.generate_mitigation_plan(context) == RULES.generate_mitigation_plan(context)


# ---------------------------------------------------------------------------------------
# Transport, still offline: the httpx client is replaced rather than the chat method
# ---------------------------------------------------------------------------------------


class FakeResponse:
    def __init__(self, status_code: int, payload: dict | None = None, headers: dict | None = None):
        self.status_code = status_code
        self._payload = payload or {}
        self.headers = headers or {}
        self.text = str(self._payload)

    def json(self) -> dict:
        return self._payload


class FakeClient:
    """Answers each post with the next scripted response, repeating the last one."""

    def __init__(self, *responses: FakeResponse):
        self._responses = list(responses)
        self.calls: list[dict] = []

    def post(self, url, json=None, headers=None, timeout=None):  # noqa: A002
        self.calls.append({"url": url, "json": json, "headers": headers, "timeout": timeout})
        return self._responses[min(len(self.calls) - 1, len(self._responses) - 1)]


def content(text: str) -> FakeResponse:
    return FakeResponse(200, {"choices": [{"message": {"content": text}}]})


def test_the_chat_call_is_openai_shaped(provider, monkeypatch) -> None:
    client = FakeClient(content("a sentence"))
    provider._client = client
    monkeypatch.setattr(settings, "openrouter_model", "anthropic/claude-sonnet-5")

    assert provider._chat("system", "user", 100) == "a sentence"

    call = client.calls[0]
    assert call["url"].endswith("/chat/completions")
    assert call["headers"]["Authorization"].startswith("Bearer ")
    assert call["json"]["model"] == "anthropic/claude-sonnet-5"
    assert call["json"]["messages"][0]["role"] == "system"
    # Narration of computed facts is a classification-like task: sampling buys nothing and costs
    # reproducibility.
    assert call["json"]["temperature"] == 0


def test_a_reply_without_a_message_is_an_extraction_error(provider) -> None:
    provider._client = FakeClient(FakeResponse(200, {"choices": []}))
    with pytest.raises(AIExtractionError):
        provider._chat("system", "user", 100)


def test_a_rate_limited_call_is_retried_and_then_gives_up(provider, monkeypatch) -> None:
    monkeypatch.setattr(settings, "openrouter_max_retries", 1)
    monkeypatch.setattr("app.ai.openrouter.time.sleep", lambda seconds: None)
    client = FakeClient(FakeResponse(429, {"error": "slow down"}, headers={"retry-after": "1"}))
    provider._client = client

    with pytest.raises(AIExtractionError):
        provider._chat("system", "user", 100)
    assert len(client.calls) == 2, "one retry, then the deterministic template takes over"


def test_the_call_stays_inside_the_operation_budget(provider) -> None:
    """AC-14 gives an AI plan or explanation 12 seconds. `explain_candidate` is issued once per
    candidate, up to three sequentially, so the per-call ceiling has to be a third of that."""
    assert settings.openrouter_timeout_seconds * 3 <= 12


# ---------------------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------------------


def test_the_runtime_prompts_are_versioned_on_disk() -> None:
    """PRD section 26.1. Keeping the prompts in files beside the code means the rule they state
    and the text actually sent cannot drift apart silently.

    They also carry the grounding rule. `find_unattested_names` is a documented heuristic with
    real blind spots, so the prompt is the primary defence against an invented capability or an
    invented colleague, not a nicety on top of the gate.
    """
    from app.ai.openrouter import CANDIDATE_PROMPT_FILE, PLAN_PROMPT_FILE, SIMULATION_PROMPT_FILE

    for path in (SIMULATION_PROMPT_FILE, CANDIDATE_PROMPT_FILE, PLAN_PROMPT_FILE):
        text = path.read_text()
        assert "invent" in text.lower(), f"{path.name} does not forbid invention"
        assert "readiness" in text.lower() or "risk" in text.lower(), (
            f"{path.name} does not state the decision boundary"
        )
