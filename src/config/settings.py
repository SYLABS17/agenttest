"""Application settings and configuration."""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "National LMS"
    app_version: str = "1.0.0"
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

    # Translation Settings
    translation_confidence_threshold: float = Field(default=0.75)
    translation_timeout_seconds: int = Field(default=10)

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

    # Video Processing
    video_segment_buffer_seconds: int = Field(default=5)
    video_frame_extraction_interval: int = Field(default=30)

    # Performance
    max_concurrent_requests: int = Field(default=100)
    request_timeout_seconds: int = Field(default=30)
    cache_ttl_seconds: int = Field(default=3600)

    # Monitoring
    enable_metrics: bool = Field(default=True)
    metrics_port: int = Field(default=9090)
    log_level: str = Field(default="INFO")

    # Supported Languages
    @property
    def supported_languages(self) -> list[str]:
        """List of supported language codes."""
        return [
            "en",  # English
            "hi",  # Hindi
            "ta",  # Tamil
            "te",  # Telugu
            "bn",  # Bengali
            "mr",  # Marathi
            "gu",  # Gujarati
            "kn",  # Kannada
            "ml",  # Malayalam
            "pa",  # Punjabi
            "or",  # Odia
            "as",  # Assamese
            "ur",  # Urdu
            "sa",  # Sanskrit
            "kok",  # Konkani
        ]

    @property
    def tier1_languages(self) -> list[str]:
        """High-resource languages with best support."""
        return ["en", "hi", "ta", "te", "bn"]

    @property
    def tier2_languages(self) -> list[str]:
        """Medium-resource languages."""
        return ["mr", "gu", "kn", "ml", "pa"]

    @property
    def tier3_languages(self) -> list[str]:
        """Emerging languages with limited resources."""
        return ["or", "as", "ur", "sa", "kok"]


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
