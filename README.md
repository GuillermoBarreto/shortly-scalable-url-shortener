# Shortly – Scalable URL Shortener

A fast, scalable URL shortener service built with FastAPI and Redis.

## Features
- Shortens long URLs into tiny links
- Fast redirection using Redis cache
- Tracks click analytics (IP + timestamp)
- Designed for scalability and easy deployment (Docker-ready)

## Tech Stack
- FastAPI (Python)
- Redis
- PostgreSQL or in-memory dict (starter)
- Docker (coming soon)

## Run Locally

```bash
uvicorn app.main:app --reload