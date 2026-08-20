import io
import math
from uuid import UUID

import qrcode
from fastapi import APIRouter, Query, Request, Response, status
from sqlalchemy import delete

from app.api.dependencies import CurrentUser, OptionalUser, SessionDep, SettingsDep
from app.models import Link
from app.repositories.links import LinkRepository
from app.schemas.links import LinkCreate, LinkResponse, LinkUpdate, Page
from app.services.analytics import link_analytics
from app.services.links import LinkService

router = APIRouter(prefix="/links", tags=["links"])


@router.post("", response_model=LinkResponse, status_code=201)
async def create_link(
    payload: LinkCreate,
    request: Request,
    session: SessionDep,
    settings: SettingsDep,
    user: OptionalUser,
):
    identity = str(user.id) if user else request.client.host if request.client else "unknown"
    request.app.state.limiter.check(f"shorten:{identity}", 20)
    service = LinkService(session, settings, request.app.state.cache)
    return service.response(await service.create(payload, user.id if user else None))


@router.get("", response_model=Page)
async def list_links(
    user: CurrentUser,
    session: SessionDep,
    settings: SettingsDep,
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = Query(None, max_length=120),
    active: bool | None = None,
):
    items, total = await LinkRepository(session).list_owned(
        user.id, page, page_size, search, active
    )
    service = LinkService(session, settings, request.app.state.cache)
    return Page(
        items=[service.response(link) for link in items],
        page=page,
        page_size=page_size,
        total=total,
        pages=math.ceil(total / page_size),
    )


@router.get("/{link_id}", response_model=LinkResponse)
async def get_link(
    link_id: UUID, user: CurrentUser, session: SessionDep, settings: SettingsDep, request: Request
):
    service = LinkService(session, settings, request.app.state.cache)
    return service.response(await service.owned(link_id, user.id))


@router.patch("/{link_id}", response_model=LinkResponse)
async def update_link(
    link_id: UUID,
    payload: LinkUpdate,
    user: CurrentUser,
    session: SessionDep,
    settings: SettingsDep,
    request: Request,
):
    service = LinkService(session, settings, request.app.state.cache)
    return service.response(await service.update(await service.owned(link_id, user.id), payload))


@router.delete("/{link_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_link(
    link_id: UUID, user: CurrentUser, session: SessionDep, settings: SettingsDep, request: Request
):
    service = LinkService(session, settings, request.app.state.cache)
    link = await service.owned(link_id, user.id)
    await request.app.state.cache.delete(link.short_code)
    await session.execute(delete(Link).where(Link.id == link.id))
    await session.commit()


@router.get("/{link_id}/qr")
async def qr_code(
    link_id: UUID, user: CurrentUser, session: SessionDep, settings: SettingsDep, request: Request
):
    service = LinkService(session, settings, request.app.state.cache)
    link = await service.owned(link_id, user.id)
    image = qrcode.make(f"{settings.public_base_url}/{link.short_code}")
    output = io.BytesIO()
    image.save(output, format="PNG")
    return Response(
        output.getvalue(),
        media_type="image/png",
        headers={"Cache-Control": "private, max-age=3600"},
    )


@router.get("/{link_id}/analytics")
async def analytics(
    link_id: UUID,
    user: CurrentUser,
    session: SessionDep,
    settings: SettingsDep,
    request: Request,
    days: int = Query(30, ge=1, le=365),
):
    service = LinkService(session, settings, request.app.state.cache)
    link = await service.owned(link_id, user.id)
    return {"link": service.response(link), **await link_analytics(session, link.id, days)}
