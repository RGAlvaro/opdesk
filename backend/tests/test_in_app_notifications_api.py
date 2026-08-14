"""Endpoint-level and service coverage for SPEC-306 in-app notifications."""

import uuid
from collections.abc import Generator
from typing import Any

import pytest
from argon2 import PasswordHasher
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import app.services.security as security_service
import app.services.tasks as task_service_module
from app.core.config import Settings, get_settings
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.notification import Notification, NotificationType
from app.models.organization import MembershipRole, OrganizationMembership
from app.models.project import ProjectMembership
from app.models.user import User


@pytest.fixture(autouse=True)
def fast_password_hasher(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep multi-user notification scenarios fast while preserving password behavior."""
    monkeypatch.setattr(
        security_service,
        "password_hasher",
        PasswordHasher(time_cost=1, memory_cost=512, parallelism=1),
    )


@pytest.fixture(autouse=True)
def disable_task_notification_enqueue(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep task notification tests independent from the external Celery broker."""
    monkeypatch.setattr(
        task_service_module,
        "enqueue_task_assignment_notification",
        lambda task: True,
    )


@pytest.fixture
def api_client() -> Generator[tuple[TestClient, Session], None, None]:
    """Run notification endpoint tests against one isolated in-memory database."""
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
        """Supply deterministic auth settings to notification API tests."""
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
    """Assert the public API error envelope and status code."""
    assert response.status_code == status_code
    assert response.json()["error"]["code"] == code
    assert response.json()["error"]["details"] == {}


def create_user(client: TestClient, session: Session, email: str) -> User:
    """Register one user through the public auth API."""
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Example1234", "full_name": email.split("@")[0]},
    )
    assert response.status_code == 201
    user = session.scalar(select(User).where(User.email == email))
    assert user is not None
    return user


def login_as(client: TestClient, user: User) -> None:
    """Replace the browser session with one user's auth cookies."""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": user.email, "password": "Example1234"},
    )
    assert response.status_code == 200


def create_organization(client: TestClient, name: str = "Notify Ops") -> dict[str, Any]:
    """Create an organization through the public API."""
    response = client.post("/api/v1/organizations", json={"name": name})
    assert response.status_code == 201
    return response.json()


def add_membership(
    session: Session, organization_id: str, user: User, role: MembershipRole
) -> OrganizationMembership:
    """Seed organization membership for project and task notification setup."""
    membership = OrganizationMembership(
        organization_id=uuid.UUID(organization_id),
        user_id=user.id,
        role=role,
    )
    session.add(membership)
    session.commit()
    session.refresh(membership)
    return membership


def add_project_membership(
    session: Session, organization_id: str, project_id: str, user: User
) -> ProjectMembership:
    """Seed explicit project access for notification recipients."""
    membership = ProjectMembership(
        organization_id=uuid.UUID(organization_id),
        project_id=uuid.UUID(project_id),
        user_id=user.id,
        added_by_id=None,
    )
    session.add(membership)
    session.commit()
    session.refresh(membership)
    return membership


def create_project(client: TestClient, organization_id: str, name: str) -> dict[str, Any]:
    """Create one project as the current authenticated user."""
    response = client.post(f"/api/v1/organizations/{organization_id}/projects", json={"name": name})
    assert response.status_code == 201
    return response.json()


def test_invitation_notifications_are_actionable_and_mark_read(
    api_client: tuple[TestClient, Session],
) -> None:
    """SPEC-303 invitations create unread notifications backed by invitation state."""
    client, session = api_client
    owner = create_user(client, session, "owner306@example.com")
    target = create_user(client, session, "target306@example.com")
    outsider = create_user(client, session, "outsider306@example.com")
    login_as(client, owner)
    organization = create_organization(client)

    invite_response = client.post(
        f"/api/v1/organizations/{organization['id']}/invitations",
        json={"email": target.email, "role": "member"},
    )
    assert invite_response.status_code == 201
    notification = session.scalar(
        select(Notification).where(Notification.recipient_user_id == target.id)
    )
    assert notification is not None
    assert notification.type == NotificationType.INVITATION_ORGANIZATION
    assert notification.action_url == "/app/invitations"
    assert notification.resource_id == uuid.UUID(invite_response.json()["id"])

    login_as(client, target)
    count_response = client.get("/api/v1/notifications/unread-count")
    list_response = client.get("/api/v1/notifications?unread=true")
    read_response = client.patch(
        f"/api/v1/notifications/{notification.id}",
        json={"read": True},
    )
    unread_after_patch = client.get("/api/v1/notifications/unread-count")
    unread_toggle = client.patch(
        f"/api/v1/notifications/{notification.id}",
        json={"read": False},
    )
    accept_response = client.post(f"/api/v1/invitations/{invite_response.json()['id']}/accept")
    unread_after_accept = client.get("/api/v1/notifications/unread-count")

    login_as(client, outsider)
    hidden_response = client.patch(
        f"/api/v1/notifications/{notification.id}",
        json={"read": True},
    )

    assert count_response.json() == {"unread_count": 1}
    assert list_response.json()["total"] == 1
    assert read_response.status_code == 200
    assert read_response.json()["read_at"] is not None
    assert unread_after_patch.json() == {"unread_count": 0}
    assert unread_toggle.status_code == 200
    assert unread_toggle.json()["read_at"] is None
    assert accept_response.status_code == 200
    assert unread_after_accept.json() == {"unread_count": 0}
    assert_error(hidden_response, 404, "notification_not_found")


def test_mark_all_read_is_recipient_scoped(api_client: tuple[TestClient, Session]) -> None:
    """Mark-all-read updates only the current user's unread notifications."""
    client, session = api_client
    first = create_user(client, session, "first306@example.com")
    second = create_user(client, session, "second306@example.com")
    session.add_all(
        [
            Notification(
                recipient_user_id=first.id,
                type=NotificationType.PROJECT_UPDATED,
                title="Project updated",
                resource_type="project",
                resource_id=uuid.uuid4(),
            ),
            Notification(
                recipient_user_id=second.id,
                type=NotificationType.PROJECT_UPDATED,
                title="Project updated",
                resource_type="project",
                resource_id=uuid.uuid4(),
            ),
        ]
    )
    session.commit()

    login_as(client, first)
    response = client.post("/api/v1/notifications/mark-all-read")

    first_count = session.scalar(
        select(Notification).where(
            Notification.recipient_user_id == first.id,
            Notification.read_at.is_(None),
        )
    )
    second_count = session.scalar(
        select(Notification).where(
            Notification.recipient_user_id == second.id,
            Notification.read_at.is_(None),
        )
    )
    assert response.status_code == 204
    assert first_count is None
    assert second_count is not None


def test_project_and_task_events_create_notifications(
    api_client: tuple[TestClient, Session],
) -> None:
    """Project and task changes fan out to the intended explicit recipients."""
    client, session = api_client
    owner = create_user(client, session, "project-owner306@example.com")
    member = create_user(client, session, "project-member306@example.com")
    watcher = create_user(client, session, "watcher306@example.com")
    login_as(client, owner)
    organization = create_organization(client)
    add_membership(session, organization["id"], member, MembershipRole.MEMBER)
    add_membership(session, organization["id"], watcher, MembershipRole.MEMBER)
    project = create_project(client, organization["id"], "Notification Rollout")
    add_project_membership(session, organization["id"], project["id"], member)
    add_project_membership(session, organization["id"], project["id"], watcher)

    project_update = client.patch(
        f"/api/v1/projects/{project['id']}",
        json={"status": "on_hold"},
    )
    task_create = client.post(
        f"/api/v1/projects/{project['id']}/tasks",
        json={
            "title": "Prepare inbox",
            "assignee_id": str(member.id),
            "watcher_ids": [str(watcher.id)],
        },
    )
    task_update = client.patch(
        f"/api/v1/tasks/{task_create.json()['id']}",
        json={"status": "in_progress"},
    )

    member_notifications = list(
        session.scalars(select(Notification).where(Notification.recipient_user_id == member.id))
    )
    watcher_notifications = list(
        session.scalars(select(Notification).where(Notification.recipient_user_id == watcher.id))
    )
    owner_notifications = list(
        session.scalars(select(Notification).where(Notification.recipient_user_id == owner.id))
    )

    assert project_update.status_code == 200
    assert task_create.status_code == 201
    assert task_update.status_code == 200
    assert {notification.type for notification in member_notifications} == {
        NotificationType.PROJECT_UPDATED,
        NotificationType.TASK_CREATED,
        NotificationType.TASK_STATUS_CHANGED,
    }
    assert {notification.type for notification in watcher_notifications} == {
        NotificationType.PROJECT_UPDATED,
        NotificationType.TASK_STATUS_CHANGED,
    }
    assert owner_notifications == []
