from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    app_name: str = "Shortly"
    environment: str = "development"
    database_url: str = "sqlite+aiosqlite:///./shortly.db"
    redis_url: str | None = None
    secret_key: str = "development-only-secret-key-change-me"
    analytics_salt: str = "development-analytics-salt-change-me"
    public_base_url: str = "http://localhost:8000"
    frontend_url: str = "http://localhost:5173"
    cors_origins: list[str] = ["http://localhost:5173"]
    access_token_minutes: int = Field(15, ge=5, le=1440)
    refresh_token_days: int = Field(7, ge=1, le=30)
    max_request_bytes: int = Field(16_384, ge=1024, le=1_048_576)
    trust_proxy_headers: bool = False

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_origins(cls, value: object) -> object:
        return (
            [item.strip() for item in value.split(",") if item.strip()]
            if isinstance(value, str)
            else value
        )

    @field_validator("public_base_url", "frontend_url")
    @classmethod
    def trim_url(cls, value: str) -> str:
        return value.rstrip("/")


@lru_cache
def get_settings() -> Settings:
    return Settings()
