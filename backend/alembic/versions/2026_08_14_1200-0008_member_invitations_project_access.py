"""Add invitations and explicit project memberships.

Revision ID: 0008
Revises: 0007
Create Date: 2026-08-14 12:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0008"
down_revision: str | None = "0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create invitation/project-membership tables and backfill existing access."""
    op.create_table(
        "invitations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("target_email", sa.String(length=320), nullable=False),
        sa.Column("target_user_id", sa.Uuid(), nullable=False),
        sa.Column(
            "role",
            postgresql.ENUM(
                "owner",
                "admin",
                "member",
                name="membership_role",
                create_type=False,
            ),
            nullable=True,
        ),
        sa.Column(
            "scope_type",
            sa.Enum("organization", "project", name="invitation_scope"),
            nullable=False,
        ),
        sa.Column("project_id", sa.Uuid(), nullable=True),
        sa.Column("invited_by_id", sa.Uuid(), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "pending",
                "accepted",
                "declined",
                "cancelled",
                "expired",
                name="invitation_status",
            ),
            nullable=False,
        ),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("declined_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["invited_by_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["target_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_invitations_organization_id", "invitations", ["organization_id"])
    op.create_index("ix_invitations_target_user_id", "invitations", ["target_user_id"])
    op.create_index("ix_invitations_project_id", "invitations", ["project_id"])
    op.create_index(
        "uq_pending_organization_invitation",
        "invitations",
        ["organization_id", "target_user_id"],
        unique=True,
        postgresql_where=sa.text("scope_type = 'organization' AND status = 'pending'"),
        sqlite_where=sa.text("scope_type = 'organization' AND status = 'pending'"),
    )
    op.create_index(
        "uq_pending_project_invitation",
        "invitations",
        ["project_id", "target_user_id"],
        unique=True,
        postgresql_where=sa.text("scope_type = 'project' AND status = 'pending'"),
        sqlite_where=sa.text("scope_type = 'project' AND status = 'pending'"),
    )

    op.create_table(
        "project_memberships",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("added_by_id", sa.Uuid(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["added_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project_id", "user_id", name="uq_project_memberships_project_user"),
    )
    op.create_index(
        "ix_project_memberships_organization_id",
        "project_memberships",
        ["organization_id"],
    )
    op.create_index("ix_project_memberships_project_id", "project_memberships", ["project_id"])
    op.create_index("ix_project_memberships_user_id", "project_memberships", ["user_id"])

    op.execute(
        sa.text(
            """
            INSERT INTO project_memberships (
                id,
                organization_id,
                project_id,
                user_id,
                added_by_id,
                created_at
            )
            SELECT
                (
                    substr(md5(projects.id::text || organization_memberships.user_id::text), 1, 8)
                    || '-' ||
                    substr(md5(projects.id::text || organization_memberships.user_id::text), 9, 4)
                    || '-' ||
                    substr(md5(projects.id::text || organization_memberships.user_id::text), 13, 4)
                    || '-' ||
                    substr(md5(projects.id::text || organization_memberships.user_id::text), 17, 4)
                    || '-' ||
                    substr(md5(projects.id::text || organization_memberships.user_id::text), 21, 12)
                )::uuid,
                projects.organization_id,
                projects.id,
                organization_memberships.user_id,
                NULL,
                now()
            FROM projects
            JOIN organization_memberships
              ON organization_memberships.organization_id = projects.organization_id
            ON CONFLICT (project_id, user_id) DO NOTHING
            """
        )
    )


def downgrade() -> None:
    """Remove invitation and explicit project membership persistence."""
    op.drop_index("ix_project_memberships_user_id", table_name="project_memberships")
    op.drop_index("ix_project_memberships_project_id", table_name="project_memberships")
    op.drop_index("ix_project_memberships_organization_id", table_name="project_memberships")
    op.drop_table("project_memberships")

    op.drop_index("uq_pending_project_invitation", table_name="invitations")
    op.drop_index("uq_pending_organization_invitation", table_name="invitations")
    op.drop_index("ix_invitations_project_id", table_name="invitations")
    op.drop_index("ix_invitations_target_user_id", table_name="invitations")
    op.drop_index("ix_invitations_organization_id", table_name="invitations")
    op.drop_table("invitations")

    invitation_status = sa.Enum(
        "pending",
        "accepted",
        "declined",
        "cancelled",
        "expired",
        name="invitation_status",
    )
    invitation_scope = sa.Enum("organization", "project", name="invitation_scope")
    invitation_status.drop(op.get_bind(), checkfirst=True)
    invitation_scope.drop(op.get_bind(), checkfirst=True)
