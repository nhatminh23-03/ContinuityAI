"""Real public GitHub evidence: privacy scrubbing and ingestion. RECOMMENDATIONS.md R-07.

The PRD data strategy (section 14.1) calls for real public GitHub activity alongside synthetic
private enterprise records. Real activity brings real, messy text for extraction to work on — and it
brings a privacy obligation, because this product infers capability readiness about named people and
the public contributors never consented to being assessed.

These tests defend the boundary: real artifacts, synthetic attribution, no real identity on disk.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

PUBLIC_DIR = Path(__file__).resolve().parents[2] / "data" / "public"
CORPUS = PUBLIC_DIR / "github_stripe_stripe-python.json"

# The four engineers carrying seeded hero coverage. Real activity must never be attributed to them:
# mixing unlabelled real work into a pair the hidden ground truth has a label for would corrupt the
# evaluation rather than add to it.
HERO_ENGINEERS = {"eng_alex_chen", "eng_maria_gomez", "eng_jordan_lee", "eng_omar_haddad"}


@pytest.fixture(scope="module")
def corpus() -> list[dict]:
    if not CORPUS.exists():
        pytest.skip("public corpus not fetched; run python -m scripts.fetch_public_github")
    return json.loads(CORPUS.read_text())


@pytest.fixture(scope="module")
def manifest() -> dict:
    return json.loads((PUBLIC_DIR / "manifest.json").read_text())


def test_the_corpus_is_committed_so_seeding_stays_offline(corpus) -> None:
    """A demo that can fail on a rate limit can fail for reasons unrelated to the product."""
    assert len(corpus) > 50


def test_every_artifact_is_attributed_to_a_synthetic_engineer(corpus) -> None:
    attributed = {p["engineer_id"] for a in corpus for p in a["participants"]}
    assert attributed, "artifacts must have participants or they evidence nothing"
    assert all(e.startswith("eng_") for e in attributed)
    assert not attributed & HERO_ENGINEERS, (
        "real activity must not land on the engineers whose coverage the ground truth labels"
    )


def test_no_real_github_login_is_stored(corpus) -> None:
    """The real login is never written to disk — not in a field, not in prose."""
    blob = json.dumps(corpus)
    assert '"login"' not in blob
    assert '"user"' not in blob

    prose = " ".join(f"{a['title']} {a['body']}" for a in corpus)
    leaks = [m for m in re.findall(r"@[A-Za-z0-9][A-Za-z0-9-]*", prose) if m != "@contributor"]
    assert not leaks, f"unscrubbed mentions: {leaks[:5]}"

    profiles = re.findall(r"github\.com/[A-Za-z0-9-]+(?![/\w])", prose)
    assert not profiles, f"unscrubbed profile links: {profiles[:5]}"


def test_artifacts_remain_traceable_to_their_real_source(corpus) -> None:
    """Pseudonymising the attribution must not cost provenance: any conclusion drawn from a real
    pull request has to be checkable against that pull request."""
    assert all(a.get("source_url", "").startswith("https://github.com/") for a in corpus)
    assert all(a["reference"].startswith("GH-") for a in corpus)


def test_bots_are_excluded(manifest) -> None:
    """Automated codegen authors a large share of real pull requests. Counting it as demonstrated
    human capability would be a plain measurement error."""
    assert manifest["bots_excluded"] is True


def test_the_manifest_states_what_is_real_and_what_is_synthetic(manifest) -> None:
    assert manifest["source_repository"]
    assert "synthetic" in manifest["anonymisation"].lower()
    assert manifest["distinct_public_contributors"] > len(manifest["pseudonym_pool"])
    assert "text_scrubbing" in manifest


def test_public_artifacts_are_ingested_alongside_synthetic_ones(session) -> None:
    from app.models import Artifact

    public = [
        a for a in session.query(Artifact).all() if a.provenance_source == "public_github_export"
    ]
    assert public, "the seed should ingest the committed public corpus"
    assert all(a.source_url for a in public)


def test_most_public_artifacts_correctly_yield_no_capability_evidence(session) -> None:
    """The substantive finding, asserted so it does not quietly change.

    A public SDK repository is mostly library maintenance — support, error handling, tests,
    packaging. The capabilities this product assesses are demonstrated in private operational
    records: incidents, runbooks, on-call history. A high match rate here would mean the matcher had
    become credulous, not that the data had improved.

    It is also a concrete measurement of the ceiling described in RECOMMENDATIONS.md R-01: the
    shipped extractor resolves capabilities by matching names in text, so it finds only what the
    text names.
    """
    from app.models import Artifact, Evidence

    public_ids = {
        a.artifact_id
        for a in session.query(Artifact).all()
        if a.provenance_source == "public_github_export"
    }
    derived = [e for e in session.query(Evidence).all() if e.artifact_id in public_ids]

    assert len(derived) < len(public_ids) / 4, (
        "a public repository yielding capability evidence at scale would suggest the matcher is "
        "too eager rather than that the corpus is richer"
    )
    for record in derived:
        assert record.engineer_id not in HERO_ENGINEERS
