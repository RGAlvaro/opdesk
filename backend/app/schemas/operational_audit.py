"""Pydantic contracts for the admin operational audit API."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.operational import OperationalAuditStatus


class OperationalAuditRunRead(BaseModel):
    """Safe scheduled-job audit row returned to owner/admin users."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    job_name: str
    scheduled_for: datetime | None
    started_at: datetime
    finished_at: datetime | None
    status: OperationalAuditStatus
    records_seen: int | None
    records_changed: int | None
    error_code: str | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime


class OperationalAuditListResponse(BaseModel):
    """Paginated operational audit response following API conventions."""

    items: list[OperationalAuditRunRead]
    total: int
    limit: int
    offset: int
