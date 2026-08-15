"""Every frozen endpoint returns a payload its response model accepts.

This is the contract-shape check, not a behaviour test. It fails the moment a fixture
and its DTO disagree, which is the whole point of both sides reading one fixture set.
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

PLATFORM = "platform_payments"
SYSTEM = "system_payment_gateway"
CAPABILITY = "cap_incident_recovery"
ENGINEER = "eng_alex_chen"
PLAN = "plan_001"


def test_all_ten_endpoints_are_mounted_under_api_v1() -> None:
    paths = {r.path for r in app.routes}
    expected = {
        "/api/v1/platforms",
        "/api/v1/platforms/{platform_id}/systems",
        "/api/v1/systems/{system_id}",
        "/api/v1/systems/{system_id}/graph",
        "/api/v1/capabilities/{capability_id}",
        "/api/v1/capabilities/{capability_id}/evidence",
        "/api/v1/simulations",
        "/api/v1/recommendations/backup-candidates",
        "/api/v1/mitigation-plans",
        "/api/v1/mitigation-plans/{plan_id}/approve",
    }
    assert expected <= paths
    assert len(expected) == 10


def test_list_platforms() -> None:
    body = client.get("/api/v1/platforms").json()
    assert body["platforms"][0]["platform_id"] == PLATFORM
    # The MVP exposes no platform-level risk score. Contract section 2.1.
    assert "continuity_risk_index" not in body["platforms"][0]


def test_list_platform_systems() -> None:
    r = client.get(f"/api/v1/platforms/{PLATFORM}/systems")
    assert r.status_code == 200
    assert r.json()["systems"][0]["system_id"] == SYSTEM


def test_get_system_detail_carries_declared_ownership() -> None:
    body = client.get(f"/api/v1/systems/{SYSTEM}").json()
    assert body["declared_ownership"]["mismatch_detected"] is True
    assert body["continuity_risk_class"] == "HIGH"


def test_get_system_graph() -> None:
    body = client.get(f"/api/v1/systems/{SYSTEM}/graph").json()
    assert {n["type"] for n in body["nodes"]} <= {
        "PLATFORM", "SYSTEM", "COMPONENT", "CAPABILITY", "ENGINEER", "EVIDENCE"
    }


def test_get_capability_detail_carries_fired_rules() -> None:
    body = client.get(f"/api/v1/capabilities/{CAPABILITY}").json()
    assert body["rules_triggered"]
    assert body["exposure"] == "DEGRADED"


def test_capability_evidence_filters_by_engineer() -> None:
    body = client.get(
        f"/api/v1/capabilities/{CAPABILITY}/evidence", params={"engineer_id": ENGINEER}
    ).json()
    assert all(e["engineer_id"] == ENGINEER for e in body["evidence"])


def test_simulation_before_and_after_reconcile_with_impacts() -> None:
    body = client.post(
        "/api/v1/simulations",
        json={
            "simulation_type": "ENGINEER_UNAVAILABLE",
            "engineer_id": ENGINEER,
            "scope": {"type": "SYSTEM", "id": SYSTEM},
        },
    ).json()
    impacts = body["capability_impacts"]
    for side in ("before", "after"):
        state = body[side]
        counts = [i[side] for i in impacts]
        assert state["critical_gap_count"] == counts.count("CRITICAL_GAP")
        assert state["degraded_capability_count"] == counts.count("DEGRADED")
        assert state["covered_capability_count"] == counts.count("COVERED")


def test_backup_candidates_respect_limit_and_carry_disclaimer() -> None:
    body = client.post(
        "/api/v1/recommendations/backup-candidates",
        json={"capability_id": CAPABILITY, "limit": 1},
    ).json()
    assert len(body["candidates"]) == 1
    assert body["disclaimer"]
    # No employee value, ranking, or match percentage anywhere.
    assert not {"score", "match", "rank"} & set(body["candidates"][0])


def test_mitigation_plan_is_created_as_draft() -> None:
    r = client.post(
        "/api/v1/mitigation-plans",
        json={
            "capability_id": CAPABILITY,
            "primary_engineer_id": ENGINEER,
            "selected_backup_engineer_id": "eng_maria_gomez",
        },
    )
    assert r.status_code == 201
    assert r.json()["status"] == "DRAFT"


def test_approval_transitions_draft_to_approved() -> None:
    body = client.post(
        f"/api/v1/mitigation-plans/{PLAN}/approve",
        json={"approved_by": "eng_manager_sarah"},
    ).json()
    assert body["status"] == "APPROVED"


def test_unknown_id_returns_the_frozen_error_envelope() -> None:
    r = client.get("/api/v1/systems/system_does_not_exist")
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "NOT_FOUND"
