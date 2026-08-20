from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.security import decode_token
from app.db.session import get_session
from app.models import User

bearer = HTTPBearer(auto_error=False)
SessionDep = Annotated[AsyncSession, Depends(get_session)]
SettingsDep = Annotated[Settings, Depends(get_settings)]


async def optional_user(
    request: Request, session: SessionDep, settings: SettingsDep
) -> User | None:
    credentials: HTTPAuthorizationCredentials | None = await bearer(request)
    if not credentials:
        return None
    payload = decode_token(credentials.credentials, "access", settings)
    try:
        user_id = UUID(payload["sub"])
    except (ValueError, KeyError) as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token subject") from exc
    return await session.scalar(select(User).where(User.id == user_id))


async def current_user(user: Annotated[User | None, Depends(optional_user)]) -> User:
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Authentication required")
    return user


CurrentUser = Annotated[User, Depends(current_user)]
OptionalUser = Annotated[User | None, Depends(optional_user)]
