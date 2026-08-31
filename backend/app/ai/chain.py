"""One provider that tries several, in order, and records which one answered.

Why this exists. Two model providers are configured and neither is reliable on its own: watsonx has a
capped token quota that can be spent mid-run, and any hosted gateway can rate-limit or time out. Left
as a single choice, `AI_PROVIDER=watsonx` means "work until the quota runs out, then stop", and
`AI_PROVIDER=openrouter` means "never use the IBM model we were asked to use". Chaining them means the
graph is model-derived whenever *any* model is reachable, which is the actual requirement.

**The failure policy is deliberately not uniform**, and the split matters more than the chaining:

* **Extraction hands over between models and then raises.** It never silently reaches the rule-based
  extractor. Extraction decides the knowledge graph that every risk number is computed from, so a
  quiet fallback would mean a model outage produced a *different* graph while every number still
  looked plausible and nothing announced it. A seed run that dies with "every provider failed" is a
  bad afternoon; a demo built on a graph you believe a model produced and it did not is a bad claim.
* **Narratives hand over between models and then fall back to the template.** That prose sits over
  facts the rules already decided, so a lost sentence costs wording. A live request must not 500
  because a gateway was slow.

So the rule is: never fake the graph, never break the screen.

Every answer is recorded in `provenance`, so "the model is running" is a checkable claim rather than
an assertion. `scripts/seed_demo.py` prints the tally, and a template fallback is reported rather than
hidden — the point is not to conceal the deterministic path but to stop it being mistaken for a model.
"""

from __future__ import annotations

import logging
import threading
from collections import Counter

from app.ai.provider import AIProvider, ExtractionContext, extraction_provenance
from app.ai.schemas import (  # noqa: I001 — grouped with the protocol import above
    ArtifactExtraction,
    ArtifactInput,
    CandidateNarrative,
    CandidateNarrativeContext,
    PlanContext,
    PlanDraft,
    SimulationSummaryContext,
)
from app.core.errors import AIExtractionError

logger = logging.getLogger(__name__)

TEMPLATE_LABEL = "deterministic-template"


def _is_permanent(exc: Exception) -> bool:
    """Is this a condition that the next artifact will hit too?

    A spent token quota does not recover inside a run, and neither does a rejected credential. Left
    untreated, a 640-artifact seed calls the dead provider 640 times, waits for 640 failures, and logs
    640 identical warnings — measured at roughly a doubling of wall-clock time on the run that
    exposed it. Retrying a permanent failure is not resilience, it is just slower.

    Matched on the error *type* where one exists, and on message text only as a fallback, because
    HTTP status alone does not distinguish "slow down" from "you have nothing left".
    """
    from app.ai.watsonx import QuotaExhaustedError

    if isinstance(exc, QuotaExhaustedError):
        return True
    text = str(exc).lower()
    return any(
        phrase in text
        for phrase in ("quota", "unauthorized", "invalid api key", "authentication", "403")
    )


class AllProvidersFailedError(AIExtractionError):
    """Every model in the chain failed on one artifact.

    Raised rather than returning rule-based extraction. See the module docstring: the alternative is
    a graph that silently stops being model-derived.
    """


class ProvenanceLog:
    """Which provider actually answered, counted per method. Thread-safe.

    Narration runs on worker threads (`app/ai/budget.py`), so this is locked. It holds counts and
    labels only — never prompt or reply content, which would put artifact text in a process that has
    no reason to retain it.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._counts: Counter[tuple[str, str]] = Counter()

    def record(self, method: str, provider_label: str) -> None:
        with self._lock:
            self._counts[(method, provider_label)] += 1

    def tally(self) -> dict[str, dict[str, int]]:
        with self._lock:
            grouped: dict[str, dict[str, int]] = {}
            for (method, label), count in sorted(self._counts.items()):
                grouped.setdefault(method, {})[label] = count
            return grouped

    def extraction_providers(self) -> dict[str, int]:
        return self.tally().get("extract_artifact_semantics", {})

    def used_a_model_for_extraction(self) -> bool:
        """True when at least one artifact was extracted by something other than the templates."""
        return any(
            label not in {TEMPLATE_LABEL, "deterministic"}
            for label in self.extraction_providers()
        )

    def reset(self) -> None:
        with self._lock:
            self._counts.clear()


class ChainedProvider:
    """Try each provider in order. First success wins.

    `providers` is ordered by preference and must contain at least one entry. `templates` is the
    deterministic provider used for narrative fallback only — never for extraction.
    """

    name = "chain"

    def __init__(self, providers: list[AIProvider], templates: AIProvider) -> None:
        if not providers:
            raise ValueError(
                "AI_PROVIDER=chain needs at least one model provider configured. Set "
                "WATSONX_API_KEY or OPENROUTER_API_KEY in backend/.env."
            )
        self._providers = providers
        self._templates = templates
        self.provenance = ProvenanceLog()

        # Stop each member substituting the template on its own.
        #
        # Both model providers degrade to the deterministic template internally, which meant a failed
        # generation returned *successfully* and this chain never reached its next provider. Measured
        # with the watsonx quota spent: `POST /simulations` came back as template prose because watsonx
        # caught its own HTTP 403, returned the template, and OpenRouter — which was working — was never
        # asked. The chain's entire reason for existing was dead code for all three narratives.
        #
        # With this off, a member raises `NarrativeUnavailableError` and `_narrate` moves on. The
        # template is applied here, once, after every model has genuinely been tried.
        for provider in providers:
            if hasattr(provider, "degrade_to_template"):
                provider.degrade_to_template = False
        # Providers retired for the rest of the process after a permanent failure. See `_is_permanent`.
        self._retired: set[str] = set()
        self._retire_lock = threading.Lock()

    def _live_providers(self) -> list[AIProvider]:
        with self._retire_lock:
            retired = set(self._retired)
        live = [p for p in self._providers if p.name not in retired]
        # Never retire the last one. A chain with nothing left cannot report *why* it failed on the
        # artifact in front of it, and "every provider is retired" is a worse error message than
        # whatever the real failure turns out to be.
        return live or self._providers[-1:]

    def _retire(self, provider: AIProvider, exc: Exception) -> None:
        with self._retire_lock:
            if provider.name in self._retired:
                return
            self._retired.add(provider.name)
        logger.warning(
            "%s is out for the rest of this run (%s). Remaining: %s",
            provider.name,
            exc,
            ", ".join(p.name for p in self._providers if p.name not in self._retired) or "none",
        )

    @property
    def extraction_provider_name(self) -> str:
        """What the chain would use for extraction, for the seed summary.

        Reports the order rather than one name, because on a long run the answer genuinely can be
        "watsonx until the quota went, then openrouter", and collapsing that to a single label would
        misdescribe the graph. The per-artifact truth is in `provenance`.
        """
        return "+".join(extraction_provenance(p) for p in self._providers)

    @property
    def model_id(self) -> str:
        return ",".join(
            f"{p.name}:{getattr(p, 'model_id', 'n/a')}" for p in self._providers
        )

    # -- extraction: models only, then raise ---------------------------------------------

    def extract_artifact_semantics(
        self, artifact: ArtifactInput, context: ExtractionContext
    ) -> ArtifactExtraction:
        errors: list[str] = []
        for provider in self._live_providers():
            try:
                extraction = provider.extract_artifact_semantics(artifact, context)
            except Exception as exc:  # noqa: BLE001 — the next provider is the response to any failure
                errors.append(f"{provider.name}: {type(exc).__name__}: {exc}")
                if _is_permanent(exc):
                    self._retire(provider, exc)
                else:
                    logger.warning(
                        "extraction via %s failed for %s (%s); trying the next provider",
                        provider.name,
                        artifact.source_reference,
                        exc,
                    )
                continue
            self.provenance.record("extract_artifact_semantics", provider.name)
            return extraction

        raise AllProvidersFailedError(
            f"Every configured model failed to extract {artifact.source_reference}. Extraction does "
            f"not fall back to rule-based output, because that would change the knowledge graph "
            f"without changing any number that depends on it. Fix a provider and re-run.",
            {"artifact_id": artifact.artifact_id, "errors": errors},
        )

    # -- narratives: models, then the template -------------------------------------------

    def summarize_simulation(self, context: SimulationSummaryContext) -> str | None:
        return self._narrate(
            "summarize_simulation", lambda p: p.summarize_simulation(context)
        )

    def explain_candidate(self, context: CandidateNarrativeContext) -> CandidateNarrative:
        return self._narrate(
            "explain_candidate", lambda p: p.explain_candidate(context)
        )

    def generate_mitigation_plan(self, context: PlanContext) -> PlanDraft:
        return self._narrate(
            "generate_mitigation_plan", lambda p: p.generate_mitigation_plan(context)
        )

    def _narrate(self, method: str, call):
        """Each model in turn, then the deterministic template.

        A subtlety worth stating: a model provider that internally rejects its own output already
        returns the template rather than raising, so this cannot tell "the model wrote it" from "the
        model's provider fell back". `provenance` therefore records the *provider* that answered, not
        a guarantee that a model wrote the words. The gate's own rejections are logged by
        `app/ai/validation.py`, which is where that distinction is visible.
        """
        for provider in self._live_providers():
            try:
                answer = call(provider)
            except Exception as exc:  # noqa: BLE001
                if _is_permanent(exc):
                    self._retire(provider, exc)
                else:
                    logger.warning(
                        "%s via %s failed (%s); trying the next provider", method, provider.name, exc
                    )
                continue
            self.provenance.record(method, provider.name)
            return answer

        logger.warning(
            "%s: every configured model failed; using the deterministic template", method
        )
        self.provenance.record(method, TEMPLATE_LABEL)
        return call(self._templates)

    # -- raw transport, for the optional enrichments -------------------------------------

    def _chat(self, system: str, user: str, max_tokens: int, timeout: float | None = None) -> str:
        """One model call through the chain, with the same failover and retirement.

        Defaults to the batch budget rather than the narrative one, because everything that reaches
        this method is an enrichment running outside an API request. See
        `openrouter_batch_timeout_seconds`.

        Exposed because `app/ai/criticality.py` (FR-010) needs a model but is not one of the four
        `AIProvider` methods. Adding a fifth method to the protocol would force every provider —
        including the deterministic one, which has no model and no opinion on business criticality — to
        implement something only two of them can do. A capability that some providers have is better
        expressed as an optional attribute callers can test for than as a protocol method most
        implementations would have to refuse.

        No template fallback here on purpose: the deterministic provider has no answer to give, and an
        enrichment that cannot be produced is correctly absent rather than invented. Callers treat a
        raised error as "no suggestion".
        """
        from app.core.config import settings

        budget = timeout if timeout is not None else settings.openrouter_batch_timeout_seconds
        errors: list[str] = []
        for provider in self._live_providers():
            call = getattr(provider, "_chat", None)
            if call is None:
                continue
            try:
                try:
                    answer = call(system, user, max_tokens, timeout=budget)
                except TypeError:
                    # Not every provider's transport takes a timeout. watsonx sizes its own.
                    answer = call(system, user, max_tokens)
            except Exception as exc:  # noqa: BLE001
                errors.append(f"{provider.name}: {exc}")
                if _is_permanent(exc):
                    self._retire(provider, exc)
                continue
            self.provenance.record("_chat", provider.name)
            return answer

        raise AllProvidersFailedError(
            "Every configured model failed on a direct call.", {"errors": errors}
        )

    def close(self) -> None:
        for provider in self._providers:
            closer = getattr(provider, "close", None)
            if callable(closer):
                closer()
