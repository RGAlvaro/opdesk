"""Environment-backed settings for backend configuration."""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed configuration values loaded from environment variables or .env."""

    app_env: str = Field(default="local")
    debug: bool = Field(default=False)
    database_url: str = Field(
        default="postgresql+psycopg://opdesk:opdesk_dev_password@localhost:5432/opdesk"
    )
    auth_secret_key: str = Field(default="local_dev_change_me_min_32_chars")
    access_token_expire_minutes: int = Field(default=15)
    refresh_token_expire_days: int = Field(default=7)
    access_token_cookie_name: str = Field(default="access_token")
    refresh_token_cookie_name: str = Field(default="refresh_token")
    auth_cookie_secure: bool = Field(default=False)
    auth_cookie_samesite: Literal["lax", "strict", "none"] = Field(default="lax")
    celery_broker_url: str = Field(default="redis://localhost:6379/0")
    celery_result_backend: str = Field(default="redis://localhost:6379/1")
    celery_task_always_eager: bool = Field(default=False)
    celery_task_eager_propagates: bool = Field(default=True)
    email_notifications_enabled: bool = Field(default=True)
    email_delivery_provider: Literal["console", "resend"] = Field(default="console")
    public_app_url: str = Field(default="http://localhost:5173")
    resend_api_key: str | None = Field(default=None)
    resend_from_email: str | None = Field(default=None)
    email_provider_timeout_seconds: float = Field(default=5.0)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Return a cached settings object for dependency injection and startup code."""
    return Settings()
