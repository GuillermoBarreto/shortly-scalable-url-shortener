import os

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_shortly.db"
os.environ["SECRET_KEY"] = "test-secret-key-that-is-long-and-private"
os.environ["ANALYTICS_SALT"] = "test-analytics-salt"
os.environ["REDIS_URL"] = ""

import pytest_asyncio
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient

from app.db.base import Base
from app.db.session import engine
from app.main import app


@pytest_asyncio.fixture(autouse=True)
async def database():
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)
    yield


@pytest_asyncio.fixture
async def client():
    async with LifespanManager(app):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as http:
            yield http


@pytest_asyncio.fixture
async def auth(client):
    response = await client.post(
        "/api/v1/auth/register", json={"email": "dev@example.com", "password": "a-secure-password"}
    )
    return {"Authorization": f"Bearer {response.json()['access_token']}"}
