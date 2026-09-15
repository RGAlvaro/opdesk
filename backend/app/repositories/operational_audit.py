"""Data access helpers for scheduled-job operational audit rows."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.operational import OperationalAuditRun, OperationalAuditStatus


class OperationalAuditRepository:
    """Keep operational audit listing and persistence rules in one boundary."""

    def __init__(self, db: Session) -> None:
        """Store the active database session for audit operations."""
        self.db = db

    def add(self, audit_run: OperationalAuditRun) -> OperationalAuditRun:
        """Stage and flush one operational audit row."""
        self.db.add(audit_run)
        self.db.flush()
        return audit_run

    def list_runs(
        self,
        *,
        limit: int,
        offset: int,
        job_name: str | None,
        status: OperationalAuditStatus | None,
    ) -> tuple[list[OperationalAuditRun], int]:
        """List operational audit rows with optional safe filters."""
        filters = []
        if job_name is not None:
            filters.append(OperationalAuditRun.job_name == job_name)
        if status is not None:
            filters.append(OperationalAuditRun.status == status)
        total = self.db.scalar(select(func.count(OperationalAuditRun.id)).where(*filters)) or 0
        rows = list(
            self.db.scalars(
                select(OperationalAuditRun)
                .where(*filters)
                .order_by(OperationalAuditRun.started_at.desc(), OperationalAuditRun.id.desc())
                .limit(limit)
                .offset(offset)
            )
        )
        return rows, total
