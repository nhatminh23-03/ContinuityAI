"""Fetch real public GitHub activity and normalise it into the internal artifact shape.

    python -m scripts.fetch_public_github                          # defaults below
    python -m scripts.fetch_public_github --repo owner/name --limit 120

Writes `data/public/github_<owner>_<repo>.json` and `data/public/manifest.json`, both committed.
Run offline afterwards: `scripts/seed_demo.py` reads the committed file and never calls GitHub, so
seeding cannot fail on a rate limit or an outage (ARCHITECTURE.md section 85).

Satisfies the second half of the PRD section 14.1 data strategy — "real public GitHub evidence"
alongside synthetic private enterprise records — and closes RECOMMENDATIONS.md R-07.

Two things this script deliberately does
---------------------------------------
**It pseudonymises contributors.** Real pull requests are ingested with their real titles, bodies,
file paths, dates, and URLs, but the *author identity* is mapped onto a synthetic NovaPay engineer.
PRD section 14.1 calls for normalising and anonymising public evidence, and the reason is
substantive rather than procedural: this product infers capability readiness about named people, and
doing that to real engineers who never consented — from a repository they do not work on, mapped
onto an invented organisation — would be exactly the behaviour the responsible-AI boundary exists to
prevent. The real login is never written to disk.

The artifact stays fully traceable: `source_url` points at the real pull request, so any conclusion
can be checked against its source. What is synthetic is the attribution, and that is stated in the
manifest rather than left for someone to discover.

**It drops bots.** `stripe-openapi[bot]` and friends author a large share of real pull requests.
Treating automated codegen as demonstrated human capability would be a straightforward measurement
error.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = REPO_ROOT / "data" / "public"

DEFAULT_REPO = "stripe/stripe-python"
DEFAULT_LIMIT = 120
DEFAULT_REVIEW_SAMPLE = 40

# The system real public activity is attributed to. A payments SDK's concerns — retries,
# idempotency, error handling — sit naturally beside the Payment Gateway taxonomy.
DEFAULT_SYSTEM = "system_payment_gateway"

# Pseudonym pool. Deliberately excludes Alex, Maria, Jordan and Omar: those four carry the seeded
# hero coverage that the frozen fixtures and the hidden ground truth both depend on, and mixing
# unlabelled real activity into a labelled pair would corrupt the evaluation rather than add to it.
PSEUDONYM_POOL = [
    "eng_priya_nair",
    "eng_tom_becker",
    "eng_lena_novak",
]


def _gh(path: str) -> list[dict]:
    if shutil.which("gh") is None:
        raise SystemExit("The GitHub CLI (gh) is required. See https://cli.github.com/")
    result = subprocess.run(
        ["gh", "api", "-H", "Accept: application/vnd.github+json", path],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise SystemExit(f"gh api failed for {path}:\n{result.stderr.strip()[:400]}")
    payload = json.loads(result.stdout or "[]")
    return payload if isinstance(payload, list) else [payload]


def _is_bot(login: str | None) -> bool:
    return not login or login.endswith("[bot]") or login in {"web-flow", "github-actions"}


def _pseudonym(login: str) -> str:
    """Stable mapping from a real login to a synthetic engineer.

    Deterministic so a given contributor always maps to the same pseudonym across refetches, which
    keeps aggregated coverage coherent instead of scattering one person's work across three.
    """
    digest = hashlib.sha256(login.encode()).digest()
    return PSEUDONYM_POOL[digest[0] % len(PSEUDONYM_POOL)]


_MENTION = re.compile(r"@[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})")
_PROFILE_URL = re.compile(r"https?://(?:www\.)?github\.com/([A-Za-z0-9-]+)(?![/\w])")


def _clean(text: str | None, limit: int = 1200) -> str:
    """Collapse whitespace, truncate, and scrub identities out of the prose.

    Pseudonymising the *participant* is not sufficient on its own: pull request bodies routinely
    name other contributors, through `@mentions` and profile links. Leaving those in would put real
    logins into an evidence corpus that then gets summarised on screen — the same problem the
    pseudonymisation exists to avoid, arriving by a different route.

    Bare logins written as ordinary prose ("as kyleconroy noted") cannot be caught by pattern alone.
    That residual is recorded in the manifest rather than glossed over.
    """
    if not text:
        return ""
    collapsed = " ".join(text.split())
    collapsed = _MENTION.sub("@contributor", collapsed)
    collapsed = _PROFILE_URL.sub("https://github.com/", collapsed)
    return collapsed[:limit]


def fetch(repo: str, limit: int, review_sample: int, system_id: str) -> list[dict]:
    owner, _, name = repo.partition("/")
    if not owner or not name:
        raise SystemExit(f"--repo must be owner/name, got {repo!r}")

    print(f"fetching up to {limit} merged pull requests from {repo}")
    raw: list[dict] = []
    page, per_page = 1, min(100, limit)
    while len(raw) < limit:
        batch = _gh(
            f"repos/{repo}/pulls?state=closed&per_page={per_page}&page={page}&sort=updated"
        )
        if not batch:
            break
        raw.extend(batch)
        page += 1
        if page > 5:
            break

    merged = [pr for pr in raw if pr.get("merged_at") and not _is_bot((pr.get("user") or {}).get("login"))]
    merged = merged[:limit]
    print(f"  {len(raw)} closed, {len(merged)} merged and human-authored")

    artifacts: list[dict] = []
    identities: set[str] = set()

    for pull in merged:
        login = pull["user"]["login"]
        identities.add(login)
        engineer_id = _pseudonym(login)
        merged_at = datetime.fromisoformat(pull["merged_at"].replace("Z", "+00:00")).date()

        artifacts.append(
            {
                "kind": "pull_requests",
                "reference": f"GH-{owner}-{name}-{pull['number']}",
                "title": _clean(pull.get("title"), 200),
                "body": _clean(pull.get("body")),
                "date": merged_at.isoformat(),
                "system_id": system_id,
                "participants": [
                    {"engineer_id": engineer_id, "participant_role": "AUTHOR"}
                ],
                "file_paths": [],
                "source_url": pull.get("html_url"),
            }
        )

    print(f"  fetching reviews for the {min(review_sample, len(merged))} most recent")
    for pull in merged[:review_sample]:
        reviews = _gh(f"repos/{repo}/pulls/{pull['number']}/reviews?per_page=20")
        reviewers = {
            (r.get("user") or {}).get("login")
            for r in reviews
            if not _is_bot((r.get("user") or {}).get("login"))
        }
        reviewers.discard(pull["user"]["login"])
        if not reviewers:
            continue
        identities.update(reviewers)
        artifacts.append(
            {
                "kind": "code_reviews",
                "reference": f"GH-{owner}-{name}-{pull['number']}-review",
                "title": _clean(f"Review: {pull.get('title')}", 200),
                "body": _clean(
                    f"Reviewed the change described as: {pull.get('title')}. {pull.get('body') or ''}"
                ),
                "date": datetime.fromisoformat(
                    pull["merged_at"].replace("Z", "+00:00")
                ).date().isoformat(),
                "system_id": system_id,
                "participants": [
                    {"engineer_id": _pseudonym(login), "participant_role": "REVIEWER"}
                    for login in sorted(reviewers)
                ],
                "file_paths": [],
                "source_url": pull.get("html_url"),
            }
        )

    artifacts.sort(key=lambda a: (a["date"], a["reference"]))

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    target = OUT_DIR / f"github_{owner}_{name}.json"
    target.write_text(json.dumps(artifacts, indent=2) + "\n")

    manifest = {
        "source_repository": repo,
        "source_url": f"https://github.com/{repo}",
        "fetched_artifacts": len(artifacts),
        "pull_requests": sum(1 for a in artifacts if a["kind"] == "pull_requests"),
        "code_reviews": sum(1 for a in artifacts if a["kind"] == "code_reviews"),
        "attributed_to_system": system_id,
        "distinct_public_contributors": len(identities),
        "pseudonym_pool": PSEUDONYM_POOL,
        "anonymisation": (
            "Pull request titles, bodies, dates and URLs are real and unmodified. Contributor "
            "identities are NOT: each real login is deterministically mapped onto a synthetic "
            "NovaPay engineer and the real login is never written to disk. ContinuityAI infers "
            "capability readiness about named people, and doing that to real engineers who never "
            "consented would breach the responsible-AI boundary in PRD section 22. Artifacts stay "
            "traceable through source_url; the attribution is what is synthetic."
        ),
        "bots_excluded": True,
        "text_scrubbing": (
            "@mentions are replaced with @contributor and GitHub profile links are stripped, "
            "because pull request bodies routinely name other contributors. Bare logins written "
            "as ordinary prose cannot be caught by pattern and may remain in body text."
        ),
        "finding": (
            "Most artifacts in a public SDK repository evidence no operational capability. The "
            "vocabulary is library maintenance — support, error handling, tests, packaging — while "
            "the capabilities this product assesses (service recovery, provider failover, "
            "certificate rotation) are demonstrated in private operational records: incidents, "
            "runbooks, on-call history. That is a finding about where capability evidence lives, "
            "not a defect in extraction, and it is what the hybrid data strategy in PRD section "
            "14.1 already assumes."
        ),
        "note": (
            "Committed so seeding is offline and reproducible. Refresh with "
            "python -m scripts.fetch_public_github"
        ),
    }
    (OUT_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")

    print(f"  wrote {len(artifacts)} artifacts to {target.relative_to(REPO_ROOT)}")
    print(f"  {len(identities)} distinct public contributors mapped onto "
          f"{len(PSEUDONYM_POOL)} synthetic engineers")
    return artifacts


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=DEFAULT_REPO)
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT)
    parser.add_argument("--reviews", type=int, default=DEFAULT_REVIEW_SAMPLE)
    parser.add_argument("--system", default=DEFAULT_SYSTEM)
    args = parser.parse_args()

    if str(REPO_ROOT / "backend") not in sys.path:
        sys.path.insert(0, str(REPO_ROOT / "backend"))

    fetch(args.repo, args.limit, args.reviews, args.system)


if __name__ == "__main__":
    main()
