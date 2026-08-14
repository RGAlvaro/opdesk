"""Data access operations for current-user notification inbox state."""

import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.notification import Notification, NotificationType


class NotificationRepository:
    """Keep notification queries recipient-scoped and pagination-friendly."""

    def __init__(self, db: Session) -> None:
        """Store the active request transaction."""
        self.db = db

    def add(self, notification: Notification) -> Notification:
        """Stage and flush a notification row."""
        self.db.add(notification)
        self.db.flush()
        return notification

    def get_for_recipient(
        self, notification_id: uuid.UUID, recipient_user_id: uuid.UUID
    ) -> Notification | None:
        """Load one notification only when owned by the supplied recipient."""
        return self.db.scalar(
            select(Notification).where(
                Notification.id == notification_id,
                Notification.recipient_user_id == recipient_user_id,
            )
        )

    def list_for_recipient(
        self, recipient_user_id: uuid.UUID, limit: int, offset: int, unread: bool | None
    ) -> tuple[list[Notification], int]:
        """List current-user notifications with optional unread filtering."""
        filters = [Notification.recipient_user_id == recipient_user_id]
        if unread is True:
            filters.append(Notification.read_at.is_(None))
        elif unread is False:
            filters.append(Notification.read_at.is_not(None))
        total = self.db.scalar(select(func.count(Notification.id)).where(*filters)) or 0
        items = list(
            self.db.scalars(
                select(Notification)
                .where(*filters)
                .order_by(Notification.created_at.desc(), Notification.id.desc())
                .limit(limit)
                .offset(offset)
            )
        )
        return items, total

    def unread_count(self, recipient_user_id: uuid.UUID) -> int:
        """Count unread notifications for one recipient."""
        return (
            self.db.scalar(
                select(func.count(Notification.id)).where(
                    Notification.recipient_user_id == recipient_user_id,
                    Notification.read_at.is_(None),
                )
            )
            or 0
        )

    def mark_all_read(self, recipient_user_id: uuid.UUID) -> list[Notification]:
        """Return unread current-user notifications for service-side marking."""
        return list(
            self.db.scalars(
                select(Notification).where(
                    Notification.recipient_user_id == recipient_user_id,
                    Notification.read_at.is_(None),
                )
            )
        )

    def find_unread_for_resource(
        self,
        *,
        recipient_user_id: uuid.UUID,
        notification_type: NotificationType,
        resource_type: str,
        resource_id: uuid.UUID,
    ) -> Notification | None:
        """Return an existing unread resource notification to prevent spammy duplicates."""
        return self.db.scalar(
            select(Notification).where(
                Notification.recipient_user_id == recipient_user_id,
                Notification.type == notification_type,
                Notification.resource_type == resource_type,
                Notification.resource_id == resource_id,
                Notification.read_at.is_(None),
            )
        )
