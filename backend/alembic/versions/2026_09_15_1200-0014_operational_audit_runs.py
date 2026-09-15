"""Add operational audit rows for scheduled jobs.

Revision ID: 0014
Revises: 0013
Create Date: 2026-09-15 12:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0014"
down_revision: str | None = "0013"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create scheduled-job audit enum, table, and query indexes."""
    audit_status = postgresql.ENUM(
        "started",
        "succeeded",
        "failed",
        "skipped",
        name="operational_audit_status",
        create_type=False,
    )
    audit_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "operational_audit_runs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("job_name", sa.String(length=120), nullable=False),
        sa.Column("scheduled_for", sa.DateTime(timezone=True), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", audit_status, nullable=False),
        sa.Column("records_seen", sa.Integer(), nullable=True),
        sa.Column("records_changed", sa.Integer(), nullable=True),
        sa.Column("error_code", sa.String(length=120), nullable=True),
        sa.Column("error_message", sa.String(length=255), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_operational_audit_runs_job_started",
        "operational_audit_runs",
        ["job_name", "started_at"],
    )
    op.create_index(
        "ix_operational_audit_runs_status_started",
        "operational_audit_runs",
        ["status", "started_at"],
    )


def downgrade() -> None:
    """Drop scheduled-job audit storage and owned enum type."""
    op.drop_index(
        "ix_operational_audit_runs_status_started",
        table_name="operational_audit_runs",
    )
    op.drop_index(
        "ix_operational_audit_runs_job_started",
        table_name="operational_audit_runs",
    )
    op.drop_table("operational_audit_runs")
    postgresql.ENUM(name="operational_audit_status").drop(op.get_bind(), checkfirst=True)
