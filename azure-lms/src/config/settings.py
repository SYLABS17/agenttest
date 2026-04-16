"""Azure-specific application settings."""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Azure-specific settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "LMS (Azure)"
    app_version: str = "1.0.0"
    cloud_provider: Literal["azure"] = "azure"
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = False

    # Azure AI Search
    azure_search_endpoint: str = Field(default="")
    azure_search_api_key: str = Field(default="")
    azure_search_index_name: str = Field(default="curriculum-index")

    # Azure OpenAI
    azure_openai_endpoint: str = Field(default="")
    azure_openai_api_key: str = Field(default="")
    azure_openai_api_version: str = Field(default="2024-02-15-preview")
    azure_openai_embedding_deployment: str = Field(default="text-embedding-ada-002")
    azure_openai_chat_deployment: str = Field(default="gpt-4o")

    # Azure Translator
    azure_translator_endpoint: str = Field(default="")
    azure_translator_key: str = Field(default="")
    azure_translator_region: str = Field(default="centralindia")

    # Azure Blob Storage
    azure_storage_connection_string: str = Field(default="")
    azure_storage_container_name: str = Field(default="lms-content")

    # Azure Video Indexer
    azure_video_indexer_account_id: str = Field(default="")
    azure_video_indexer_location: str = Field(default="centralindia")

    # Translation Settings
    translation_confidence_threshold: float = Field(default=0.75)

    # Search Settings
    search_top_k: int = Field(default=50)
    search_rerank_top_k: int = Field(default=7)
    search_semantic_config: str = Field(default="curriculum-config")

    # Chunking Settings
    parent_chunk_size: int = Field(default=2000)
    child_chunk_size: int = Field(default=400)
    chunk_overlap: int = Field(default=50)

    # Generation Settings
    generation_temperature: float = Field(default=0.3)
    generation_max_tokens: int = Field(default=1500)

    # Performance
    cache_ttl_seconds: int = Field(default=3600)
    log_level: str = Field(default="INFO")

    @property
    def supported_languages(self) -> list[str]:
        """List of supported language codes."""
        return [
            "en", "hi", "ta", "te", "bn", "mr", "gu", "kn", "ml", "pa",
            "or", "as", "ur", "sa", "kok",
        ]


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
