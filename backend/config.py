"""Configuration module for AI Research System."""

import os
from pathlib import Path
from typing import Optional, Dict, Any
from pydantic_settings import BaseSettings
from pydantic import Field, validator
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Settings(BaseSettings):
    """Application settings with validation."""
    
    # Application Settings
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")
    api_env: str = Field(default="development", env="API_ENV")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # Azure OpenAI
    azure_openai_endpoint: Optional[str] = Field(default=None, env="AZURE_OPENAI_ENDPOINT")
    azure_openai_api_key: Optional[str] = Field(default=None, env="AZURE_OPENAI_API_KEY")
    azure_openai_deployment_name: str = Field(default="gpt-4", env="AZURE_OPENAI_DEPLOYMENT_NAME")
    azure_openai_api_version: str = Field(default="2024-02-15-preview", env="AZURE_OPENAI_API_VERSION")
    
    # Azure AI Search
    azure_search_endpoint: Optional[str] = Field(default=None, env="AZURE_SEARCH_ENDPOINT")
    azure_search_api_key: Optional[str] = Field(default=None, env="AZURE_SEARCH_API_KEY")
    azure_search_index_name: str = Field(default="research-index", env="AZURE_SEARCH_INDEX_NAME")
    
    # Bing Search
    bing_search_api_key: Optional[str] = Field(default=None, env="BING_SEARCH_API_KEY")
    bing_search_endpoint: str = Field(default="https://api.bing.microsoft.com/v7.0/search", env="BING_SEARCH_ENDPOINT")
    
    # Application Insights
    applicationinsights_connection_string: Optional[str] = Field(default=None, env="APPLICATIONINSIGHTS_CONNECTION_STRING")
    appinsights_instrumentationkey: Optional[str] = Field(default=None, env="APPINSIGHTS_INSTRUMENTATIONKEY")
    
    # Azure Storage
    azure_storage_connection_string: Optional[str] = Field(default=None, env="AZURE_STORAGE_CONNECTION_STRING")
    azure_storage_container_name: str = Field(default="research-data", env="AZURE_STORAGE_CONTAINER_NAME")
    
    # CORS Settings
    cors_origins: list = Field(default=["*"])
    cors_allow_credentials: bool = Field(default=True)
    cors_allow_methods: list = Field(default=["*"])
    cors_allow_headers: list = Field(default=["*"])
    
    # Agent Configuration
    max_agent_retries: int = Field(default=3)
    agent_timeout_seconds: int = Field(default=30)
    enable_agent_caching: bool = Field(default=True)
    cache_ttl_seconds: int = Field(default=3600)
    
    # Rate Limiting
    rate_limit_enabled: bool = Field(default=True)
    rate_limit_per_minute: int = Field(default=60)
    
    @validator("api_env")
    def validate_environment(cls, v):
        """Validate environment setting."""
        valid_envs = ["development", "test", "production"]
        if v not in valid_envs:
            raise ValueError(f"Invalid environment: {v}. Must be one of {valid_envs}")
        return v
    
    @validator("log_level")
    def validate_log_level(cls, v):
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Invalid log level: {v}. Must be one of {valid_levels}")
        return v.upper()
    
    def get_openai_config(self) -> Dict[str, Any]:
        """Get OpenAI configuration."""
        return {
            "api_type": "azure",
            "api_base": self.azure_openai_endpoint,
            "api_key": self.azure_openai_api_key,
            "api_version": self.azure_openai_api_version,
            "deployment_name": self.azure_openai_deployment_name
        }
    
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.api_env == "production"
    
    def is_development(self) -> bool:
        """Check if running in development."""
        return self.api_env == "development"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()


# Feature flags
class FeatureFlags:
    """Feature flags for the application."""
    
    ENABLE_CACHING = os.getenv("ENABLE_CACHING", "true").lower() == "true"
    ENABLE_METRICS = os.getenv("ENABLE_METRICS", "true").lower() == "true"
    ENABLE_TRACING = os.getenv("ENABLE_TRACING", "true").lower() == "true"
    ENABLE_RATE_LIMITING = os.getenv("ENABLE_RATE_LIMITING", "true").lower() == "true"
    ENABLE_DUMMY_MODE = os.getenv("ENABLE_DUMMY_MODE", "true").lower() == "true"  # For testing without Azure services
    

# Paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"
TEMP_DIR = BASE_DIR / "temp"

# Create directories if they don't exist
for dir_path in [DATA_DIR, LOGS_DIR, TEMP_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)