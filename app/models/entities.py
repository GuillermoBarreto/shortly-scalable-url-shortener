import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def utc_now() -> datetime:
    return datetime.now(UTC)


class User(Base):
    __tablename__ = "users"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )
    links: Mapped[list["Link"]] = relationship(back_populates="owner", cascade="all, delete")


class Link(Base):
    __tablename__ = "links"
    __table_args__ = (
        Index("ix_links_owner_created", "owner_id", "created_at"),
        Index("ix_links_active_expires", "is_active", "expires_at"),
    )
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    short_code: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    original_url: Mapped[str] = mapped_column(Text)
    title: Mapped[str | None] = mapped_column(String(120))
    custom_alias: Mapped[str | None] = mapped_column(String(64), unique=True)
    owner_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )
    total_clicks: Mapped[int] = mapped_column(Integer, default=0)
    owner: Mapped[User | None] = relationship(back_populates="links")
    clicks: Mapped[list["ClickEvent"]] = relationship(
        back_populates="link", cascade="all, delete-orphan"
    )


class ClickEvent(Base):
    __tablename__ = "click_events"
    __table_args__ = (Index("ix_click_link_timestamp", "link_id", "timestamp"),)
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    link_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("links.id", ondelete="CASCADE"))
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, index=True
    )
    referrer: Mapped[str | None] = mapped_column(String(500))
    browser: Mapped[str] = mapped_column(String(80), default="Unknown")
    operating_system: Mapped[str] = mapped_column(String(80), default="Unknown")
    device_category: Mapped[str] = mapped_column(String(40), default="Unknown")
    country: Mapped[str | None] = mapped_column(String(2))
    visitor_hash: Mapped[str] = mapped_column(String(64), index=True)
    link: Mapped[Link] = relationship(back_populates="clicks")
