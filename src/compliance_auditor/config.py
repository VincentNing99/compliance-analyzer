"""
Configuration module using Pydantic Settings.

This module provides a Settings class that:
1. Reads configuration from environment variables (and .env file)
2. Validates that all required settings are present and correctly typed
3. Provides default values where appropriate

Usage:
    from compliance_auditor.config import get_settings

    settings = get_settings()
    print(settings.google_api_key)
"""

from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# Find the project root (where .env is located)
_PROJECT_ROOT = Path(__file__).parent.parent.parent
_ENV_FILE = _PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    """

    # LlamaCloud API Configuration
    llama_cloud_api_key: str  # Required - no default, must be set in .env

    # LlamaCloud Index Configuration
    llama_cloud_index_name: str = "compliance-auditor"
    llama_cloud_project_name: str = "Default"
    llama_cloud_organization_id: str | None = None  # Optional, for multi-org accounts

    # LlamaParse Configuration
    llama_parse_result_type: str = "markdown"  # "markdown" or "text"
    llama_parse_language: str = "en"

    # Gemini API Configuration
    google_api_key: str  # Required for Gemini LLM

    # Document Chunking Configuration (used as fallback)
    chunk_size: int = 1000  # Characters per chunk
    chunk_overlap: int = 200  # Overlap between consecutive chunks

    # Logging Configuration
    log_level: str = "INFO"

    # Pydantic Settings configuration
    model_config = SettingsConfigDict(
        # Use absolute path to .env file
        env_file=str(_ENV_FILE),
        # Environment variables are case-insensitive
        case_sensitive=False,
        # Allow extra fields in .env that aren't defined here
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """
    Get the application settings (cached).

    Uses lru_cache to ensure we only load settings once.
    This is a common pattern - settings don't change at runtime,
    so we cache the Settings instance.

    Returns:
        Settings: The application settings instance
    """
    return Settings()
