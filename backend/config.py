from __future__ import annotations

from functools import lru_cache
from uuid import UUID

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    APP_NAME: str = "Smart Transit Security Backend"
    SERVICE_VERSION: str = "1.0.0"
    DATABASE_URL: str = "postgresql+asyncpg://postgres:root123@localhost:5432/smart_transit"
    CLIPS_BASE_DIR: str = "clips"
    CORS_ORIGINS: str = "*"
    LOG_LEVEL: str = "INFO"
    DEFAULT_CAMERA_ID: UUID = UUID("11111111-1111-4111-8111-111111111111")

    @property
    def cors_origins_list(self) -> list[str]:
        """Return CORS origins as a list for FastAPI middleware."""
        if self.CORS_ORIGINS == "*":
            return ["*"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]


@lru_cache
def get_settings() -> Settings:
    """Return the cached application settings instance."""
    return Settings()
