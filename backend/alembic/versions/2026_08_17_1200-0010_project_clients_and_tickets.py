"""Add restricted client accounts and ticket comments.

Revision ID: 0010
Revises: 0009
Create Date: 2026-08-17 12:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0010"
down_revision: str | None = "0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create client access and ticket-comment persistence."""
    user_account_type = sa.Enum("internal", "client", name="user_account_type")
    user_account_type.create(op.get_bind(), checkfirst=True)
    op.add_column(
        "users",
        sa.Column(
            "account_type",
            user_account_type,
            server_default="internal",
            nullable=False,
        ),
    )
    op.alter_column("users", "account_type", server_default=None)

    op.add_column("tasks", sa.Column("client_user_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        "fk_tasks_client_user_id_users",
        "tasks",
        "users",
        ["client_user_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.execute("ALTER TYPE task_type ADD VALUE IF NOT EXISTS 'ticket'")
    op.execute("ALTER TYPE notification_type ADD VALUE IF NOT EXISTS 'ticket.comment'")

    op.create_table(
        "project_client_accesses",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("client_user_id", sa.Uuid(), nullable=False),
        sa.Column("granted_by_id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["client_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["granted_by_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "project_id", "client_user_id", name="uq_project_client_access_project_client"
        ),
    )
    op.create_index(
        "ix_project_client_accesses_organization_id",
        "project_client_accesses",
        ["organization_id"],
    )
    op.create_index(
        "ix_project_client_accesses_project_id", "project_client_accesses", ["project_id"]
    )
    op.create_index(
        "ix_project_client_accesses_client_user_id",
        "project_client_accesses",
        ["client_user_id"],
    )

    op.create_table(
        "ticket_comments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("task_id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("author_user_id", sa.Uuid(), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["author_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ticket_comments_task_created", "ticket_comments", ["task_id", "created_at"])
    op.create_index("ix_ticket_comments_organization_id", "ticket_comments", ["organization_id"])
    op.create_index("ix_ticket_comments_project_id", "ticket_comments", ["project_id"])
    op.create_index("ix_ticket_comments_author_user_id", "ticket_comments", ["author_user_id"])


def downgrade() -> None:
    """Remove client ticket data structures."""
    op.drop_index("ix_ticket_comments_author_user_id", table_name="ticket_comments")
    op.drop_index("ix_ticket_comments_project_id", table_name="ticket_comments")
    op.drop_index("ix_ticket_comments_organization_id", table_name="ticket_comments")
    op.drop_index("ix_ticket_comments_task_created", table_name="ticket_comments")
    op.drop_table("ticket_comments")
    op.drop_index("ix_project_client_accesses_client_user_id", table_name="project_client_accesses")
    op.drop_index("ix_project_client_accesses_project_id", table_name="project_client_accesses")
    op.drop_index(
        "ix_project_client_accesses_organization_id", table_name="project_client_accesses"
    )
    op.drop_table("project_client_accesses")
    op.drop_constraint("fk_tasks_client_user_id_users", "tasks", type_="foreignkey")
    op.drop_column("tasks", "client_user_id")
    op.drop_column("users", "account_type")
    user_account_type = sa.Enum("internal", "client", name="user_account_type")
    user_account_type.drop(op.get_bind(), checkfirst=True)
