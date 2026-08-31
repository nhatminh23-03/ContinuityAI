"""Replay model extraction from a committed cache.

docs/ARCHITECTURE.md sections 85-86: preprocess artifact ingestion and semantic extraction, keep
interactive operations live. A model call per artifact is slow, costs money, and is not perfectly
repeatable — none of which a demo or an evaluation should inherit.

So extraction runs once through `scripts/extract_with_provider.py`, the structured result is written
to `data/extraction/` and committed, and `AI_PROVIDER=cached` replays it. The graph is
model-derived; seeding is offline, free, and byte-identical on a clean clone with no credential.

A missing artifact raises rather than silently falling back to the rule-based provider. A graph half
derived by a model and half by string matching would be neither, and no number in it could be
explained by reference to a single method.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from app.ai.deterministic import DeterministicProvider
from app.ai.provider import ExtractionContext
from app.ai.schemas import (
    ArtifactExtraction,
    ArtifactInput,
    CandidateNarrative,
    CandidateNarrativeContext,
    PlanContext,
    PlanDraft,
    SimulationSummaryContext,
)
from app.core.config import settings
from app.core.errors import AIExtractionError

CACHE_DIR_NAME = "extraction"
DEFAULT_CACHE_FILE = "watsonx_cache.json"


def cache_path(filename: str = DEFAULT_CACHE_FILE) -> Path:
    return settings.data_path / CACHE_DIR_NAME / filename


def artifact_fingerprint(artifact: ArtifactInput) -> str:
    """Detect a changed artifact so stale extraction is never replayed as if it were current."""
    material = "|".join(
        [
            artifact.source_type.value,
            artifact.source_reference,
            artifact.title or "",
            artifact.body,
            artifact.artifact_date.isoformat(),
            ",".join(f"{p.engineer_id}:{p.participant_role}" for p in artifact.participants),
            artifact.system_hint or "",
        ]
    )
    return hashlib.sha256(material.encode()).hexdigest()[:16]


class ExtractionCache:
    """`artifact_id -> {fingerprint, extraction}`, persisted as one JSON file."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or cache_path()
        self.provider_name = ""
        self.model_id = ""
        self.entries: dict[str, dict] = {}

    @classmethod
    def load(cls, path: Path | None = None) -> ExtractionCache:
        cache = cls(path)
        if not cache.path.exists():
            return cache
        payload = json.loads(cache.path.read_text())
        cache.provider_name = payload.get("provider", "")
        cache.model_id = payload.get("model_id", "")
        cache.entries = payload.get("entries", {})
        return cache

    def save(self, provider_name: str, model_id: str) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(
                {
                    "provider": provider_name,
                    "model_id": model_id,
                    "entry_count": len(self.entries),
                    "note": (
                        "Structured extraction output, committed so seeding is offline and "
                        "reproducible without a credential. Regenerate with "
                        "python -m scripts.extract_with_provider. Keyed by artifact fingerprint, so "
                        "a changed artifact invalidates its entry rather than replaying stale "
                        "extraction."
                    ),
                    "entries": self.entries,
                },
                indent=2,
                sort_keys=True,
            )
            + "\n"
        )

    def put(self, artifact: ArtifactInput, extraction: ArtifactExtraction) -> None:
        self.entries[artifact.artifact_id] = {
            "fingerprint": artifact_fingerprint(artifact),
            "extraction": extraction.model_dump(mode="json"),
        }

    def get(self, artifact: ArtifactInput) -> ArtifactExtraction | None:
        entry = self.entries.get(artifact.artifact_id)
        if entry is None or entry.get("fingerprint") != artifact_fingerprint(artifact):
            return None
        return ArtifactExtraction.model_validate(entry["extraction"])

    def __len__(self) -> int:
        return len(self.entries)


class CachedProvider:
    name = "cached"

    def __init__(self, path: Path | None = None, narrator: object | None = None) -> None:
        self.cache = ExtractionCache.load(path or cache_path(settings.extraction_cache_file))
        if not self.cache.entries:
            raise ValueError(
                f"AI_PROVIDER=cached needs an extraction cache at {self.cache.path}. Build one with: "
                f"python -m scripts.extract_with_provider --provider chain — then set "
                f"EXTRACTION_CACHE_FILE to the file it wrote."
            )
        self.model_id = self.cache.model_id
        # What actually built this graph, which is the cache's provider rather than `cached`. Replaying
        # a model's output is still that model's output, and the seed summary should say so.
        self.extraction_provider_name = f"cached:{self.cache.provider_name or 'unknown'}"
        self._fallback = DeterministicProvider()
        self._narrator = narrator or self._fallback

    def extract_artifact_semantics(
        self, artifact: ArtifactInput, context: ExtractionContext
    ) -> ArtifactExtraction:
        extraction = self.cache.get(artifact)
        if extraction is None:
            raise AIExtractionError(
                f"No cached extraction for {artifact.source_reference}. The corpus has changed "
                f"since the cache was built; re-run scripts.extract_with_provider.",
                {"artifact_id": artifact.artifact_id, "cache": str(self.cache.path)},
            )
        return extraction

    # Narratives are not cached, and should not be: they are cheap, live, and grounded in facts the
    # rules already decided, so a cache would only make them stale. But they should not silently be
    # *templates* either. `narrator` is whatever can actually write them — the model chain when
    # credentials exist, the deterministic templates when they do not — which is what makes
    # `AI_PROVIDER=cached` a fully model-backed configuration rather than half of one.
    #
    # This is the combination worth running day to day: extraction replayed from a committed cache, so
    # seeding is instant, offline and reproducible, with live model prose over the top.
    def summarize_simulation(self, context: SimulationSummaryContext) -> str | None:
        return self._narrator.summarize_simulation(context)

    def explain_candidate(self, context: CandidateNarrativeContext) -> CandidateNarrative:
        return self._narrator.explain_candidate(context)

    def generate_mitigation_plan(self, context: PlanContext) -> PlanDraft:
        return self._narrator.generate_mitigation_plan(context)
