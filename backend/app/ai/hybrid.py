"""Rule-based extraction, model-written prose. The configuration the measurement argues for.

This is the provider to run. It is not a compromise between the other two — it is the arrangement the
evaluation selected, with each half done by whichever method measurably does it better.

**Extraction stays rule-based because it wins.** The whole corpus was extracted by
`anthropic/claude-sonnet-5` and scored against hidden ground truth beside the rules: readiness 54/56
against 56/56, counterfactual simulation 15/25 against 25/25. The model made two errors, both on the
hero capability and both too generous, which flipped Incident Recovery from `DEGRADED` to `COVERED` and
made the product's opening claim false. Full write-up in `data/extraction/comparison_report.md`.

**Everything a model is better at, a model does.** The three manager-facing narratives, the taxonomy
concepts the organisation has no name for (FR-005), and suggested system criticality (FR-010) all go to
the model chain, so watsonx is tried first and OpenRouter picks up when its quota is spent.

Why this split rather than `AI_PROVIDER=chain`: `chain` extracts with a model, which means it ships the
configuration we measured as worse. Why not `deterministic`: nothing there calls a model at all, so the
product's interpretation work is done by string matching and template text. This is the honest middle,
and "honest" here means each half is assigned by evidence rather than by preference.

What a caller gets is unchanged either way. No endpoint, DTO, enum, or number differs between providers —
readiness, exposure, continuity risk and the simulation are computed by the same rules under all of them,
which is the property the provider interface exists to guarantee.
"""

from __future__ import annotations

import logging

from app.ai.deterministic import DeterministicProvider
from app.ai.provider import AIProvider, ExtractionContext
from app.ai.schemas import (
    ArtifactExtraction,
    ArtifactInput,
    CandidateNarrative,
    CandidateNarrativeContext,
    PlanContext,
    PlanDraft,
    SimulationSummaryContext,
)

logger = logging.getLogger(__name__)


class HybridProvider:
    name = "hybrid"

    def __init__(self, narrator: AIProvider) -> None:
        self._rules = DeterministicProvider()
        self._narrator = narrator

    @property
    def extraction_provider_name(self) -> str:
        """`deterministic`, and saying so is the point.

        The graph is rule-derived under this provider. Reporting `hybrid` in the seed summary would let
        a reader conclude a model built the knowledge graph, which is exactly the misdescription the
        provenance mechanism exists to prevent — and here it would be flattering rather than modest,
        which makes it worse.
        """
        return self._rules.name

    @property
    def model_id(self) -> str:
        return getattr(self._narrator, "model_id", "n/a")

    @property
    def provenance(self):
        """The narrator's provenance log, so the seed and any diagnostics still see which model answered."""
        return getattr(self._narrator, "provenance", None)

    # -- extraction: rules, because they measured better ---------------------------------

    def extract_artifact_semantics(
        self, artifact: ArtifactInput, context: ExtractionContext
    ) -> ArtifactExtraction:
        return self._rules.extract_artifact_semantics(artifact, context)

    # -- narratives: the model chain -----------------------------------------------------

    def summarize_simulation(self, context: SimulationSummaryContext) -> str | None:
        return self._narrator.summarize_simulation(context)

    def explain_candidate(self, context: CandidateNarrativeContext) -> CandidateNarrative:
        return self._narrator.explain_candidate(context)

    def generate_mitigation_plan(self, context: PlanContext) -> PlanDraft:
        return self._narrator.generate_mitigation_plan(context)

    # -- the optional enrichments (FR-005, FR-010) ---------------------------------------

    def _chat(self, system: str, user: str, max_tokens: int, timeout: float | None = None) -> str:
        """Passed through so `app/ai/criticality.py` can reach a model.

        Present as an optional attribute rather than a protocol method: only providers with a model can
        answer, and forcing the deterministic provider to implement something it has no opinion about
        would be worse than letting callers test for the capability.
        """
        call = getattr(self._narrator, "_chat", None)
        if call is None:
            raise AttributeError(f"{self._narrator.name} has no model transport")
        return call(system, user, max_tokens, timeout) if timeout is not None else call(
            system, user, max_tokens
        )

    def close(self) -> None:
        closer = getattr(self._narrator, "close", None)
        if callable(closer):
            closer()
