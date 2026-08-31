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

import json
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
from app.evidence.strength import strength_for_role
from app.schemas.enums import EvidenceRole, EvidenceSourceType

RULES = DeterministicProvider()


def _extraction_artifact() -> ArtifactInput:
    return ArtifactInput(
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


def _extraction_context() -> ExtractionContext:
    return ExtractionContext(
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

# AC-14: an AI plan or explanation operation answers within 12 seconds.
AI_OPERATION_BUDGET_SECONDS = 12

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


@pytest.mark.parametrize(
    ("field", "named"),
    [("openrouter_base_url", "OPENROUTER_BASE_URL"), ("openrouter_model", "OPENROUTER_MODEL")],
)
def test_an_empty_setting_that_has_a_default_still_fails_at_construction(
    monkeypatch, field, named
) -> None:
    """An empty value in .env beats the default silently, and the only symptom would be every
    narrative degrading to the template behind one WARN line."""
    monkeypatch.setattr(settings, "openrouter_api_key", "test-key")
    monkeypatch.setattr(settings, field, "")
    from app.ai.openrouter import OpenRouterProvider

    with pytest.raises(ValueError, match=named):
        OpenRouterProvider()


def test_the_provider_is_registered_and_selectable(monkeypatch) -> None:
    monkeypatch.setattr(settings, "openrouter_api_key", "test-key")
    from app.ai.provider import get_provider

    assert get_provider("openrouter").name == "openrouter"
    assert get_provider("deterministic").name == "deterministic"


def test_extraction_is_model_written_and_closed_world(provider) -> None:
    """FR-004 through this provider, which now extracts with the model rather than delegating.

    Two properties matter more than the happy path, and both are asserted below: the model's reply is
    the source of the claims, and anything outside the supplied lists is discarded rather than
    trusted. A model that could name a capability it was not given, or attribute work to someone who
    was not present, could move a risk number by inventing evidence — so the closed world is enforced
    in code, not requested in the prompt.
    """
    artifact = _extraction_artifact()
    context = _extraction_context()
    # The model answers, and it tries to smuggle in two ungrounded claims alongside a good one.
    reply = json.dumps(
        {
            "claims": [
                {
                    "capability_id": "cap_incident_recovery",
                    "engineer_id": "eng_alex_chen",
                    "evidence_role": "INDEPENDENT_EXECUTION",
                    "summary": "Alex Chen recovered the payment gateway without escalation.",
                    "rationale": "'performed without escalation'",
                },
                {
                    "capability_id": "cap_invented_by_the_model",
                    "engineer_id": "eng_alex_chen",
                    "evidence_role": "INDEPENDENT_EXECUTION",
                    "summary": "invented capability",
                    "rationale": "invented",
                },
                {
                    "capability_id": "cap_incident_recovery",
                    "engineer_id": "eng_somebody_who_was_not_there",
                    "evidence_role": "INDEPENDENT_EXECUTION",
                    "summary": "invented person",
                    "rationale": "invented",
                },
            ],
            "ambiguity": [],
        }
    )
    provider._chat = lambda system, user, max_tokens, timeout=None: reply

    extraction = provider.extract_artifact_semantics(artifact, context)

    assert len(extraction.claims) == 1, "ungrounded claims must be discarded, not merged in"
    claim = extraction.claims[0]
    assert claim.capability_id == "cap_incident_recovery"
    assert claim.engineer_id == "eng_alex_chen"
    # The words came from the model, so provenance names the model and its id.
    assert claim.rationale.startswith(f"openrouter/{settings.openrouter_model}:")
    # Strength is derived from the role, never accepted from the model (PRD 16.1).
    assert claim.evidence_strength == strength_for_role(EvidenceRole.INDEPENDENT_EXECUTION)
    # Discards are reported rather than swallowed.
    assert len(extraction.ambiguity) == 2


def test_extraction_raises_rather_than_falling_back_to_the_template(provider) -> None:
    """The one place this provider must not degrade quietly.

    A narrative that fails costs a wording, so it falls back. Extraction decides the graph every risk
    number is computed from, so a silent fallback would mean a model outage produced a *different*
    knowledge graph while every number still looked plausible. It has to be loud.
    """
    fail(provider)
    with pytest.raises(Exception) as raised:
        provider.extract_artifact_semantics(_extraction_artifact(), _extraction_context())
    assert not isinstance(raised.value, AssertionError)


def test_extraction_provenance_now_names_openrouter(provider) -> None:
    """`scripts/seed_demo.py` reports what built the evidence in the database.

    This used to have to report `deterministic`, because extraction delegated to string matching and
    saying `openrouter` would have credited a model with rule-based output. That is no longer true —
    the model does the extraction — so the same honesty requirement now points the other way, and
    reporting `deterministic` would understate what built the graph.
    """
    from app.ai.provider import extraction_provenance

    assert provider.name == "openrouter"
    assert extraction_provenance(provider) == "openrouter"
    assert extraction_provenance(RULES) == "deterministic"


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


def test_strengths_returned_as_objects_fall_back_rather_than_printing_a_repr(provider) -> None:
    """Coercing whatever came back into a string would put `{'capability': ...}` in front of a
    manager, and it would sail through the gate as one unremarkable line."""
    reply(
        provider,
        """{"strengths": [{"capability": "Provider Failover", "note": "totally made up"}],
        "gaps": ["No qualifying evidence for Ledger Reconciliation"]}""",
    )
    context = candidate_context()
    narrative = provider.explain_candidate(context)

    assert narrative == RULES.explain_candidate(context)
    assert not any("capability" in s and "{" in s for s in narrative.strengths)


def test_an_overstated_strength_falls_back(provider) -> None:
    """Incident Recovery is assisted-only in this context, so a strength claiming it was
    demonstrated independently is the overstatement the whole product is built to avoid."""
    reply(
        provider,
        """{"strengths": ["Demonstrated Incident Recovery independently"],
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


def test_a_plan_field_returned_as_an_object_falls_back(provider) -> None:
    """The same coercion hole as the candidate strengths, on the artifact a manager approves."""
    tasks = good_plan_tasks()
    tasks[0]["title"] = {"text": "Review the runbook"}
    reply(provider, plan_payload(tasks))
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


def test_backpressure_is_waited_out_rather_than_treated_as_a_failure(provider, monkeypatch) -> None:
    """A refused request is not a failed one, and the two deserve different budgets.

    `openrouter_max_retries` stays at 0 because a *failed* narrative is not worth a second call — the
    template is already there. Backpressure never ran, so retrying costs nothing and usually works.
    """
    from app.ai.openrouter import BACKPRESSURE_ATTEMPTS

    monkeypatch.setattr(settings, "openrouter_max_retries", 0)
    monkeypatch.setattr("app.ai.openrouter.time.sleep", lambda seconds: None)
    client = FakeClient(FakeResponse(429, {"error": "slow down"}, headers={"retry-after": "1"}))
    provider._client = client

    with pytest.raises(AIExtractionError):
        provider._chat("system", "user", 100)
    assert len(client.calls) == BACKPRESSURE_ATTEMPTS + 1, (
        "backpressure should be waited out several times before the template takes over, and must "
        "not be governed by openrouter_max_retries"
    )


def test_a_concurrency_402_is_backpressure_and_not_an_empty_wallet(provider, monkeypatch) -> None:
    """OPEN-15. The 402 that cost a fifth of a 640-artifact run.

    OpenRouter answers *payment required* when concurrent requests would exceed the available balance.
    It reads like "you are out of money" and means "not all at once". Treating it as terminal abandoned
    127 artifacts that the same run at one worker completed — and pointed the person debugging at a
    billing problem that did not exist.
    """
    from app.ai.openrouter import BACKPRESSURE_ATTEMPTS

    monkeypatch.setattr(settings, "openrouter_max_retries", 0)
    monkeypatch.setattr("app.ai.openrouter.time.sleep", lambda seconds: None)
    client = FakeClient(
        FakeResponse(
            402,
            {
                "error": {
                    "message": "This request would exceed your available credits given your "
                    "current in-flight requests. Retry after in-flight requests settle.",
                    "code": 402,
                }
            },
        )
    )
    provider._client = client

    with pytest.raises(AIExtractionError):
        provider._chat("system", "user", 100)
    assert len(client.calls) == BACKPRESSURE_ATTEMPTS + 1, "the concurrency 402 was not waited out"


def test_a_genuinely_exhausted_balance_fails_fast(provider, monkeypatch) -> None:
    """The other half of the 402, and the reason the body is inspected rather than the status alone.

    A real empty balance will not recover by waiting, so sleeping three times on the way to the same
    answer wastes the caller's budget and buries the actual cause.
    """
    monkeypatch.setattr(settings, "openrouter_max_retries", 0)
    monkeypatch.setattr("app.ai.openrouter.time.sleep", lambda seconds: None)
    client = FakeClient(
        FakeResponse(402, {"error": {"message": "Insufficient credits. Add more to continue."}})
    )
    provider._client = client

    with pytest.raises(AIExtractionError):
        provider._chat("system", "user", 100)
    assert len(client.calls) == 1, "an exhausted balance should not be retried"


def test_the_per_call_timeout_is_a_total_and_not_a_ceiling_per_phase(provider) -> None:
    """The AC-14 arithmetic is only true if the configured number bounds the call.

    `httpx.Client(timeout=3.5)` gives connect, write, read and pool 3.5 seconds *each*, so a call
    that spends 3.4 connecting and 3.4 reading is inside every one of those and outside the
    budget three of them were multiplied into. Splitting one budget across the four phases makes
    the documented number the ceiling rather than a nominal figure.
    """
    import httpx

    client = FakeClient(content("a sentence"))
    provider._client = client
    provider._chat("system", "user", 100)

    timeout = client.calls[0]["timeout"]
    assert isinstance(timeout, httpx.Timeout)
    total = timeout.connect + timeout.write + timeout.read + timeout.pool
    assert total == pytest.approx(settings.openrouter_timeout_seconds)
    # Every phase has to carry some of it; a zero share is a phase that times out instantly.
    assert min(timeout.connect, timeout.write, timeout.read, timeout.pool) > 0


def test_the_plan_gets_twice_the_budget_and_it_is_still_a_total(provider) -> None:
    """The one narrative that is a single call per request may spend more of AC-14's 12 seconds,
    but the multiplier has to apply to a real ceiling for that to mean anything."""
    import httpx

    from app.ai.openrouter import PLAN_TIMEOUT_MULTIPLIER

    client = FakeClient(content("a sentence"))
    provider._client = client
    provider._chat(
        "system", "user", 100, timeout=settings.openrouter_timeout_seconds * PLAN_TIMEOUT_MULTIPLIER
    )

    timeout = client.calls[0]["timeout"]
    total = timeout.connect + timeout.write + timeout.read + timeout.pool
    assert total == pytest.approx(
        settings.openrouter_timeout_seconds * PLAN_TIMEOUT_MULTIPLIER
    )
    assert isinstance(timeout, httpx.Timeout)


def test_the_call_stays_inside_the_operation_budget() -> None:
    """AC-14 gives an AI plan or explanation 12 seconds.

    `explain_candidate` is issued once per returned candidate, so the number of sequential calls
    is bounded by the contract's cap on `limit` and the per-call ceiling has to divide the budget
    by that. Read from the field rather than written as a literal: a hardcoded 3 here asserts an
    assumption about the caller instead of the caller's actual bound, which is how the earlier
    version of this test passed while the service was making four calls.

    The multiplication is only meaningful because the per-call figure is a total rather than a
    per-phase ceiling — see `test_the_per_call_timeout_is_a_total_and_not_a_ceiling_per_phase`.
    """
    from app.schemas.recommendation import BackupCandidateRequest

    constraints = BackupCandidateRequest.model_fields["limit"].metadata
    max_candidates = next(c.le for c in constraints if hasattr(c, "le"))

    assert settings.openrouter_timeout_seconds * max_candidates <= AI_OPERATION_BUDGET_SECONDS


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
