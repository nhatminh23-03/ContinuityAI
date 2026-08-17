"""Generate the synthetic NovaPay artifact corpus from the hidden ground truth.

    python backend/scripts/generate_synthetic_data.py

Reads:
    data/org/novapay.json              organisation structure
    data/ground_truth/novapay_truth.json   HIDDEN readiness labels

Writes:
    data/synthetic/{incidents,pull_requests,code_reviews,issues,tickets,documents,codeowners}.json
    data/synthetic/manifest.json

This script is one of only two places allowed to read the ground truth
(docs/ARCHITECTURE.md section 40). The application never runs it and never reads its input;
it consumes the *output* in `data/synthetic/` and must re-derive readiness from scratch.

What the generator emits per true readiness label
-------------------------------------------------
Each label maps to an evidence pattern that the readiness rules in
`app/continuity/readiness.py` should independently classify back to that label:

    VALIDATED   two independent incident resolutions + an authored runbook
    PRACTICED   one independent incident resolution + an authored change
    ASSISTED    one assisted incident response + an authored change
    EXPOSED     a review and a discussion comment, no execution
    NONE        nothing

Artifacts carry no capability identifier. They carry a title, a body, a system, file paths,
and participants with the role the *source system* recorded (resolver, assisting responder,
author, reviewer, commenter). Turning that into `(capability, evidence_role, strength)` is the
extraction step's job, in `app/ai/`.

Determinism
-----------
Fixed seed, sorted iteration, and no wall-clock reads. Running this twice produces identical
files, which is what makes the committed corpus and PRD AC-15 compatible.
"""

from __future__ import annotations

import json
import random
import sys
from datetime import date, timedelta
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
ORG_FILE = REPO_ROOT / "data" / "org" / "novapay.json"
TRUTH_FILE = REPO_ROOT / "data" / "ground_truth" / "novapay_truth.json"
OUT_DIR = REPO_ROOT / "data" / "synthetic"

RANDOM_SEED = 20260815
REFERENCE_DATE = date(2026, 8, 15)

# Age buckets, in days before the reference date. These sit comfortably inside the freshness
# thresholds in docs/DOMAIN_MODEL.md section 18 (FRESH < 18 months, AGING 18-36, STALE > 36)
# so a boundary shift in the rules does not silently reclassify the whole corpus.
FRESH_WINDOW = (30, 400)
AGING_WINDOW = (620, 900)
STALE_WINDOW = (1180, 1500)

# The hero capability is authored rather than generated. The demo, the frozen fixtures, and the
# mitigation plan all reference these exact identifiers (evidence_inc_184, evidence_inc_230,
# evidence_pr_402, evidence_pr_391), so they cannot be allocated by a counter.
HERO_CAPABILITY = "cap_incident_recovery"

PINNED_HERO_ARTIFACTS: list[dict] = [
    {
        "kind": "incidents",
        "reference": "INC-184",
        "title": "P1 Payment Gateway Provider Failure",
        "body": (
            "Card transactions began failing at 19:04. Alex Chen was paged, traced the fault to a "
            "stalled connection pool in the gateway integration layer, restarted the affected "
            "workers, and restored transaction routing without escalation. Root cause recorded as "
            "a connection leak under sustained retry pressure."
        ),
        "date": "2026-05-14",
        "system_id": "system_payment_gateway",
        "participants": [{"engineer_id": "eng_alex_chen", "participant_role": "RESOLVER"}],
        "file_paths": [],
    },
    {
        "kind": "incidents",
        "reference": "INC-221",
        "title": "P1 Payment Gateway transaction routing stall",
        "body": (
            "A partial outage left roughly 12 percent of authorisations unrouted. Alex Chen "
            "diagnosed a misapplied routing weight, corrected it, and confirmed transaction "
            "routing had recovered. Handled single-handedly during the out-of-hours window."
        ),
        "date": "2026-03-02",
        "system_id": "system_payment_gateway",
        "participants": [{"engineer_id": "eng_alex_chen", "participant_role": "RESOLVER"}],
        "file_paths": [],
    },
    {
        "kind": "documents",
        "reference": "DOC-17",
        "title": "Payment Gateway incident recovery runbook",
        "body": (
            "Runbook authored by Alex Chen covering gateway recovery: how to confirm the blast "
            "radius, how to drain and restart the integration workers, and how to verify that "
            "transaction routing has been restored. Rollback guidance is still outstanding."
        ),
        "date": "2026-06-01",
        "system_id": "system_payment_gateway",
        "participants": [{"engineer_id": "eng_alex_chen", "participant_role": "AUTHOR"}],
        "file_paths": ["docs/runbooks/gateway-recovery.md"],
    },
    {
        "kind": "incidents",
        "reference": "INC-230",
        "title": "P2 Payment Gateway degraded authorisations",
        "body": (
            "Authorisation latency tripled for eleven minutes. Maria Gomez joined the response and "
            "assisted with gateway recovery, working through the checks with the lead responder "
            "rather than driving the restoration."
        ),
        "date": "2026-04-18",
        "system_id": "system_payment_gateway",
        "participants": [
            {"engineer_id": "eng_maria_gomez", "participant_role": "ASSISTING_RESPONDER"}
        ],
        "file_paths": [],
    },
    {
        "kind": "pull_requests",
        "reference": "PR-402",
        "title": "Harden gateway recovery health checks",
        "body": (
            "Maria Gomez authored this change to the gateway integration health probes so a "
            "half-open connection pool is detected before it affects incident recovery."
        ),
        "date": "2026-02-10",
        "system_id": "system_payment_gateway",
        "participants": [{"engineer_id": "eng_maria_gomez", "participant_role": "AUTHOR"}],
        "file_paths": ["services/gateway/integration/health.py"],
    },
    {
        "kind": "code_reviews",
        "reference": "PR-391",
        "title": "Review: adjust incident recovery timeouts",
        "body": (
            "Jordan Lee reviewed a change to the incident recovery timeout constants and approved "
            "it with a comment about metric naming. No execution involved."
        ),
        "date": "2024-06-12",
        "system_id": "system_payment_gateway",
        "participants": [{"engineer_id": "eng_jordan_lee", "participant_role": "REVIEWER"}],
        "file_paths": ["services/gateway/integration/timeouts.py"],
    },
    {
        "kind": "issues",
        "reference": "ISSUE-77",
        "title": "Discussion: incident recovery ordering",
        "body": (
            "Jordan Lee commented on the ordering of steps during gateway recovery and asked "
            "whether the drain step could be automated."
        ),
        "date": "2024-08-05",
        "system_id": "system_payment_gateway",
        "participants": [{"engineer_id": "eng_jordan_lee", "participant_role": "COMMENTER"}],
        "file_paths": [],
    },
]

# An attempt that did not hold. The extraction layer marks it conflicting, so it never supports a
# claim, it appears separately in the provenance drawer, and it drags Evidence Confidence down to
# LOW — demonstrating that "risk HIGH, confidence LOW" is a state the product can actually reach.
#
# Deliberately placed on Authorization rather than Payment Gateway: it must exercise the path
# without moving any number the frozen fixtures pin. Daniel keeps PRACTICED (his two qualifying
# records are untouched) and Policy Rollback stays DEGRADED at 54, so the Identity Platform still
# reports a highest system index of 68.
PINNED_CONFLICT_ARTIFACTS: list[dict] = [
    {
        "kind": "incidents",
        "reference": "INC-259",
        "title": "P2 Authorization — Policy Rollback attempt",
        "body": (
            "Daniel Kim attempted Policy Rollback after a bad policy release. The change was "
            "rolled back after the decision cache failed to invalidate, leaving stale entitlements "
            "in place, and the incident was handed off unresolved to the following shift."
        ),
        "date": "2026-01-22",
        "system_id": "system_authorization",
        "participants": [{"engineer_id": "eng_daniel_kim", "participant_role": "RESOLVER"}],
        "file_paths": [],
    },
]

# Evidence pattern per true readiness label. Each entry is (kind, participant_role).
RECIPES: dict[str, list[tuple[str, str]]] = {
    "VALIDATED": [
        ("incidents", "RESOLVER"),
        ("incidents", "RESOLVER"),
        ("documents", "AUTHOR"),
    ],
    "PRACTICED": [
        ("incidents", "RESOLVER"),
        ("pull_requests", "AUTHOR"),
    ],
    "ASSISTED": [
        ("incidents", "ASSISTING_RESPONDER"),
        ("tickets", "ASSIGNEE"),
    ],
    "EXPOSED": [
        ("code_reviews", "REVIEWER"),
        ("issues", "COMMENTER"),
    ],
    "NONE": [],
}

REFERENCE_PREFIX = {
    "incidents": "INC",
    "pull_requests": "PR",
    "code_reviews": "REV",
    "issues": "ISS",
    "tickets": "TCK",
    "documents": "DOC",
}

REFERENCE_START = {
    "incidents": 300,
    "pull_requests": 500,
    "code_reviews": 700,
    "issues": 800,
    "tickets": 900,
    "documents": 200,
}

# Artifacts that mention no capability. They exist so the extraction step has to decline
# rather than always finding something, and so the corpus is not suspiciously tidy.
NOISE_TITLES = [
    "Bump dependency versions",
    "Fix flaky test in CI",
    "Update service README",
    "Remove unused configuration flag",
    "Tidy log formatting",
    "Upgrade base container image",
    "Correct a typo in an error message",
    "Add a missing type annotation",
    "Reduce build time in the release pipeline",
    "Delete a deprecated feature flag",
]

TARGET_TOTAL_ARTIFACTS = 520


class ReferenceAllocator:
    def __init__(self, used: set[str]) -> None:
        self._counters = dict(REFERENCE_START)
        self._used = set(used)

    def next(self, kind: str) -> str:
        prefix = REFERENCE_PREFIX[kind]
        while True:
            value = self._counters[kind]
            self._counters[kind] = value + 1
            reference = f"{prefix}-{value}"
            if reference not in self._used:
                self._used.add(reference)
                return reference


def _load(path: Path) -> dict:
    return json.loads(path.read_text())


def _flatten_org(org: dict) -> tuple[dict[str, dict], dict[str, dict], dict[str, str]]:
    """Return (capabilities by id, systems by id, engineer name by id)."""
    capabilities: dict[str, dict] = {}
    systems: dict[str, dict] = {}
    for platform in org["platforms"]:
        for system in platform["systems"]:
            systems[system["system_id"]] = system
            for component in system["components"]:
                for capability in component["capabilities"]:
                    capabilities[capability["capability_id"]] = {
                        **capability,
                        "system_id": system["system_id"],
                        "system_name": system["name"],
                        "component_id": component["component_id"],
                        "component_name": component["name"],
                    }
    engineer_names = {e["engineer_id"]: e["name"] for e in org["engineers"]}
    return capabilities, systems, engineer_names


def _pick_date(rng: random.Random, profile: str, slot: int) -> date:
    window = {"aging": AGING_WINDOW, "stale": STALE_WINDOW}.get(profile, FRESH_WINDOW)
    span = window[1] - window[0]
    # Spread items in a recipe apart so repeated demonstration reads as repeated over time
    # rather than as one burst of activity.
    offset = window[0] + (slot * span // 4) + rng.randint(0, max(1, span // 5))
    return REFERENCE_DATE - timedelta(days=min(offset, window[1]))


def _compose(kind: str, role: str, capability: dict, engineer_name: str) -> tuple[str, str]:
    """Title and body. The capability name always appears verbatim in the text.

    That is what the extraction step matches on, scoped to the artifact's system. It is a
    deliberately simple signal — see RECOMMENDATIONS.md R-01 on what a language model would
    add here.
    """
    name = capability["name"]
    system = capability["system_name"]
    component = capability["component_name"]

    if kind == "incidents" and role == "RESOLVER":
        return (
            f"P1 {system} — {name} failure",
            f"{engineer_name} was paged, diagnosed the fault in {component}, and carried out "
            f"{name} to restore service. Completed without escalation or a second responder.",
        )
    if kind == "incidents" and role == "ASSISTING_RESPONDER":
        return (
            f"P2 {system} — degraded {name}",
            f"{engineer_name} joined the response and assisted with {name} in {component}, "
            f"following the lead responder's direction rather than driving the restoration.",
        )
    if kind == "documents":
        return (
            f"{system} {name} runbook",
            f"{engineer_name} authored this runbook describing {name} for {component}, "
            f"including the verification steps used after a change.",
        )
    if kind == "pull_requests":
        return (
            f"{name}: correctness fix in {component}",
            f"{engineer_name} authored this change affecting {name} in {component}.",
        )
    if kind == "code_reviews":
        return (
            f"Review: change to {name}",
            f"{engineer_name} reviewed a change to {name} in {component} and left comments. "
            f"No execution involved.",
        )
    if kind == "issues":
        return (
            f"Discussion: {name} behaviour",
            f"{engineer_name} commented on a discussion about {name} behaviour in {component}.",
        )
    if kind == "tickets":
        return (
            f"{name}: scheduled work in {component}",
            f"{engineer_name} was assigned work on {name} in {component} and completed it.",
        )
    raise ValueError(f"no template for {kind}/{role}")


def _file_paths(kind: str, capability: dict) -> list[str]:
    if kind not in {"pull_requests", "code_reviews"}:
        return []
    slug = capability["component_id"].replace("component_", "").replace("_", "-")
    return [f"services/{slug}/{capability['capability_id'].replace('cap_', '')}.py"]


def _match_capabilities(title: str, body: str, system_id: str, capabilities: dict) -> set[str]:
    """Same matching the extractor uses, run here as a self-check.

    An artifact that matches two capabilities would produce evidence the ground truth did not
    ask for, which would quietly move a readiness level. Better to fail generation than to ship
    a corpus that cannot reproduce its own labels.
    """
    text = f"{title}\n{body}".lower()
    matched = set()
    for capability_id, capability in capabilities.items():
        if capability["system_id"] != system_id:
            continue
        needles = [capability["name"].lower(), *(a.lower() for a in capability["aliases"])]
        if any(needle in text for needle in needles):
            matched.add(capability_id)
    return matched


def generate() -> dict[str, list[dict]]:
    org = _load(ORG_FILE)
    truth = _load(TRUTH_FILE)
    capabilities, systems, engineer_names = _flatten_org(org)
    rng = random.Random(RANDOM_SEED)

    buckets: dict[str, list[dict]] = {kind: [] for kind in REFERENCE_PREFIX}
    problems: list[str] = []

    # 1. Authored artifacts: the hero capability, plus the one conflicting record.
    pinned = [*PINNED_HERO_ARTIFACTS, *PINNED_CONFLICT_ARTIFACTS]
    for artifact in pinned:
        record = {k: v for k, v in artifact.items() if k != "kind"}
        buckets[artifact["kind"]].append(record)

    allocator = ReferenceAllocator({a["reference"] for a in pinned})

    # 2. Generated artifacts, one pass per ground-truth coverage entry, sorted for determinism.
    entries = sorted(
        truth["coverage"], key=lambda e: (e["capability_id"], e["engineer_id"])
    )
    for entry in entries:
        capability_id = entry["capability_id"]
        if capability_id == HERO_CAPABILITY:
            continue  # authored above
        capability = capabilities[capability_id]
        engineer_id = entry["engineer_id"]
        engineer_name = engineer_names[engineer_id]
        profile = entry.get("evidence_profile", "default")
        recipe = list(RECIPES[entry["true_readiness"]])
        if profile == "sparse":
            recipe = recipe[:1]

        for slot, (kind, role) in enumerate(recipe):
            title, body = _compose(kind, role, capability, engineer_name)
            record = {
                "reference": allocator.next(kind),
                "title": title,
                "body": body,
                "date": _pick_date(rng, profile, slot).isoformat(),
                "system_id": capability["system_id"],
                "participants": [{"engineer_id": engineer_id, "participant_role": role}],
                "file_paths": _file_paths(kind, capability),
            }
            buckets[kind].append(record)

    # 3. Noise. Never on the hero capability: its evidence counts drive the frozen fixture
    #    values for coverage freshness and evidence confidence.
    system_ids = sorted(systems)
    noise_needed = max(0, TARGET_TOTAL_ARTIFACTS - sum(len(v) for v in buckets.values()))
    for index in range(noise_needed):
        kind = ["pull_requests", "issues", "tickets", "code_reviews"][index % 4]
        system_id = system_ids[index % len(system_ids)]
        title = NOISE_TITLES[index % len(NOISE_TITLES)]
        engineer_id = sorted(engineer_names)[index % len(engineer_names)]
        buckets[kind].append(
            {
                "reference": allocator.next(kind),
                "title": f"{title} ({systems[system_id]['name']})",
                "body": (
                    f"{engineer_names[engineer_id]} made a routine maintenance change with no "
                    f"operational significance."
                ),
                "date": _pick_date(rng, "default", index % 4).isoformat(),
                "system_id": system_id,
                "participants": [
                    {"engineer_id": engineer_id, "participant_role": "AUTHOR"}
                ],
                "file_paths": [],
            }
        )

    # 4. Self-check: every artifact must match exactly zero or one capability.
    for kind, records in buckets.items():
        for record in records:
            matched = _match_capabilities(
                record["title"], record["body"], record["system_id"], capabilities
            )
            if len(matched) > 1:
                problems.append(
                    f"{record['reference']} ({kind}) matches {sorted(matched)} — ambiguous"
                )
    if problems:
        for problem in problems:
            print(f"  ambiguous: {problem}", file=sys.stderr)
        raise SystemExit(
            f"{len(problems)} artifact(s) match more than one capability. Fix the templates or "
            f"the aliases in data/org/novapay.json before committing the corpus."
        )

    # 5. CODEOWNERS, so declared ownership arrives as an ingested artifact with provenance
    #    rather than as a hardcoded field. The declared-versus-demonstrated beat depends on it.
    codeowners = {
        "reference": "CODEOWNERS",
        "title": "CODEOWNERS",
        "date": REFERENCE_DATE.isoformat(),
        "entries": [
            {
                "system_id": system["system_id"],
                "path": f"/services/{system['system_id'].replace('system_', '')}/",
                "engineer_id": system["declared_owner"]["engineer_id"],
                "source_reference": system["declared_owner"]["source_reference"],
            }
            for platform in org["platforms"]
            for system in platform["systems"]
        ],
    }

    for kind, records in buckets.items():
        records.sort(key=lambda r: r["reference"])

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for kind, records in buckets.items():
        (OUT_DIR / f"{kind}.json").write_text(json.dumps(records, indent=2) + "\n")
    (OUT_DIR / "codeowners.json").write_text(json.dumps(codeowners, indent=2) + "\n")

    manifest = {
        "generator_version": "1.0",
        "random_seed": RANDOM_SEED,
        "reference_date": REFERENCE_DATE.isoformat(),
        "counts": {kind: len(records) for kind, records in sorted(buckets.items())},
        "total_artifacts": sum(len(v) for v in buckets.values()),
        "codeowners_entries": len(codeowners["entries"]),
        "note": (
            "Generated by backend/scripts/generate_synthetic_data.py from data/org/ and the "
            "hidden ground truth. Committed so a clean clone reproduces the demo (PRD AC-15). "
            "Regenerate with the same seed to reproduce byte for byte."
        ),
    }
    (OUT_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")

    return buckets


def main() -> None:
    buckets = generate()
    total = sum(len(v) for v in buckets.values())
    print(f"wrote {total} artifacts to {OUT_DIR.relative_to(REPO_ROOT)}")
    for kind, records in sorted(buckets.items()):
        print(f"  {kind:<16} {len(records):>4}")


if __name__ == "__main__":
    main()
