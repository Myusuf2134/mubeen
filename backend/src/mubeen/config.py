from __future__ import annotations

from functools import lru_cache

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Known placeholder values that must never reach production.
_PLACEHOLDER_KEYS: frozenset[str] = frozenset(
    {
        "change-me",
        "change-me-in-production",
        "dev-secret-key-change-in-production",
        "your-secret-key-here",
        "replace-me",
        "secret",
        "changeme",
    }
)


class Settings(BaseSettings):
    # ".env" is checked first (backend-local override); "../.env" is the repo-root
    # .env used during local development and pytest runs from the backend/ directory.
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "postgresql+asyncpg://mubeen:mubeen@localhost:5432/mubeen"
    database_url_sync: str = "postgresql://mubeen:mubeen@localhost:5432/mubeen"
    # No default — must be supplied via SECRET_KEY env var or .env.
    # repr=False keeps the value out of __repr__ and structured log lines.
    secret_key: str = Field(repr=False)
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

    @model_validator(mode="after")
    def validate_secret_key(self) -> "Settings":
        """Fail fast when SECRET_KEY is missing or dangerously weak.

        All environments: key must be non-empty.
        Non-development environments: key must also be ≥ 32 chars and not a placeholder.
        The value is never included in the error message.
        """
        if not self.secret_key:
            raise ValueError(
                "SECRET_KEY is not set. "
                "Set it in your .env file or as an environment variable. "
                "Generate a strong value with: openssl rand -hex 32"
            )
        if self.environment != "development":
            if self.secret_key in _PLACEHOLDER_KEYS or len(self.secret_key) < 32:
                raise ValueError(
                    "SECRET_KEY is a placeholder or too short for a non-development environment "
                    "(minimum 32 characters required). "
                    "Generate a strong value with: openssl rand -hex 32"
                )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
