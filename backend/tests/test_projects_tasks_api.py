"""Endpoint-level projects and tasks coverage for SPEC-103."""

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
from app.models.organization import MembershipRole, OrganizationMembership
from app.models.project import Task
from app.models.user import User


@pytest.fixture(autouse=True)
def fast_password_hasher(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep multi-user API scenarios fast while preserving password behavior."""
    monkeypatch.setattr(
        security_service,
        "password_hasher",
        PasswordHasher(time_cost=1, memory_cost=512, parallelism=1),
    )


@pytest.fixture
def api_client() -> Generator[tuple[TestClient, Session], None, None]:
    """Run project/task endpoints against one isolated in-memory database."""
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
        """Supply the same test transaction source to every API request."""
        yield session

    def override_get_settings() -> Settings:
        """Supply deterministic auth settings to project/task API tests."""
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
    """Assert the status and stable error envelope returned by the public API."""
    assert response.status_code == status_code
    assert response.json()["error"] == {
        "code": code,
        "message": response.json()["error"]["message"],
        "details": {},
    }


def create_user(client: TestClient, session: Session, email: str) -> User:
    """Register a user through HTTP and return its persisted model."""
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Example1234", "full_name": email.split("@")[0]},
    )
    assert response.status_code == 201
    user = session.scalar(select(User).where(User.email == email))
    assert user is not None
    return user


def login_as(client: TestClient, user: User) -> None:
    """Replace the client's browser session with the supplied user's cookies."""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": user.email, "password": "Example1234"},
    )
    assert response.status_code == 200


def create_organization(client: TestClient, name: str = "Acme Ops") -> dict[str, Any]:
    """Create an organization through HTTP and return its response document."""
    response = client.post("/api/v1/organizations", json={"name": name})
    assert response.status_code == 201
    return response.json()


def add_membership(
    session: Session, organization_id: str, user: User, role: MembershipRole
) -> OrganizationMembership:
    """Seed a membership because invitations are outside the active specs."""
    membership = OrganizationMembership(
        organization_id=uuid.UUID(organization_id),
        user_id=user.id,
        role=role,
    )
    session.add(membership)
    session.commit()
    session.refresh(membership)
    return membership


def create_project(
    client: TestClient, organization_id: str, name: str = "Customer Onboarding"
) -> dict[str, Any]:
    """Create a project through HTTP and return its response document."""
    response = client.post(
        f"/api/v1/organizations/{organization_id}/projects",
        json={"name": name, "description": "Implementation work"},
    )
    assert response.status_code == 201
    return response.json()


def create_task(
    client: TestClient,
    project_id: str,
    *,
    title: str = "Call customer",
    priority: str = "medium",
    assignee_id: uuid.UUID | None = None,
    due_date: str | None = None,
) -> dict[str, Any]:
    """Create a task through HTTP and return its response document."""
    payload: dict[str, Any] = {"title": title, "priority": priority}
    if assignee_id is not None:
        payload["assignee_id"] = str(assignee_id)
    if due_date is not None:
        payload["due_date"] = due_date
    response = client.post(f"/api/v1/projects/{project_id}/tasks", json=payload)
    assert response.status_code == 201
    return response.json()


def organization_team(
    client: TestClient, session: Session
) -> tuple[dict[str, Any], User, User, User, User]:
    """Create one organization with owner, admin, member, and outsider actors."""
    owner = create_user(client, session, "owner@example.com")
    admin = create_user(client, session, "admin@example.com")
    member = create_user(client, session, "member@example.com")
    outsider = create_user(client, session, "outsider@example.com")
    login_as(client, owner)
    organization = create_organization(client)
    add_membership(session, organization["id"], admin, MembershipRole.ADMIN)
    add_membership(session, organization["id"], member, MembershipRole.MEMBER)
    return organization, owner, admin, member, outsider


def test_owner_creates_project_and_member_cannot(
    api_client: tuple[TestClient, Session],
) -> None:
    """Owners and admins can create projects while regular members receive 403."""
    client, session = api_client
    organization, owner, _, member, _ = organization_team(client, session)
    login_as(client, owner)

    created = client.post(
        f"/api/v1/organizations/{organization['id']}/projects",
        json={"name": "  Customer   Onboarding  ", "description": "Implementation work"},
    )
    login_as(client, member)
    forbidden = client.post(
        f"/api/v1/organizations/{organization['id']}/projects",
        json={"name": "Member Project"},
    )

    assert created.status_code == 201
    assert created.json()["name"] == "Customer Onboarding"
    assert created.json()["organization_id"] == organization["id"]
    assert_error(forbidden, 403, "insufficient_role")


def test_non_member_cannot_discover_project(api_client: tuple[TestClient, Session]) -> None:
    """Project detail hides an existing tenant resource from a non-member."""
    client, session = api_client
    organization, owner, _, _, outsider = organization_team(client, session)
    login_as(client, owner)
    project = create_project(client, organization["id"])
    login_as(client, outsider)

    response = client.get(f"/api/v1/projects/{project['id']}")

    assert_error(response, 404, "project_not_found")


def test_project_list_uses_standard_pagination(api_client: tuple[TestClient, Session]) -> None:
    """Project listing returns only organization projects and pagination metadata."""
    client, session = api_client
    organization, owner, _, _, outsider = organization_team(client, session)
    login_as(client, owner)
    first = create_project(client, organization["id"], "First Project")
    second = create_project(client, organization["id"], "Second Project")
    login_as(client, outsider)
    hidden_org = create_organization(client, "Hidden Org")
    create_project(client, hidden_org["id"], "Hidden Project")
    login_as(client, owner)

    response = client.get(
        f"/api/v1/organizations/{organization['id']}/projects",
        params={"limit": 1, "offset": 1},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    assert body["limit"] == 1
    assert body["offset"] == 1
    assert body["items"][0]["id"] in {first["id"], second["id"]}


def test_valid_task_creation_stores_organization_scope(
    api_client: tuple[TestClient, Session],
) -> None:
    """Task creation stores project, organization, creator, and assignee fields."""
    client, session = api_client
    organization, owner, _, member, _ = organization_team(client, session)
    login_as(client, owner)
    project = create_project(client, organization["id"])

    task = create_task(
        client,
        project["id"],
        title="Call customer",
        priority="high",
        assignee_id=member.id,
        due_date="2026-06-20",
    )

    assert task["organization_id"] == organization["id"]
    assert task["project_id"] == project["id"]
    assert task["created_by_id"] == str(owner.id)
    assert task["assignee_id"] == str(member.id)
    assert task["status"] == "todo"
    assert task["priority"] == "high"


def test_cross_organization_assignee_is_rejected(
    api_client: tuple[TestClient, Session],
) -> None:
    """Assignees must belong to the task organization on create and update."""
    client, session = api_client
    organization, owner, admin, _, outsider = organization_team(client, session)
    login_as(client, outsider)
    create_organization(client, "Hidden Org")
    login_as(client, owner)
    project = create_project(client, organization["id"])
    task = create_task(client, project["id"], assignee_id=admin.id)

    create_response = client.post(
        f"/api/v1/projects/{project['id']}/tasks",
        json={"title": "Invalid assignee", "assignee_id": str(outsider.id)},
    )
    update_response = client.patch(
        f"/api/v1/tasks/{task['id']}",
        json={"assignee_id": str(outsider.id)},
    )

    assert_error(create_response, 400, "invalid_task")
    assert_error(update_response, 400, "invalid_task")


def test_archived_project_rejects_task_creation(
    api_client: tuple[TestClient, Session],
) -> None:
    """Archived projects remain readable but cannot receive new tasks."""
    client, session = api_client
    organization, owner, _, _, _ = organization_team(client, session)
    login_as(client, owner)
    project = create_project(client, organization["id"])

    archived = client.patch(f"/api/v1/projects/{project['id']}", json={"is_archived": True})
    created = client.post(f"/api/v1/projects/{project['id']}/tasks", json={"title": "Blocked"})
    detail = client.get(f"/api/v1/projects/{project['id']}")

    assert archived.status_code == 200
    assert archived.json()["is_archived"] is True
    assert_error(created, 409, "project_archived")
    assert detail.status_code == 200


def test_status_transitions_set_and_clear_completed_at(
    api_client: tuple[TestClient, Session],
) -> None:
    """Done transitions set completion time and non-done transitions clear it."""
    client, session = api_client
    organization, owner, _, _, _ = organization_team(client, session)
    login_as(client, owner)
    project = create_project(client, organization["id"])
    task = create_task(client, project["id"])

    done = client.patch(f"/api/v1/tasks/{task['id']}", json={"status": "done"})
    reopened = client.patch(f"/api/v1/tasks/{task['id']}", json={"status": "in_progress"})

    assert done.status_code == 200
    assert done.json()["completed_at"] is not None
    assert reopened.status_code == 200
    assert reopened.json()["completed_at"] is None


def test_task_filters_and_pagination(api_client: tuple[TestClient, Session]) -> None:
    """Task listing applies documented filters while preserving pagination shape."""
    client, session = api_client
    organization, owner, _, member, _ = organization_team(client, session)
    login_as(client, owner)
    project = create_project(client, organization["id"])
    matching = create_task(
        client,
        project["id"],
        title="Matching",
        priority="urgent",
        assignee_id=member.id,
        due_date="2026-06-20",
    )
    other = create_task(client, project["id"], title="Other", priority="low", due_date="2026-07-01")
    client.patch(f"/api/v1/tasks/{matching['id']}", json={"status": "blocked"})

    response = client.get(
        f"/api/v1/projects/{project['id']}/tasks",
        params={
            "status": "blocked",
            "assignee_id": str(member.id),
            "priority": "urgent",
            "due_before": "2026-06-30",
            "due_after": "2026-06-01",
            "limit": 10,
            "offset": 0,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["limit"] == 10
    assert body["offset"] == 0
    assert body["items"][0]["id"] == matching["id"]
    assert other["id"] not in {item["id"] for item in body["items"]}


def test_member_task_assignment_restrictions(api_client: tuple[TestClient, Session]) -> None:
    """Regular members may self-assign on create but cannot assign others."""
    client, session = api_client
    organization, owner, _, member, _ = organization_team(client, session)
    login_as(client, owner)
    project = create_project(client, organization["id"])
    login_as(client, member)

    self_assigned = client.post(
        f"/api/v1/projects/{project['id']}/tasks",
        json={"title": "Mine", "assignee_id": str(member.id)},
    )
    forbidden = client.post(
        f"/api/v1/projects/{project['id']}/tasks",
        json={"title": "Not mine", "assignee_id": str(owner.id)},
    )

    assert self_assigned.status_code == 201
    assert self_assigned.json()["assignee_id"] == str(member.id)
    assert_error(forbidden, 403, "insufficient_role")


def test_member_update_restrictions(api_client: tuple[TestClient, Session]) -> None:
    """Members can update assigned tasks but not unassigned tasks or assignee_id."""
    client, session = api_client
    organization, owner, _, member, _ = organization_team(client, session)
    login_as(client, owner)
    project = create_project(client, organization["id"])
    assigned = create_task(client, project["id"], title="Assigned", assignee_id=member.id)
    unassigned = create_task(client, project["id"], title="Unassigned")
    login_as(client, member)

    own_update = client.patch(f"/api/v1/tasks/{assigned['id']}", json={"status": "in_progress"})
    reassign = client.patch(f"/api/v1/tasks/{assigned['id']}", json={"assignee_id": str(member.id)})
    forbidden = client.patch(f"/api/v1/tasks/{unassigned['id']}", json={"status": "blocked"})

    assert own_update.status_code == 200
    assert own_update.json()["status"] == "in_progress"
    assert_error(reassign, 403, "insufficient_role")
    assert_error(forbidden, 403, "insufficient_role")


def test_non_member_cannot_discover_task(api_client: tuple[TestClient, Session]) -> None:
    """Task detail hides an existing tenant resource from a non-member."""
    client, session = api_client
    organization, owner, _, _, outsider = organization_team(client, session)
    login_as(client, owner)
    project = create_project(client, organization["id"])
    task = create_task(client, project["id"])
    login_as(client, outsider)

    response = client.get(f"/api/v1/tasks/{task['id']}")

    assert_error(response, 404, "task_not_found")


def test_task_model_keeps_denormalized_organization_scope(
    api_client: tuple[TestClient, Session],
) -> None:
    """Persisted tasks include organization_id for tenant isolation queries."""
    client, session = api_client
    organization, owner, _, _, _ = organization_team(client, session)
    login_as(client, owner)
    project = create_project(client, organization["id"])
    task = create_task(client, project["id"])

    persisted = session.get(Task, uuid.UUID(task["id"]))

    assert persisted is not None
    assert persisted.organization_id == uuid.UUID(organization["id"])
