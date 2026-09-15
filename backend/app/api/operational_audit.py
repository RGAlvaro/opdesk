"""Owner/admin API endpoints for scheduled-job operational audit rows."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.operational_audit import (
    OperationalAuditListResponse,
    OperationalAuditRunRead,
)
from app.services.operational_audit import OperationalAuditService

router = APIRouter(prefix="/api/v1/admin/operational-audit", tags=["operational-audit"])


@router.get("", response_model=OperationalAuditListResponse)
def list_operational_audit(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
    job_name: str | None = None,
    status: str | None = None,
) -> OperationalAuditListResponse:
    """List scheduled-job audit rows for users with an admin organization context."""
    rows, total = OperationalAuditService(db).list_runs(
        current_user,
        limit=limit,
        offset=offset,
        job_name=job_name,
        status=status,
    )
    return OperationalAuditListResponse(
        items=[OperationalAuditRunRead.model_validate(row) for row in rows],
        total=total,
        limit=limit,
        offset=offset,
    )
