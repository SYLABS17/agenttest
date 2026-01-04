"""AWS-specific application settings."""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """AWS-specific settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "National LMS (AWS)"
    app_version: str = "1.0.0"
    cloud_provider: Literal["aws"] = "aws"
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = False

    # AWS Configuration
    aws_region: str = Field(default="ap-south-1")
    aws_access_key_id: str = Field(default="")
    aws_secret_access_key: str = Field(default="")

    # Amazon OpenSearch
    opensearch_endpoint: str = Field(default="")
    opensearch_index_name: str = Field(default="curriculum-index")

    # Amazon Bedrock
    bedrock_model_id: str = Field(default="anthropic.claude-3-sonnet-20240229-v1:0")
    bedrock_embedding_model_id: str = Field(default="amazon.titan-embed-text-v2:0")

    # Amazon Translate
    translate_terminology_name: str = Field(default="academic-glossary")

    # Amazon S3
    s3_bucket_name: str = Field(default="lms-content")
    s3_frames_prefix: str = Field(default="frames/")

    # Amazon Transcribe
    transcribe_language_code: str = Field(default="en-IN")

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
