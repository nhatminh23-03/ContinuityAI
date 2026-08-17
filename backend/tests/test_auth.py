"""Optional shared-token authentication. RECOMMENDATIONS.md R-03.

Two properties matter, and the first matters most: **the default posture is unchanged**. The
frontend developer must not have to coordinate a secret to run the demo locally, so with no token
configured every endpoint stays open exactly as before.
"""

from __future__ import annotations

import pytest

from app.core.config import settings

TOKEN = "demo-token-not-a-secret"


@pytest.fixture()
def token_required(monkeypatch):
    """Turn the token requirement on for one test, then off again."""
    monkeypatch.setattr(settings, "api_token", TOKEN)
    yield TOKEN
    monkeypatch.setattr(settings, "api_token", "")


def test_the_api_is_open_when_no_token_is_configured(client) -> None:
    """The default. Nothing about local development or the frontend changes."""
    assert settings.api_token == ""
    assert client.get("/api/v1/platforms").status_code == 200


def test_health_is_never_gated(client, token_required) -> None:
    """Liveness has to answer without a credential, or a container cannot report ready."""
    assert client.get("/health").status_code == 200


def test_a_configured_token_is_required_on_the_api(client, token_required) -> None:
    response = client.get("/api/v1/platforms")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"
    # Same envelope as every other error, so the frontend still switches on `code`.
    assert "message" in response.json()["error"]


def test_a_valid_token_is_accepted(client, token_required) -> None:
    response = client.get(
        "/api/v1/platforms", headers={"Authorization": f"Bearer {token_required}"}
    )
    assert response.status_code == 200


def test_a_wrong_token_is_rejected(client, token_required) -> None:
    response = client.get("/api/v1/platforms", headers={"Authorization": "Bearer wrong"})
    assert response.status_code == 401


def test_a_missing_bearer_scheme_is_rejected(client, token_required) -> None:
    response = client.get("/api/v1/platforms", headers={"Authorization": token_required})
    assert response.status_code == 401


def test_the_requirement_covers_writes_as_well_as_reads(client, token_required) -> None:
    """Plan approval is the endpoint where an open API is least defensible: `approved_by` is a
    caller-supplied string, so without a credential anyone can approve as anyone."""
    response = client.post(
        "/api/v1/mitigation-plans",
        json={
            "capability_id": "cap_incident_recovery",
            "primary_engineer_id": "eng_alex_chen",
            "selected_backup_engineer_id": "eng_maria_gomez",
        },
    )
    assert response.status_code == 401
