"""Create organizations and organization memberships.

Revision ID: 0003
Revises: 0002
Create Date: 2026-06-18 10:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

membership_role = sa.Enum("owner", "admin", "member", name="membership_role")


def upgrade() -> None:
    """Create tenant workspaces, memberships, constraints, and lookup indexes."""
    op.create_table(
        "organizations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("slug", sa.String(length=120), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_table(
        "organization_memberships",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("role", membership_role, nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "organization_id", name="uq_membership_user_organization"),
    )
    op.create_index(
        "ix_memberships_organization_role",
        "organization_memberships",
        ["organization_id", "role"],
        unique=False,
    )
    op.create_index("ix_memberships_user_id", "organization_memberships", ["user_id"], unique=False)


def downgrade() -> None:
    """Remove membership and organization storage introduced by this revision."""
    op.drop_index("ix_memberships_user_id", table_name="organization_memberships")
    op.drop_index("ix_memberships_organization_role", table_name="organization_memberships")
    op.drop_table("organization_memberships")
    op.drop_table("organizations")
    membership_role.drop(op.get_bind(), checkfirst=True)
