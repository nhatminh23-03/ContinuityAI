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

FORBIDDEN_PHRASES = (
    "best employee",
    "cannot recover",
    "chance of failure",
    "probability of outage",
    "irreplaceable",
    "critical employee",
    "weak engineer",
    "low-value engineer",
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
    user-visible prose is produced."""
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
