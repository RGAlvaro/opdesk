"""Endpoint-level coverage for SPEC-305 project clients and tickets."""

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
from app.core.config import Settings, get_settings
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.notification import Notification, NotificationType
from app.models.organization import MembershipRole, OrganizationMembership
from app.models.project import (
    ProjectMembership,
    Task,
    TaskType,
    TicketAssignmentRequest,
    TicketAssignmentRequestStatus,
)
from app.models.user import User, UserAccountType


@pytest.fixture(autouse=True)
def fast_password_hasher(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep multi-account API scenarios fast while preserving password behavior."""
    monkeypatch.setattr(
        security_service,
        "password_hasher",
        PasswordHasher(time_cost=1, memory_cost=512, parallelism=1),
    )


@pytest.fixture
def api_client() -> Generator[tuple[TestClient, Session], None, None]:
    """Run SPEC-305 endpoints against one isolated in-memory database."""
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
        """Supply the same test session to every request."""
        yield session

    def override_get_settings() -> Settings:
        """Supply deterministic auth settings."""
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
    """Assert the stable API error envelope."""
    assert response.status_code == status_code
    assert response.json()["error"]["code"] == code


def create_user(client: TestClient, session: Session, email: str) -> User:
    """Register an internal user through HTTP and return its model."""
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Example1234", "full_name": email.split("@")[0]},
    )
    assert response.status_code == 201
    user = session.scalar(select(User).where(User.email == email))
    assert user is not None
    return user


def login_as(client: TestClient, email: str, password: str = "Example1234") -> None:
    """Replace TestClient cookies with one user's session."""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200


def create_organization(client: TestClient) -> dict[str, Any]:
    """Create one organization through the public API."""
    response = client.post("/api/v1/organizations", json={"name": "Acme Ops"})
    assert response.status_code == 201
    return response.json()


def add_membership(
    session: Session, organization_id: str, user: User, role: MembershipRole
) -> None:
    """Seed organization membership for non-invitation scenarios."""
    session.add(
        OrganizationMembership(
            organization_id=uuid.UUID(organization_id),
            user_id=user.id,
            role=role,
        )
    )
    session.commit()


def add_project_membership(
    session: Session, organization_id: str, project_id: str, user: User
) -> None:
    """Seed explicit project membership for assignment and visibility."""
    session.add(
        ProjectMembership(
            organization_id=uuid.UUID(organization_id),
            project_id=uuid.UUID(project_id),
            user_id=user.id,
            added_by_id=None,
        )
    )
    session.commit()


def create_project(client: TestClient, organization_id: str) -> dict[str, Any]:
    """Create one project through the public API."""
    response = client.post(
        f"/api/v1/organizations/{organization_id}/projects",
        json={"name": "Customer Support", "description": "Support work"},
    )
    assert response.status_code == 201
    return response.json()


def setup_project(
    client: TestClient, session: Session
) -> tuple[dict[str, Any], dict[str, Any], User, User]:
    """Create an owner, worker, organization, and project for SPEC-305 tests."""
    owner = create_user(client, session, "owner@example.com")
    worker = create_user(client, session, "worker@example.com")
    login_as(client, owner.email)
    organization = create_organization(client)
    add_membership(session, organization["id"], worker, MembershipRole.MEMBER)
    project = create_project(client, organization["id"])
    add_project_membership(session, organization["id"], project["id"], worker)
    return organization, project, owner, worker


def grant_client(client: TestClient, project_id: str) -> dict[str, Any]:
    """Create a restricted client account for a project."""
    response = client.post(
        f"/api/v1/projects/{project_id}/clients",
        json={
            "email": "client@example.com",
            "full_name": "Client User",
            "password": "Example1234",
        },
    )
    assert response.status_code == 201
    return response.json()


def test_owner_grants_restricted_client_account(api_client: tuple[TestClient, Session]) -> None:
    """Owner-created clients can authenticate but are not organization members."""
    client, session = api_client
    _, project, _, _ = setup_project(client, session)

    access = grant_client(client, project["id"])
    persisted_client = session.get(User, uuid.UUID(access["client_user_id"]))
    login_as(client, "client@example.com")
    me = client.get("/api/v1/users/me")
    projects = client.get("/api/v1/client/projects")
    internal_clients = client.get(f"/api/v1/projects/{project['id']}/clients")

    assert persisted_client is not None
    assert persisted_client.account_type == UserAccountType.CLIENT
    assert access["client"]["account_type"] == "client"
    assert me.json()["account_type"] == "client"
    assert projects.status_code == 200
    assert projects.json()["items"][0]["id"] == project["id"]
    assert_error(internal_clients, 403, "internal_member_required")


def test_client_creates_and_tracks_own_ticket(api_client: tuple[TestClient, Session]) -> None:
    """Clients create tickets only in accessible projects and see only their own tickets."""
    client, session = api_client
    _, project, owner, worker = setup_project(client, session)
    access = grant_client(client, project["id"])
    login_as(client, "client@example.com")

    created = client.post(
        f"/api/v1/client/projects/{project['id']}/tickets",
        json={"subject": "Printer down", "description": "The front desk printer is offline."},
    )
    own_list = client.get("/api/v1/client/tickets")
    login_as(client, owner.email)
    internal_list = client.get(f"/api/v1/projects/{project['id']}/tickets")
    assigned = client.patch(
        f"/api/v1/tickets/{created.json()['id']}",
        json={"assignee_id": str(worker.id), "status": "in_progress"},
    )
    login_as(client, "client@example.com")
    revoke_blocked = client.delete(f"/api/v1/projects/{project['id']}/clients/{access['id']}")

    assert created.status_code == 201
    ticket = created.json()
    assert ticket["task_type"] == "ticket"
    assert ticket["client_user_id"] == access["client_user_id"]
    assert session.get(Task, uuid.UUID(ticket["id"])).task_type == TaskType.TICKET
    assert own_list.json()["items"][0]["id"] == ticket["id"]
    assert internal_list.json()["items"][0]["id"] == ticket["id"]
    assert assigned.status_code == 200
    assert assigned.json()["assignee_id"] == str(worker.id)
    assert_error(revoke_blocked, 403, "internal_member_required")


def test_revoked_client_cannot_create_new_tickets_but_can_view_history(
    api_client: tuple[TestClient, Session],
) -> None:
    """Revocation blocks new tickets while preserving client-owned ticket history."""
    client, session = api_client
    _, project, owner, _ = setup_project(client, session)
    access = grant_client(client, project["id"])
    login_as(client, "client@example.com")
    created = client.post(
        f"/api/v1/client/projects/{project['id']}/tickets",
        json={"subject": "Door code", "description": "The current door code does not work."},
    )
    login_as(client, owner.email)
    revoked = client.delete(f"/api/v1/projects/{project['id']}/clients/{access['id']}")
    login_as(client, "client@example.com")
    blocked = client.post(
        f"/api/v1/client/projects/{project['id']}/tickets",
        json={"subject": "Another issue", "description": "This should be blocked."},
    )
    history = client.get(f"/api/v1/client/tickets/{created.json()['id']}")

    assert revoked.status_code == 204
    assert_error(blocked, 409, "client_access_revoked")
    assert history.status_code == 200
    assert history.json()["id"] == created.json()["id"]


def test_ticket_comments_notify_once_per_unread_ticket(
    api_client: tuple[TestClient, Session],
) -> None:
    """Ticket comments create aggregate unread notifications instead of one per comment."""
    client, session = api_client
    _, project, owner, worker = setup_project(client, session)
    grant_client(client, project["id"])
    login_as(client, "client@example.com")
    ticket = client.post(
        f"/api/v1/client/projects/{project['id']}/tickets",
        json={"subject": "Slow laptop", "description": "Boot takes ten minutes."},
    ).json()
    login_as(client, owner.email)
    client.patch(f"/api/v1/tickets/{ticket['id']}", json={"assignee_id": str(worker.id)})
    login_as(client, "client@example.com")

    first = client.post(
        f"/api/v1/client/tickets/{ticket['id']}/comments", json={"body": "Any update?"}
    )
    second = client.post(
        f"/api/v1/client/tickets/{ticket['id']}/comments", json={"body": "Still blocked."}
    )
    login_as(client, worker.email)
    worker_comments = client.get(f"/api/v1/tickets/{ticket['id']}/comments")
    login_as(client, owner.email)
    owner_reply = client.post(
        f"/api/v1/tickets/{ticket['id']}/comments", json={"body": "We are checking it."}
    )
    notifications = list(
        session.scalars(
            select(Notification).where(
                Notification.type == NotificationType.TICKET_COMMENT,
                Notification.resource_id == uuid.UUID(ticket["id"]),
            )
        )
    )

    assert first.status_code == 201
    assert second.status_code == 201
    assert worker_comments.status_code == 200
    assert len(worker_comments.json()["items"]) == 2
    assert owner_reply.status_code == 201
    assert len([item for item in notifications if item.recipient_user_id == worker.id]) == 1


def test_assigned_worker_requests_and_target_accepts_reassignment(
    api_client: tuple[TestClient, Session],
) -> None:
    """Worker handoffs notify the target and apply only after target acceptance."""
    client, session = api_client
    organization, project, owner, worker = setup_project(client, session)
    target = create_user(client, session, "target@example.com")
    add_membership(session, organization["id"], target, MembershipRole.ADMIN)
    add_project_membership(session, organization["id"], project["id"], target)
    grant_client(client, project["id"])
    login_as(client, "client@example.com")
    ticket = client.post(
        f"/api/v1/client/projects/{project['id']}/tickets",
        json={"subject": "Laptop handoff", "description": "Please move this ticket."},
    ).json()
    login_as(client, owner.email)
    assigned = client.patch(f"/api/v1/tickets/{ticket['id']}", json={"assignee_id": str(worker.id)})
    login_as(client, worker.email)
    status_update = client.patch(f"/api/v1/tickets/{ticket['id']}", json={"status": "in_progress"})
    request = client.post(
        f"/api/v1/tickets/{ticket['id']}/assignment-requests",
        json={"target_user_id": str(target.id)},
    )
    persisted_before_accept = session.get(Task, uuid.UUID(ticket["id"]))
    assert persisted_before_accept is not None
    assignee_before_accept = persisted_before_accept.assignee_id
    login_as(client, target.email)
    pending = client.get("/api/v1/ticket-assignment-requests")
    accepted = client.post(f"/api/v1/ticket-assignment-requests/{request.json()['id']}/accept")
    persisted_after_accept = session.get(Task, uuid.UUID(ticket["id"]))
    notifications = list(
        session.scalars(
            select(Notification).where(
                Notification.type == NotificationType.TICKET_ASSIGNMENT_REQUESTED,
                Notification.resource_id == uuid.UUID(ticket["id"]),
                Notification.recipient_user_id == target.id,
            )
        )
    )

    assert assigned.status_code == 200
    assert status_update.status_code == 200
    assert status_update.json()["status"] == "in_progress"
    assert request.status_code == 201
    assert request.json()["status"] == "pending"
    assert assignee_before_accept == worker.id
    assert pending.status_code == 200
    assert pending.json()["items"][0]["id"] == request.json()["id"]
    assert accepted.status_code == 200
    assert accepted.json()["status"] == "accepted"
    assert persisted_after_accept is not None
    assert persisted_after_accept.assignee_id == target.id
    assert len(notifications) == 1


def test_assignment_request_decline_keeps_original_assignee(
    api_client: tuple[TestClient, Session],
) -> None:
    """Declining a ticket handoff resolves the request without changing assignee."""
    client, session = api_client
    organization, project, owner, worker = setup_project(client, session)
    target = create_user(client, session, "decline-target@example.com")
    add_membership(session, organization["id"], target, MembershipRole.ADMIN)
    add_project_membership(session, organization["id"], project["id"], target)
    grant_client(client, project["id"])
    login_as(client, "client@example.com")
    ticket = client.post(
        f"/api/v1/client/projects/{project['id']}/tickets",
        json={"subject": "Decline handoff", "description": "Please decline this ticket."},
    ).json()
    login_as(client, owner.email)
    client.patch(f"/api/v1/tickets/{ticket['id']}", json={"assignee_id": str(worker.id)})
    login_as(client, worker.email)
    request = client.post(
        f"/api/v1/tickets/{ticket['id']}/assignment-requests",
        json={"target_user_id": str(target.id)},
    )
    login_as(client, target.email)
    declined = client.post(f"/api/v1/ticket-assignment-requests/{request.json()['id']}/decline")
    persisted_ticket = session.get(Task, uuid.UUID(ticket["id"]))
    persisted_request = session.get(TicketAssignmentRequest, uuid.UUID(request.json()["id"]))

    assert request.status_code == 201
    assert declined.status_code == 200
    assert declined.json()["status"] == "declined"
    assert persisted_ticket is not None
    assert persisted_ticket.assignee_id == worker.id
    assert persisted_request is not None
    assert persisted_request.status == TicketAssignmentRequestStatus.DECLINED


def test_assignment_request_list_revalidates_target_project_access(
    api_client: tuple[TestClient, Session],
) -> None:
    """Removed project members do not keep seeing pending handoff ticket metadata."""
    client, session = api_client
    organization, project, owner, worker = setup_project(client, session)
    target = create_user(client, session, "removed-target@example.com")
    add_membership(session, organization["id"], target, MembershipRole.MEMBER)
    add_project_membership(session, organization["id"], project["id"], target)
    grant_client(client, project["id"])
    login_as(client, "client@example.com")
    ticket = client.post(
        f"/api/v1/client/projects/{project['id']}/tickets",
        json={"subject": "Hidden handoff", "description": "Do not leak this ticket."},
    ).json()
    login_as(client, owner.email)
    client.patch(f"/api/v1/tickets/{ticket['id']}", json={"assignee_id": str(worker.id)})
    login_as(client, worker.email)
    request = client.post(
        f"/api/v1/tickets/{ticket['id']}/assignment-requests",
        json={"target_user_id": str(target.id)},
    )
    project_membership = session.scalar(
        select(ProjectMembership).where(
            ProjectMembership.project_id == uuid.UUID(project["id"]),
            ProjectMembership.user_id == target.id,
        )
    )
    assert project_membership is not None
    session.delete(project_membership)
    session.commit()
    login_as(client, target.email)

    pending = client.get("/api/v1/ticket-assignment-requests")

    assert request.status_code == 201
    assert pending.status_code == 200
    assert pending.json()["items"] == []
    assert pending.json()["total"] == 0


def test_assignment_request_accept_revalidates_target_project_access(
    api_client: tuple[TestClient, Session],
) -> None:
    """Targets who lose project access cannot accept and become ticket assignees."""
    client, session = api_client
    organization, project, owner, worker = setup_project(client, session)
    target = create_user(client, session, "accept-removed-target@example.com")
    add_membership(session, organization["id"], target, MembershipRole.ADMIN)
    add_project_membership(session, organization["id"], project["id"], target)
    grant_client(client, project["id"])
    login_as(client, "client@example.com")
    ticket = client.post(
        f"/api/v1/client/projects/{project['id']}/tickets",
        json={"subject": "Blocked accept", "description": "Do not assign removed users."},
    ).json()
    login_as(client, owner.email)
    client.patch(f"/api/v1/tickets/{ticket['id']}", json={"assignee_id": str(worker.id)})
    login_as(client, worker.email)
    request = client.post(
        f"/api/v1/tickets/{ticket['id']}/assignment-requests",
        json={"target_user_id": str(target.id)},
    )
    project_membership = session.scalar(
        select(ProjectMembership).where(
            ProjectMembership.project_id == uuid.UUID(project["id"]),
            ProjectMembership.user_id == target.id,
        )
    )
    assert project_membership is not None
    session.delete(project_membership)
    session.commit()
    login_as(client, target.email)

    accepted = client.post(f"/api/v1/ticket-assignment-requests/{request.json()['id']}/accept")
    persisted_ticket = session.get(Task, uuid.UUID(ticket["id"]))
    persisted_request = session.get(TicketAssignmentRequest, uuid.UUID(request.json()["id"]))

    assert_error(accepted, 400, "invalid_ticket")
    assert persisted_ticket is not None
    assert persisted_ticket.assignee_id == worker.id
    assert persisted_request is not None
    assert persisted_request.status == TicketAssignmentRequestStatus.PENDING
