"""Backend coverage for SPEC-314 external notification delivery."""

import uuid
from collections.abc import Generator
from typing import Any

import httpx
import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import Settings
from app.db.base import Base
from app.jobs import tasks as task_module
from app.models.notification import (
    Notification,
    NotificationDelivery,
    NotificationDeliveryStatus,
    NotificationType,
)
from app.models.project import Task
from app.models.user import User
from app.notifications.delivery import (
    DeliveryResult,
    EmailMessage,
    ExternalNotificationDeliveryService,
    ResendEmailProvider,
)
from app.services.notifications import NotificationService


class FakeProvider:
    """Deterministic provider used to exercise worker delivery state transitions."""

    provider_key = "fake"

    def __init__(self, result: DeliveryResult) -> None:
        """Store the result returned for every send."""
        self.result = result
        self.messages: list[EmailMessage] = []

    def send(self, message: EmailMessage) -> DeliveryResult:
        """Record the message and return the configured outcome."""
        self.messages.append(message)
        return self.result


@pytest.fixture(autouse=True)
def disable_broker_enqueue(monkeypatch: pytest.MonkeyPatch) -> None:
    """Prevent service tests from contacting a Celery broker."""
    import app.jobs.enqueue as enqueue_module

    monkeypatch.setattr(
        enqueue_module,
        "enqueue_external_notification_delivery",
        lambda delivery_id: True,
    )


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """Run delivery service tests against an isolated in-memory database."""
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)
        engine.dispose()


def create_user(session: Session, *, is_active: bool = True) -> User:
    """Persist one recipient account for notification delivery tests."""
    user = User(
        email=f"{uuid.uuid4()}@example.com",
        password_hash="hash",
        full_name="Recipient",
        is_active=is_active,
    )
    session.add(user)
    session.commit()
    return user


def create_notification(
    session: Session, user: User, notification_type: NotificationType
) -> Notification:
    """Persist one in-app notification that can be wrapped by delivery audit rows."""
    notification = Notification(
        recipient_user_id=user.id,
        type=notification_type,
        title="Delivery event",
        body="A safe notification summary.",
        action_url="/app/notifications",
        resource_type="test",
        resource_id=uuid.uuid4(),
    )
    session.add(notification)
    session.commit()
    return notification


def first_delivery(session: Session) -> NotificationDelivery:
    """Return the single delivery row expected by focused service tests."""
    delivery = session.scalar(select(NotificationDelivery))
    assert delivery is not None
    return delivery


def test_eligible_notification_creates_pending_delivery_after_commit(
    db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Eligible in-app notifications create one delivery audit row and post-commit job."""
    queued: list[uuid.UUID] = []
    import app.jobs.enqueue as enqueue_module

    monkeypatch.setattr(enqueue_module, "enqueue_external_notification_delivery", queued.append)
    recipient = create_user(db_session)
    ticket = Task(id=uuid.uuid4(), title="Broken VPN")

    NotificationService(db_session).notify_ticket_created(uuid.uuid4(), ticket, {recipient.id})
    db_session.commit()

    delivery = first_delivery(db_session)
    assert delivery.status == NotificationDeliveryStatus.PENDING
    assert delivery.recipient_user_id == recipient.id
    assert queued == [delivery.id]


def test_noneligible_notification_skips_external_delivery(db_session: Session) -> None:
    """Non-eligible inbox events remain in-app only."""
    recipient = create_user(db_session)
    notification = create_notification(db_session, recipient, NotificationType.PROJECT_UPDATED)

    delivery = ExternalNotificationDeliveryService(db_session).enqueue_email_delivery(notification)
    db_session.commit()

    assert delivery is None
    assert db_session.scalar(select(NotificationDelivery)) is None


def test_worker_marks_successful_delivery_sent(db_session: Session) -> None:
    """Worker success stores provider status and safe message id."""
    recipient = create_user(db_session)
    notification = create_notification(db_session, recipient, NotificationType.TICKET_COMMENT)
    delivery = ExternalNotificationDeliveryService(db_session).enqueue_email_delivery(notification)
    db_session.commit()
    assert delivery is not None
    provider = FakeProvider(
        DeliveryResult(
            status=NotificationDeliveryStatus.SENT,
            provider_message_id="provider-123",
        )
    )

    result = ExternalNotificationDeliveryService(db_session).process_delivery(delivery.id, provider)

    persisted = first_delivery(db_session)
    assert result == "sent"
    assert persisted.status == NotificationDeliveryStatus.SENT
    assert persisted.provider == "fake"
    assert persisted.provider_message_id == "provider-123"
    assert len(provider.messages) == 1


def test_worker_task_processes_pending_delivery(
    db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Celery task entrypoint loads a delivery id and records console success."""
    recipient = create_user(db_session)
    notification = create_notification(db_session, recipient, NotificationType.TICKET_CREATED)
    delivery = ExternalNotificationDeliveryService(db_session).enqueue_email_delivery(notification)
    db_session.commit()
    assert delivery is not None
    monkeypatch.setattr(task_module, "SessionLocal", lambda: db_session)

    result = task_module.send_external_notification_delivery(str(delivery.id))

    persisted = first_delivery(db_session)
    assert result == "sent"
    assert persisted.status == NotificationDeliveryStatus.SENT
    assert persisted.provider == "console"


def test_worker_records_transient_retry_state(db_session: Session) -> None:
    """Transient provider failures stay pending until the bounded retry limit."""
    recipient = create_user(db_session)
    notification = create_notification(db_session, recipient, NotificationType.CHAT_UNREAD)
    delivery = ExternalNotificationDeliveryService(db_session).enqueue_email_delivery(notification)
    db_session.commit()
    assert delivery is not None
    provider = FakeProvider(
        DeliveryResult(
            status=NotificationDeliveryStatus.FAILED,
            error_code="provider_timeout",
            retryable=True,
        )
    )

    result = ExternalNotificationDeliveryService(db_session).process_delivery(delivery.id, provider)

    persisted = first_delivery(db_session)
    assert result == "retry"
    assert persisted.status == NotificationDeliveryStatus.PENDING
    assert persisted.attempt_count == 1
    assert persisted.next_attempt_at is not None
    assert persisted.last_error_code == "provider_timeout"


def test_worker_marks_permanent_failure_failed(db_session: Session) -> None:
    """Permanent provider failures do not loop through retries."""
    recipient = create_user(db_session)
    notification = create_notification(
        db_session, recipient, NotificationType.TICKET_ASSIGNMENT_REQUESTED
    )
    delivery = ExternalNotificationDeliveryService(db_session).enqueue_email_delivery(notification)
    db_session.commit()
    assert delivery is not None
    provider = FakeProvider(
        DeliveryResult(
            status=NotificationDeliveryStatus.FAILED,
            error_code="provider_status_400",
            retryable=False,
        )
    )

    result = ExternalNotificationDeliveryService(db_session).process_delivery(delivery.id, provider)

    persisted = first_delivery(db_session)
    assert result == "failed"
    assert persisted.status == NotificationDeliveryStatus.FAILED
    assert persisted.next_attempt_at is None


def test_worker_suppresses_inactive_recipient(db_session: Session) -> None:
    """Inactive recipients suppress pending external delivery before provider send."""
    recipient = create_user(db_session, is_active=False)
    notification = create_notification(db_session, recipient, NotificationType.INVITATION_PROJECT)
    delivery = ExternalNotificationDeliveryService(db_session).enqueue_email_delivery(notification)
    db_session.commit()
    assert delivery is not None
    provider = FakeProvider(DeliveryResult(status=NotificationDeliveryStatus.SENT))

    result = ExternalNotificationDeliveryService(db_session).process_delivery(delivery.id, provider)

    persisted = first_delivery(db_session)
    assert result == "suppressed"
    assert persisted.status == NotificationDeliveryStatus.SUPPRESSED
    assert persisted.last_error_code == "recipient_not_eligible"
    assert provider.messages == []


def test_sent_delivery_is_idempotent(db_session: Session) -> None:
    """Already-sent deliveries are not submitted to the provider twice."""
    recipient = create_user(db_session)
    notification = create_notification(
        db_session, recipient, NotificationType.INVITATION_ORGANIZATION
    )
    delivery = ExternalNotificationDeliveryService(db_session).enqueue_email_delivery(notification)
    db_session.commit()
    assert delivery is not None
    provider = FakeProvider(DeliveryResult(status=NotificationDeliveryStatus.SENT))
    service = ExternalNotificationDeliveryService(db_session)

    assert service.process_delivery(delivery.id, provider) == "sent"
    assert service.process_delivery(delivery.id, provider) == "already_sent"
    assert len(provider.messages) == 1


def test_resend_provider_uses_mocked_http_client(monkeypatch: pytest.MonkeyPatch) -> None:
    """Resend adapter sends through HTTPX while tests avoid external network calls."""
    captured: dict[str, Any] = {}

    def fake_post(*args: object, **kwargs: object) -> httpx.Response:
        """Capture the outbound provider request and return a fake Resend id."""
        captured["args"] = args
        captured["kwargs"] = kwargs
        return httpx.Response(200, json={"id": "email_123"})

    monkeypatch.setattr(httpx, "post", fake_post)
    provider = ResendEmailProvider(
        Settings(
            email_delivery_provider="resend",
            resend_api_key="test_resend_key",
            resend_from_email="OpsDesk <notifications@example.com>",
        )
    )

    result = provider.send(
        EmailMessage(
            to_email="recipient@example.com",
            subject="OpsDesk: Test",
            text="Body",
        )
    )

    kwargs = captured["kwargs"]
    assert isinstance(kwargs, dict)
    assert result.status == NotificationDeliveryStatus.SENT
    assert result.provider_message_id == "email_123"
    assert kwargs["json"]["to"] == ["recipient@example.com"]
    assert kwargs["headers"]["Authorization"] == "Bearer test_resend_key"
