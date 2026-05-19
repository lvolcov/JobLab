"""joblab API settings.

Purpose: typed access to environment-driven configuration.
Created: 2026-05-19
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Process configuration loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=None, extra="ignore")

    # Database
    database_url: str = Field(
        default="postgresql+psycopg://joblab:joblab@db:5432/joblab",
        alias="DATABASE_URL",
    )

    # Secrets
    fernet_key: str = Field(default="", alias="FERNET_KEY")
    jwt_secret: str = Field(default="", alias="JWT_SECRET")

    # CORS — comma-separated origins
    cors_origins_raw: str = Field(default="", alias="CORS_ORIGINS")

    # Seed admin (consumed by scripts/seed_admin.py in Prompt 3)
    admin_email: str = Field(default="admin@example.com", alias="ADMIN_EMAIL")
    admin_password: str = Field(default="", alias="ADMIN_PASSWORD")

    # Uploads
    max_upload_mb: int = Field(default=5, alias="MAX_UPLOAD_MB")

    # Optional global provider keys (used to bootstrap admin global keys)
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    anthropic_api_key: str = Field(default="", alias="ANTHROPIC_API_KEY")
    gemini_api_key: str = Field(default="", alias="GEMINI_API_KEY")

    @property
    def cors_origins(self) -> list[str]:
        """Parsed list of allowed CORS origins."""
        return [o.strip() for o in self.cors_origins_raw.split(",") if o.strip()]

    @property
    def sync_database_url(self) -> str:
        """Sync URL for Alembic. psycopg3 driver is sync by default with this prefix."""
        return self.database_url

    @property
    def async_database_url(self) -> str:
        """Async URL for the runtime engine."""
        url = self.database_url
        if url.startswith("postgresql+psycopg://"):
            return url
        if url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+psycopg://", 1)
        return url


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a process-wide cached Settings instance."""
    return Settings()
