"""GCP-specific application settings."""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """GCP-specific settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "LMS (GCP)"
    app_version: str = "1.0.0"
    cloud_provider: Literal["gcp"] = "gcp"
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = False

    # Google Cloud Project
    google_cloud_project: str = Field(default="")
    google_cloud_region: str = Field(default="asia-south1")

    # Vertex AI Search
    vertex_search_datastore_id: str = Field(default="")
    vertex_search_location: str = Field(default="global")

    # Vertex AI (Gemini)
    vertex_ai_location: str = Field(default="asia-south1")
    gemini_model: str = Field(default="gemini-2.0-flash")
    embedding_model: str = Field(default="text-embedding-005")

    # Cloud Translation
    translation_parent: str = Field(default="")
    glossary_id: str = Field(default="academic-glossary")

    # Cloud Storage
    gcs_bucket_name: str = Field(default="lms-content")
    gcs_frames_prefix: str = Field(default="frames/")

    # Video Intelligence
    video_location: str = Field(default="asia-south1")

    # Translation Settings
    translation_confidence_threshold: float = Field(default=0.75)

    # Search Settings
    search_top_k: int = Field(default=50)
    search_rerank_top_k: int = Field(default=7)

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
