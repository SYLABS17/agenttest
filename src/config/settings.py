"""Azure AI Foundry + Voice Live settings."""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Settings for Azure AI Foundry and Voice Live."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "LMS"
    app_version: str = "1.0.0"
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = False
    log_level: str = "INFO"

    # Azure AI Foundry
    azure_ai_project_connection_string: str = Field(default="")

    # Azure AI Search
    azure_search_index_name: str = Field(default="lms-index")

    # Azure Speech (Voice Live)
    azure_speech_key: str = Field(default="")
    azure_speech_region: str = Field(default="eastus")

    # Model Settings
    chat_model: str = Field(default="gpt-4o")

    # Generation Settings
    generation_temperature: float = Field(default=0.3)
    generation_max_tokens: int = Field(default=1500)


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
