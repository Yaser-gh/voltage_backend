"""
Application configuration.

All runtime configuration is sourced from environment variables (12-factor
app style) via Pydantic's `BaseSettings`. Never hard-code secrets here.
"""
from functools import lru_cache
from typing import List

from pydantic import Field, PostgresDsn, RedisDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central application settings, loaded from environment / .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # ---------------------------------------------------------------- App
    APP_NAME: str = "Electrical Projects Management API"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = Field(default="development")  # development | staging | production
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    # ---------------------------------------------------------------- Server
    HOST: str = "0.0.0.0"
    PORT: int = 8443

    # ---------------------------------------------------------------- Security / JWT
    SECRET_KEY: str = Field(..., description="Used to sign access tokens")
    REFRESH_SECRET_KEY: str = Field(..., description="Used to sign refresh tokens, must differ from SECRET_KEY")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    REFRESH_TOKEN_EXPIRE_DAYS_REMEMBER_ME: int = 30
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int = 30

    # ---------------------------------------------------------------- Password hashing
    PASSWORD_HASH_SCHEME: str = "argon2"

    # ---------------------------------------------------------------- Database
    DATABASE_URL: PostgresDsn = Field(..., description="postgresql+asyncpg://user:pass@host:5432/db")
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_ECHO: bool = False

    # ---------------------------------------------------------------- Redis
    REDIS_URL: RedisDsn = Field(default="redis://localhost:6379/0")
    REDIS_CACHE_TTL_SECONDS: int = 300

    # ---------------------------------------------------------------- CORS
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]
    CORS_ALLOW_CREDENTIALS: bool = True

    # ---------------------------------------------------------------- Rate limiting
    RATE_LIMIT_DEFAULT: str = "100/minute"
    RATE_LIMIT_LOGIN: str = "5/minute"
    RATE_LIMIT_REGISTER: str = "3/minute"

    # ---------------------------------------------------------------- Uploads
    UPLOAD_DIR: str = "app/uploads"
    MAX_UPLOAD_SIZE_MB: int = 25
    ALLOWED_IMAGE_EXTENSIONS: List[str] = ["jpg", "jpeg", "png", "webp", "gif"]
    ALLOWED_DOCUMENT_EXTENSIONS: List[str] = ["pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx"]
    ALLOWED_ARCHIVE_EXTENSIONS: List[str] = ["zip", "rar", "7z"]
    ALLOWED_VIDEO_EXTENSIONS: List[str] = ["mp4", "mov", "avi", "mkv"]
    AVATAR_MAX_SIZE_MB: int = 5

    # ---------------------------------------------------------------- Logging
    LOG_LEVEL: str = "INFO"
    LOG_JSON: bool = True

    @field_validator("ENVIRONMENT")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        allowed = {"development", "staging", "production", "test"}
        if v not in allowed:
            raise ValueError(f"ENVIRONMENT must be one of {allowed}")
        return v

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"


@lru_cache
def get_settings() -> Settings:
    """Cached settings accessor, avoids re-parsing environment on every call."""
    return Settings()


settings = get_settings()
