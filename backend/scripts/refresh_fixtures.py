"""Regenerate the shared contract fixtures from live engine output.

    python -m scripts.refresh_fixtures            # from backend/
    python -m scripts.refresh_fixtures --check    # fail if any fixture is stale

`fixtures/` is jointly owned and the frontend renders it, so it must be what the API actually
returns — otherwise the frontend is built against a payload that never arrives. Regenerating from a
freshly seeded database makes drift impossible to accumulate silently.

The fixtures remain subordinate to `docs/API_CONTRACT.md`: where a regenerated payload disagrees
with the contract, the contract is right and the implementation is wrong. This script does not get
to decide that — it only makes the disagreement visible.

Two values are pinned rather than captured: `approved_at` and a challenge's `submitted_at` are real
timestamps, so recording them live would churn their fixtures on every run. Both are frozen to an
illustrative instant.

Every file in `fixtures/` must be captured here. Two of them were not, having been added from live
captures by hand: `identity-systems.json` and `challenge-attest-jordan.json`. An uncaptured fixture
is worse than a missing one, because `--check` reports "all fixtures match live engine output"
without ever having looked at it, so it can drift from the API indefinitely while the check stays
green. Both are captured now (GAP-03), and `test_fixture_coverage` asserts the set matches the
directory so the next addition cannot repeat it.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT / "backend") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "backend"))

FIXTURES = REPO_ROOT / "fixtures"

PLATFORM = "platform_payments"
IDENTITY_PLATFORM = "platform_identity"
SYSTEM = "system_payment_gateway"
CAPABILITY = "cap_incident_recovery"
ALEX = "eng_alex_chen"
MARIA = "eng_maria_gomez"
JORDAN = "eng_jordan_lee"
MANAGER = "eng_manager_sarah"

ILLUSTRATIVE_APPROVED_AT = "2026-08-15T10:30:00Z"
ILLUSTRATIVE_SUBMITTED_AT = "2026-08-15T10:35:00Z"

# Every fixture this script is responsible for. Declared rather than inferred so a test can compare
# it against `fixtures/` without seeding a database and replaying the golden path, and verified
# against the real capture in `main()` so the declaration cannot quietly become a lie.
CAPTURED_FIXTURES = frozenset(
    {
        "platforms",
        "payments-systems",
        "identity-systems",
        "payment-gateway",
        "payment-gateway-graph",
        "incident-recovery",
        "incident-recovery-evidence",
        "alex-simulation",
        "backup-candidates",
        "mitigation-plan",
        "mitigation-plan-approved",
        "challenge-attest-jordan",
    }
)


def _capture() -> dict[str, dict]:
    from fastapi.testclient import TestClient

    from app.main import app

    client = TestClient(app)
    captured: dict[str, dict] = {}

    def get(name: str, url: str, **kwargs) -> dict:
        response = client.get(url, **kwargs)
        response.raise_for_status()
        captured[name] = response.json()
        return captured[name]

    def post(name: str, url: str, payload: dict) -> dict:
        response = client.post(url, json=payload)
        response.raise_for_status()
        captured[name] = response.json()
        return captured[name]

    get("platforms", "/api/v1/platforms")
    get("payments-systems", f"/api/v1/platforms/{PLATFORM}/systems")
    get("identity-systems", f"/api/v1/platforms/{IDENTITY_PLATFORM}/systems")
    get("payment-gateway", f"/api/v1/systems/{SYSTEM}")
    get("payment-gateway-graph", f"/api/v1/systems/{SYSTEM}/graph")
    get("incident-recovery", f"/api/v1/capabilities/{CAPABILITY}")
    get("incident-recovery-evidence", f"/api/v1/capabilities/{CAPABILITY}/evidence")

    simulation = post(
        "alex-simulation",
        "/api/v1/simulations",
        {
            "simulation_type": "ENGINEER_UNAVAILABLE",
            "engineer_id": ALEX,
            "scope": {"type": "SYSTEM", "id": SYSTEM},
        },
    )
    post(
        "backup-candidates",
        "/api/v1/recommendations/backup-candidates",
        {"capability_id": CAPABILITY, "limit": 3, "simulation_id": simulation["simulation_id"]},
    )
    plan = post(
        "mitigation-plan",
        "/api/v1/mitigation-plans",
        {
            "capability_id": CAPABILITY,
            "primary_engineer_id": ALEX,
            "selected_backup_engineer_id": MARIA,
            "simulation_id": simulation["simulation_id"],
        },
    )
    approved = post(
        "mitigation-plan-approved",
        f"/api/v1/mitigation-plans/{plan['plan_id']}/approve",
        {"approved_by": MANAGER},
    )
    approved["approved_at"] = ILLUSTRATIVE_APPROVED_AT

    # Captured last, and deliberately so: this is the only call here that changes the assessment.
    # The manager attests that Jordan once recovered the gateway unaided, readiness is recomputed,
    # and Incident Recovery gains a second adequate engineer. Anything captured after it would show
    # the corrected graph rather than the demo baseline, so every fixture above must already be on
    # disk before this runs.
    challenge = post(
        "challenge-attest-jordan",
        f"/api/v1/capabilities/{CAPABILITY}/challenge",
        {
            "challenge_type": "MANAGER_ATTESTATION",
            "engineer_id": JORDAN,
            "submitted_by": MANAGER,
            "evidence_role": "INDEPENDENT_EXECUTION",
            "comment": "Jordan restored the gateway alone during the March incident; never written up.",
        },
    )
    challenge["submitted_at"] = ILLUSTRATIVE_SUBMITTED_AT

    # Undo it. A developer who runs this script and then starts the server should get the demo
    # baseline, not a database carrying an attestation they did not make.
    from scripts.seed_demo import seed

    seed(verbose=False)

    return captured


def _serialise(payload: dict) -> str:
    return json.dumps(payload, indent=2) + "\n"


def main() -> int:
    check_only = "--check" in sys.argv

    from scripts.seed_demo import seed

    # A fresh database, so `sim_001` and `plan_001` are the first of their kind and the fixtures
    # keep the identifiers the contract examples use.
    seed(verbose=False)
    captured = _capture()

    # The manifest must describe what actually happened, or the test that trusts it proves nothing.
    if set(captured) != CAPTURED_FIXTURES:
        print(
            "CAPTURED_FIXTURES does not match what this run captured. "
            f"Captured but undeclared: {sorted(set(captured) - CAPTURED_FIXTURES)}. "
            f"Declared but not captured: {sorted(CAPTURED_FIXTURES - set(captured))}."
        )
        return 1

    stale: list[str] = []
    for name, payload in captured.items():
        path = FIXTURES / f"{name}.json"
        rendered = _serialise(payload)
        if path.exists() and path.read_text() == rendered:
            continue
        stale.append(name)
        if not check_only:
            path.write_text(rendered)

    if check_only:
        if stale:
            print("stale fixtures: " + ", ".join(sorted(stale)))
            print("run: python -m scripts.refresh_fixtures")
            return 1
        print("all fixtures match live engine output")
        return 0

    if stale:
        print(f"updated {len(stale)} fixture(s):")
        for name in sorted(stale):
            print(f"  fixtures/{name}.json")
        print("\nThis is a contract-visible change. Tell Person B and log it in docs/DECISIONS.md.")
    else:
        print("all fixtures already match live engine output")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
