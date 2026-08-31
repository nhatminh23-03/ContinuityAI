"""Test fixtures.

The whole suite runs against a **freshly seeded database**, built once per session by the same
`scripts.seed_demo` a developer runs. Tests therefore exercise the real pipeline — ingestion, AI
extraction, aggregation, readiness, exposure, risk — rather than a hand-built fake. If seeding
breaks, every test fails, which is the correct signal.

The database file is redirected to a temporary path before any application module imports, so a
test run never touches `backend/continuity.db`.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURES = REPO_ROOT / "fixtures"

_TMP_DB = Path(tempfile.gettempdir()) / "continuityai_test.db"
os.environ["DATABASE_URL"] = f"sqlite:///{_TMP_DB}"
os.environ["AUTO_SEED"] = "false"

# The test suite never calls a model, whatever `backend/.env` says.
#
# This was a latent trap rather than a preference. `Settings` reads `.env`, so configuring any
# model-backed provider for the running app silently pointed the whole suite at a live gateway:
# `seed()` extracts once per artifact, so a single `pytest` run would have made 640 network calls,
# taken minutes, and cost money — and it would have started failing the moment a key expired or a
# quota ran out, for reasons having nothing to do with the code under test.
#
# Pinned here rather than documented, because a comment cannot stop it happening.
os.environ["AI_PROVIDER"] = "deterministic"


@pytest.fixture(scope="session", autouse=True)
def seeded_database():
    """Build the demo dataset once for the whole session."""
    from scripts.seed_demo import seed

    if _TMP_DB.exists():
        _TMP_DB.unlink()
    seed(verbose=False)
    yield
    if _TMP_DB.exists():
        _TMP_DB.unlink()


@pytest.fixture(scope="session")
def client(seeded_database):
    """Shared across the session.

    Safe even though the challenge tests reseed: each request opens its own session through the
    `get_session` dependency, so the client holds no database state of its own.
    """
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def session(seeded_database):
    """Function-scoped on purpose.

    `scripts.seed_demo` drops and recreates every table, and the challenge tests reseed to undo
    their own mutations. A session held open across that would keep referring to tables that no
    longer exist, which surfaced as `OperationalError` in unrelated modules — a test failure caused
    by fixture lifetime rather than by any behaviour under test.
    """
    from app.db.session import SessionLocal

    with SessionLocal() as db_session:
        yield db_session


def load_fixture(name: str) -> dict:
    """Read a shared contract fixture from the repository-root `fixtures/` directory.

    Jointly owned with the frontend (contract decision CI-14). Both sides validate against these
    same files, so a disagreement surfaces here rather than on integration day.
    """
    return json.loads((FIXTURES / f"{name}.json").read_text())
