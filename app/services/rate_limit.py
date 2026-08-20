import time
from collections import defaultdict, deque

from fastapi import HTTPException, status


class RateLimiter:
    """Process-local fallback limiter; Redis-backed deployments can replace this adapter."""

    def __init__(self) -> None:
        self.events: dict[str, deque[float]] = defaultdict(deque)

    def check(self, key: str, limit: int, window: int = 60) -> None:
        now = time.monotonic()
        bucket = self.events[key]
        while bucket and bucket[0] <= now - window:
            bucket.popleft()
        if len(bucket) >= limit:
            raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Rate limit exceeded")
        bucket.append(now)
