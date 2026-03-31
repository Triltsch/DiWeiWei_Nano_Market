"""Application configuration and settings"""

from functools import lru_cache
from typing import ClassVar, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, SecretStr, model_validator
from pydantic_settings import BaseSettings


class SMTPSettings(BaseModel):
    """Typed SMTP transport settings with TLS mode safety validation."""

    DEV_DEFAULT_HOST: ClassVar[str] = "mailpit"
    DEV_DEFAULT_USERNAME: ClassVar[str] = "mailpit"
    DEV_DEFAULT_PASSWORD: ClassVar[str] = "mailpit"
    DEV_DEFAULT_FROM_ADDRESS: ClassVar[str] = "no-reply@example.com"

    smtp_host: str
    smtp_port: int
    smtp_username: str
    smtp_password: SecretStr
    smtp_from_address: EmailStr
    smtp_from_name: str
    smtp_use_tls: bool = False
    smtp_use_starttls: bool = True
    smtp_connect_timeout_seconds: int = 10
    smtp_read_timeout_seconds: int = 30
    smtp_retry_max_attempts: int = 3
    smtp_retry_backoff_seconds: float = 2.0
    environment: str = "development"

    @model_validator(mode="after")
    def validate_transport_mode(self) -> "SMTPSettings":
        """Validate mutually-exclusive transport flags and production constraints."""
        if self.smtp_use_tls and self.smtp_use_starttls:
            raise ValueError(
                "Invalid SMTP configuration: SMTP_USE_TLS and SMTP_USE_STARTTLS cannot both be true."
            )

        if (
            not self.smtp_use_tls
            and not self.smtp_use_starttls
            and self.environment == "production"
        ):
            raise ValueError(
                "Invalid SMTP configuration: unencrypted SMTP mode is not allowed in production."
            )

        if self.environment == "production":
            uses_dev_defaults = (
                self.smtp_host == self.DEV_DEFAULT_HOST
                or self.smtp_username == self.DEV_DEFAULT_USERNAME
                or self.smtp_password.get_secret_value() == self.DEV_DEFAULT_PASSWORD
                or str(self.smtp_from_address) == self.DEV_DEFAULT_FROM_ADDRESS
            )
            if uses_dev_defaults:
                raise ValueError(
                    "Invalid SMTP configuration: production requires explicit SMTP_HOST, "
                    "SMTP_USERNAME, SMTP_PASSWORD, and SMTP_FROM_ADDRESS values (not development defaults)."
                )

        return self


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    model_config = ConfigDict(env_file=".env", case_sensitive=True, extra="ignore")

    # App settings
    APP_NAME: str = "DiWeiWei Nano-Marktplatz"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    ENV: str = "development"

    # Database settings
    DATABASE_URL: Optional[str] = None
    TEST_DB_URL: Optional[str] = None

    # JWT settings
    SECRET_KEY: Optional[str] = None
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Redis settings
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    REDIS_URL: Optional[str] = None

    # Email verification
    EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS: int = 24

    # SMTP settings
    SMTP_HOST: str = "mailpit"
    SMTP_PORT: int = 1025
    SMTP_USERNAME: str = "mailpit"
    SMTP_PASSWORD: SecretStr = SecretStr("mailpit")
    SMTP_FROM_ADDRESS: EmailStr = "no-reply@example.com"
    SMTP_FROM_NAME: str = "DiWeiWei Nano-Marktplatz"
    SMTP_USE_TLS: bool = False
    SMTP_USE_STARTTLS: bool = True
    SMTP_CONNECT_TIMEOUT_SECONDS: int = 10
    SMTP_READ_TIMEOUT_SECONDS: int = 30
    SMTP_RETRY_MAX_ATTEMPTS: int = 3
    SMTP_RETRY_BACKOFF_SECONDS: float = 2.0

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

    # Transport security and endpoint abuse protection
    SECURITY_ENFORCE_TLS: bool = False
    SECURITY_TLS_REDIRECT_INSECURE: bool = True
    SECURITY_TLS_PROTECTED_PATHS: str = "/api/v1/chats,/api/v1/auth/login"
    SECURITY_TRUSTED_PROXIES: str = "127.0.0.1,::1"
    SECURITY_ALLOWED_HOSTS: str = ""
    RATE_LIMIT_LOGIN_MAX_REQUESTS: int = 10
    RATE_LIMIT_LOGIN_WINDOW_SECONDS: int = 60
    RATE_LIMIT_CHAT_MESSAGE_MAX_REQUESTS: int = 30
    RATE_LIMIT_CHAT_MESSAGE_WINDOW_SECONDS: int = 60

    # MinIO settings
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET_NAME: str = "nanos"
    MINIO_ROOT_USER: Optional[str] = None
    MINIO_ROOT_PASSWORD: Optional[str] = None
    MINIO_IMAGE_TAG: Optional[str] = None
    MINIO_MC_IMAGE_TAG: Optional[str] = None
    MINIO_SECURE: bool = False  # Use HTTPS in production
    MINIO_REGION: str = "us-east-1"

    # Docker Compose database service settings
    POSTGRES_USER: Optional[str] = None
    POSTGRES_PASSWORD: Optional[str] = None
    POSTGRES_DB: Optional[str] = None

    # Meilisearch settings
    MEILI_URL: str = "http://localhost:7700"
    MEILI_MASTER_KEY: Optional[str] = None
    MEILI_INDEX_UID: str = "nanos_v1"

    # Search cache settings (Redis)
    SEARCH_CACHE_TTL_SECONDS: int = 1800  # 30 minutes
    SEARCH_CACHE_KEY_PREFIX: str = "search:v1"

    # Upload settings
    UPLOAD_MAX_RETRIES: int = 3
    UPLOAD_TIMEOUT_SECONDS: int = 600

    @model_validator(mode="after")
    def validate_smtp_transport_flags(self) -> "Settings":
        """Fail fast by delegating SMTP transport validation to SMTPSettings."""
        _ = self.smtp_settings

        return self

    @property
    def smtp_settings(self) -> SMTPSettings:
        """Return validated typed SMTP settings."""
        return SMTPSettings(
            smtp_host=self.SMTP_HOST,
            smtp_port=self.SMTP_PORT,
            smtp_username=self.SMTP_USERNAME,
            smtp_password=self.SMTP_PASSWORD,
            smtp_from_address=self.SMTP_FROM_ADDRESS,
            smtp_from_name=self.SMTP_FROM_NAME,
            smtp_use_tls=self.SMTP_USE_TLS,
            smtp_use_starttls=self.SMTP_USE_STARTTLS,
            smtp_connect_timeout_seconds=self.SMTP_CONNECT_TIMEOUT_SECONDS,
            smtp_read_timeout_seconds=self.SMTP_READ_TIMEOUT_SECONDS,
            smtp_retry_max_attempts=self.SMTP_RETRY_MAX_ATTEMPTS,
            smtp_retry_backoff_seconds=self.SMTP_RETRY_BACKOFF_SECONDS,
            environment=self.ENV,
        )


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance.

    Selects the appropriate database URL based on environment and availability:
    - If TEST_DB_URL is set, use it (Docker Compose PostgreSQL on port 5433)
    - If DATABASE_URL is set, use it (production/development config)
    - Otherwise, use a default suitable for the environment
    """
    settings = Settings()

    # Select database URL based on environment
    if settings.TEST_DB_URL:
        # Docker Compose test environment (port 5433)
        settings.DATABASE_URL = settings.TEST_DB_URL
    elif not settings.DATABASE_URL:
        # No DATABASE_URL provided, use default based on environment
        if settings.ENV == "test":
            # SQLite for unit tests (handled separately by conftest.py)
            settings.DATABASE_URL = "sqlite:///:memory:"
        else:
            # Default PostgreSQL for development
            settings.DATABASE_URL = "postgresql://user:password@localhost:5432/diwei_nano_market"

    if not settings.SECRET_KEY:
        if settings.ENV in ("development", "test"):
            settings.SECRET_KEY = "dev-unsafe-change-me"
        else:
            raise ValueError("SECRET_KEY must be set for production environments")

    if settings.SECRET_KEY == "change-me-in-production-use-env" and settings.ENV == "production":
        raise ValueError("SECRET_KEY must be replaced in production environments")

    return settings
