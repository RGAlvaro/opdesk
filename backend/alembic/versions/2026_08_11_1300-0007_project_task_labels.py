"""Add project-scoped task labels.

Revision ID: 0007
Revises: 0006
Create Date: 2026-08-11 13:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0007"
down_revision: str | None = "0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create task label taxonomy and assignment persistence."""
    op.create_table(
        "task_labels",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=60), nullable=False),
        sa.Column("color", sa.String(length=7), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_by_id", sa.Uuid(), nullable=False),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_task_labels_project_archived", "task_labels", ["project_id", "archived_at"])
    op.create_index(
        "ix_task_labels_organization_project",
        "task_labels",
        ["organization_id", "project_id"],
    )
    op.create_index(
        "uq_task_labels_active_project_name_lower",
        "task_labels",
        [sa.text("project_id"), sa.text("lower(name)")],
        unique=True,
        postgresql_where=sa.text("archived_at IS NULL"),
    )

    op.create_table(
        "task_label_assignments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("task_id", sa.Uuid(), nullable=False),
        sa.Column("label_id", sa.Uuid(), nullable=False),
        sa.Column("applied_by_id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["applied_by_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["label_id"], ["task_labels.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("task_id", "label_id", name="uq_task_label_assignments_task_label"),
    )
    op.create_index(
        "ix_task_label_assignments_organization_project",
        "task_label_assignments",
        ["organization_id", "project_id"],
    )
    op.create_index("ix_task_label_assignments_task_id", "task_label_assignments", ["task_id"])
    op.create_index("ix_task_label_assignments_label_id", "task_label_assignments", ["label_id"])


def downgrade() -> None:
    """Remove task label assignment and taxonomy persistence."""
    op.drop_index("ix_task_label_assignments_label_id", table_name="task_label_assignments")
    op.drop_index("ix_task_label_assignments_task_id", table_name="task_label_assignments")
    op.drop_index(
        "ix_task_label_assignments_organization_project",
        table_name="task_label_assignments",
    )
    op.drop_table("task_label_assignments")

    op.drop_index("uq_task_labels_active_project_name_lower", table_name="task_labels")
    op.drop_index("ix_task_labels_organization_project", table_name="task_labels")
    op.drop_index("ix_task_labels_project_archived", table_name="task_labels")
    op.drop_table("task_labels")
