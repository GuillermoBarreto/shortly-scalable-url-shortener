import re
from datetime import UTC, datetime
from uuid import UUID

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field, field_validator

RESERVED_ALIASES = {
    "api",
    "docs",
    "redoc",
    "openapi.json",
    "health",
    "ready",
    "login",
    "register",
    "dashboard",
    "links",
    "analytics",
    "admin",
    "static",
    "assets",
    "favicon.ico",
}
ALIAS_PATTERN = re.compile(r"^[a-z0-9](?:[a-z0-9_-]{1,62}[a-z0-9])?$")


def normalize_alias(value: str | None) -> str | None:
    if value is None:
        return None
    alias = value.strip().lower()
    if alias in RESERVED_ALIASES:
        raise ValueError("This alias is reserved")
    if not ALIAS_PATTERN.fullmatch(alias):
        raise ValueError("Alias must be 3-64 lowercase letters, numbers, hyphens, or underscores")
    return alias


class LinkCreate(BaseModel):
    original_url: AnyHttpUrl
    title: str | None = Field(None, max_length=120)
    custom_alias: str | None = None
    expires_at: datetime | None = None
    _alias = field_validator("custom_alias", mode="before")(normalize_alias)

    @field_validator("expires_at")
    @classmethod
    def future_expiry(cls, value: datetime | None) -> datetime | None:
        if value and (value if value.tzinfo else value.replace(tzinfo=UTC)) <= datetime.now(UTC):
            raise ValueError("Expiration must be in the future")
        return value


class LinkUpdate(BaseModel):
    original_url: AnyHttpUrl | None = None
    title: str | None = Field(None, max_length=120)
    custom_alias: str | None = None
    expires_at: datetime | None = None
    is_active: bool | None = None
    _alias = field_validator("custom_alias", mode="before")(normalize_alias)


class LinkResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    short_code: str
    original_url: str
    title: str | None
    custom_alias: str | None
    is_active: bool
    expires_at: datetime | None
    created_at: datetime
    updated_at: datetime
    total_clicks: int
    short_url: str | None = None


class Page(BaseModel):
    items: list[LinkResponse]
    page: int
    page_size: int
    total: int
    pages: int
