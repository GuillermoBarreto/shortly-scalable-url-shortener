import json
import logging
from dataclasses import asdict, dataclass
from datetime import UTC, datetime

from redis.asyncio import Redis

from app.core.config import Settings

logger = logging.getLogger(__name__)


@dataclass
class CachedLink:
    id: str
    destination: str
    active: bool
    expires_at: str | None


class CacheService:
    def __init__(self, settings: Settings):
        self.client = (
            Redis.from_url(settings.redis_url, decode_responses=True)
            if settings.redis_url
            else None
        )

    async def get(self, code: str) -> CachedLink | None:
        if not self.client:
            return None
        try:
            value = await self.client.get(f"link:{code}")
            return CachedLink(**json.loads(value)) if value else None
        except Exception:
            logger.warning("redis_unavailable", exc_info=True)
            return None

    async def set(self, code: str, value: CachedLink) -> None:
        if not self.client:
            return
        ttl = 3600
        if value.expires_at:
            expires = datetime.fromisoformat(value.expires_at)
            ttl = max(1, min(ttl, int((expires - datetime.now(UTC)).total_seconds())))
        try:
            await self.client.setex(f"link:{code}", ttl, json.dumps(asdict(value)))
        except Exception:
            logger.warning("redis_unavailable", exc_info=True)

    async def delete(self, *codes: str) -> None:
        if self.client and codes:
            try:
                await self.client.delete(*(f"link:{code}" for code in codes))
            except Exception:
                logger.warning("redis_unavailable", exc_info=True)

    async def close(self) -> None:
        if self.client:
            await self.client.aclose()
