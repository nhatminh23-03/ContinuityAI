"""Regenerate the shared contract fixtures from live engine output.

    python -m scripts.refresh_fixtures            # from backend/
    python -m scripts.refresh_fixtures --check    # fail if any fixture is stale

`fixtures/` is jointly owned and the frontend renders it, so it must be what the API actually
returns — otherwise the frontend is built against a payload that never arrives. Regenerating from a
freshly seeded database makes drift impossible to accumulate silently.

The fixtures remain subordinate to `docs/API_CONTRACT.md`: where a regenerated payload disagrees
with the contract, the contract is right and the implementation is wrong. This script does not get
to decide that — it only makes the disagreement visible.

One value is pinned rather than captured: `approved_at` is a real timestamp, so recording it live
would churn the fixture on every run. It is frozen to an illustrative instant.
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
SYSTEM = "system_payment_gateway"
CAPABILITY = "cap_incident_recovery"
ALEX = "eng_alex_chen"
MARIA = "eng_maria_gomez"
MANAGER = "eng_manager_sarah"

ILLUSTRATIVE_APPROVED_AT = "2026-08-15T10:30:00Z"


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
