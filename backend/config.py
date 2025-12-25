from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent
REPO_ROOT = BASE_DIR.parent
DEFAULT_DATA_DIR = REPO_ROOT / "test" / "data"
DEFAULT_REPORT_DIR = REPO_ROOT / "test" / "reports"


class AppConfig(BaseSettings):
    """Centralised configuration for the FastAPI service."""

    app_name: str = Field("Azure Research Orchestrator", description="Service display name.")
    environment: str = Field("dev", description="Deployment environment (dev/test/prod).")
    log_level: str = Field("INFO", description="Python logging level.")
    bing_api_key: Optional[str] = Field(default=None, description="Optional Bing Search API key.")
    azure_search_endpoint: Optional[str] = Field(default=None, description="Azure Cognitive Search endpoint.")
    azure_search_api_key: Optional[str] = Field(default=None, description="Azure Cognitive Search API key.")
    app_insights_connection_string: Optional[str] = Field(
        default=None, description="Application Insights connection string for telemetry export."
    )
    key_vault_uri: Optional[str] = Field(default=None, description="Azure Key Vault URI for secret resolution.")
    data_dir: Path = Field(default=DEFAULT_DATA_DIR, description="Directory holding dummy data payloads.")
    reports_dir: Path = Field(default=DEFAULT_REPORT_DIR, description="Directory where mock reports are persisted.")
    enable_mock_latency: bool = Field(
        default=True, description="Toggle to inject synthetic latency for agents when running locally."
    )
    default_timeout_seconds: int = Field(default=30, description="Default timeout for downstream calls.")

    model_config = SettingsConfigDict(
        env_file=REPO_ROOT / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


settings = AppConfig()
