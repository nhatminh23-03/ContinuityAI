"""Runtime configuration. docs/ARCHITECTURE.md section 49."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "local"
    log_level: str = "INFO"
    database_url: str = "sqlite:///./continuity.db"

    ai_provider: str = "none"
    ai_model: str = ""
    ai_api_key: str = ""

    # Shared contract fixtures, jointly owned. Contract decision CI-14.
    fixtures_path: Path = REPO_ROOT / "fixtures"


settings = Settings()
