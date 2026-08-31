"""Responsible-AI boundaries, asserted rather than promised.

PRD section 22, DOMAIN_MODEL.md sections 10.2, 43 and 44, API contract section 13. AC-13 requires
that no employee productivity, value, ranking, promotion, bonus, or layoff output exists anywhere
in the UI or the API.

Wording rules are checked too, because the difference between "no qualifying evidence was found"
and "cannot recover the system" is the difference between a defensible product and a liability.
"""

from __future__ import annotations

import ast
from pathlib import Path

from sqlalchemy import inspect

from app.ai.language_policy import FORBIDDEN_PHRASES, find_forbidden_phrases
from app.db.session import ENGINE

APP_ROOT = Path(__file__).resolve().parents[1] / "app"

# DOMAIN_MODEL.md section 10.2 names these explicitly as fields that must not exist.
FORBIDDEN_FIELD_FRAGMENTS = (
    "productivity",
    "employee_value",
    "importance_score",
    "layoff",
    "promotion",
    "bonus",
    "salary",
    "compensation",
    "engagement_score",
    "personality",
    "sentiment",
    "loyalty",
    "performance_score",
    "performance_rating",
    "working_hours",
    "hours_worked",
    "match_percentage",
)

ENGINEER_COLUMN_ALLOWLIST = {"engineer_id", "name", "role", "team"}


def test_the_engineer_table_holds_no_score_of_any_kind() -> None:
    """People are coverage relationships, not scored assets. Risk attaches to capabilities and
    systems, never to an engineer (DOMAIN_MODEL.md invariant 17)."""
    columns = {c["name"] for c in inspect(ENGINE).get_columns("engineers")}
    assert columns == ENGINEER_COLUMN_ALLOWLIST, (
        f"unexpected columns on `engineers`: {sorted(columns - ENGINEER_COLUMN_ALLOWLIST)}"
    )


def test_no_table_carries_a_prohibited_field() -> None:
    inspector = inspect(ENGINE)
    offenders: list[str] = []
    for table in inspector.get_table_names():
        for column in inspector.get_columns(table):
            lowered = column["name"].lower()
            for fragment in FORBIDDEN_FIELD_FRAGMENTS:
                if fragment in lowered:
                    offenders.append(f"{table}.{column['name']}")
    assert not offenders, f"prohibited columns: {offenders}"


def test_no_response_schema_declares_a_prohibited_field() -> None:
    """The API surface, checked at the schema level rather than per response."""
    schemas = APP_ROOT / "schemas"
    offenders: list[str] = []
    for path in sorted(schemas.rglob("*.py")):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                lowered = node.target.id.lower()
                for fragment in FORBIDDEN_FIELD_FRAGMENTS:
                    if fragment in lowered:
                        offenders.append(f"{path.name}:{node.target.id}")
    assert not offenders, f"prohibited DTO fields: {offenders}"


def test_no_prohibited_phrase_appears_in_generated_text() -> None:
    """Applies to templates and literals in the AI layer and the services, which is where
    user-visible prose is produced — including model instructions, since those shape output.

    Scope note: prompt files under `app/ai/prompts/` and the specification documents are excluded.
    They legitimately quote prohibited wording *in order to prohibit it* ("`cannot recover the
    system` is prohibited"), and an allowlist for that would make the check fragile in exactly the
    place it needs to be blunt. Runtime instruction strings in code are therefore phrased to avoid
    the banned words rather than to quote them.

    `FORBIDDEN_PHRASES` is imported from `app.ai.language_policy` rather than duplicated here, so
    this static scan and the runtime scan below stay checks against one list. This static scan is
    necessarily blind to prose a model writes at runtime — see
    `test_no_prohibited_phrase_appears_in_narrative_endpoint_responses` for that.
    """
    offenders: list[str] = []
    for directory in ("ai", "services", "recommendation", "mitigation", "simulation", "continuity"):
        for path in sorted((APP_ROOT / directory).rglob("*.py")):
            tree = ast.parse(path.read_text())
            docstrings = {
                ast.get_docstring(node, clean=False)
                for node in ast.walk(tree)
                if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
            }
            for node in ast.walk(tree):
                if not (isinstance(node, ast.Constant) and isinstance(node.value, str)):
                    continue
                if node.value in docstrings:
                    continue  # prose about the rules, not output
                lowered = node.value.lower()
                for phrase in FORBIDDEN_PHRASES:
                    if phrase in lowered:
                        offenders.append(f"{path.name}: {phrase!r} in {node.value[:60]!r}")
    assert not offenders, "\n".join(offenders)


def test_candidate_comparison_states_what_it_does_not_evaluate(client) -> None:
    """PRD section 11.6. The manager must be told which staffing factors are outside the model."""
    body = client.post(
        "/api/v1/recommendations/backup-candidates",
        json={"capability_id": "cap_incident_recovery", "limit": 3},
    ).json()
    disclaimer = body["disclaimer"].lower()
    for factor in ("workload", "availability", "career goals"):
        assert factor in disclaimer


def test_no_endpoint_exposes_an_engineer_score(client) -> None:
    responses = [
        client.get("/api/v1/platforms").json(),
        client.get("/api/v1/platforms/platform_payments/systems").json(),
        client.get("/api/v1/systems/system_payment_gateway").json(),
        client.get("/api/v1/systems/system_payment_gateway/graph").json(),
        client.get("/api/v1/capabilities/cap_incident_recovery").json(),
        client.get("/api/v1/capabilities/cap_incident_recovery/evidence").json(),
    ]
    serialised = str(responses).lower()
    for fragment in FORBIDDEN_FIELD_FRAGMENTS:
        assert fragment not in serialised, fragment


def test_risk_is_never_attached_to_an_engineer(client) -> None:
    """PRD section 22.3: "Payment Gateway has a 93/100 index", never "Alex is a 93 risk"."""
    body = client.get("/api/v1/capabilities/cap_incident_recovery").json()
    for coverage in body["engineer_coverage"]:
        assert "continuity_risk_index" not in coverage
        assert "continuity_risk_class" not in coverage
        assert "exposure" not in coverage

    graph = client.get("/api/v1/systems/system_payment_gateway/graph").json()
    for node in graph["nodes"]:
        if node["type"] == "ENGINEER":
            assert "continuity_risk_index" not in node.get("metadata", {})
            assert node.get("status") is None


def test_no_prohibited_phrase_appears_in_narrative_endpoint_responses(client) -> None:
    """The runtime counterpart to `test_no_prohibited_phrase_appears_in_generated_text` above.

    That test AST-scans `.py` string literals, so it cannot see anything a model writes at
    request time — it would keep passing even if a configured provider started emitting banned
    wording, because nothing about that wording exists as a literal in the source tree. These are
    the three endpoints in the whole API that return model-generated prose: a simulation summary,
    a candidate explanation (strengths and gaps), and a mitigation plan (task titles,
    descriptions, and acceptance criteria). No other endpoint produces free text, so no other
    endpoint needs to be here.

    Tests run against the deterministic provider (`conftest.py` never sets `AI_PROVIDER`), so this
    currently asserts the template output is clean. That is the point: the same assertions then
    also cover whatever a configured model provider writes, without the test needing to change.
    """
    fields: list[tuple[str, str]] = []

    simulation = client.post(
        "/api/v1/simulations",
        json={
            "simulation_type": "ENGINEER_UNAVAILABLE",
            "engineer_id": "eng_alex_chen",
            "scope": {"type": "SYSTEM", "id": "system_payment_gateway"},
        },
    ).json()
    fields.append(("simulation.summary", simulation["summary"]))

    candidates = client.post(
        "/api/v1/recommendations/backup-candidates",
        json={"capability_id": "cap_incident_recovery", "limit": 3},
    ).json()
    for candidate in candidates["candidates"]:
        engineer_id = candidate["engineer_id"]
        for index, strength in enumerate(candidate["strengths"]):
            fields.append((f"candidate[{engineer_id}].strengths[{index}]", strength))
        for index, gap in enumerate(candidate["gaps"]):
            fields.append((f"candidate[{engineer_id}].gaps[{index}]", gap))

    plan = client.post(
        "/api/v1/mitigation-plans",
        json={
            "capability_id": "cap_incident_recovery",
            "primary_engineer_id": "eng_alex_chen",
            "selected_backup_engineer_id": "eng_maria_gomez",
        },
    ).json()
    for task_index, task in enumerate(plan["tasks"]):
        fields.append((f"task[{task_index}].title", task["title"]))
        fields.append((f"task[{task_index}].description", task["description"]))
        for index, criterion in enumerate(task["acceptance_criteria"]):
            fields.append((f"task[{task_index}].acceptance_criteria[{index}]", criterion))

    assert fields, "the three narrative endpoints produced no prose fields to scan"

    offenders = [
        f"{label}: {phrase!r} in {text[:80]!r}"
        for label, text in fields
        for phrase in find_forbidden_phrases(text)
    ]
    assert not offenders, "\n".join(offenders)
