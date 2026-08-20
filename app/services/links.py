import secrets
import string
from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.models import Link
from app.repositories.links import LinkRepository
from app.schemas.links import LinkCreate, LinkResponse, LinkUpdate
from app.services.cache import CacheService

ALPHABET = string.ascii_letters + string.digits


class LinkService:
    def __init__(self, session: AsyncSession, settings: Settings, cache: CacheService):
        self.session = session
        self.settings = settings
        self.cache = cache
        self.repo = LinkRepository(session)

    def response(self, link: Link) -> LinkResponse:
        result = LinkResponse.model_validate(link)
        result.short_url = f"{self.settings.public_base_url}/{link.short_code}"
        return result

    async def create(self, payload: LinkCreate, owner_id: UUID | None) -> Link:
        alias = payload.custom_alias
        for _ in range(5):
            code = alias or "".join(secrets.choice(ALPHABET) for _ in range(7))
            try:
                link = await self.repo.create(
                    code=code,
                    url=str(payload.original_url),
                    title=payload.title,
                    alias=alias,
                    expires_at=payload.expires_at,
                    owner_id=owner_id,
                )
                await self.session.commit()
                await self.session.refresh(link)
                return link
            except IntegrityError as exc:
                await self.session.rollback()
                if alias:
                    raise HTTPException(
                        status.HTTP_409_CONFLICT, "Custom alias is already in use"
                    ) from exc
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Could not allocate a short code")

    async def owned(self, link_id: UUID, owner_id: UUID) -> Link:
        link = await self.repo.owned(link_id, owner_id)
        if not link:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Link not found")
        return link

    async def update(self, link: Link, payload: LinkUpdate) -> Link:
        old_code = link.short_code
        changes = payload.model_dump(exclude_unset=True)
        if "original_url" in changes:
            changes["original_url"] = str(changes["original_url"])
        if "custom_alias" in changes and changes["custom_alias"]:
            changes["short_code"] = changes["custom_alias"]
        for key, value in changes.items():
            setattr(link, key, value)
        try:
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise HTTPException(status.HTTP_409_CONFLICT, "Custom alias is already in use") from exc
        await self.session.refresh(link)
        await self.cache.delete(old_code, link.short_code)
        return link

    @staticmethod
    def unavailable(link: Link) -> str | None:
        if not link.is_active:
            return "disabled"
        expires = link.expires_at
        if expires:
            expires = expires if expires.tzinfo else expires.replace(tzinfo=UTC)
            if expires <= datetime.now(UTC):
                return "expired"
        return None
