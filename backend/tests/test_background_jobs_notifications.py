"""Backend coverage for SPEC-201 background jobs and task notifications."""

import uuid
from collections.abc import Generator
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from argon2 import PasswordHasher
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import app.jobs.tasks as job_tasks
import app.services.security as security_service
import app.services.tasks as task_service_module
from app.core.config import Settings, get_settings
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.organization import MembershipRole, Organization, OrganizationMembership
from app.models.project import Project, ProjectMembership, Task
from app.models.user import User
from app.notifications.assignment import (
    TaskAssignmentNotificationPayload,
    build_task_assignment_notification_payload,
    process_task_assignment_notification,
)


@pytest.fixture(autouse=True)
def fast_password_hasher(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep API setup fast while preserving password behavior."""
    monkeypatch.setattr(
        security_service,
        "password_hasher",
        PasswordHasher(time_cost=1, memory_cost=512, parallelism=1),
    )


@pytest.fixture
def api_client() -> Generator[tuple[TestClient, Session], None, None]:
    """Run notification API integration tests against an isolated database."""
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
        celery_task_always_eager=True,
    )

    def override_get_db() -> Generator[Session, None, None]:
        """Supply the same database session to all requests in one test."""
        yield session

    def override_get_settings() -> Settings:
        """Supply deterministic auth and Celery settings."""
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


def register_user(client: TestClient, session: Session, email: str) -> User:
    """Create a user through the public auth API and return its model."""
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Example1234", "full_name": email.split("@")[0]},
    )
    assert response.status_code == 201
    user = session.query(User).filter_by(email=email).one()
    return user


def login_as(client: TestClient, user: User) -> None:
    """Replace the test client's session cookies with the selected user."""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": user.email, "password": "Example1234"},
    )
    assert response.status_code == 200


def create_org_project_and_member(
    client: TestClient, session: Session
) -> tuple[dict[str, Any], dict[str, Any], User, User]:
    """Create one organization, one project, and a member assignee."""
    owner = register_user(client, session, "owner201@example.com")
    member = register_user(client, session, "member201@example.com")
    login_as(client, owner)
    organization_response = client.post("/api/v1/organizations", json={"name": "Notify Ops"})
    assert organization_response.status_code == 201
    organization = organization_response.json()
    session.add(
        OrganizationMembership(
            organization_id=uuid.UUID(organization["id"]),
            user_id=member.id,
            role=MembershipRole.MEMBER,
        )
    )
    session.commit()
    project_response = client.post(
        f"/api/v1/organizations/{organization['id']}/projects",
        json={"name": "Notification Project"},
    )
    assert project_response.status_code == 201
    session.add(
        ProjectMembership(
            organization_id=uuid.UUID(organization["id"]),
            project_id=uuid.UUID(project_response.json()["id"]),
            user_id=member.id,
            added_by_id=owner.id,
        )
    )
    session.commit()
    return organization, project_response.json(), owner, member


def test_task_assignment_payload_is_minimal() -> None:
    """Payload creation keeps only safe IDs and an assignment version."""
    task_id = uuid.uuid4()
    assignee_id = uuid.uuid4()
    updated_at = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)
    task = Task(
        id=task_id,
        organization_id=uuid.uuid4(),
        project_id=uuid.uuid4(),
        title="Notify assignee",
        assignee_id=assignee_id,
        created_by_id=uuid.uuid4(),
        updated_at=updated_at,
    )

    payload = build_task_assignment_notification_payload(task)

    assert payload == TaskAssignmentNotificationPayload(
        task_id=task_id,
        assignee_id=assignee_id,
        assignment_version=updated_at.isoformat(),
    )


def test_task_create_and_reassign_enqueue_notification_jobs(
    api_client: tuple[TestClient, Session],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Task creation with an assignee and reassignment both enqueue jobs."""
    client, session = api_client
    _, project, _, member = create_org_project_and_member(client, session)
    enqueued: list[TaskAssignmentNotificationPayload] = []

    def record_enqueue(task: Task) -> bool:
        """Capture the payload that service code would publish to Celery."""
        enqueued.append(build_task_assignment_notification_payload(task))
        return True

    monkeypatch.setattr(task_service_module, "enqueue_task_assignment_notification", record_enqueue)

    created = client.post(
        f"/api/v1/projects/{project['id']}/tasks",
        json={"title": "Assigned at creation", "assignee_id": str(member.id)},
    )
    unassigned = client.post(
        f"/api/v1/projects/{project['id']}/tasks",
        json={"title": "Assigned later"},
    )
    reassigned = client.patch(
        f"/api/v1/tasks/{unassigned.json()['id']}",
        json={"assignee_id": str(member.id)},
    )

    assert created.status_code == 201
    assert unassigned.status_code == 201
    assert reassigned.status_code == 200
    assert [payload.assignee_id for payload in enqueued] == [member.id, member.id]
    assert {str(payload.task_id) for payload in enqueued} == {
        created.json()["id"],
        reassigned.json()["id"],
    }


def test_worker_process_delivers_current_assignment(session_factory: sessionmaker[Session]) -> None:
    """Worker processing delivers when the payload still matches current task state."""
    session = session_factory()
    organization_id = uuid.uuid4()
    assignee = User(
        id=uuid.uuid4(),
        email="worker-assignee@example.com",
        password_hash="hash",
        full_name="Worker Assignee",
    )
    creator = User(
        id=uuid.uuid4(),
        email="worker-owner@example.com",
        password_hash="hash",
        full_name="Worker Owner",
    )
    organization = Organization(id=organization_id, name="Worker Org", slug="worker-org")
    project = Project(id=uuid.uuid4(), organization_id=organization_id, name="Worker Project")
    task = Task(
        id=uuid.uuid4(),
        organization_id=organization_id,
        project_id=project.id,
        title="Worker task",
        assignee_id=assignee.id,
        created_by_id=creator.id,
        updated_at=datetime(2026, 7, 7, 12, 0, tzinfo=UTC),
    )
    session.add_all([assignee, creator, organization, project, task])
    session.commit()
    payload = build_task_assignment_notification_payload(task)

    result = process_task_assignment_notification(session, payload)

    assert result == "delivered"
    session.close()


def test_worker_process_ignores_stale_assignment_version(
    session_factory: sessionmaker[Session],
) -> None:
    """Worker processing ignores old jobs when assignment version no longer matches."""
    session = session_factory()
    organization_id = uuid.uuid4()
    assignee = User(
        id=uuid.uuid4(),
        email="stale-assignee@example.com",
        password_hash="hash",
        full_name="Stale Assignee",
    )
    creator = User(
        id=uuid.uuid4(),
        email="stale-owner@example.com",
        password_hash="hash",
        full_name="Stale Owner",
    )
    organization = Organization(id=organization_id, name="Stale Org", slug="stale-org")
    project = Project(id=uuid.uuid4(), organization_id=organization_id, name="Stale Project")
    first_version = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)
    task = Task(
        id=uuid.uuid4(),
        organization_id=organization_id,
        project_id=project.id,
        title="Stale task",
        assignee_id=assignee.id,
        created_by_id=creator.id,
        updated_at=first_version,
    )
    session.add_all([assignee, creator, organization, project, task])
    session.commit()
    payload = build_task_assignment_notification_payload(task)
    task.updated_at = first_version + timedelta(minutes=5)
    session.add(task)
    session.commit()

    result = process_task_assignment_notification(session, payload)

    assert result == "stale"
    session.close()


def test_worker_task_uses_eager_style_database_session(
    session_factory: sessionmaker[Session],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The Celery task can run synchronously with a fake broker and local session factory."""
    session = session_factory()
    organization_id = uuid.uuid4()
    assignee = User(
        id=uuid.uuid4(),
        email="eager-assignee@example.com",
        password_hash="hash",
        full_name="Eager Assignee",
    )
    creator = User(
        id=uuid.uuid4(),
        email="eager-owner@example.com",
        password_hash="hash",
        full_name="Eager Owner",
    )
    organization = Organization(id=organization_id, name="Eager Org", slug="eager-org")
    project = Project(id=uuid.uuid4(), organization_id=organization_id, name="Eager Project")
    task = Task(
        id=uuid.uuid4(),
        organization_id=organization_id,
        project_id=project.id,
        title="Eager task",
        assignee_id=assignee.id,
        created_by_id=creator.id,
        updated_at=datetime(2026, 7, 7, 12, 0, tzinfo=UTC),
    )
    session.add_all([assignee, creator, organization, project, task])
    session.commit()
    payload = build_task_assignment_notification_payload(task)
    session.close()
    monkeypatch.setattr(job_tasks, "SessionLocal", session_factory)

    result = job_tasks.send_task_assignment_notification.run(
        str(payload.task_id),
        str(payload.assignee_id),
        payload.assignment_version,
    )

    assert result == "delivered"


def test_worker_task_rejects_invalid_payload_without_retry() -> None:
    """Invalid job identifiers are logged and treated as non-retryable payloads."""
    result = job_tasks.send_task_assignment_notification.run(
        "not-a-uuid",
        str(uuid.uuid4()),
        "2026-07-07T12:00:00+00:00",
    )

    assert result == "invalid"


@pytest.fixture
def session_factory() -> Generator[sessionmaker[Session], None, None]:
    """Provide a reusable in-memory session factory for worker tests."""
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    try:
        yield factory
    finally:
        Base.metadata.drop_all(engine)
        engine.dispose()
