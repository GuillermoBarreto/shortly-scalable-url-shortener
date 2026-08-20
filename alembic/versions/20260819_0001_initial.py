"""Create users, links, and privacy-conscious click events."""

import sqlalchemy as sa

from alembic import op

revision = "20260819_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_table(
        "links",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("short_code", sa.String(64), nullable=False),
        sa.Column("original_url", sa.Text(), nullable=False),
        sa.Column("title", sa.String(120)),
        sa.Column("custom_alias", sa.String(64), unique=True),
        sa.Column("owner_id", sa.Uuid(), sa.ForeignKey("users.id")),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("total_clicks", sa.Integer(), nullable=False),
    )
    op.create_index("ix_links_short_code", "links", ["short_code"], unique=True)
    op.create_index("ix_links_owner_id", "links", ["owner_id"])
    op.create_index("ix_links_owner_created", "links", ["owner_id", "created_at"])
    op.create_index("ix_links_active_expires", "links", ["is_active", "expires_at"])
    op.create_index("ix_links_expires_at", "links", ["expires_at"])
    op.create_index("ix_links_is_active", "links", ["is_active"])
    op.create_table(
        "click_events",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "link_id", sa.Uuid(), sa.ForeignKey("links.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("referrer", sa.String(500)),
        sa.Column("browser", sa.String(80), nullable=False),
        sa.Column("operating_system", sa.String(80), nullable=False),
        sa.Column("device_category", sa.String(40), nullable=False),
        sa.Column("country", sa.String(2)),
        sa.Column("visitor_hash", sa.String(64), nullable=False),
    )
    op.create_index("ix_click_events_timestamp", "click_events", ["timestamp"])
    op.create_index("ix_click_events_visitor_hash", "click_events", ["visitor_hash"])
    op.create_index("ix_click_link_timestamp", "click_events", ["link_id", "timestamp"])


def downgrade():
    op.drop_table("click_events")
    op.drop_table("links")
    op.drop_table("users")
