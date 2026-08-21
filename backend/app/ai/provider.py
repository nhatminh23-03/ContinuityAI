"""AI provider abstraction. docs/ARCHITECTURE.md sections 19 and 23.

Model access lives behind this interface and nowhere else. No route, service, or engine calls a
model directly, which is what lets the runtime provider change without touching the continuity
engine — and what lets the deterministic provider stand in when no model is configured.

Four operations, matching section 19:

    extract_artifact_semantics   unstructured artifact -> structured capability claims
    summarize_simulation         deterministic simulation facts -> one grounded sentence
    explain_candidate            structured overlap facts -> strengths and gaps as prose
    generate_mitigation_plan     capability gap + evidence -> draft transfer tasks

Note what is absent. There is no `assess_readiness`, no `score_risk`, and no `pick_candidate`.
Those would hand a model a decision the rules own, and no amount of prompt care would make the
result explainable. The interface shape is itself the guardrail.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

from app.ai.schemas import (
    ArtifactExtraction,
    ArtifactInput,
    CandidateNarrative,
    CandidateNarrativeContext,
    PlanContext,
    PlanDraft,
    SimulationSummaryContext,
    TaxonomyCapability,
)
from app.core.config import settings


@dataclass
class ExtractionContext:
    """The closed world a provider may attribute evidence within.

    Passing the taxonomy in rather than letting the provider discover it is what makes
    "invented capability" a validation failure instead of a plausible-looking claim.
    """

    capabilities: list[TaxonomyCapability] = field(default_factory=list)
    engineer_names: dict[str, str] = field(default_factory=dict)

    def by_system(self, system_id: str | None) -> list[TaxonomyCapability]:
        if system_id is None:
            return list(self.capabilities)
        return [c for c in self.capabilities if c.system_id == system_id]

    def taxonomy_index(self) -> dict[str, TaxonomyCapability]:
        return {c.capability_id: c for c in self.capabilities}


@runtime_checkable
class AIProvider(Protocol):
    name: str

    def extract_artifact_semantics(
        self, artifact: ArtifactInput, context: ExtractionContext
    ) -> ArtifactExtraction: ...

    def summarize_simulation(self, context: SimulationSummaryContext) -> str | None: ...

    def explain_candidate(self, context: CandidateNarrativeContext) -> CandidateNarrative: ...

    def generate_mitigation_plan(self, context: PlanContext) -> PlanDraft: ...


def get_provider(name: str | None = None) -> AIProvider:
    """Resolve the configured provider.

    `deterministic` is the default and the only implementation shipped. It is a real
    implementation of the interface, not a mock: it performs the same closed-world capability
    resolution and role interpretation a model would be prompted for, using explicit rules.
    Everything downstream — validation, aggregation, readiness, risk — is identical either way,
    so swapping in a model changes extraction quality without touching a single conclusion path.

    See RECOMMENDATIONS.md R-01 for what a language model adds here and what it costs.
    """
    from app.ai.deterministic import DeterministicProvider

    requested = (name or settings.ai_provider or "deterministic").lower()
    if requested in {"deterministic", "none", "", "stub"}:
        return DeterministicProvider()
    if requested in {"watsonx", "ibm", "granite"}:
        from app.ai.watsonx import WatsonxProvider

        return WatsonxProvider()
    if requested in {"openrouter", "openrouter.ai"}:
        # The mirror image of watsonx: rule-based extraction, model-written narratives.
        from app.ai.openrouter import OpenRouterProvider

        return OpenRouterProvider()
    if requested == "cached":
        # Extraction replayed from a committed cache: model-derived evidence, offline seeding.
        from app.ai.cache import CachedProvider

        return CachedProvider()
    raise ValueError(
        f"Unknown AI_PROVIDER '{requested}'. Implement the AIProvider protocol in app/ai/ and "
        f"register it here. Do not call a model from outside this package."
    )
