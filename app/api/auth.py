from uuid import UUID

from fastapi import APIRouter, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.api.dependencies import CurrentUser, SessionDep, SettingsDep
from app.core.security import create_token, decode_token, hash_password, verify_password
from app.models import User
from app.schemas.auth import LoginRequest, RefreshRequest, RegisterRequest, TokenPair
from app.schemas.users import UserResponse

router = APIRouter(prefix="/auth", tags=["authentication"])


def tokens(user: User, settings: SettingsDep) -> TokenPair:
    return TokenPair(
        access_token=create_token(user.id, "access", settings),
        refresh_token=create_token(user.id, "refresh", settings),
    )


@router.post("/register", response_model=TokenPair, status_code=201)
async def register(
    payload: RegisterRequest, request: Request, session: SessionDep, settings: SettingsDep
):
    request.app.state.limiter.check(
        f"register:{request.client.host if request.client else 'unknown'}", 5
    )
    user = User(email=str(payload.email).lower(), password_hash=hash_password(payload.password))
    session.add(user)
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(
            status.HTTP_409_CONFLICT, "An account with this email already exists"
        ) from exc
    await session.refresh(user)
    return tokens(user, settings)


@router.post("/login", response_model=TokenPair)
async def login(
    payload: LoginRequest, request: Request, session: SessionDep, settings: SettingsDep
):
    request.app.state.limiter.check(
        f"login:{request.client.host if request.client else 'unknown'}", 10
    )
    user = await session.scalar(select(User).where(User.email == str(payload.email).lower()))
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password")
    return tokens(user, settings)


@router.post("/refresh", response_model=TokenPair)
async def refresh(payload: RefreshRequest, session: SessionDep, settings: SettingsDep):
    data = decode_token(payload.refresh_token, "refresh", settings)
    user = await session.get(User, UUID(data["sub"]))
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User no longer exists")
    return tokens(user, settings)


@router.get("/me", response_model=UserResponse)
async def me(user: CurrentUser):
    return user


@router.post("/logout", status_code=204)
async def logout(_: CurrentUser):
    return None
