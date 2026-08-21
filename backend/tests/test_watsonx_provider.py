"""The watsonx provider, without touching the network.

Per `ARCHITECTURE.md` section 60, these do not test whether a model returns particular prose. They
test the parts that must hold whatever the model says: that output parses, that claims outside the
supplied lists are discarded, that evidence strength is derived rather than trusted, and that a spent
token quota fails loudly instead of quietly degrading.

`_chat` is replaced so no credential and no network are needed. That matters beyond convenience — a
test suite that only passes with a working API key and available quota is a test suite that stops
running.
"""

from __future__ import annotations

from datetime import date

import pytest

from app.ai.provider import ExtractionContext
from app.ai.schemas import ArtifactInput, ArtifactParticipant, TaxonomyCapability
from app.core.config import settings
from app.core.errors import AIExtractionError
from app.schemas.enums import EvidenceRole, EvidenceSourceType, EvidenceStrength

GATEWAY = TaxonomyCapability(
    capability_id="cap_incident_recovery",
    name="Incident Recovery",
    aliases=["gateway recovery"],
    system_id="system_payment_gateway",
    component_id="component_gateway_integration",
)
FAILOVER = TaxonomyCapability(
    capability_id="cap_provider_failover",
    name="Provider Failover",
    aliases=["failover"],
    system_id="system_payment_gateway",
    component_id="component_gateway_integration",
)
CONTEXT = ExtractionContext(
    capabilities=[GATEWAY, FAILOVER],
    engineer_names={"eng_alex_chen": "Alex Chen", "eng_maria_gomez": "Maria Gomez"},
)

ARTIFACT = ArtifactInput(
    artifact_id="artifact_inc_184",
    source_type=EvidenceSourceType.INCIDENT,
    source_reference="INC-184",
    title="P1 Payment Gateway Provider Failure",
    body="Alex was paged and restored transaction routing without escalation.",
    artifact_date=date(2026, 5, 14),
    participants=[ArtifactParticipant(engineer_id="eng_alex_chen", participant_role="RESOLVER")],
    system_hint="system_payment_gateway",
    provenance_source="synthetic_incident_dataset",
)


@pytest.fixture()
def provider(monkeypatch):
    """A provider with credentials present but every network call stubbed."""
    monkeypatch.setattr(settings, "watsonx_api_key", "test-key")
    monkeypatch.setattr(settings, "watsonx_project_id", "test-project")
    from app.ai.watsonx import WatsonxProvider

    instance = WatsonxProvider()
    instance._token = "stub"
    instance._token_expires_at = float("inf")
    return instance


def reply(provider, payload: str):
    provider._chat = lambda system, user, max_tokens: payload  # type: ignore[assignment]
    return provider


# ---------------------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------------------


def test_a_clean_json_reply_becomes_a_claim(provider) -> None:
    reply(
        provider,
        """{"claims": [{"capability_id": "cap_incident_recovery", "engineer_id": "eng_alex_chen",
        "evidence_role": "INDEPENDENT_EXECUTION", "summary": "Alex restored routing alone.",
        "rationale": "restored transaction routing without escalation"}], "ambiguity": []}""",
    )
    extraction = provider.extract_artifact_semantics(ARTIFACT, CONTEXT)

    assert len(extraction.claims) == 1
    claim = extraction.claims[0]
    assert claim.capability_id == "cap_incident_recovery"
    assert claim.evidence_role is EvidenceRole.INDEPENDENT_EXECUTION
    # Derived from the role, never taken from the model (PRD section 16.1).
    assert claim.evidence_strength is EvidenceStrength.STRONG
    assert claim.rationale.startswith("watsonx/"), "provenance should name what produced the claim"


def test_json_wrapped_in_markdown_fences_is_recovered(provider) -> None:
    """Models add fences often enough that failing on them would be a self-inflicted outage."""
    reply(
        provider,
        """```json
{"claims": [{"capability_id": "cap_provider_failover", "engineer_id": "eng_alex_chen",
"evidence_role": "CONTRIBUTION", "summary": "Alex changed failover config.", "rationale": "config"}]}
```""",
    )
    extraction = provider.extract_artifact_semantics(ARTIFACT, CONTEXT)
    assert [c.capability_id for c in extraction.claims] == ["cap_provider_failover"]


def test_json_embedded_in_prose_is_recovered(provider) -> None:
    reply(
        provider,
        'Here is the result: {"claims": []} — nothing was demonstrated.',
    )
    extraction = provider.extract_artifact_semantics(ARTIFACT, CONTEXT)
    assert extraction.claims == []


def test_output_that_is_not_json_at_all_raises(provider) -> None:
    reply(provider, "I think Alex is a strong engineer.")
    with pytest.raises(AIExtractionError):
        provider.extract_artifact_semantics(ARTIFACT, CONTEXT)


def test_an_empty_claim_list_is_a_valid_answer(provider) -> None:
    reply(provider, '{"claims": [], "ambiguity": ["routine maintenance"]}')
    extraction = provider.extract_artifact_semantics(ARTIFACT, CONTEXT)
    assert extraction.claims == []
    assert extraction.ambiguity == ["routine maintenance"]


# ---------------------------------------------------------------------------------------
# The closed world
# ---------------------------------------------------------------------------------------


def test_an_invented_capability_is_discarded_and_recorded(provider) -> None:
    reply(
        provider,
        """{"claims": [{"capability_id": "cap_totally_invented", "engineer_id": "eng_alex_chen",
        "evidence_role": "INDEPENDENT_EXECUTION", "summary": "s", "rationale": "r"}]}""",
    )
    extraction = provider.extract_artifact_semantics(ARTIFACT, CONTEXT)
    assert extraction.claims == []
    assert any("outside the supplied lists" in a for a in extraction.ambiguity)


def test_a_claim_against_a_non_participant_is_discarded(provider) -> None:
    """Maria is a known engineer but is not a participant of this artifact. The most damaging output
    available to this product is an unsupported claim against a named person."""
    reply(
        provider,
        """{"claims": [{"capability_id": "cap_incident_recovery", "engineer_id": "eng_maria_gomez",
        "evidence_role": "INDEPENDENT_EXECUTION", "summary": "s", "rationale": "r"}]}""",
    )
    extraction = provider.extract_artifact_semantics(ARTIFACT, CONTEXT)
    assert extraction.claims == []


def test_an_uncited_claim_is_discarded(provider) -> None:
    reply(
        provider,
        """{"claims": [{"capability_id": "cap_incident_recovery", "engineer_id": "eng_alex_chen",
        "evidence_role": "INDEPENDENT_EXECUTION", "summary": "", "rationale": ""}]}""",
    )
    extraction = provider.extract_artifact_semantics(ARTIFACT, CONTEXT)
    assert extraction.claims == []
    assert any("uncited" in a for a in extraction.ambiguity)


def test_an_unrecognised_evidence_role_is_discarded(provider) -> None:
    reply(
        provider,
        """{"claims": [{"capability_id": "cap_incident_recovery", "engineer_id": "eng_alex_chen",
        "evidence_role": "TOTAL_LEGEND", "summary": "s", "rationale": "r"}]}""",
    )
    extraction = provider.extract_artifact_semantics(ARTIFACT, CONTEXT)
    assert extraction.claims == []
    assert any("evidence_role" in a for a in extraction.ambiguity)


def test_no_model_call_is_made_when_there_is_nothing_to_attribute(provider) -> None:
    """A model call to confirm that an artifact with no participants demonstrates nothing would be
    pure cost — and on a quota-limited plan, cost that stops the run finishing."""

    def explode(*args, **kwargs):
        raise AssertionError("the model should not have been called")

    provider._chat = explode  # type: ignore[assignment]
    empty = ARTIFACT.model_copy(update={"participants": []})
    assert provider.extract_artifact_semantics(empty, CONTEXT).claims == []


# ---------------------------------------------------------------------------------------
# The one model-written narrative, and the gate over it
# ---------------------------------------------------------------------------------------


def sim_context() -> "SimulationSummaryContext":
    from app.ai.schemas import SimulationSummaryContext

    return SimulationSummaryContext(
        engineer_name="Alex Chen",
        scope_name="Payment Gateway",
        critical_gap_capabilities=["Incident Recovery"],
        degraded_capabilities=[],
        preserved_capabilities=["Retry Logic"],
        risk_class_before="HIGH",
        risk_class_after="CRITICAL",
    )


def test_a_grounded_summary_is_returned(provider) -> None:
    """The gate is a filter, not a blanket refusal.

    Paired with the rejection test below on purpose: a validator that rejected everything would
    still pass that one, because both outcomes look like the deterministic template.
    """
    grounded = (
        "With Alex Chen unavailable, Incident Recovery in Payment Gateway would have no adequate "
        "demonstrated coverage, while Retry Logic keeps it."
    )
    reply(provider, f'"{grounded}"')
    assert provider.summarize_simulation(sim_context()) == grounded


def test_a_poisoned_summary_is_rejected_and_the_template_is_returned(provider) -> None:
    """`summarize_simulation` is the one watsonx narrative a model writes, so it is the one place
    where model prose could reach `POST /simulations` — and `result_json`, which is persisted —
    without a rule having read it first.

    The sentence below states a likelihood twice, predicts a failure, uses two phrases from
    `prohibited_phrases.txt`, and names someone the simulation never mentioned. None of it may
    survive: the answer is the deterministic template, byte for byte.
    """
    from app.ai.deterministic import DeterministicProvider

    poisoned = (
        "Alex Chen is a critical employee, so there is a 92% chance of failure and Payment "
        "Gateway will fail without him; ask Priya Raman to cover the settlement work."
    )
    context = sim_context()
    reply(provider, poisoned)

    summary = provider.summarize_simulation(context)

    assert summary == DeterministicProvider().summarize_simulation(context)
    assert "Priya Raman" not in summary
    assert "%" not in summary


# ---------------------------------------------------------------------------------------
# Failure behaviour
# ---------------------------------------------------------------------------------------


def test_narrative_generation_falls_back_instead_of_breaking(provider) -> None:
    """Prose over facts the rules already decided should degrade in wording, not fail. The structured
    result is unchanged either way, so a timeout must not break a demo."""
    from app.ai.schemas import SimulationSummaryContext

    def explode(*args, **kwargs):
        raise AIExtractionError("model unavailable")

    provider._chat = explode  # type: ignore[assignment]
    summary = provider.summarize_simulation(
        SimulationSummaryContext(
            engineer_name="Alex Chen",
            scope_name="Payment Gateway",
            critical_gap_capabilities=["Incident Recovery"],
            degraded_capabilities=[],
            preserved_capabilities=["Retry Logic"],
            risk_class_before="HIGH",
            risk_class_after="CRITICAL",
        )
    )
    assert summary and "Alex Chen" in summary


def test_extraction_does_not_fall_back(provider) -> None:
    """Extraction must fail loudly. A silent fallback would mean a model outage quietly produced a
    different knowledge graph while every number still looked plausible."""

    def explode(*args, **kwargs):
        raise AIExtractionError("model unavailable")

    provider._chat = explode  # type: ignore[assignment]
    with pytest.raises(AIExtractionError):
        provider.extract_artifact_semantics(ARTIFACT, CONTEXT)


def test_missing_credentials_fail_at_construction(monkeypatch) -> None:
    monkeypatch.setattr(settings, "watsonx_api_key", "")
    from app.ai.watsonx import WatsonxProvider

    with pytest.raises(ValueError, match="WATSONX_API_KEY"):
        WatsonxProvider()


def test_a_spent_quota_is_a_distinct_error(provider) -> None:
    """A rate limit clears in a second; a spent quota needs a plan change or a new window. Retrying
    the second one turns a clear problem into a slow, confusing one."""
    from app.ai.watsonx import QuotaExhaustedError

    assert issubclass(QuotaExhaustedError, AIExtractionError)


def test_the_provider_is_registered_and_selectable(monkeypatch) -> None:
    monkeypatch.setattr(settings, "watsonx_api_key", "test-key")
    monkeypatch.setattr(settings, "watsonx_project_id", "test-project")
    from app.ai.provider import get_provider

    assert get_provider("watsonx").name == "watsonx"
    assert get_provider("deterministic").name == "deterministic"


def test_the_runtime_prompt_is_versioned_on_disk() -> None:
    """PRD section 26.1 requires prompts to be versioned. Keeping the runtime prompt in a file beside
    the code means the spec and the thing actually sent cannot drift apart silently."""
    from app.ai.watsonx import SYSTEM_PROMPT_FILE

    prompt = SYSTEM_PROMPT_FILE.read_text()
    assert "RETURN ONLY JSON" in prompt
    assert "Never invent one" in prompt
    # The boundary must be stated to the model, not only enforced after it answers.
    assert "readiness" in prompt.lower()
