from datetime import datetime
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Link


class LinkRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def by_code(self, code: str) -> Link | None:
        return await self.session.scalar(select(Link).where(Link.short_code == code))

    async def owned(self, link_id: UUID, owner_id: UUID) -> Link | None:
        return await self.session.scalar(
            select(Link).where(Link.id == link_id, Link.owner_id == owner_id)
        )

    async def list_owned(
        self, owner_id: UUID, page: int, size: int, search: str | None, active: bool | None
    ) -> tuple[list[Link], int]:
        filters = [Link.owner_id == owner_id]
        if search:
            filters.append(
                or_(
                    Link.title.ilike(f"%{search}%"),
                    Link.short_code.ilike(f"%{search}%"),
                    Link.original_url.ilike(f"%{search}%"),
                )
            )
        if active is not None:
            filters.append(Link.is_active == active)
        total = await self.session.scalar(select(func.count(Link.id)).where(*filters)) or 0
        rows = await self.session.scalars(
            select(Link)
            .where(*filters)
            .order_by(Link.created_at.desc())
            .offset((page - 1) * size)
            .limit(size)
        )
        return list(rows), total

    async def create(
        self,
        *,
        code: str,
        url: str,
        title: str | None,
        alias: str | None,
        expires_at: datetime | None,
        owner_id: UUID | None,
    ) -> Link:
        link = Link(
            short_code=code,
            original_url=url,
            title=title,
            custom_alias=alias,
            expires_at=expires_at,
            owner_id=owner_id,
        )
        self.session.add(link)
        await self.session.flush()
        return link
