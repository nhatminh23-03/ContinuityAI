"""Runtime configuration. docs/ARCHITECTURE.md section 49.

Note the deliberate absence of a ground-truth path. The hidden readiness labels under
`data/ground_truth/` are readable by the evaluation scripts only, never by application
runtime (docs/ARCHITECTURE.md section 40). `app/evaluation/ground_truth.py` resolves that
path itself, and `tests/test_ground_truth_isolation.py` enforces the boundary.
"""

from datetime import date
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "local"
    log_level: str = "INFO"
    database_url: str = f"sqlite:///{REPO_ROOT / 'backend' / 'continuity.db'}"

    ai_provider: str = "deterministic"
    ai_model: str = ""
    ai_api_key: str = ""

    # Shared contract fixtures, jointly owned. Contract decision CI-14.
    fixtures_path: Path = REPO_ROOT / "fixtures"

    # Seed inputs. The organisation structure and the generated artifacts are both
    # committed so a clean clone reproduces the demo exactly (PRD AC-15).
    data_path: Path = REPO_ROOT / "data"

    # Serve an empty database by seeding it on first boot. Keeps `uvicorn app.main:app`
    # a one-command start for the frontend developer.
    auto_seed: bool = True

    # Freshness is evaluated against this date so a seeded demo does not silently age
    # into different classifications between now and judging. Set to a real date to
    # observe drift. docs/DOMAIN_MODEL.md section 18.
    reference_date: date = date(2026, 8, 15)


settings = Settings()
