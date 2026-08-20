from datetime import UTC, datetime, timedelta

from fastapi import APIRouter
from sqlalchemy import func, select

from app.api.dependencies import CurrentUser, SessionDep
from app.models import ClickEvent, Link

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats")
async def dashboard_stats(user: CurrentUser, session: SessionDep):
    total_links = (
        await session.scalar(select(func.count(Link.id)).where(Link.owner_id == user.id)) or 0
    )
    active_links = (
        await session.scalar(
            select(func.count(Link.id)).where(Link.owner_id == user.id, Link.is_active.is_(True))
        )
        or 0
    )
    total_clicks = (
        await session.scalar(
            select(func.coalesce(func.sum(Link.total_clicks), 0)).where(Link.owner_id == user.id)
        )
        or 0
    )
    since = datetime.now(UTC) - timedelta(days=14)
    trend = await session.execute(
        select(func.date(ClickEvent.timestamp), func.count())
        .join(Link)
        .where(Link.owner_id == user.id, ClickEvent.timestamp >= since)
        .group_by(func.date(ClickEvent.timestamp))
        .order_by(func.date(ClickEvent.timestamp))
    )
    top = await session.scalars(
        select(Link).where(Link.owner_id == user.id).order_by(Link.total_clicks.desc()).limit(5)
    )
    recent = await session.scalars(
        select(Link).where(Link.owner_id == user.id).order_by(Link.created_at.desc()).limit(5)
    )

    def compact(link: Link) -> dict:
        return {
            "id": str(link.id),
            "title": link.title,
            "short_code": link.short_code,
            "total_clicks": link.total_clicks,
            "is_active": link.is_active,
            "created_at": link.created_at,
        }

    return {
        "total_links": total_links,
        "active_links": active_links,
        "total_clicks": total_clicks,
        "click_trend": [{"date": str(day), "clicks": clicks} for day, clicks in trend],
        "top_links": [compact(x) for x in top],
        "recent_links": [compact(x) for x in recent],
    }
