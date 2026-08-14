"""Add persistent in-app notifications.

Revision ID: 0009
Revises: 0008
Create Date: 2026-08-14 15:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0009"
down_revision: str | None = "0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the notification inbox table and lookup indexes."""
    op.create_table(
        "notifications",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("recipient_user_id", sa.Uuid(), nullable=False),
        sa.Column(
            "type",
            sa.Enum(
                "invitation.organization",
                "invitation.project",
                "project.membership",
                "project.updated",
                "task.assigned",
                "task.created",
                "task.status_changed",
                name="notification_type",
            ),
            nullable=False,
        ),
        sa.Column("title", sa.String(length=160), nullable=False),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("action_url", sa.String(length=2048), nullable=True),
        sa.Column("resource_type", sa.String(length=80), nullable=True),
        sa.Column("resource_id", sa.Uuid(), nullable=True),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["recipient_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_notifications_recipient_read_created",
        "notifications",
        ["recipient_user_id", "read_at", "created_at"],
    )
    op.create_index(
        "ix_notifications_recipient_created",
        "notifications",
        ["recipient_user_id", "created_at"],
    )
    op.create_index(
        "ix_notifications_resource",
        "notifications",
        ["resource_type", "resource_id"],
    )


def downgrade() -> None:
    """Remove persistent notification inbox state."""
    op.drop_index("ix_notifications_resource", table_name="notifications")
    op.drop_index("ix_notifications_recipient_created", table_name="notifications")
    op.drop_index("ix_notifications_recipient_read_created", table_name="notifications")
    op.drop_table("notifications")
    notification_type = sa.Enum(
        "invitation.organization",
        "invitation.project",
        "project.membership",
        "project.updated",
        "task.assigned",
        "task.created",
        "task.status_changed",
        name="notification_type",
    )
    notification_type.drop(op.get_bind(), checkfirst=True)
