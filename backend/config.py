from functools import lru_cache
from pathlib import Path
from uuid import UUID

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parent / ".env",
        case_sensitive=True,
        extra="ignore",
    )

    APP_NAME: str = "Smart Transit Security Backend"
    APP_ENV: str = "development"
    API_V1_PREFIX: str = "/api/v1"
    SERVICE_VERSION: str = "1.0.0"
    SECRET_KEY: str = "change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/smart_transit"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    DATABASE_POOL_TIMEOUT: int = 30
    DATABASE_POOL_RECYCLE: int = 1800
    DATABASE_ECHO: bool = False
    CLIPS_BASE_DIR: str = "./clips"
    CORS_ORIGINS: str = "http://localhost:3000"
    LOG_LEVEL: str = "INFO"
    DEFAULT_CAMERA_ID: UUID = UUID("00000000-0000-0000-0000-000000000001")

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
