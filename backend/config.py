"""
Configuration management for AI Research System
"""

import os
from typing import Optional, List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, validator
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Application configuration settings"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    # Application Settings
    app_name: str = "AI Research System"
    app_version: str = "1.0.0"
    app_env: str = Field(default="development", alias="APP_ENV")
    app_debug: bool = Field(default=True, alias="APP_DEBUG")
    app_host: str = Field(default="0.0.0.0", alias="APP_HOST")
    app_port: int = Field(default=8000, alias="APP_PORT")
    
    # Azure Configuration
    azure_subscription_id: Optional[str] = Field(default=None, alias="AZURE_SUBSCRIPTION_ID")
    azure_resource_group: str = Field(default="ai-research-rg", alias="AZURE_RESOURCE_GROUP")
    azure_location: str = Field(default="eastus", alias="AZURE_LOCATION")
    
    # Azure OpenAI Configuration
    azure_openai_endpoint: Optional[str] = Field(default=None, alias="AZURE_OPENAI_ENDPOINT")
    azure_openai_api_key: Optional[str] = Field(default=None, alias="AZURE_OPENAI_API_KEY")
    azure_openai_deployment_name: str = Field(default="gpt-4", alias="AZURE_OPENAI_DEPLOYMENT_NAME")
    azure_openai_api_version: str = Field(default="2024-02-15-preview", alias="AZURE_OPENAI_API_VERSION")
    
    # Azure Cognitive Search Configuration
    azure_search_endpoint: Optional[str] = Field(default=None, alias="AZURE_SEARCH_ENDPOINT")
    azure_search_api_key: Optional[str] = Field(default=None, alias="AZURE_SEARCH_API_KEY")
    azure_search_index_name: str = Field(default="research-index", alias="AZURE_SEARCH_INDEX_NAME")
    
    # Bing Search Configuration
    bing_search_api_key: Optional[str] = Field(default=None, alias="BING_SEARCH_API_KEY")
    bing_search_endpoint: str = Field(
        default="https://api.bing.microsoft.com/v7.0/search",
        alias="BING_SEARCH_ENDPOINT"
    )
    
    # Azure Application Insights
    appinsights_instrumentation_key: Optional[str] = Field(
        default=None,
        alias="APPINSIGHTS_INSTRUMENTATION_KEY"
    )
    appinsights_connection_string: Optional[str] = Field(
        default=None,
        alias="APPINSIGHTS_CONNECTION_STRING"
    )
    
    # Azure Storage
    azure_storage_connection_string: Optional[str] = Field(
        default=None,
        alias="AZURE_STORAGE_CONNECTION_STRING"
    )
    
    # Security
    jwt_secret_key: str = Field(default="your-secret-key-change-in-production", alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_expiry_hours: int = Field(default=24, alias="JWT_EXPIRY_HOURS")
    
    # CORS Settings
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        alias="CORS_ORIGINS"
    )
    
    # Logging
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_format: str = Field(default="json", alias="LOG_FORMAT")
    log_output: str = Field(default="console,file,azure", alias="LOG_OUTPUT")
    
    # Agent Configuration
    agent_timeout_seconds: int = Field(default=30, alias="AGENT_TIMEOUT_SECONDS")
    agent_max_retries: int = Field(default=3, alias="AGENT_MAX_RETRIES")
    agent_retry_delay_seconds: int = Field(default=2, alias="AGENT_RETRY_DELAY_SECONDS")
    
    # Manager Agent Configuration
    manager_max_iterations: int = Field(default=5, alias="MANAGER_MAX_ITERATIONS")
    manager_temperature: float = Field(default=0.7, alias="MANAGER_TEMPERATURE")
    
    # Worker Agent Configuration
    worker_temperature: float = Field(default=0.5, alias="WORKER_TEMPERATURE")
    worker_max_tokens: int = Field(default=2000, alias="WORKER_MAX_TOKENS")
    
    # Evaluation Configuration
    evaluation_enabled: bool = Field(default=True, alias="EVALUATION_ENABLED")
    evaluation_metrics: List[str] = Field(
        default=["accuracy", "latency", "relevance", "completeness"],
        alias="EVALUATION_METRICS"
    )
    
    # Cache Configuration
    cache_enabled: bool = Field(default=True, alias="CACHE_ENABLED")
    cache_ttl_seconds: int = Field(default=3600, alias="CACHE_TTL_SECONDS")
    
    @validator("app_env")
    def validate_app_env(cls, v):
        allowed_envs = ["development", "test", "staging", "production"]
        if v not in allowed_envs:
            raise ValueError(f"app_env must be one of {allowed_envs}")
        return v
    
    @validator("cors_origins", pre=True)
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @validator("log_output", pre=True)
    def parse_log_output(cls, v):
        if isinstance(v, str):
            return v.lower()
        return v
    
    @validator("evaluation_metrics", pre=True)
    def parse_evaluation_metrics(cls, v):
        if isinstance(v, str):
            return [metric.strip() for metric in v.split(",")]
        return v
    
    @property
    def is_development(self) -> bool:
        """Check if running in development mode"""
        return self.app_env == "development"
    
    @property
    def is_production(self) -> bool:
        """Check if running in production mode"""
        return self.app_env == "production"
    
    @property
    def is_test(self) -> bool:
        """Check if running in test mode"""
        return self.app_env == "test"
    
    @property
    def azure_configured(self) -> bool:
        """Check if Azure services are properly configured"""
        return all([
            self.azure_openai_endpoint,
            self.azure_openai_api_key,
            self.azure_search_endpoint,
            self.azure_search_api_key,
        ])
    
    @property
    def observability_configured(self) -> bool:
        """Check if observability services are configured"""
        return bool(self.appinsights_instrumentation_key or self.appinsights_connection_string)
    
    def get_database_url(self) -> str:
        """Get database connection URL"""
        # Placeholder for future database configuration
        return "sqlite:///./research.db"
    
    def get_redis_url(self) -> str:
        """Get Redis connection URL for caching"""
        # Placeholder for future Redis configuration
        return "redis://localhost:6379"
    
    def validate_configuration(self) -> bool:
        """Validate that all required configuration is present"""
        errors = []
        
        if self.is_production:
            if not self.azure_configured:
                errors.append("Azure services not fully configured for production")
            if not self.observability_configured:
                errors.append("Observability not configured for production")
            if self.jwt_secret_key == "your-secret-key-change-in-production":
                errors.append("JWT secret key must be changed for production")
        
        if errors:
            for error in errors:
                logger.error(f"Configuration error: {error}")
            return False
        
        return True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    settings = Settings()
    
    # Log configuration status
    logger.info(f"Loading configuration for environment: {settings.app_env}")
    
    if not settings.validate_configuration():
        logger.warning("Configuration validation failed - some features may not work correctly")
    
    return settings


# Export settings instance
settings = get_settings()