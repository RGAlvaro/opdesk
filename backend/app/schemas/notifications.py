"""Pydantic contracts for the authenticated notification inbox API."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.notification import NotificationType


class NotificationRead(BaseModel):
    """Public representation of one user-owned notification."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    recipient_user_id: uuid.UUID
    type: NotificationType
    title: str
    body: str | None
    action_url: str | None
    resource_type: str | None
    resource_id: uuid.UUID | None
    read_at: datetime | None
    created_at: datetime


class NotificationListResponse(BaseModel):
    """Paginated notification list response."""

    items: list[NotificationRead]
    total: int
    limit: int
    offset: int


class NotificationUpdateRequest(BaseModel):
    """Request body for changing a notification read state."""

    read: bool


class NotificationUnreadCountResponse(BaseModel):
    """Small response used by app-shell unread badges."""

    unread_count: int
