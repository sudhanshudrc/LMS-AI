"""Application configuration settings."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings read from environment variables or .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database
    database_url: str = (
        "postgresql+asyncpg://postgres:postgres_secure_password@localhost:5432/lms_db"
    )
    db_pool_pre_ping: bool = True
    db_pool_size: int = 10
    db_max_overflow: int = 20

    # AI & Services
    gemini_api_key: str = ""
    api_port: int = 8000
    app_env: str = "development"


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings singleton."""
    return Settings()
