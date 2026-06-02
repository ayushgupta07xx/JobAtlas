"""API settings, loaded from environment / .env via pydantic-settings."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = ""
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    search_default_limit: int = 20
    search_max_limit: int = 100


settings = Settings()
