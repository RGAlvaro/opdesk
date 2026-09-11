"""SQLAlchemy model for user-facing in-app notifications."""

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from app.db.base import Base


class NotificationType(str, enum.Enum):
    """Stable notification event names exposed through the public API."""

    INVITATION_ORGANIZATION = "invitation.organization"
    INVITATION_PROJECT = "invitation.project"
    PROJECT_MEMBERSHIP = "project.membership"
    PROJECT_UPDATED = "project.updated"
    TASK_ASSIGNED = "task.assigned"
    TASK_CREATED = "task.created"
    TASK_STATUS_CHANGED = "task.status_changed"
    TICKET_COMMENT = "ticket.comment"
    TICKET_CREATED = "ticket.created"
    TICKET_ASSIGNMENT_REQUESTED = "ticket.assignment_requested"
    CHAT_UNREAD = "chat.unread"


class NotificationDeliveryChannel(str, enum.Enum):
    """External notification channels supported by delivery audit rows."""

    EMAIL = "email"


class NotificationDeliveryStatus(str, enum.Enum):
    """Delivery lifecycle states stored for retries and safe diagnostics."""

    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    SUPPRESSED = "suppressed"


class Notification(Base):
    """Persist one inbox item for exactly one recipient user."""

    __tablename__ = "notifications"
    __table_args__ = (
        Index(
            "ix_notifications_recipient_read_created", "recipient_user_id", "read_at", "created_at"
        ),
        Index("ix_notifications_recipient_created", "recipient_user_id", "created_at"),
        Index("ix_notifications_resource", "resource_type", "resource_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    recipient_user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    type: Mapped[NotificationType] = mapped_column(
        Enum(
            NotificationType,
            name="notification_type",
            values_callable=lambda values: [v.value for v in values],
        ),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)
    action_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    resource_type: Mapped[str | None] = mapped_column(String(80), nullable=True)
    resource_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class NotificationDelivery(Base):
    """Audit one external delivery attempt stream for a notification recipient."""

    __tablename__ = "notification_deliveries"
    __table_args__ = (
        Index("ix_notification_deliveries_recipient_created", "recipient_user_id", "created_at"),
        Index("ix_notification_deliveries_notification_channel", "notification_id", "channel"),
        Index("ix_notification_deliveries_status_next_attempt", "status", "next_attempt_at"),
        UniqueConstraint(
            "notification_id",
            "channel",
            name="uq_notification_deliveries_notification_channel",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    notification_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("notifications.id", ondelete="CASCADE"), nullable=False
    )
    recipient_user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    channel: Mapped[NotificationDeliveryChannel] = mapped_column(
        Enum(
            NotificationDeliveryChannel,
            name="notification_delivery_channel",
            values_callable=lambda values: [v.value for v in values],
        ),
        nullable=False,
    )
    provider: Mapped[str] = mapped_column(String(40), nullable=False)
    provider_message_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[NotificationDeliveryStatus] = mapped_column(
        Enum(
            NotificationDeliveryStatus,
            name="notification_delivery_status",
            values_callable=lambda values: [v.value for v in values],
        ),
        nullable=False,
        default=NotificationDeliveryStatus.PENDING,
    )
    attempt_count: Mapped[int] = mapped_column(nullable=False, default=0, server_default="0")
    last_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    next_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error_code: Mapped[str | None] = mapped_column(String(120), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
