from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    APP_NAME: str = "Smart Transit Security Backend"
    SERVICE_VERSION: str = "0.1.0"
    DATABASE_URL: str = "sqlite+aiosqlite:///./transit_security.db"
    CLIPS_BASE_DIR: str = "clips"
    CORS_ORIGINS: str = "*"
    LOG_LEVEL: str = "INFO"

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
