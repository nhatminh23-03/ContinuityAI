"""Run extraction over the whole corpus with a chosen provider, cache it, and compare providers.

    python -m scripts.extract_with_provider --provider watsonx
    python -m scripts.extract_with_provider --provider watsonx --limit 40 --compare

Writes `data/extraction/<provider>_cache.json`, which `AI_PROVIDER=cached` replays so seeding stays
offline and reproducible without a credential (ARCHITECTURE.md sections 85-86).

`--compare` also diffs the run against the deterministic provider, per artifact and per claim. That
comparison is worth more than the cache: it measures what a language model actually adds over string
matching on this corpus, in claims found, claims missed, and roles disagreed. The hidden-ground-truth
evaluation then says which of the two reconstructs the true readiness distribution better — run
`scripts.seed_demo` followed by `scripts.run_evaluation` under each provider.
"""

from __future__ import annotations

import argparse
import sys
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT / "backend") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "backend"))

from app.ai.cache import ExtractionCache, cache_path  # noqa: E402
from app.ai.deterministic import DeterministicProvider  # noqa: E402
from app.ai.provider import ExtractionContext, get_provider  # noqa: E402
from app.ai.schemas import ArtifactExtraction, ArtifactInput, TaxonomyCapability  # noqa: E402
from app.core.config import settings  # noqa: E402
from app.core.errors import AIExtractionError  # noqa: E402
from app.ingestion import load_public_github_corpus, load_synthetic_corpus  # noqa: E402

import json  # noqa: E402


def build_context() -> ExtractionContext:
    org = json.loads((settings.data_path / "org" / "novapay.json").read_text())
    capabilities: list[TaxonomyCapability] = []
    for platform in org["platforms"]:
        for system in platform["systems"]:
            for component in system["components"]:
                for capability in component["capabilities"]:
                    capabilities.append(
                        TaxonomyCapability(
                            capability_id=capability["capability_id"],
                            name=capability["name"],
                            aliases=capability.get("aliases", []),
                            system_id=system["system_id"],
                            component_id=component["component_id"],
                        )
                    )
    return ExtractionContext(
        capabilities=capabilities,
        engineer_names={e["engineer_id"]: e["name"] for e in org["engineers"]},
    )


def claim_set(extraction: ArtifactExtraction) -> set[tuple[str, str, str]]:
    return {(c.capability_id, c.engineer_id, c.evidence_role.value) for c in extraction.claims}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--provider", default="watsonx")
    parser.add_argument("--limit", type=int, default=0, help="0 means the whole corpus")
    parser.add_argument(
        "--workers",
        type=int,
        default=2,
        help="Keep at or below the service requests-per-second ceiling; the provider paces itself too",
    )
    parser.add_argument("--compare", action="store_true", help="diff against the deterministic provider")
    parser.add_argument("--refresh", action="store_true", help="re-extract artifacts already cached")
    parser.add_argument("--out", default="")
    args = parser.parse_args()

    all_artifacts: list[ArtifactInput] = [
        *load_synthetic_corpus(settings.data_path),
        *load_public_github_corpus(settings.data_path),
    ]
    if args.limit:
        all_artifacts = all_artifacts[: args.limit]

    context = build_context()
    provider = get_provider(args.provider)
    baseline = DeterministicProvider()

    target = cache_path(args.out) if args.out else cache_path(f"{provider.name}_cache.json")
    cache = ExtractionCache.load(target)
    cache.path = target

    # Resume by default. A 640-call run against a rate-limited, quota-limited service will not always
    # finish in one pass, and re-paying for work already done is the difference between a task that
    # can be completed incrementally and one that cannot be completed at all.
    results: dict[str, ArtifactExtraction] = {}
    artifacts: list[ArtifactInput] = []
    for artifact in all_artifacts:
        cached = None if args.refresh else cache.get(artifact)
        if cached is not None:
            results[artifact.artifact_id] = cached
        else:
            artifacts.append(artifact)

    print(f"provider   {provider.name} ({getattr(provider, 'model_id', 'n/a')})")
    print(f"corpus     {len(all_artifacts)} artifacts")
    print(f"cached     {len(results)} reused")
    print(f"to do      {len(artifacts)}")
    print(f"workers    {args.workers} (paced to {settings.watsonx_requests_per_second}/s)\n")

    failures: list[str] = []
    started = time.time()

    def extract(artifact: ArtifactInput) -> tuple[str, ArtifactExtraction | None, str | None]:
        try:
            return artifact.artifact_id, provider.extract_artifact_semantics(artifact, context), None
        except AIExtractionError as exc:
            return artifact.artifact_id, None, str(exc)
        except Exception as exc:  # a single bad artifact must not abort a 640-call run
            return artifact.artifact_id, None, f"{type(exc).__name__}: {exc}"

    by_id = {a.artifact_id: a for a in all_artifacts}
    quota_exhausted = False
    if artifacts:
        with ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
            futures = [pool.submit(extract, artifact) for artifact in artifacts]
            for index, future in enumerate(as_completed(futures), start=1):
                artifact_id, extraction, error = future.result()
                if extraction is not None:
                    results[artifact_id] = extraction
                else:
                    failures.append(f"{artifact_id}: {error}")
                    if error and "quota" in error.lower():
                        quota_exhausted = True
                if index % 25 == 0 or index == len(futures):
                    elapsed = time.time() - started
                    print(f"  {index}/{len(futures)}  {elapsed:5.1f}s  {len(failures)} failed")

    total_claims = sum(len(e.claims) for e in results.values())
    with_claims = sum(1 for e in results.values() if e.claims)
    print(
        f"\n{len(results)}/{len(all_artifacts)} artifacts extracted, {total_claims} claims from "
        f"{with_claims} of them, in {time.time() - started:.1f}s"
    )
    if failures:
        print(f"{len(failures)} failures:")
        for failure in failures[:5]:
            print(f"  {failure}")

    # Save even on partial completion: the whole point of resuming is that a partial run is progress.
    for artifact_id, extraction in results.items():
        cache.put(by_id[artifact_id], extraction)
    cache.save(provider.name, getattr(provider, "model_id", ""))
    coverage = len(cache) / len(all_artifacts) * 100
    print(f"cache: {cache.path.relative_to(REPO_ROOT)} — {len(cache)}/{len(all_artifacts)} ({coverage:.0f}%)")

    if quota_exhausted:
        print(
            "\nThe token quota is exhausted, so this run stopped early. Nothing is lost: re-run the\n"
            "same command once the quota resets and it will resume from the cache."
        )
    if len(cache) < len(all_artifacts):
        print(
            f"\nAI_PROVIDER=cached needs full coverage and the cache is at {coverage:.0f}%. Until it\n"
            f"is complete, keep AI_PROVIDER=deterministic — a graph half derived by a model and half\n"
            f"by string matching would be neither."
        )

    if args.compare:
        print("\ncomparison against the deterministic provider\n" + "=" * 68)
        agree = only_model = only_rules = role_conflict = 0
        identical_artifacts = 0
        role_shifts: Counter[str] = Counter()

        for artifact_id, extraction in sorted(results.items()):
            artifact = by_id[artifact_id]
            rules = claim_set(baseline.extract_artifact_semantics(artifact, context))
            model = claim_set(extraction)
            if rules == model:
                identical_artifacts += 1

            agree += len(rules & model)
            model_pairs = {(c, e) for c, e, _ in model}
            rules_pairs = {(c, e) for c, e, _ in rules}
            only_model += len(model_pairs - rules_pairs)
            only_rules += len(rules_pairs - model_pairs)

            for capability_id, engineer_id in model_pairs & rules_pairs:
                model_role = next(r for c, e, r in model if (c, e) == (capability_id, engineer_id))
                rules_role = next(r for c, e, r in rules if (c, e) == (capability_id, engineer_id))
                if model_role != rules_role:
                    role_conflict += 1
                    role_shifts[f"{rules_role} -> {model_role}"] += 1

        print(f"  artifacts with identical output   {identical_artifacts}/{len(results)}")
        print(f"  claims both agree on              {agree}")
        print(f"  found only by the model           {only_model}")
        print(f"  found only by the rules           {only_rules}")
        print(f"  same pair, different role         {role_conflict}")
        for shift, count in role_shifts.most_common(8):
            print(f"      {shift:<48} {count}")
        print(
            "\n  Neither column is automatically right. Run scripts.seed_demo and "
            "scripts.run_evaluation\n  under each provider: the hidden ground truth decides which "
            "reconstruction is better."
        )

        report = _comparison_report(
            provider_name=provider.name,
            model_id=getattr(provider, "model_id", ""),
            covered=len(results),
            corpus=len(all_artifacts),
            identical=identical_artifacts,
            agree=agree,
            only_model=only_model,
            only_rules=only_rules,
            role_conflict=role_conflict,
            role_shifts=role_shifts,
        )
        report_path = cache.path.parent / "comparison_report.md"
        report_path.write_text(report)
        print(f"\n  report: {report_path.relative_to(REPO_ROOT)}")

    return 1 if failures else 0


def _comparison_report(
    *,
    provider_name: str,
    model_id: str,
    covered: int,
    corpus: int,
    identical: int,
    agree: int,
    only_model: int,
    only_rules: int,
    role_conflict: int,
    role_shifts: Counter[str],
) -> str:
    shift_rows = "\n".join(f"| `{shift}` | {count} |" for shift, count in role_shifts.most_common())
    return f"""# Extraction comparison — {provider_name} vs rule-based

Generated by `scripts/extract_with_provider.py --compare`. Measures what a language model adds over
string matching on this corpus, as a step in the evaluation rather than as a claim on its own.

**Model:** `{model_id}`
**Coverage:** {covered} of {corpus} artifacts extracted by the model

| Measure | Count |
|---|---|
| Artifacts where both produced identical output | {identical} / {covered} |
| Claims both providers agree on | {agree} |
| Claims found only by the model | {only_model} |
| Claims found only by the rules | {only_rules} |
| Same `(capability, engineer)` pair, different evidence role | {role_conflict} |

## Role disagreements

| Rules → model | Count |
|---|---|
{shift_rows or "| none | 0 |"}

## Reading this

The two providers agree on the large majority of artifacts, which is expected: most of the corpus
either clearly names a capability or clearly names none, and both methods handle those the same way.

The disagreements are where the interesting information is. `CONTRIBUTION → INDEPENDENT_EXECUTION`
means the model read the narrative and concluded the person acted alone where the rule saw only that
they authored something. That is exactly the judgement a rule cannot make, and it is also exactly the
judgement that most needs checking — promoting a contribution to an independent execution is what
moves an engineer toward `PRACTICED`, and therefore what closes or opens a coverage gap.

**Neither column is automatically correct.** The hidden ground truth decides. Seed and evaluate under
each provider and compare the reconstruction scores:

```bash
AI_PROVIDER=deterministic python -m scripts.seed_demo && python -m scripts.run_evaluation
AI_PROVIDER=cached        python -m scripts.seed_demo && python -m scripts.run_evaluation
```

Until the cache reaches full coverage, `AI_PROVIDER=cached` will refuse to run: a graph half derived
by a model and half by string matching would be neither, and no number in it could be explained by
reference to a single method.
"""


if __name__ == "__main__":
    raise SystemExit(main())
