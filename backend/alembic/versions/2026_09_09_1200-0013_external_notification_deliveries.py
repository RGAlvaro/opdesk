"""Add external notification delivery audit rows.

Revision ID: 0013
Revises: 0012
Create Date: 2026-09-09 12:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0013"
down_revision: str | None = "0012"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create delivery audit enums, table, and retry indexes."""
    op.execute("ALTER TYPE notification_type ADD VALUE IF NOT EXISTS 'ticket.created'")

    delivery_channel = postgresql.ENUM(
        "email",
        name="notification_delivery_channel",
        create_type=False,
    )
    delivery_status = postgresql.ENUM(
        "pending",
        "sent",
        "failed",
        "suppressed",
        name="notification_delivery_status",
        create_type=False,
    )
    delivery_channel.create(op.get_bind(), checkfirst=True)
    delivery_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "notification_deliveries",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("notification_id", sa.Uuid(), nullable=False),
        sa.Column("recipient_user_id", sa.Uuid(), nullable=False),
        sa.Column("channel", delivery_channel, nullable=False),
        sa.Column("provider", sa.String(length=40), nullable=False),
        sa.Column("provider_message_id", sa.String(length=255), nullable=True),
        sa.Column("status", delivery_status, nullable=False),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_attempt_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_attempt_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error_code", sa.String(length=120), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["notification_id"], ["notifications.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["recipient_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "notification_id",
            "channel",
            name="uq_notification_deliveries_notification_channel",
        ),
    )
    op.create_index(
        "ix_notification_deliveries_recipient_created",
        "notification_deliveries",
        ["recipient_user_id", "created_at"],
    )
    op.create_index(
        "ix_notification_deliveries_notification_channel",
        "notification_deliveries",
        ["notification_id", "channel"],
    )
    op.create_index(
        "ix_notification_deliveries_status_next_attempt",
        "notification_deliveries",
        ["status", "next_attempt_at"],
    )


def downgrade() -> None:
    """Drop delivery audit storage and owned enum types."""
    op.drop_index(
        "ix_notification_deliveries_status_next_attempt",
        table_name="notification_deliveries",
    )
    op.drop_index(
        "ix_notification_deliveries_notification_channel",
        table_name="notification_deliveries",
    )
    op.drop_index(
        "ix_notification_deliveries_recipient_created",
        table_name="notification_deliveries",
    )
    op.drop_table("notification_deliveries")
    postgresql.ENUM(name="notification_delivery_status").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="notification_delivery_channel").drop(op.get_bind(), checkfirst=True)
