"""Backend coverage for SPEC-316 scheduled jobs and operational audit."""

import uuid
from collections.abc import Generator
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from argon2 import PasswordHasher
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import app.services.security as security_service
from app.core.config import Settings, get_settings
from app.db.base import Base
from app.db.session import get_db
from app.jobs.celery_app import celery_app
from app.main import app
from app.models.notification import (
    Notification,
    NotificationDelivery,
    NotificationDeliveryChannel,
    NotificationDeliveryStatus,
    NotificationType,
)
from app.models.operational import OperationalAuditRun, OperationalAuditStatus
from app.models.organization import Invitation, InvitationScope, InvitationStatus, MembershipRole
from app.models.project import (
    ProjectMembership,
    Task,
    TaskType,
    TicketAssignmentRequest,
    TicketAssignmentRequestStatus,
)
from app.models.user import User, UserAccountType
from app.services.operational_audit import (
    JobRunResult,
    OperationalAuditService,
    expired_invitations_job_name,
    external_delivery_retry_job_name,
    heartbeat_job_name,
    ticket_assignment_reminders_job_name,
)


@pytest.fixture(autouse=True)
def fast_password_hasher(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep multi-user operational audit scenarios fast."""
    monkeypatch.setattr(
        security_service,
        "password_hasher",
        PasswordHasher(time_cost=1, memory_cost=512, parallelism=1),
    )


@pytest.fixture
def api_client() -> Generator[tuple[TestClient, Session], None, None]:
    """Run operational audit tests against one isolated in-memory database."""
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = session_factory()
    settings = Settings(
        auth_secret_key="test_secret_key_minimum_32_chars",
        auth_cookie_secure=False,
    )

    def override_get_db() -> Generator[Session, None, None]:
        """Supply the same test database session to every API request."""
        yield session

    def override_get_settings() -> Settings:
        """Supply deterministic auth settings to API tests."""
        return settings

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_settings] = override_get_settings
    try:
        with TestClient(app, backend_options={"use_uvloop": True}) as client:
            yield client, session
    finally:
        app.dependency_overrides.clear()
        session.close()
        Base.metadata.drop_all(engine)
        engine.dispose()


def assert_error(response: Any, status_code: int, code: str) -> None:
    """Assert the stable API error envelope and status code."""
    assert response.status_code == status_code
    assert response.json()["error"]["code"] == code


def create_user(
    client: TestClient,
    session: Session,
    email: str,
    *,
    account_type: UserAccountType = UserAccountType.INTERNAL,
) -> User:
    """Register one user and optionally convert it to a restricted client."""
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Example1234", "full_name": email.split("@")[0]},
    )
    assert response.status_code == 201
    user = session.scalar(select(User).where(User.email == email))
    assert user is not None
    user.account_type = account_type
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def login_as(client: TestClient, user: User) -> None:
    """Replace TestClient cookies with one user's authenticated session."""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": user.email, "password": "Example1234"},
    )
    assert response.status_code == 200


def create_organization(client: TestClient) -> dict[str, Any]:
    """Create one organization through the public API."""
    response = client.post("/api/v1/organizations", json={"name": "Audit Ops"})
    assert response.status_code == 201
    return response.json()


def add_membership(
    session: Session, organization_id: str, user: User, role: MembershipRole
) -> None:
    """Seed organization membership for role-gated audit access."""
    from app.models.organization import OrganizationMembership

    session.add(
        OrganizationMembership(
            organization_id=uuid.UUID(organization_id),
            user_id=user.id,
            role=role,
        )
    )
    session.commit()


def test_celery_beat_registers_expected_scheduled_jobs() -> None:
    """Celery beat exposes the deterministic SPEC-316 job schedule."""
    schedule = celery_app.conf.beat_schedule

    assert schedule["scheduler-heartbeat"]["task"] == "operational.scheduler_heartbeat"
    assert (
        schedule["external-delivery-retry-sweep"]["task"]
        == "operational.external_delivery_retry_sweep"
    )
    assert (
        schedule["expired-invitation-maintenance"]["task"]
        == "operational.expired_invitation_maintenance"
    )
    assert (
        schedule["stale-ticket-assignment-request-reminders"]["task"]
        == "operational.stale_ticket_assignment_request_reminders"
    )


def test_run_job_records_success_and_failure(api_client: tuple[TestClient, Session]) -> None:
    """Scheduled job wrapper records safe success and failure audit rows."""
    _client, session = api_client
    service = OperationalAuditService(session)

    success = service.run_job(
        heartbeat_job_name,
        lambda: JobRunResult(records_seen=3, records_changed=2),
    )

    def fail() -> JobRunResult:
        """Raise a provider-like failure without storing raw sensitive data."""
        raise RuntimeError("secret token abc should be summarized")

    failure = service.run_job("failing_job", fail)

    assert success.status == OperationalAuditStatus.SUCCEEDED
    assert success.records_seen == 3
    assert success.records_changed == 2
    assert failure.status == OperationalAuditStatus.FAILED
    assert failure.error_code == "RuntimeError"
    assert failure.error_message is not None
    assert len(failure.error_message) <= 255
    assert "secret" not in failure.error_message
    assert "token" not in failure.error_message
    assert "abc" not in failure.error_message


def test_external_delivery_retry_sweep_audits_due_delivery(
    api_client: tuple[TestClient, Session],
) -> None:
    """Retry sweep processes due pending deliveries and records safe counts."""
    _client, session = api_client
    recipient = User(
        email="delivery316@example.com",
        password_hash="hash",
        full_name="Delivery User",
    )
    session.add(recipient)
    session.flush()
    notification = Notification(
        recipient_user_id=recipient.id,
        type=NotificationType.TICKET_CREATED,
        title="Ticket created",
        resource_type="ticket",
        resource_id=uuid.uuid4(),
    )
    session.add(notification)
    session.flush()
    delivery = NotificationDelivery(
        notification_id=notification.id,
        recipient_user_id=recipient.id,
        channel=NotificationDeliveryChannel.EMAIL,
        provider="console",
        status=NotificationDeliveryStatus.PENDING,
        next_attempt_at=datetime.now(UTC) - timedelta(minutes=1),
    )
    session.add(delivery)
    session.commit()

    service = OperationalAuditService(session)
    audit = service.run_job(
        external_delivery_retry_job_name,
        lambda: service.external_delivery_retry_sweep(),
    )

    persisted_delivery = session.get(NotificationDelivery, delivery.id)
    assert audit.status == OperationalAuditStatus.SUCCEEDED
    assert audit.records_seen == 1
    assert audit.records_changed == 1
    assert persisted_delivery is not None
    assert persisted_delivery.status == NotificationDeliveryStatus.SENT


def test_expired_invitation_maintenance_marks_pending_expired(
    api_client: tuple[TestClient, Session],
) -> None:
    """Expired pending invitations become terminal without deleting history."""
    client, session = api_client
    owner = create_user(client, session, "owner316@example.com")
    login_as(client, owner)
    organization = create_organization(client)
    target = create_user(client, session, "target316@example.com")
    invitation = Invitation(
        organization_id=uuid.UUID(organization["id"]),
        target_email=target.email,
        target_user_id=target.id,
        role=MembershipRole.MEMBER,
        scope_type=InvitationScope.ORGANIZATION,
        invited_by_id=owner.id,
        status=InvitationStatus.PENDING,
        expires_at=datetime.now(UTC) - timedelta(minutes=1),
    )
    session.add(invitation)
    session.commit()

    service = OperationalAuditService(session)
    audit = service.run_job(expired_invitations_job_name, service.expire_pending_invitations)

    persisted = session.get(Invitation, invitation.id)
    assert audit.records_seen == 1
    assert audit.records_changed == 1
    assert persisted is not None
    assert persisted.status == InvitationStatus.EXPIRED


def test_stale_assignment_request_reminders_are_idempotent(
    api_client: tuple[TestClient, Session],
) -> None:
    """Stale ticket handoff reminders reuse unread resource notifications."""
    client, session = api_client
    owner = create_user(client, session, "owner-reminder316@example.com")
    worker = create_user(client, session, "worker-reminder316@example.com")
    login_as(client, owner)
    organization = create_organization(client)
    project_response = client.post(
        f"/api/v1/organizations/{organization['id']}/projects",
        json={"name": "Reminder Project"},
    )
    assert project_response.status_code == 201
    project_id = uuid.UUID(project_response.json()["id"])
    session.add(
        ProjectMembership(
            organization_id=uuid.UUID(organization["id"]),
            project_id=project_id,
            user_id=worker.id,
            added_by_id=owner.id,
        )
    )
    task = Task(
        organization_id=uuid.UUID(organization["id"]),
        project_id=project_id,
        title="Reminder ticket",
        task_type=TaskType.TICKET,
        assignee_id=owner.id,
        client_user_id=owner.id,
        created_by_id=owner.id,
    )
    session.add(task)
    session.flush()
    request = TicketAssignmentRequest(
        organization_id=uuid.UUID(organization["id"]),
        project_id=project_id,
        task_id=task.id,
        requested_by_id=owner.id,
        target_user_id=worker.id,
        status=TicketAssignmentRequestStatus.PENDING,
        created_at=datetime.now(UTC) - timedelta(days=2),
    )
    session.add(request)
    session.commit()

    service = OperationalAuditService(session)
    first = service.run_job(
        ticket_assignment_reminders_job_name,
        service.remind_stale_assignment_requests,
    )
    second = service.run_job(
        ticket_assignment_reminders_job_name,
        service.remind_stale_assignment_requests,
    )
    notifications = list(
        session.scalars(
            select(Notification).where(
                Notification.recipient_user_id == worker.id,
                Notification.type == NotificationType.TICKET_ASSIGNMENT_REQUESTED,
                Notification.resource_id == task.id,
            )
        )
    )

    assert first.records_seen == 1
    assert first.records_changed == 1
    assert second.records_seen == 1
    assert second.records_changed == 0
    assert len(notifications) == 1


def test_operational_audit_api_filters_and_denies_non_admins(
    api_client: tuple[TestClient, Session],
) -> None:
    """Owner/admin users can list audit rows while members and clients cannot."""
    client, session = api_client
    owner = create_user(client, session, "api-owner316@example.com")
    member = create_user(client, session, "api-member316@example.com")
    client_user = create_user(
        client,
        session,
        "api-client316@example.com",
        account_type=UserAccountType.CLIENT,
    )
    login_as(client, owner)
    organization = create_organization(client)
    add_membership(session, organization["id"], member, MembershipRole.MEMBER)
    session.add_all(
        [
            OperationalAuditRun(
                job_name=heartbeat_job_name,
                started_at=datetime.now(UTC) - timedelta(minutes=2),
                finished_at=datetime.now(UTC) - timedelta(minutes=1),
                status=OperationalAuditStatus.SUCCEEDED,
                records_seen=1,
                records_changed=1,
            ),
            OperationalAuditRun(
                job_name=expired_invitations_job_name,
                started_at=datetime.now(UTC),
                finished_at=datetime.now(UTC),
                status=OperationalAuditStatus.FAILED,
                error_code="RuntimeError",
                error_message="safe failure",
            ),
        ]
    )
    session.commit()

    filtered = client.get(
        "/api/v1/admin/operational-audit",
        params={"job_name": heartbeat_job_name, "status": "succeeded", "limit": 1},
    )
    login_as(client, member)
    member_response = client.get("/api/v1/admin/operational-audit")
    login_as(client, client_user)
    client_response = client.get("/api/v1/admin/operational-audit")
    client.cookies.clear()
    unauthenticated = client.get("/api/v1/admin/operational-audit")

    assert filtered.status_code == 200
    assert filtered.json()["total"] == 1
    assert filtered.json()["items"][0]["job_name"] == heartbeat_job_name
    assert_error(member_response, 403, "insufficient_role")
    assert_error(client_response, 403, "insufficient_role")
    assert_error(unauthenticated, 401, "not_authenticated")
