"""Add enriched metadata fields and task watchers.

Revision ID: 0006
Revises: 0005
Create Date: 2026-08-11 10:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


project_status = postgresql.ENUM(
    "planned",
    "active",
    "on_hold",
    "completed",
    "cancelled",
    name="project_status",
    create_type=False,
)
project_visibility = postgresql.ENUM(
    "organization",
    "project_members",
    name="project_visibility",
    create_type=False,
)
task_type = postgresql.ENUM("internal", "operational", name="task_type", create_type=False)


def upgrade() -> None:
    """Add nullable metadata columns, enums, indexes, and watcher persistence."""
    bind = op.get_bind()
    postgresql.ENUM(
        "planned",
        "active",
        "on_hold",
        "completed",
        "cancelled",
        name="project_status",
    ).create(bind, checkfirst=True)
    postgresql.ENUM("organization", "project_members", name="project_visibility").create(
        bind, checkfirst=True
    )
    postgresql.ENUM("internal", "operational", name="task_type").create(bind, checkfirst=True)

    op.add_column("users", sa.Column("job_title", sa.String(length=120), nullable=True))
    op.add_column("users", sa.Column("phone", sa.String(length=40), nullable=True))
    op.add_column("users", sa.Column("timezone", sa.String(length=120), nullable=True))
    op.add_column("users", sa.Column("locale", sa.String(length=40), nullable=True))
    op.add_column("users", sa.Column("avatar_url", sa.String(length=2048), nullable=True))
    op.add_column("users", sa.Column("bio", sa.Text(), nullable=True))

    op.add_column("organizations", sa.Column("employee_count", sa.Integer(), nullable=True))
    op.add_column("organizations", sa.Column("industry", sa.String(length=120), nullable=True))
    op.add_column("organizations", sa.Column("website", sa.String(length=2048), nullable=True))
    op.add_column("organizations", sa.Column("contact_email", sa.String(length=320), nullable=True))
    op.add_column("organizations", sa.Column("phone", sa.String(length=40), nullable=True))
    op.add_column("organizations", sa.Column("address_line1", sa.String(length=160), nullable=True))
    op.add_column("organizations", sa.Column("address_line2", sa.String(length=160), nullable=True))
    op.add_column("organizations", sa.Column("city", sa.String(length=120), nullable=True))
    op.add_column("organizations", sa.Column("region", sa.String(length=120), nullable=True))
    op.add_column("organizations", sa.Column("postal_code", sa.String(length=40), nullable=True))
    op.add_column("organizations", sa.Column("country", sa.String(length=120), nullable=True))
    op.add_column("organizations", sa.Column("tax_id", sa.String(length=80), nullable=True))
    op.add_column("organizations", sa.Column("logo_url", sa.String(length=2048), nullable=True))
    op.add_column("organizations", sa.Column("description", sa.Text(), nullable=True))

    op.add_column(
        "projects",
        sa.Column("status", project_status, server_default="active", nullable=False),
    )
    op.add_column("projects", sa.Column("start_date", sa.Date(), nullable=True))
    op.add_column("projects", sa.Column("end_date", sa.Date(), nullable=True))
    op.add_column("projects", sa.Column("budget_amount", sa.Numeric(12, 2), nullable=True))
    op.add_column("projects", sa.Column("budget_currency", sa.String(length=3), nullable=True))
    op.add_column(
        "projects",
        sa.Column("visibility", project_visibility, server_default="organization", nullable=False),
    )
    op.add_column("projects", sa.Column("project_owner_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        "fk_projects_project_owner_id_users",
        "projects",
        "users",
        ["project_owner_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_projects_status", "projects", ["status"])
    op.create_index("ix_projects_project_owner_id", "projects", ["project_owner_id"])
    op.create_index("ix_projects_visibility", "projects", ["visibility"])

    op.add_column("tasks", sa.Column("estimated_hours", sa.Numeric(8, 2), nullable=True))
    op.add_column("tasks", sa.Column("actual_hours", sa.Numeric(8, 2), nullable=True))
    op.add_column("tasks", sa.Column("sort_order", sa.Integer(), nullable=True))
    op.add_column("tasks", sa.Column("blocked_reason", sa.Text(), nullable=True))
    op.add_column("tasks", sa.Column("external_reference", sa.String(length=200), nullable=True))
    op.add_column(
        "tasks",
        sa.Column("task_type", task_type, server_default="internal", nullable=False),
    )
    op.create_index("ix_tasks_project_sort_order", "tasks", ["project_id", "sort_order"])
    op.create_index("ix_tasks_task_type", "tasks", ["task_type"])

    op.create_table(
        "task_watchers",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("task_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("added_by_id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["added_by_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("task_id", "user_id", name="uq_task_watchers_task_user"),
    )
    op.create_index("ix_task_watchers_organization_id", "task_watchers", ["organization_id"])
    op.create_index("ix_task_watchers_project_id", "task_watchers", ["project_id"])
    op.create_index("ix_task_watchers_user_id", "task_watchers", ["user_id"])


def downgrade() -> None:
    """Remove SPEC-308 metadata fields and watcher persistence."""
    op.drop_index("ix_task_watchers_user_id", table_name="task_watchers")
    op.drop_index("ix_task_watchers_project_id", table_name="task_watchers")
    op.drop_index("ix_task_watchers_organization_id", table_name="task_watchers")
    op.drop_table("task_watchers")

    op.drop_index("ix_tasks_task_type", table_name="tasks")
    op.drop_index("ix_tasks_project_sort_order", table_name="tasks")
    op.drop_column("tasks", "task_type")
    op.drop_column("tasks", "external_reference")
    op.drop_column("tasks", "blocked_reason")
    op.drop_column("tasks", "sort_order")
    op.drop_column("tasks", "actual_hours")
    op.drop_column("tasks", "estimated_hours")

    op.drop_index("ix_projects_visibility", table_name="projects")
    op.drop_index("ix_projects_project_owner_id", table_name="projects")
    op.drop_index("ix_projects_status", table_name="projects")
    op.drop_constraint("fk_projects_project_owner_id_users", "projects", type_="foreignkey")
    op.drop_column("projects", "project_owner_id")
    op.drop_column("projects", "visibility")
    op.drop_column("projects", "budget_currency")
    op.drop_column("projects", "budget_amount")
    op.drop_column("projects", "end_date")
    op.drop_column("projects", "start_date")
    op.drop_column("projects", "status")

    for column in (
        "description",
        "logo_url",
        "tax_id",
        "country",
        "postal_code",
        "region",
        "city",
        "address_line2",
        "address_line1",
        "phone",
        "contact_email",
        "website",
        "industry",
        "employee_count",
    ):
        op.drop_column("organizations", column)

    for column in ("bio", "avatar_url", "locale", "timezone", "phone", "job_title"):
        op.drop_column("users", column)

    bind = op.get_bind()
    task_type.drop(bind, checkfirst=True)
    project_visibility.drop(bind, checkfirst=True)
    project_status.drop(bind, checkfirst=True)
