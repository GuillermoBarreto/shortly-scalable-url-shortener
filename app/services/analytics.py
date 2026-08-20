from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from ua_parser import parse

from app.core.config import Settings
from app.core.security import visitor_hash
from app.models import ClickEvent, Link


def client_ip(headers: dict[str, str], direct_ip: str, settings: Settings) -> str:
    if settings.trust_proxy_headers:
        return headers.get("x-forwarded-for", direct_ip).split(",")[0].strip()
    return direct_ip


async def record_click(
    session: AsyncSession, link: Link, headers: dict[str, str], ip: str, settings: Settings
) -> None:
    agent = parse(headers.get("user-agent", ""))
    browser = agent.user_agent.family if agent.user_agent else "Unknown"
    os_name = agent.os.family if agent.os else "Unknown"
    device_family = agent.device.family if agent.device else "Other"
    device = (
        "Mobile"
        if "Mobile" in device_family
        else "Desktop"
        if device_family in {"Other", "Spider"}
        else "Tablet"
    )
    country = headers.get("cf-ipcountry") or headers.get("x-country-code")
    session.add(
        ClickEvent(
            link_id=link.id,
            referrer=headers.get("referer", "")[:500] or None,
            browser=browser[:80],
            operating_system=os_name[:80],
            device_category=device,
            country=country[:2].upper() if country else None,
            visitor_hash=visitor_hash(ip, settings),
        )
    )
    link.total_clicks += 1
    await session.commit()


async def link_analytics(session: AsyncSession, link_id: UUID, days: int = 30) -> dict:
    since = datetime.now(UTC) - timedelta(days=days)
    base = [ClickEvent.link_id == link_id, ClickEvent.timestamp >= since]
    trend_rows = await session.execute(
        select(func.date(ClickEvent.timestamp), func.count())
        .where(*base)
        .group_by(func.date(ClickEvent.timestamp))
        .order_by(func.date(ClickEvent.timestamp))
    )

    async def breakdown(column):
        rows = await session.execute(
            select(column, func.count())
            .where(*base)
            .group_by(column)
            .order_by(func.count().desc())
            .limit(10)
        )
        return [{"name": name or "Direct / unknown", "value": count} for name, count in rows]

    return {
        "clicks_over_time": [{"date": str(day), "clicks": count} for day, count in trend_rows],
        "referrers": await breakdown(ClickEvent.referrer),
        "browsers": await breakdown(ClickEvent.browser),
        "operating_systems": await breakdown(ClickEvent.operating_system),
        "devices": await breakdown(ClickEvent.device_category),
        "countries": await breakdown(ClickEvent.country),
    }
