"""Application configuration and settings"""

from functools import lru_cache
from typing import Optional

from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    model_config = ConfigDict(env_file=".env", case_sensitive=True)

    # App settings
    APP_NAME: str = "DiWeiWei Nano-Marktplatz"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    ENV: str = "development"

    # Database settings
    DATABASE_URL: str = "postgresql://user:password@localhost/diwei_nano_market"

    # JWT settings
    SECRET_KEY: Optional[str] = None
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Email verification
    EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS: int = 24

    # Account security
    MAX_LOGIN_ATTEMPTS: int = 3
    ACCOUNT_LOCKOUT_DURATION_MINUTES: int = 60

    # Password policy
    MIN_PASSWORD_LENGTH: int = 8
    REQUIRE_SPECIAL_CHAR: bool = True
    REQUIRE_DIGIT: bool = True
    REQUIRE_UPPERCASE: bool = True

    # Session settings
    SESSION_TIMEOUT_MINUTES: int = 30


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance"""
    settings = Settings()

    if not settings.SECRET_KEY:
        if settings.ENV in ("development", "test"):
            settings.SECRET_KEY = "dev-unsafe-change-me"
        else:
            raise ValueError("SECRET_KEY must be set for production environments")

    if settings.SECRET_KEY == "change-me-in-production-use-env" and settings.ENV == "production":
        raise ValueError("SECRET_KEY must be replaced in production environments")

    return settings
