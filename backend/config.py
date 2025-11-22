from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import List, Optional

from pydantic import BaseSettings, Field


BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent


class Settings(BaseSettings):
  environment: str = Field(default="dev", env="ENVIRONMENT")
  allowed_origins_raw: str = Field(default="*", env="ALLOW_ORIGINS")
  appinsights_connection_string: Optional[str] = Field(default=None, env="APPINSIGHTS_CONNECTION_STRING")

  bing_fixture_path: Path = Field(
      default=ROOT_DIR / "test" / "data" / "bing_results.json",
      env="BING_FIXTURE_PATH",
  )
  ai_search_fixture_path: Path = Field(
      default=ROOT_DIR / "test" / "data" / "ai_search_results.json",
      env="AI_SEARCH_FIXTURE_PATH",
  )
  reports_dir: Path = Field(default=ROOT_DIR / "test" / "reports", env="REPORTS_DIR")

  api_host: str = Field(default="0.0.0.0", env="FASTAPI_HOST")
  api_port: int = Field(default=8080, env="FASTAPI_PORT")
  default_timeout_seconds: int = Field(default=20, env="DEFAULT_TIMEOUT_SECONDS")

  class Config:
    env_file = ROOT_DIR / ".env"
    env_file_encoding = "utf-8"

  @property
  def allowed_origins(self) -> List[str]:
    if self.allowed_origins_raw.strip() == "*":
      return ["*"]
    return [origin.strip() for origin in self.allowed_origins_raw.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
  return Settings()
