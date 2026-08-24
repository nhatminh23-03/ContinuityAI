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

    # Provider: `deterministic` (offline, reproducible), `cached` (replayed model extraction),
    # `watsonx` (IBM watsonx.ai) or `openrouter` (model-written narratives, rule-based extraction).
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

    # OpenRouter, an OpenAI-compatible gateway. Used the other way round from watsonx: extraction
    # stays deterministic and the model writes only the three manager-facing narratives, each of
    # which passes app/ai/validation.py before it can be returned. Credentials live in
    # backend/.env, which is gitignored.
    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_model: str = "anthropic/claude-sonnet-5"
    # AC-14 allows 12 seconds for an AI plan or explanation operation. `explain_candidate` is
    # issued once per *returned* candidate — app/recommendation/service.py narrates after the
    # `limit` slice — and the contract caps `limit` at 3, so three sequential calls is the bound
    # and the per-call ceiling is a third of the budget. Narrating inside the scoring loop instead
    # made that bound the number of eligible engineers, which is four on the seeded data and
    # capped by nothing. A slower answer is worth less than the template it falls back to.
    openrouter_timeout_seconds: float = 3.5
    # One attempt by default, for the same reason: a second call costs the rest of the budget and
    # buys a wording, while the template is already sitting there. Raise it where latency is not
    # budgeted.
    openrouter_max_retries: int = 0

    # The wall-clock ceiling on the narration phase of one request, enforced by app/ai/budget.py
    # rather than by the transport. `openrouter_timeout_seconds` above turned out not to bound a
    # call at all — httpx's read timeout bounds the gap between socket reads, and the gateway keeps
    # the socket warm while the model generates — so a real total has to be imposed by something
    # that can stop waiting. See OPEN-11.
    #
    # 8 seconds against AC-14's 12 for an AI explanation operation. The margin is for the rest of
    # the request: scoring, evidence reads, serialisation. Measured generation is about 6 seconds,
    # so a healthy call fits and a stalled one is cut off with the template in its place. Set to 0
    # to skip model narration entirely and always use the templates.
    narrative_deadline_seconds: float = 8.0
    # The contract caps `limit` at 3, so three is the most that is ever asked for at once.
    narrative_max_workers: int = 3

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
