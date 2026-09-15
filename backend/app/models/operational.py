"""SQLAlchemy model for scheduled-job operational audit evidence."""

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from app.db.base import Base


class OperationalAuditStatus(str, enum.Enum):
    """Lifecycle states persisted for one scheduled job run."""

    STARTED = "started"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    SKIPPED = "skipped"


class OperationalAuditRun(Base):
    """Persist safe, operator-visible evidence for one scheduled job run."""

    __tablename__ = "operational_audit_runs"
    __table_args__ = (
        Index("ix_operational_audit_runs_job_started", "job_name", "started_at"),
        Index("ix_operational_audit_runs_status_started", "status", "started_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    job_name: Mapped[str] = mapped_column(String(120), nullable=False)
    scheduled_for: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[OperationalAuditStatus] = mapped_column(
        Enum(
            OperationalAuditStatus,
            name="operational_audit_status",
            values_callable=lambda values: [v.value for v in values],
        ),
        nullable=False,
        default=OperationalAuditStatus.STARTED,
    )
    records_seen: Mapped[int | None] = mapped_column(nullable=True)
    records_changed: Mapped[int | None] = mapped_column(nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(120), nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
