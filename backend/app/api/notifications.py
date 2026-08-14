"""HTTP endpoints for the authenticated in-app notification inbox."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.notifications import (
    NotificationListResponse,
    NotificationRead,
    NotificationUnreadCountResponse,
    NotificationUpdateRequest,
)
from app.services.notifications import NotificationService

router = APIRouter(prefix="/api/v1/notifications", tags=["notifications"])


@router.get("", response_model=NotificationListResponse)
def list_notifications(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
    unread: bool | None = None,
) -> NotificationListResponse:
    """List notifications owned by the current authenticated user."""
    notifications, total = NotificationService(db).list_notifications(
        current_user, limit, offset, unread
    )
    return NotificationListResponse(
        items=[NotificationRead.model_validate(notification) for notification in notifications],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/unread-count", response_model=NotificationUnreadCountResponse)
def get_unread_count(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> NotificationUnreadCountResponse:
    """Return the current user's unread notification count."""
    return NotificationUnreadCountResponse(
        unread_count=NotificationService(db).unread_count(current_user)
    )


@router.patch("/{notification_id}", response_model=NotificationRead)
def update_notification(
    notification_id: uuid.UUID,
    payload: NotificationUpdateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> NotificationRead:
    """Update one current-user notification read state."""
    notification = NotificationService(db).set_read_state(
        current_user, notification_id, read=payload.read
    )
    return NotificationRead.model_validate(notification)


@router.post("/mark-all-read", status_code=204)
def mark_all_read(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> Response:
    """Mark all current-user notifications read."""
    NotificationService(db).mark_all_read(current_user)
    return Response(status_code=204)
