"""Walk the golden path against the live engine and diff it against the shared fixtures.

    python -m scripts.verify_golden_path        # from backend/

The daily integration check from docs/API_CONTRACT.md section 19, automated. It reports every
place the real response differs from the fixture the frontend renders, so a drift is a listed
difference rather than a surprise during a demo rehearsal.

Exit code is 0 even when differences exist: some are expected and deliberate (the engine produces
richer data than the hand-written fixtures did). The point is to see them, and to decide which
side is wrong.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT / "backend") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "backend"))

FIXTURES = REPO_ROOT / "fixtures"

PLATFORM = "platform_payments"
SYSTEM = "system_payment_gateway"
CAPABILITY = "cap_incident_recovery"
ENGINEER = "eng_alex_chen"
CANDIDATE = "eng_maria_gomez"
MANAGER = "eng_manager_sarah"


def _load(name: str) -> Any:
    return json.loads((FIXTURES / f"{name}.json").read_text())


def _diff(path: str, expected: Any, actual: Any, out: list[str]) -> None:
    if isinstance(expected, dict) and isinstance(actual, dict):
        for key in expected:
            if key not in actual:
                out.append(f"{path}.{key}: missing (fixture has {expected[key]!r})")
            else:
                _diff(f"{path}.{key}", expected[key], actual[key], out)
        for key in actual:
            if key not in expected:
                out.append(f"{path}.{key}: extra (engine has {actual[key]!r})")
        return
    if isinstance(expected, list) and isinstance(actual, list):
        if len(expected) != len(actual):
            out.append(f"{path}: length {len(expected)} -> {len(actual)}")
        for index, (exp, act) in enumerate(zip(expected, actual)):
            _diff(f"{path}[{index}]", exp, act, out)
        return
    if expected != actual:
        out.append(f"{path}: {expected!r} -> {actual!r}")


def main() -> None:
    from fastapi.testclient import TestClient

    from app.main import app

    client = TestClient(app)
    differences: dict[str, list[str]] = {}
    failures: list[str] = []

    def check(label: str, fixture: str, response) -> Any:
        # elapsed is measured by httpx and covers the full request/response cycle, which is what
        # AC-14 is about. Reads target < 800 ms local p95, deterministic simulation < 2 s.
        timings.append((label, response.elapsed.total_seconds() * 1000))
        if response.status_code >= 400:
            failures.append(f"{label}: HTTP {response.status_code} {response.text[:200]}")
            return None
        body = response.json()
        found: list[str] = []
        _diff(label, _load(fixture), body, found)
        if found:
            differences[label] = found
        return body

    timings: list[tuple[str, float]] = []
    print("golden path\n" + "=" * 72)

    check("GET /platforms", "platforms", client.get("/api/v1/platforms"))
    check(
        "GET /platforms/{id}/systems",
        "payments-systems",
        client.get(f"/api/v1/platforms/{PLATFORM}/systems"),
    )
    check("GET /systems/{id}", "payment-gateway", client.get(f"/api/v1/systems/{SYSTEM}"))
    check(
        "GET /systems/{id}/graph",
        "payment-gateway-graph",
        client.get(f"/api/v1/systems/{SYSTEM}/graph"),
    )
    check(
        "GET /capabilities/{id}", "incident-recovery", client.get(f"/api/v1/capabilities/{CAPABILITY}")
    )
    check(
        "GET /capabilities/{id}/evidence",
        "incident-recovery-evidence",
        client.get(f"/api/v1/capabilities/{CAPABILITY}/evidence"),
    )
    simulation = check(
        "POST /simulations",
        "alex-simulation",
        client.post(
            "/api/v1/simulations",
            json={
                "simulation_type": "ENGINEER_UNAVAILABLE",
                "engineer_id": ENGINEER,
                "scope": {"type": "SYSTEM", "id": SYSTEM},
            },
        ),
    )
    check(
        "POST /recommendations/backup-candidates",
        "backup-candidates",
        client.post(
            "/api/v1/recommendations/backup-candidates",
            json={
                "capability_id": CAPABILITY,
                "limit": 3,
                "simulation_id": simulation["simulation_id"] if simulation else None,
            },
        ),
    )
    plan = check(
        "POST /mitigation-plans",
        "mitigation-plan",
        client.post(
            "/api/v1/mitigation-plans",
            json={
                "capability_id": CAPABILITY,
                "primary_engineer_id": ENGINEER,
                "selected_backup_engineer_id": CANDIDATE,
                "simulation_id": simulation["simulation_id"] if simulation else None,
            },
        ),
    )
    if plan:
        check(
            "POST /mitigation-plans/{id}/approve",
            "mitigation-plan-approved",
            client.post(
                f"/api/v1/mitigation-plans/{plan['plan_id']}/approve",
                json={"approved_by": MANAGER},
            ),
        )

    if failures:
        print("\nREQUEST FAILURES")
        for failure in failures:
            print(f"  {failure}")

    if not differences:
        print("\nevery response is identical to its fixture.")
    else:
        print(f"\n{sum(len(v) for v in differences.values())} difference(s) from the fixtures:\n")
        for label, found in differences.items():
            print(f"  {label}")
            for item in found:
                print(f"    - {item}")

    print("\nlatency (AC-14: reads < 800 ms, simulation < 2 s)")
    breaches = []
    for label, milliseconds in timings:
        budget = 2000.0 if "simulations" in label else 800.0
        status = "ok" if milliseconds <= budget else "OVER"
        if status == "OVER":
            breaches.append(f"{label} {milliseconds:.0f} ms > {budget:.0f} ms")
        print(f"  [{status:>4}] {milliseconds:7.1f} ms  {label}")
    if breaches:
        print("\n  AC-14 breaches: " + "; ".join(breaches))

    print("\n" + "=" * 72)
    print("Differences are not automatically failures. Decide per item whether the fixture or the")
    print("implementation is wrong, then fix that side (fixtures/README.md).")


if __name__ == "__main__":
    main()
