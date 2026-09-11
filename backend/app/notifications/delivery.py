"""External notification delivery providers and audit state transitions."""

import logging
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Protocol

import httpx
from sqlalchemy import event
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.models.notification import (
    Notification,
    NotificationDelivery,
    NotificationDeliveryChannel,
    NotificationDeliveryStatus,
    NotificationType,
)
from app.models.user import User
from app.repositories.notifications import NotificationRepository
from app.repositories.users import UserRepository

logger = logging.getLogger(__name__)

eligible_email_types = {
    NotificationType.INVITATION_ORGANIZATION,
    NotificationType.INVITATION_PROJECT,
    NotificationType.TICKET_CREATED,
    NotificationType.TICKET_COMMENT,
    NotificationType.TICKET_ASSIGNMENT_REQUESTED,
    NotificationType.CHAT_UNREAD,
}
max_delivery_attempts = 3
pending_external_delivery_jobs_key = "pending_external_delivery_jobs"


@event.listens_for(Session, "after_commit")
def enqueue_external_delivery_jobs_after_commit(session: Session) -> None:
    """Publish delivery jobs only after their audit rows are committed."""
    delivery_ids: list[uuid.UUID] = session.info.pop(pending_external_delivery_jobs_key, [])
    if not delivery_ids:
        return
    from app.jobs.enqueue import enqueue_external_notification_delivery

    for delivery_id in delivery_ids:
        enqueue_external_notification_delivery(delivery_id)


@event.listens_for(Session, "after_rollback")
def discard_external_delivery_jobs_after_rollback(session: Session) -> None:
    """Forget queued delivery jobs when the owning transaction rolls back."""
    session.info.pop(pending_external_delivery_jobs_key, None)


@dataclass(frozen=True)
class EmailMessage:
    """Safe transactional email content derived from an in-app notification."""

    to_email: str
    subject: str
    text: str


@dataclass(frozen=True)
class DeliveryResult:
    """Provider outcome used to update audit state without leaking raw responses."""

    status: NotificationDeliveryStatus
    provider_message_id: str | None = None
    error_code: str | None = None
    retryable: bool = False


class EmailProvider(Protocol):
    """Minimal provider interface for transactional notification email."""

    provider_key: str

    def send(self, message: EmailMessage) -> DeliveryResult:
        """Send one email and return a safe provider outcome."""


class ConsoleEmailProvider:
    """Local and CI-safe provider that records a fake successful send."""

    provider_key = "console"

    def send(self, message: EmailMessage) -> DeliveryResult:
        """Pretend to send without contacting an external provider."""
        logger.info("email_delivery console_sent")
        return DeliveryResult(
            status=NotificationDeliveryStatus.SENT,
            provider_message_id=f"console-{uuid.uuid4()}",
        )


class ResendEmailProvider:
    """Resend transactional email adapter using environment-backed credentials."""

    provider_key = "resend"

    def __init__(self, settings: Settings) -> None:
        """Store provider configuration without logging secrets."""
        self.api_key = settings.resend_api_key
        self.from_email = settings.resend_from_email
        self.timeout_seconds = settings.email_provider_timeout_seconds

    def send(self, message: EmailMessage) -> DeliveryResult:
        """Send one transactional email through the Resend API."""
        if not self.api_key or not self.from_email:
            return DeliveryResult(
                status=NotificationDeliveryStatus.FAILED,
                error_code="missing_provider_config",
                retryable=False,
            )
        try:
            response = httpx.post(
                "https://api.resend.com/emails",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "from": self.from_email,
                    "to": [message.to_email],
                    "subject": message.subject,
                    "text": message.text,
                },
                timeout=self.timeout_seconds,
            )
        except httpx.TimeoutException:
            return DeliveryResult(
                status=NotificationDeliveryStatus.FAILED,
                error_code="provider_timeout",
                retryable=True,
            )
        except httpx.HTTPError:
            return DeliveryResult(
                status=NotificationDeliveryStatus.FAILED,
                error_code="provider_http_error",
                retryable=True,
            )
        if 200 <= response.status_code < 300:
            try:
                body = response.json()
            except ValueError:
                body = {}
            return DeliveryResult(
                status=NotificationDeliveryStatus.SENT,
                provider_message_id=str(body.get("id")) if body.get("id") else None,
            )
        retryable = response.status_code >= 500 or response.status_code == 429
        return DeliveryResult(
            status=NotificationDeliveryStatus.FAILED,
            error_code=f"provider_status_{response.status_code}",
            retryable=retryable,
        )


def email_provider_for_settings(settings: Settings) -> EmailProvider:
    """Choose the configured provider while keeping local and CI network-free."""
    if settings.email_delivery_provider == "resend":
        return ResendEmailProvider(settings)
    return ConsoleEmailProvider()


class ExternalNotificationDeliveryService:
    """Coordinate eligibility, audit rows, provider sends, and bounded retries."""

    def __init__(self, db: Session, settings: Settings | None = None) -> None:
        """Create collaborators for one worker or request transaction."""
        self.db = db
        self.settings = settings or get_settings()
        self.notifications = NotificationRepository(db)
        self.users = UserRepository(db)

    def enqueue_email_delivery(self, notification: Notification) -> NotificationDelivery | None:
        """Create a pending email delivery audit row for eligible notifications."""
        if not self._should_deliver(notification):
            return None
        existing = self.notifications.get_delivery_for_notification(
            notification.id, NotificationDeliveryChannel.EMAIL
        )
        if existing is not None:
            return existing
        delivery = self.notifications.add_delivery(
            NotificationDelivery(
                notification_id=notification.id,
                recipient_user_id=notification.recipient_user_id,
                channel=NotificationDeliveryChannel.EMAIL,
                provider=self.settings.email_delivery_provider,
                status=NotificationDeliveryStatus.PENDING,
            )
        )
        self.db.flush()
        delivery_ids: list[uuid.UUID] = self.db.info.setdefault(
            pending_external_delivery_jobs_key, []
        )
        delivery_ids.append(delivery.id)
        return delivery

    def process_delivery(
        self,
        delivery_id: uuid.UUID,
        provider: EmailProvider | None = None,
    ) -> str:
        """Send one pending delivery and update audit state."""
        delivery = self.notifications.get_delivery(delivery_id)
        if delivery is None:
            return "missing"
        if delivery.status == NotificationDeliveryStatus.SENT:
            return "already_sent"
        notification = self.notifications.get_notification(delivery.notification_id)
        recipient = self.users.get_by_id(delivery.recipient_user_id)
        if notification is None or recipient is None or not recipient.is_active:
            self._mark_suppressed(delivery, "recipient_not_eligible")
            self._log_delivery_outcome(delivery)
            return "suppressed"
        if not self._should_deliver(notification):
            self._mark_suppressed(delivery, "notification_not_eligible")
            self._log_delivery_outcome(delivery)
            return "suppressed"
        selected_provider = provider or email_provider_for_settings(self.settings)
        message = self._message_for(notification, recipient)
        delivery.attempt_count += 1
        delivery.last_attempt_at = datetime.now(UTC)
        result = selected_provider.send(message)
        delivery.provider = selected_provider.provider_key
        delivery.provider_message_id = result.provider_message_id
        delivery.last_error_code = result.error_code
        if result.status == NotificationDeliveryStatus.SENT:
            delivery.status = NotificationDeliveryStatus.SENT
            delivery.next_attempt_at = None
            self.db.add(delivery)
            self.db.commit()
            self._log_delivery_outcome(delivery)
            return "sent"
        if result.retryable and delivery.attempt_count < max_delivery_attempts:
            delivery.status = NotificationDeliveryStatus.PENDING
            delivery.next_attempt_at = datetime.now(UTC) + timedelta(
                minutes=5 * delivery.attempt_count
            )
            self.db.add(delivery)
            self.db.commit()
            self._log_delivery_outcome(delivery)
            return "retry"
        delivery.status = NotificationDeliveryStatus.FAILED
        delivery.next_attempt_at = None
        self.db.add(delivery)
        self.db.commit()
        self._log_delivery_outcome(delivery)
        return "failed"

    def process_due_deliveries(self, limit: int = 100) -> int:
        """Process currently due pending deliveries for maintenance sweeps."""
        count = 0
        for delivery in self.notifications.list_due_deliveries(limit):
            self.process_delivery(delivery.id)
            count += 1
        return count

    def _should_deliver(self, notification: Notification) -> bool:
        """Return whether this notification type is eligible for email delivery."""
        return (
            self.settings.email_notifications_enabled and notification.type in eligible_email_types
        )

    def _message_for(self, notification: Notification, recipient: User) -> EmailMessage:
        """Build safe plain-text transactional email from the notification row."""
        action_url = notification.action_url or "/app/notifications"
        link = self._absolute_url(action_url)
        body = notification.body or "You have a new OpsDesk notification."
        return EmailMessage(
            to_email=recipient.email,
            subject=f"OpsDesk: {notification.title}",
            text=f"{body}\n\nOpen in OpsDesk: {link}",
        )

    def _absolute_url(self, action_url: str) -> str:
        """Convert relative app routes to absolute links for email clients."""
        base_url = self.settings.public_app_url.rstrip("/")
        if action_url.startswith("http://") or action_url.startswith("https://"):
            return action_url
        return f"{base_url}{action_url if action_url.startswith('/') else f'/{action_url}'}"

    def _mark_suppressed(self, delivery: NotificationDelivery, error_code: str) -> None:
        """Record a non-retryable suppression for an ineligible delivery."""
        delivery.status = NotificationDeliveryStatus.SUPPRESSED
        delivery.last_error_code = error_code
        delivery.next_attempt_at = None
        self.db.add(delivery)
        self.db.commit()

    def _log_delivery_outcome(self, delivery: NotificationDelivery) -> None:
        """Log safe delivery diagnostics without provider payloads or message bodies."""
        logger.info(
            "external_notification_delivery delivery_id=%s notification_id=%s "
            "channel=%s provider=%s recipient_user_id=%s status=%s error_code=%s",
            delivery.id,
            delivery.notification_id,
            delivery.channel.value,
            delivery.provider,
            delivery.recipient_user_id,
            delivery.status.value,
            delivery.last_error_code,
        )
