"""The provider chain: failover between models, and the two different failure policies.

No network. Fake providers stand in for watsonx and OpenRouter, because what needs testing is the
*policy* — which provider is tried, what happens when one dies, and whether rule-based output can
reach the graph unannounced — not either vendor's transport, which has its own tests.

The property this file exists to protect: **extraction never silently falls back to the templates.**
Every risk number in the product is computed from the extracted graph, so a quiet fallback would mean
a model outage produced a different graph while every number still looked plausible. Narratives are
allowed to fall back, because a lost sentence costs wording and a live request must not fail.
"""

from __future__ import annotations

from datetime import date

import pytest

from app.ai.chain import (
    TEMPLATE_LABEL,
    AllProvidersFailedError,
    ChainedProvider,
    ProvenanceLog,
    _is_permanent,
)
from app.ai.deterministic import DeterministicProvider
from app.ai.provider import ExtractionContext
from app.ai.schemas import (
    ArtifactExtraction,
    ArtifactInput,
    ArtifactParticipant,
    CandidateNarrative,
    TaxonomyCapability,
)
from app.ai.watsonx import QuotaExhaustedError
from app.schemas.enums import EvidenceSourceType

TEMPLATES = DeterministicProvider()


def artifact() -> ArtifactInput:
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


def context() -> ExtractionContext:
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


class Fake:
    """A provider that either answers or raises, and counts how often it was asked."""

    def __init__(self, name: str, error: Exception | None = None) -> None:
        self.name = name
        self.model_id = f"{name}-model"
        self._error = error
        self.calls = 0

    def _maybe_fail(self) -> None:
        self.calls += 1
        if self._error is not None:
            raise self._error

    def extract_artifact_semantics(self, artifact_input, extraction_context):
        self._maybe_fail()
        return ArtifactExtraction(
            artifact_id=artifact_input.artifact_id,
            system_id=artifact_input.system_hint,
            ambiguity=[f"answered by {self.name}"],
        )

    def summarize_simulation(self, ctx):
        self._maybe_fail()
        return f"sentence from {self.name}"

    def explain_candidate(self, ctx):
        self._maybe_fail()
        return CandidateNarrative(strengths=[f"from {self.name}"], gaps=[])

    def generate_mitigation_plan(self, ctx):
        self._maybe_fail()
        raise NotImplementedError("not exercised here")


# ---------------------------------------------------------------------------------------
# Failover order
# ---------------------------------------------------------------------------------------


def test_the_first_working_provider_answers_and_the_second_is_never_called() -> None:
    primary, secondary = Fake("watsonx"), Fake("openrouter")
    chain = ChainedProvider([primary, secondary], templates=TEMPLATES)

    extraction = chain.extract_artifact_semantics(artifact(), context())

    assert extraction.ambiguity == ["answered by watsonx"]
    assert secondary.calls == 0, "the fallback must not be paid for when the primary works"
    assert chain.provenance.extraction_providers() == {"watsonx": 1}


def test_when_the_primary_fails_the_secondary_extracts() -> None:
    """The case the chain was built for: the watsonx quota is spent, OpenRouter carries the run."""
    primary = Fake("watsonx", QuotaExhaustedError("token quota exhausted", {}))
    secondary = Fake("openrouter")
    chain = ChainedProvider([primary, secondary], templates=TEMPLATES)

    extraction = chain.extract_artifact_semantics(artifact(), context())

    assert extraction.ambiguity == ["answered by openrouter"]
    assert chain.provenance.extraction_providers() == {"openrouter": 1}
    assert chain.provenance.used_a_model_for_extraction() is True


def test_a_chain_needs_at_least_one_model() -> None:
    with pytest.raises(ValueError, match="at least one model provider"):
        ChainedProvider([], templates=TEMPLATES)


# ---------------------------------------------------------------------------------------
# The two failure policies, which are the point of the module
# ---------------------------------------------------------------------------------------


def test_extraction_raises_rather_than_using_the_templates(monkeypatch) -> None:
    """The rule that protects every number in the product.

    If both models are down, seeding must stop. Returning rule-based extraction here would produce a
    knowledge graph that nobody asked for and nothing announced — readiness, exposure and every risk
    index would still compute, still look plausible, and no longer mean what the demo says they mean.
    """
    templates_called = []
    monkeypatch.setattr(
        TEMPLATES,
        "extract_artifact_semantics",
        lambda *a, **k: templates_called.append(1),
    )
    chain = ChainedProvider(
        [Fake("watsonx", RuntimeError("down")), Fake("openrouter", RuntimeError("also down"))],
        templates=TEMPLATES,
    )

    with pytest.raises(AllProvidersFailedError) as raised:
        chain.extract_artifact_semantics(artifact(), context())

    assert not templates_called, "extraction must never reach the deterministic templates"
    # The error has to name both failures, or the person debugging it learns nothing.
    errors = " ".join(raised.value.details["errors"])
    assert "watsonx" in errors and "openrouter" in errors


def test_a_narrative_falls_back_to_the_template_and_says_so() -> None:
    """The opposite policy, and the labelling that keeps it honest.

    A live request must not fail over a sentence. But the fallback is recorded, so nobody can look at
    a template sentence and believe a model wrote it.
    """
    chain = ChainedProvider(
        [Fake("watsonx", RuntimeError("down")), Fake("openrouter", RuntimeError("also down"))],
        templates=TEMPLATES,
    )

    narrative = chain.explain_candidate(_candidate_context())

    assert narrative.strengths, "the caller still gets a usable narrative"
    assert chain.provenance.tally()["explain_candidate"] == {TEMPLATE_LABEL: 1}
    assert chain.provenance.used_a_model_for_extraction() is False


# ---------------------------------------------------------------------------------------
# Retiring a dead provider
# ---------------------------------------------------------------------------------------


def test_a_permanently_failed_provider_is_not_retried_on_every_artifact() -> None:
    """A spent quota does not recover inside a run.

    Without this, a 640-artifact seed calls the dead provider 640 times and waits for 640 failures.
    Retrying a permanent failure is not resilience, it is just slower — measured at roughly double the
    wall-clock time on the run that exposed it.
    """
    primary = Fake("watsonx", QuotaExhaustedError("token quota exhausted", {}))
    secondary = Fake("openrouter")
    chain = ChainedProvider([primary, secondary], templates=TEMPLATES)

    for _ in range(5):
        chain.extract_artifact_semantics(artifact(), context())

    assert primary.calls == 1, f"the dead provider was called {primary.calls} times, not once"
    assert secondary.calls == 5
    assert chain.provenance.extraction_providers() == {"openrouter": 5}


def test_a_transient_failure_does_not_retire_a_provider() -> None:
    """A timeout is not a quota. Retiring on one is how a working provider gets dropped for an hour."""
    primary = Fake("watsonx", TimeoutError("read timeout"))
    secondary = Fake("openrouter")
    chain = ChainedProvider([primary, secondary], templates=TEMPLATES)

    for _ in range(3):
        chain.extract_artifact_semantics(artifact(), context())

    assert primary.calls == 3, "a transient failure must be retried on the next artifact"


def test_permanent_and_transient_failures_are_told_apart() -> None:
    assert _is_permanent(QuotaExhaustedError("spent", {})) is True
    assert _is_permanent(RuntimeError("HTTP 401: unauthorized")) is True
    assert _is_permanent(RuntimeError("invalid api key")) is True
    assert _is_permanent(TimeoutError("read timeout")) is False
    assert _is_permanent(RuntimeError("HTTP 429: rate_limit_reached")) is False
    assert _is_permanent(RuntimeError("HTTP 503: upstream unavailable")) is False


def test_the_last_provider_is_never_retired() -> None:
    """"Everything is retired" is a worse error than whatever actually went wrong.

    A chain with nothing left cannot report why it failed on the artifact in front of it, so the final
    provider stays in and is allowed to raise its own error.
    """
    only = Fake("openrouter", QuotaExhaustedError("spent", {}))
    chain = ChainedProvider([only], templates=TEMPLATES)

    with pytest.raises(AllProvidersFailedError):
        chain.extract_artifact_semantics(artifact(), context())
    with pytest.raises(AllProvidersFailedError):
        chain.extract_artifact_semantics(artifact(), context())

    assert only.calls == 2, "the sole provider must keep being asked, and keep reporting its reason"


# ---------------------------------------------------------------------------------------
# Provenance
# ---------------------------------------------------------------------------------------


def test_provenance_reports_the_chain_order_not_a_single_name() -> None:
    """On a long run the honest answer really is "watsonx until the quota went, then openrouter"."""
    chain = ChainedProvider([Fake("watsonx"), Fake("openrouter")], templates=TEMPLATES)
    assert chain.extraction_provider_name == "watsonx+openrouter"


def test_the_provenance_log_holds_counts_and_labels_only() -> None:
    """It must not accumulate prompt or reply text.

    Artifact bodies are the most sensitive thing this system handles, and a diagnostic counter is no
    reason to keep a second copy of them in memory.
    """
    log = ProvenanceLog()
    log.record("extract_artifact_semantics", "openrouter")
    log.record("extract_artifact_semantics", "openrouter")
    log.record("summarize_simulation", TEMPLATE_LABEL)

    assert log.tally() == {
        "extract_artifact_semantics": {"openrouter": 2},
        "summarize_simulation": {TEMPLATE_LABEL: 1},
    }
    assert all(isinstance(v, int) for m in log.tally().values() for v in m.values())


def _candidate_context():
    from app.ai.schemas import CandidateNarrativeContext

    return CandidateNarrativeContext(
        candidate_name="Maria Gomez",
        capability_name="Incident Recovery",
        technical_overlap="HIGH",
        demonstrated_capabilities=["Provider Failover"],
        assisted_capabilities=["Incident Recovery"],
        missing_capabilities=[],
    )
