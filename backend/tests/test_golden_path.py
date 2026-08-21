"""The golden path, end to end. docs/API_CONTRACT.md section 19.

Dashboard -> system -> capability -> evidence -> simulate Alex unavailable -> compare candidates
-> select Maria -> generate plan -> approve.

If this file fails, feature work stops until it passes (TEAM_WORKFLOW_PERSON_A_B.md section 15).
"""

from __future__ import annotations

from app.ai.language_policy import find_forbidden_phrases, find_probability_language
from tests.conftest import load_fixture

PLATFORM = "platform_payments"
SYSTEM = "system_payment_gateway"
CAPABILITY = "cap_incident_recovery"
ALEX = "eng_alex_chen"
MARIA = "eng_maria_gomez"
JORDAN = "eng_jordan_lee"
MANAGER = "eng_manager_sarah"


def simulate(client, engineer_id: str = ALEX, scope_id: str = SYSTEM):
    return client.post(
        "/api/v1/simulations",
        json={
            "simulation_type": "ENGINEER_UNAVAILABLE",
            "engineer_id": engineer_id,
            "scope": {"type": "SYSTEM", "id": scope_id},
        },
    )


# ---------------------------------------------------------------------------------------
# 7. Simulation
# ---------------------------------------------------------------------------------------


def test_simulating_the_sole_expert_reproduces_the_frozen_before_and_after(client) -> None:
    """AC-06 and AC-07. Deterministically reproducible from the rules, and specific about which
    capabilities move — Incident Recovery and Certificate Management become gaps while Retry Logic
    stays covered."""
    body = simulate(client).json()
    reference = load_fixture("alex-simulation")

    assert body["engineer"] == {"engineer_id": ALEX, "name": "Alex Chen"}
    assert body["scope"] == {"type": "SYSTEM", "id": SYSTEM, "name": "Payment Gateway"}

    for side in ("before", "after"):
        for key, expected in reference[side].items():
            assert body[side][key] == expected, f"{side}.{key}"

    impacts = {i["capability_id"]: i for i in body["capability_impacts"]}
    for capability_id, expected in {i["capability_id"]: i for i in reference["capability_impacts"]}.items():
        actual = impacts[capability_id]
        assert actual["before"] == expected["before"], capability_id
        assert actual["after"] == expected["after"], capability_id
        assert actual["remaining_best_readiness"] == expected["remaining_best_readiness"], capability_id


def test_simulation_states_reconcile_against_their_own_impact_list(client) -> None:
    body = simulate(client).json()
    impacts = body["capability_impacts"]
    for side in ("before", "after"):
        exposures = [i[side] for i in impacts]
        assert body[side]["critical_gap_count"] == exposures.count("CRITICAL_GAP")
        assert body[side]["degraded_capability_count"] == exposures.count("DEGRADED")
        assert body[side]["covered_capability_count"] == exposures.count("COVERED")


def test_simulation_is_repeatable_and_does_not_change_the_baseline(client) -> None:
    """ARCHITECTURE.md quality bar E: the simulator cannot corrupt persisted state."""
    before_detail = client.get(f"/api/v1/systems/{SYSTEM}").json()
    first = simulate(client).json()
    second = simulate(client).json()
    after_detail = client.get(f"/api/v1/systems/{SYSTEM}").json()

    assert first["before"] == second["before"]
    assert first["after"] == second["after"]
    assert first["capability_impacts"] == second["capability_impacts"]
    assert first["simulation_id"] != second["simulation_id"]
    assert before_detail == after_detail


def test_simulation_summary_never_predicts_an_outage(client) -> None:
    """Checked against the shared `language_policy` source rather than a locally hardcoded list,
    so this stays aligned with the runtime scan in test_responsible_ai.py. "outage will" is kept
    as an explicit check on top: it is not itself a canonical marker, but this test previously
    asserted against it and dropping it would weaken the assertion."""
    summary = simulate(client).json()["summary"]
    assert summary
    assert not find_probability_language(summary)
    assert not find_forbidden_phrases(summary)
    assert "outage will" not in summary.lower()


def test_simulating_an_engineer_with_no_coverage_in_scope_says_so(client) -> None:
    body = simulate(client, engineer_id="eng_sofia_ruiz").json()
    assert body["capability_impacts"] == []
    assert body["before"] == body["after"]
    assert "no demonstrated capability coverage" in body["summary"]


def test_platform_scope_is_rejected_rather_than_silently_treated_as_a_system(client) -> None:
    response = client.post(
        "/api/v1/simulations",
        json={
            "simulation_type": "ENGINEER_UNAVAILABLE",
            "engineer_id": ALEX,
            "scope": {"type": "PLATFORM", "id": PLATFORM},
        },
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_unknown_engineer_is_a_404(client) -> None:
    assert simulate(client, engineer_id="eng_nobody").status_code == 404


# ---------------------------------------------------------------------------------------
# 8. Candidate comparison
# ---------------------------------------------------------------------------------------


def test_candidates_are_ranked_by_evidence_overlap_and_exclude_the_current_expert(client) -> None:
    """AC-08. Maria HIGH, Jordan MEDIUM, Alex absent because he is the person being backed up."""
    simulation = simulate(client).json()
    body = client.post(
        "/api/v1/recommendations/backup-candidates",
        json={"capability_id": CAPABILITY, "limit": 3, "simulation_id": simulation["simulation_id"]},
    ).json()

    overlap = {c["engineer_id"]: c["technical_overlap"] for c in body["candidates"]}
    assert overlap.get(MARIA) == "HIGH"
    assert overlap.get(JORDAN) == "MEDIUM"
    assert ALEX not in overlap

    for candidate in body["candidates"]:
        assert candidate["strengths"], "a candidate must say what they have demonstrated"
        assert candidate["gaps"], "and what would need closing"
        assert candidate["supporting_evidence_ids"]

    assert body["disclaimer"] == load_fixture("backup-candidates")["disclaimer"]


def test_candidate_output_contains_no_score_ranking_or_match_percentage(client) -> None:
    body = client.post(
        "/api/v1/recommendations/backup-candidates",
        json={"capability_id": CAPABILITY, "limit": 3},
    ).json()
    for candidate in body["candidates"]:
        assert not {"score", "match", "rank", "percentage", "value"} & set(candidate)
        for gap in candidate["gaps"]:
            assert "cannot" not in gap.lower()


def test_candidate_limit_is_respected(client) -> None:
    body = client.post(
        "/api/v1/recommendations/backup-candidates",
        json={"capability_id": CAPABILITY, "limit": 1},
    ).json()
    assert len(body["candidates"]) == 1


def test_a_limit_above_three_is_rejected(client) -> None:
    response = client.post(
        "/api/v1/recommendations/backup-candidates",
        json={"capability_id": CAPABILITY, "limit": 9},
    )
    assert response.status_code == 422


# ---------------------------------------------------------------------------------------
# 9-10. Mitigation plan
# ---------------------------------------------------------------------------------------


def create_plan(client, candidate: str = MARIA):
    return client.post(
        "/api/v1/mitigation-plans",
        json={
            "capability_id": CAPABILITY,
            "primary_engineer_id": ALEX,
            "selected_backup_engineer_id": candidate,
        },
    )


def test_a_generated_plan_is_a_draft_targeting_the_exposed_capability(client) -> None:
    """AC-10. Between three and five actions, each with observable acceptance criteria, aimed at the
    capability rather than at cloning the source engineer."""
    response = create_plan(client)
    assert response.status_code == 201
    body = response.json()

    assert body["status"] == "DRAFT"
    assert body["capability"]["capability_id"] == CAPABILITY
    assert body["source_engineer"]["engineer_id"] == ALEX
    assert body["backup_candidate"]["engineer_id"] == MARIA
    assert body["target_readiness"] == "PRACTICED"
    assert 3 <= len(body["tasks"]) <= 5

    for task in body["tasks"]:
        assert task["acceptance_criteria"], task["title"]
        assert task["type"] in {
            "KNOWLEDGE_REVIEW", "SHADOWING", "PRACTICE", "RECOVERY_DRILL",
            "DOCUMENTATION", "ARCHITECTURE_REVIEW",
        }

    assert body["tasks"][0]["linked_evidence_ids"], "the review task should link the evidence it rests on"


def test_the_plan_reflects_the_chosen_candidates_gap(client) -> None:
    """AC-09: a manager may pick a non-top candidate and still get a candidate-specific plan.
    Jordan has no hands-on evidence, so his plan adds an unaided drill Maria's does not need."""
    maria = create_plan(client, MARIA).json()
    jordan = create_plan(client, JORDAN).json()

    maria_types = [t["type"] for t in maria["tasks"]]
    jordan_types = [t["type"] for t in jordan["tasks"]]
    assert "RECOVERY_DRILL" not in maria_types
    assert "RECOVERY_DRILL" in jordan_types
    assert len(jordan["tasks"]) > len(maria["tasks"])


def test_generating_a_plan_does_not_change_readiness_or_risk(client) -> None:
    """Nobody becomes more capable because work was scheduled."""
    before = client.get(f"/api/v1/capabilities/{CAPABILITY}").json()
    create_plan(client)
    after = client.get(f"/api/v1/capabilities/{CAPABILITY}").json()
    assert before == after


def test_approval_transitions_draft_to_approved(client) -> None:
    plan = create_plan(client).json()
    body = client.post(
        f"/api/v1/mitigation-plans/{plan['plan_id']}/approve", json={"approved_by": MANAGER}
    ).json()
    assert body["status"] == "APPROVED"
    assert body["approved_by"] == MANAGER
    assert body["approved_at"]


def test_a_manager_can_edit_the_plan_on_the_way_through_approval(client) -> None:
    """Contract decision CI-12: edits ride on the approval request, no eleventh endpoint."""
    plan = create_plan(client).json()
    edited = plan["tasks"][:3]
    edited[0]["title"] = "Review the recovery path with the on-call rota"

    response = client.post(
        f"/api/v1/mitigation-plans/{plan['plan_id']}/approve",
        json={"approved_by": MANAGER, "tasks": edited},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "APPROVED"


def test_an_approved_plan_cannot_be_approved_again(client) -> None:
    plan = create_plan(client).json()
    client.post(f"/api/v1/mitigation-plans/{plan['plan_id']}/approve", json={"approved_by": MANAGER})
    response = client.post(
        f"/api/v1/mitigation-plans/{plan['plan_id']}/approve", json={"approved_by": MANAGER}
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_an_edit_outside_the_permitted_action_count_is_rejected(client) -> None:
    plan = create_plan(client).json()
    response = client.post(
        f"/api/v1/mitigation-plans/{plan['plan_id']}/approve",
        json={"approved_by": MANAGER, "tasks": plan["tasks"][:1]},
    )
    assert response.status_code == 422


def test_source_and_backup_cannot_be_the_same_person(client) -> None:
    response = client.post(
        "/api/v1/mitigation-plans",
        json={
            "capability_id": CAPABILITY,
            "primary_engineer_id": ALEX,
            "selected_backup_engineer_id": ALEX,
        },
    )
    assert response.status_code == 422


def test_unknown_plan_is_a_404(client) -> None:
    response = client.post(
        "/api/v1/mitigation-plans/plan_999/approve", json={"approved_by": MANAGER}
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"
