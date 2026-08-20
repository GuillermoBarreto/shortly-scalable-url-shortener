import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import jwt
from fastapi import HTTPException, status
from pwdlib import PasswordHash

from app.core.config import Settings

password_context = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return password_context.verify(password, password_hash)


def create_token(user_id: UUID, token_type: str, settings: Settings) -> str:
    lifetime = (
        timedelta(minutes=settings.access_token_minutes)
        if token_type == "access"
        else timedelta(days=settings.refresh_token_days)
    )
    now = datetime.now(UTC)
    return jwt.encode(
        {
            "sub": str(user_id),
            "type": token_type,
            "iat": now,
            "exp": now + lifetime,
            "jti": secrets.token_urlsafe(16),
        },
        settings.secret_key,
        algorithm="HS256",
    )


def decode_token(token: str, expected_type: str, settings: Settings) -> dict[str, Any]:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        if payload.get("type") != expected_type:
            raise ValueError("Unexpected token type")
        return payload
    except (jwt.PyJWTError, ValueError) as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token") from exc


def visitor_hash(ip: str, settings: Settings) -> str:
    day = datetime.now(UTC).date().isoformat()
    return hashlib.sha256(f"{settings.analytics_salt}:{day}:{ip}".encode()).hexdigest()
