"""Enforce one owner membership per organization.

Revision ID: 0004
Revises: 0003
Create Date: 2026-06-18 12:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Prevent a second owner membership for the same organization."""
    op.create_index(
        "uq_memberships_single_owner",
        "organization_memberships",
        ["organization_id"],
        unique=True,
        postgresql_where=sa.text("role = 'owner'"),
    )


def downgrade() -> None:
    """Remove the single-owner database constraint."""
    op.drop_index("uq_memberships_single_owner", table_name="organization_memberships")
