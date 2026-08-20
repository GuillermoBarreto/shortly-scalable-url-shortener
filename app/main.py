import logging
from contextlib import asynccontextmanager
from uuid import UUID

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy import text

from app.api import auth, dashboard, links
from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models import Link
from app.repositories.links import LinkRepository
from app.services.analytics import client_ip, record_click
from app.services.cache import CachedLink, CacheService
from app.services.links import LinkService
from app.services.rate_limit import RateLimiter

settings = get_settings()
logging.basicConfig(
    level=logging.INFO,
    format='{"time":"%(asctime)s","level":"%(levelname)s","logger":"%(name)s","message":"%(message)s"}',
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.cache = CacheService(settings)
    app.state.limiter = RateLimiter()
    yield
    await app.state.cache.close()


app = FastAPI(
    title="Shortly API",
    summary="Secure URL management and privacy-conscious analytics",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)
app.include_router(auth.router, prefix="/api/v1")
app.include_router(links.router, prefix="/api/v1")
app.include_router(dashboard.router, prefix="/api/v1")


@app.middleware("http")
async def request_size_limit(request: Request, call_next):
    length = request.headers.get("content-length")
    if length and int(length) > settings.max_request_bytes:
        return JSONResponse(status_code=413, content={"detail": "Request body is too large"})
    return await call_next(request)


@app.get("/health", tags=["operations"])
async def health():
    return {"status": "ok"}


@app.get("/ready", tags=["operations"])
async def ready():
    try:
        async with SessionLocal() as session:
            await session.execute(text("SELECT 1"))
        return {"status": "ready", "database": "ok"}
    except Exception as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Database unavailable") from exc


@app.get("/{short_code}", include_in_schema=False)
async def redirect(short_code: str, request: Request):
    request.app.state.limiter.check(
        f"redirect:{request.client.host if request.client else 'unknown'}", 120
    )
    cached = await request.app.state.cache.get(short_code)
    async with SessionLocal() as session:
        link: Link | None = None
        if cached:
            link = await session.get(Link, UUID(cached.id))
        if not link:
            link = await LinkRepository(session).by_code(short_code)
        if not link:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Short link not found")
        reason = LinkService.unavailable(link)
        if reason:
            return JSONResponse(
                status_code=410,
                content={"detail": f"This short link is {reason}", "reason": reason},
            )
        await request.app.state.cache.set(
            short_code,
            CachedLink(
                id=str(link.id),
                destination=link.original_url,
                active=link.is_active,
                expires_at=link.expires_at.isoformat() if link.expires_at else None,
            ),
        )
        ip = client_ip(
            dict(request.headers), request.client.host if request.client else "unknown", settings
        )
        await record_click(session, link, dict(request.headers), ip, settings)
        return RedirectResponse(link.original_url, status_code=307)
