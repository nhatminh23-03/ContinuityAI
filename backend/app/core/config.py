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

    # Extraction provider: `deterministic` (offline, reproducible) or `watsonx` (IBM watsonx.ai).
    ai_provider: str = "deterministic"
    ai_model: str = ""
    ai_api_key: str = ""

    # IBM watsonx.ai. Credentials live in backend/.env, which is gitignored; nothing here has a
    # real default, so a missing credential fails loudly rather than silently degrading.
    watsonx_api_key: str = ""
    watsonx_project_id: str = ""
    watsonx_api_url: str = "https://us-south.ml.cloud.ibm.com"
    watsonx_model_id: str = "ibm/granite-4-h-small"
    # A model call is slower and less predictable than a rule. Bound both.
    watsonx_timeout_seconds: float = 60.0
    watsonx_max_retries: int = 2
    # Hard service ceiling per instance — 2/s on the plan this was developed against. Exceeding it
    # returns 429 for the whole burst, so the client paces itself rather than discovering the limit.
    watsonx_requests_per_second: float = 2.0

    # Shared contract fixtures, jointly owned. Contract decision CI-14.
    fixtures_path: Path = REPO_ROOT / "fixtures"

    # Seed inputs. The organisation structure and the generated artifacts are both
    # committed so a clean clone reproduces the demo exactly (PRD AC-15).
    data_path: Path = REPO_ROOT / "data"

    # Serve an empty database by seeding it on first boot. Keeps `uvicorn app.main:app`
    # a one-command start for the frontend developer.
    auto_seed: bool = True

    # Optional shared bearer token. Empty by default, which leaves the API open exactly as it was —
    # the frontend is unaffected and nobody has to coordinate a secret to run the demo locally.
    # Set it before exposing the API beyond localhost. Enterprise IAM is deliberately out of MVP
    # scope (ARCHITECTURE.md section 50); this is the minimum that makes "the manager approves"
    # mean something. See RECOMMENDATIONS.md R-03.
    api_token: str = ""

    # Freshness is evaluated against this date so a seeded demo does not silently age
    # into different classifications between now and judging. Set to a real date to
    # observe drift. docs/DOMAIN_MODEL.md section 18.
    reference_date: date = date(2026, 8, 15)


settings = Settings()
