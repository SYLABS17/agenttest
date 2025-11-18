import os
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Configuration settings for the application, loaded from environment variables.
    """

    # --- LLM Provider ---
    # Use either OpenAI or Azure OpenAI
    openai_api_key: str = "default_openai_key"
    azure_openai_api_key: str | None = None
    azure_openai_endpoint: str | None = None
    azure_openai_deployment_name: str | None = None

    # --- LangSmith ---
    langsmith_api_key: str | None = None
    langsmith_project: str = "multi-agent-salary-analysis"

    # --- Data ---
    data_path: str = "data/employee_salary_analysis.csv"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    """
    Returns a cached instance of the Settings.
    """
    return Settings()

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()
