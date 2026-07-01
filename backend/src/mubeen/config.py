from __future__ import annotations

from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://mubeen:mubeen@localhost:5432/mubeen"
    database_url_sync: str = "postgresql://mubeen:mubeen@localhost:5432/mubeen"
    secret_key: str = "dev-secret-key-change-in-production"
    deepgram_api_key: str = ""
    openai_api_key: str = ""
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:8000"]
    environment: str = "development"
    log_level: str = "INFO"

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        allowed = {"development", "production", "test"}
        if v not in allowed:
            raise ValueError(f"environment must be one of {allowed}")
        return v


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
