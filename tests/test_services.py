import pytest
from fastapi import HTTPException

from app.core.config import Settings
from app.schemas.links import LinkCreate
from app.services.cache import CacheService
from app.services.rate_limit import RateLimiter


def test_rate_limit():
    limiter = RateLimiter()
    limiter.check("test", 2)
    limiter.check("test", 2)
    with pytest.raises(HTTPException) as exc:
        limiter.check("test", 2)
    assert exc.value.status_code == 429


async def test_redis_unavailable_falls_back():
    cache = CacheService(Settings(redis_url="redis://127.0.0.1:1", secret_key="x" * 32))
    assert await cache.get("missing") is None
    await cache.delete("missing")
    await cache.close()


def test_expiration_must_be_future():
    with pytest.raises(ValueError):
        LinkCreate(original_url="https://example.com", expires_at="2000-01-01T00:00:00Z")
