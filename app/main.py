from fastapi import FastAPI
from app.routes import router

app = FastAPI(
    title="Shortly - Scalable URL Shortener",
    description="A fast, scalable URL shortening service with caching and analytics.",
    version="1.0.0"
)

app.include_router(router)