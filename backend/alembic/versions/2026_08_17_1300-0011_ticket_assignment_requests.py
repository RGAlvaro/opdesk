"""Add ticket assignment handoff requests.

Revision ID: 0011
Revises: 0010
Create Date: 2026-08-17 13:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0011"
down_revision: str | None = "0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create persisted ticket handoff requests for target acceptance."""
    op.execute("ALTER TYPE notification_type ADD VALUE IF NOT EXISTS 'ticket.assignment_requested'")
    ticket_assignment_request_status = postgresql.ENUM(
        "pending",
        "accepted",
        "declined",
        name="ticket_assignment_request_status",
        create_type=False,
    )
    ticket_assignment_request_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "ticket_assignment_requests",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("task_id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("requested_by_id", sa.Uuid(), nullable=False),
        sa.Column("target_user_id", sa.Uuid(), nullable=False),
        sa.Column("status", ticket_assignment_request_status, nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("responded_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["requested_by_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["target_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_ticket_assignment_requests_task_id", "ticket_assignment_requests", ["task_id"]
    )
    op.create_index(
        "ix_ticket_assignment_requests_target_status",
        "ticket_assignment_requests",
        ["target_user_id", "status"],
    )
    op.create_index(
        "ix_ticket_assignment_requests_organization_project",
        "ticket_assignment_requests",
        ["organization_id", "project_id"],
    )


def downgrade() -> None:
    """Remove ticket handoff request persistence."""
    op.drop_index(
        "ix_ticket_assignment_requests_organization_project",
        table_name="ticket_assignment_requests",
    )
    op.drop_index(
        "ix_ticket_assignment_requests_target_status", table_name="ticket_assignment_requests"
    )
    op.drop_index("ix_ticket_assignment_requests_task_id", table_name="ticket_assignment_requests")
    op.drop_table("ticket_assignment_requests")
    ticket_assignment_request_status = postgresql.ENUM(
        "pending", "accepted", "declined", name="ticket_assignment_request_status"
    )
    ticket_assignment_request_status.drop(op.get_bind(), checkfirst=True)
