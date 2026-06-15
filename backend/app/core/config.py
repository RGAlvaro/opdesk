from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
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

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
