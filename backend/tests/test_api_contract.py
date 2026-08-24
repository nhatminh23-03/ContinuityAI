"""The ten frozen endpoints, against a real seeded database.

Two things are checked together:

* **The contract holds** — paths, shapes, enum values, the error envelope.
* **The values agree with the shared fixtures** — the same files the frontend renders
  (contract decision CI-14). Key scalars are compared rather than whole payloads, because the
  engine legitimately returns more than the hand-written fixtures did; where a *value* disagrees,
  one side is wrong and it gets fixed.
"""

from __future__ import annotations

from tests.conftest import load_fixture

PLATFORM = "platform_payments"
SYSTEM = "system_payment_gateway"
CAPABILITY = "cap_incident_recovery"
ALEX = "eng_alex_chen"
MARIA = "eng_maria_gomez"
JORDAN = "eng_jordan_lee"
MANAGER = "eng_manager_sarah"


def test_the_api_surface_is_exactly_the_agreed_endpoints() -> None:
    """Ten frozen endpoints plus the challenge endpoint added to close FR-020 and AC-11 (DEC-10).

    Asserted as an exact set rather than a subset: a route appearing without a logged decision is
    precisely the silent contract drift the change process exists to prevent.
    """
    from app.main import app

    frozen = {
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
    added_by_decision = {"/api/v1/capabilities/{capability_id}/challenge"}

    assert len(frozen) == 10
    versioned = {p for p in {route.path for route in app.routes} if p.startswith("/api/v1")}
    assert versioned == frozen | added_by_decision


def test_every_shared_fixture_is_captured_by_the_refresh_script() -> None:
    """A fixture the refresh script does not capture cannot be checked for drift.

    `refresh_fixtures --check` only compares the payloads it captured, so an uncaptured file makes
    it print "all fixtures match live engine output" without having looked at that file at all.
    `identity-systems.json` and `challenge-attest-jordan.json` were both in that state — added by
    hand from live captures — which is `docs/BACKEND_GAPS.md` GAP-03. Asserting set equality against
    the directory means the next fixture added on either side fails here instead of drifting
    silently for a week.

    This is the cheapest of the fixture tests and the only one that catches an *absence*.
    """
    from tests.conftest import FIXTURES

    from scripts.refresh_fixtures import CAPTURED_FIXTURES

    on_disk = {path.stem for path in FIXTURES.glob("*.json")}
    assert on_disk == CAPTURED_FIXTURES, (
        "fixtures/ and the refresh script disagree. Only in fixtures/: "
        f"{sorted(on_disk - CAPTURED_FIXTURES)}. Only in the script: "
        f"{sorted(CAPTURED_FIXTURES - on_disk)}."
    )


# ---------------------------------------------------------------------------------------
# 1-2. Platforms
# ---------------------------------------------------------------------------------------


def test_platforms_match_the_fixture_and_expose_no_platform_risk_score(client) -> None:
    body = client.get("/api/v1/platforms").json()
    expected = {p["platform_id"]: p for p in load_fixture("platforms")["platforms"]}

    assert {p["platform_id"] for p in body["platforms"]} == set(expected)
    for platform in body["platforms"]:
        reference = expected[platform["platform_id"]]
        assert platform["highest_system_risk_index"] == reference["highest_system_risk_index"]
        assert platform["critical_gap_count"] == reference["critical_gap_count"]
        assert platform["system_count"] == reference["system_count"]
        assert platform["drift_status"] == reference["drift_status"]
        assert (
            platform["single_expert_dependency_count"]
            == reference["single_expert_dependency_count"]
        )
        # Contract section 2.1: no synthesised platform-level score exists.
        assert "continuity_risk_index" not in platform
        assert "continuity_risk_class" not in platform


def test_single_expert_dependency_count_counts_capabilities_with_exactly_one_adequate_engineer(
    client, session
) -> None:
    """The field must equal the persisted per-capability count, not a re-derivation.

    Guards DEC-17/GAP-01: the number is aggregated in SQL from
    `capability_assessments.adequate_engineer_count`, so this recomputes the same thing in Python
    from the same rows and requires agreement. If someone later reimplements the aggregate with a
    different notion of "adequate", this fails.
    """
    from app.models import Capability, CapabilityAssessment, System

    rows = (
        session.query(System.platform_id, CapabilityAssessment.adequate_engineer_count)
        .join(Capability, Capability.system_id == System.system_id)
        .join(
            CapabilityAssessment,
            CapabilityAssessment.capability_id == Capability.capability_id,
        )
        .all()
    )
    expected: dict[str, int] = {}
    for platform_id, adequate in rows:
        expected.setdefault(platform_id, 0)
        if adequate == 1:
            expected[platform_id] += 1

    body = client.get("/api/v1/platforms").json()
    assert expected, "no capability assessments were seeded, so this test proves nothing"
    for platform in body["platforms"]:
        assert platform["single_expert_dependency_count"] == expected[platform["platform_id"]]


def test_single_expert_dependency_count_is_not_the_degraded_count(client) -> None:
    """The reason the field had to exist at all.

    `docs/BACKEND_GAPS.md` GAP-01 warned that the frontend must not approximate this by summing
    `degraded_capability_count`. That warning is only worth trusting if the two actually differ on
    the seeded data, so this asserts they do — otherwise a client-side approximation would pass
    every test we have and be wrong on the first dataset where the shortcut breaks.

    They differ because under DEC-07 a lower-criticality capability with *zero* adequate engineers
    is DEGRADED rather than a critical gap, so the degraded count spans both the one-expert and the
    no-expert cases.
    """
    platforms = client.get("/api/v1/platforms").json()["platforms"]
    for platform in platforms:
        systems = client.get(f"/api/v1/platforms/{platform['platform_id']}/systems").json()
        degraded_total = sum(s["degraded_capability_count"] for s in systems["systems"])
        if platform["single_expert_dependency_count"] != degraded_total:
            return
    raise AssertionError(
        "single_expert_dependency_count equals the summed degraded count on every platform, so "
        "this dataset no longer demonstrates why the field is not client-derivable. Either the "
        "seed changed or DEC-07 changed; re-read GAP-01 before deleting this test."
    )


def test_systems_under_a_platform_are_returned_with_their_assessments(client) -> None:
    body = client.get(f"/api/v1/platforms/{PLATFORM}/systems").json()
    assert body["platform"]["platform_id"] == PLATFORM
    gateway = next(s for s in body["systems"] if s["system_id"] == SYSTEM)
    reference = next(
        s for s in load_fixture("payments-systems")["systems"] if s["system_id"] == SYSTEM
    )
    for key in (
        "continuity_risk_index",
        "continuity_risk_class",
        "exposure",
        "evidence_confidence",
        "critical_gap_count",
        "degraded_capability_count",
        "covered_capability_count",
        "insufficient_evidence_count",
    ):
        assert gateway[key] == reference[key], key


def test_unknown_platform_returns_the_frozen_error_envelope(client) -> None:
    response = client.get("/api/v1/platforms/platform_nope/systems")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


# ---------------------------------------------------------------------------------------
# 3-4. System detail and graph
# ---------------------------------------------------------------------------------------


def test_system_detail_carries_risk_ownership_and_every_capability(client) -> None:
    body = client.get(f"/api/v1/systems/{SYSTEM}").json()
    reference = load_fixture("payment-gateway")

    assert body["continuity_risk_index"] == reference["continuity_risk_index"]
    assert body["continuity_risk_class"] == reference["continuity_risk_class"]
    assert body["criticality_source"] == "HUMAN_CONFIRMED"
    assert body["rules_triggered"] == reference["rules_triggered"]

    # The demo's opening beat: declared ownership and demonstrated coverage disagree.
    assert body["declared_ownership"]["engineer_id"] == JORDAN
    assert body["declared_ownership"]["source"] == "CODEOWNERS"
    assert body["declared_ownership"]["mismatch_detected"] is True

    # Every capability must be reachable through a component, or the counts cannot reconcile.
    listed = [cid for component in body["components"] for cid in component["capability_ids"]]
    assert len(listed) == (
        body["critical_gap_count"]
        + body["degraded_capability_count"]
        + body["covered_capability_count"]
        + body["insufficient_evidence_count"]
    )
    assert CAPABILITY in listed


def test_graph_contains_only_documented_node_and_edge_types(client) -> None:
    body = client.get(f"/api/v1/systems/{SYSTEM}/graph").json()
    assert body["scope"] == {"type": "SYSTEM", "id": SYSTEM, "name": "Payment Gateway"}

    assert {n["type"] for n in body["nodes"]} <= {
        "PLATFORM", "SYSTEM", "COMPONENT", "CAPABILITY", "ENGINEER", "EVIDENCE",
    }
    assert {e["type"] for e in body["edges"]} <= {
        "HAS_SYSTEM", "HAS_COMPONENT", "REQUIRES_CAPABILITY", "DEMONSTRATES",
        "SUPPORTED_BY", "DECLARED_OWNER",
    }

    node_ids = {n["id"] for n in body["nodes"]}
    for edge in body["edges"]:
        assert edge["source"] in node_ids, edge
        assert edge["target"] in node_ids, edge

    # Declared ownership must be drawable, otherwise the mismatch cannot be shown on the graph.
    assert any(e["type"] == "DECLARED_OWNER" for e in body["edges"])
    demonstrates = [e for e in body["edges"] if e["type"] == "DEMONSTRATES"]
    assert demonstrates and all("readiness" in e["metadata"] for e in demonstrates)


def test_focusing_the_graph_narrows_it_and_adds_evidence_nodes(client) -> None:
    body = client.get(
        f"/api/v1/systems/{SYSTEM}/graph", params={"focus_capability_id": CAPABILITY}
    ).json()
    capabilities = [n for n in body["nodes"] if n["type"] == "CAPABILITY"]
    assert [n["id"] for n in capabilities] == [CAPABILITY]
    assert any(n["type"] == "EVIDENCE" for n in body["nodes"])
    assert any(e["type"] == "SUPPORTED_BY" for e in body["edges"])


def test_focusing_on_a_capability_from_another_system_is_a_404(client) -> None:
    response = client.get(
        f"/api/v1/systems/{SYSTEM}/graph", params={"focus_capability_id": "cap_refund_reversal"}
    )
    assert response.status_code == 404


# ---------------------------------------------------------------------------------------
# 5-6. Capability detail and provenance
# ---------------------------------------------------------------------------------------


def test_capability_detail_reproduces_the_seeded_hero_coverage(client) -> None:
    """AC-05. Alex VALIDATED, Maria ASSISTED, Jordan EXPOSED — inferred from artifacts, not seeded."""
    body = client.get(f"/api/v1/capabilities/{CAPABILITY}").json()
    reference = load_fixture("incident-recovery")

    assert body["continuity_risk_index"] == reference["continuity_risk_index"]
    assert body["continuity_risk_class"] == reference["continuity_risk_class"]
    assert body["exposure"] == reference["exposure"]
    assert body["rules_triggered"] == reference["rules_triggered"]
    assert body["primary_engineer"] == {
        "engineer_id": ALEX, "name": "Alex Chen", "readiness": "VALIDATED"
    }
    assert body["best_remaining_coverage"]["engineer_id"] == MARIA

    readiness = {c["engineer_id"]: c["readiness"] for c in body["engineer_coverage"]}
    assert readiness == {ALEX: "VALIDATED", MARIA: "ASSISTED", JORDAN: "EXPOSED"}

    freshness = {c["engineer_id"]: c["freshness"] for c in body["engineer_coverage"]}
    assert freshness[JORDAN] == "AGING", "Jordan's only evidence is two years old"


def test_every_readiness_claim_opens_supporting_evidence(client) -> None:
    """AC-04 and FR-024. A claim about a named person with nothing behind it is the one output this
    product must never produce."""
    body = client.get(f"/api/v1/capabilities/{CAPABILITY}/evidence").json()
    assert body["assessment"]["rules_triggered"] == load_fixture("incident-recovery")["rules_triggered"]
    assert body["evidence"], "a DEGRADED capability must be able to show its evidence"

    for record in body["evidence"]:
        assert record["provenance"]["record_id"]
        assert record["source_reference"]
        assert record["summary"]

    # Strongest evidence first: the independent production recovery, not the most recent document.
    assert body["evidence"][0]["evidence_id"] == "evidence_inc_184"
    assert body["evidence"][0]["evidence_role"] == "INDEPENDENT_EXECUTION"

    mismatch = body["declared_vs_demonstrated"]
    assert mismatch["declared_owner"]["engineer_id"] == JORDAN
    assert mismatch["strongest_demonstrated_coverage"]["engineer_id"] == ALEX
    assert mismatch["mismatch_detected"] is True


def test_absence_of_evidence_is_reported_as_absence_not_inability(client) -> None:
    body = client.get(f"/api/v1/capabilities/{CAPABILITY}/evidence").json()
    notes = {m["engineer_id"]: m["description"] for m in body["missing_evidence"]}
    assert JORDAN in notes
    text = notes[JORDAN].lower()
    assert "no qualifying" in text
    for forbidden in ("cannot", "unable", "incapable", "not capable"):
        assert forbidden not in text


def test_evidence_can_be_filtered_to_one_engineer(client) -> None:
    body = client.get(
        f"/api/v1/capabilities/{CAPABILITY}/evidence", params={"engineer_id": ALEX}
    ).json()
    assert body["evidence"]
    assert all(e["engineer_id"] == ALEX for e in body["evidence"])
    assert all(m["engineer_id"] == ALEX for m in body["missing_evidence"])


def test_a_sparse_capability_returns_insufficient_evidence_and_no_index(client) -> None:
    """AC-12."""
    body = client.get("/api/v1/capabilities/cap_permission_audit").json()
    assert body["exposure"] == "INSUFFICIENT_EVIDENCE"
    assert body["continuity_risk_index"] is None
    assert body["continuity_risk_class"] is None
