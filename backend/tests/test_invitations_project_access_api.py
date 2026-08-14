"""Endpoint-level coverage for SPEC-303 invitations and project access."""

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
import app.services.tasks as task_service_module
from app.core.config import Settings, get_settings
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.organization import Invitation, MembershipRole, OrganizationMembership
from app.models.project import ProjectMembership
from app.models.user import User


@pytest.fixture(autouse=True)
def fast_password_hasher(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep multi-user invitation scenarios fast while preserving password behavior."""
    monkeypatch.setattr(
        security_service,
        "password_hasher",
        PasswordHasher(time_cost=1, memory_cost=512, parallelism=1),
    )


@pytest.fixture(autouse=True)
def disable_task_notification_enqueue(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep task assignment checks independent from the Celery broker."""
    monkeypatch.setattr(
        task_service_module,
        "enqueue_task_assignment_notification",
        lambda task: True,
    )


@pytest.fixture
def api_client() -> Generator[tuple[TestClient, Session], None, None]:
    """Run SPEC-303 endpoint tests against one isolated in-memory database."""
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
        """Supply deterministic auth settings to invitation API tests."""
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


def create_organization(client: TestClient, name: str = "Invite Ops") -> dict[str, Any]:
    """Create an organization through the public API."""
    response = client.post("/api/v1/organizations", json={"name": name})
    assert response.status_code == 201
    return response.json()


def add_membership(
    session: Session, organization_id: str, user: User, role: MembershipRole
) -> OrganizationMembership:
    """Seed organization membership for project-invitation setup."""
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
    """Seed explicit project access when a test needs a preexisting member."""
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
    """Create one project as the current user."""
    response = client.post(f"/api/v1/organizations/{organization_id}/projects", json={"name": name})
    assert response.status_code == 201
    return response.json()


def test_organization_invitation_acceptance_and_safe_failures(
    api_client: tuple[TestClient, Session],
) -> None:
    """Organization invitations grant no access until the target accepts."""
    client, session = api_client
    owner = create_user(client, session, "owner303@example.com")
    target = create_user(client, session, "target303@example.com")
    member = create_user(client, session, "member303@example.com")
    login_as(client, owner)
    organization = create_organization(client)
    add_membership(session, organization["id"], member, MembershipRole.MEMBER)

    invited = client.post(
        f"/api/v1/organizations/{organization['id']}/invitations",
        json={"email": "TARGET303@EXAMPLE.COM", "role": "admin"},
    )
    duplicate = client.post(
        f"/api/v1/organizations/{organization['id']}/invitations",
        json={"email": target.email, "role": "member"},
    )
    existing = client.post(
        f"/api/v1/organizations/{organization['id']}/invitations",
        json={"email": member.email, "role": "member"},
    )
    unknown = client.post(
        f"/api/v1/organizations/{organization['id']}/invitations",
        json={"email": "missing@example.com", "role": "member"},
    )
    login_as(client, target)
    hidden_before_accept = client.get(f"/api/v1/organizations/{organization['id']}")
    my_invitations = client.get("/api/v1/invitations")
    accepted = client.post(f"/api/v1/invitations/{invited.json()['id']}/accept")

    assert invited.status_code == 201
    assert invited.json()["target_email"] == target.email
    assert invited.json()["role"] == "admin"
    assert_error(duplicate, 409, "invitation_exists")
    assert_error(existing, 409, "membership_exists")
    assert_error(unknown, 404, "user_not_found")
    assert_error(hidden_before_accept, 404, "organization_not_found")
    assert my_invitations.json()["total"] == 1
    assert accepted.status_code == 200
    assert accepted.json()["status"] == "accepted"
    membership = session.scalar(
        select(OrganizationMembership).where(
            OrganizationMembership.organization_id == uuid.UUID(organization["id"]),
            OrganizationMembership.user_id == target.id,
        )
    )
    assert membership is not None
    assert membership.role == MembershipRole.ADMIN


def test_admin_and_member_organization_invitation_permissions(
    api_client: tuple[TestClient, Session],
) -> None:
    """Admins can invite members only while regular members cannot invite."""
    client, session = api_client
    owner = create_user(client, session, "owner-perms303@example.com")
    admin = create_user(client, session, "admin-perms303@example.com")
    member = create_user(client, session, "member-perms303@example.com")
    target = create_user(client, session, "target-perms303@example.com")
    login_as(client, owner)
    organization = create_organization(client)
    add_membership(session, organization["id"], admin, MembershipRole.ADMIN)
    add_membership(session, organization["id"], member, MembershipRole.MEMBER)

    login_as(client, admin)
    admin_invites_admin = client.post(
        f"/api/v1/organizations/{organization['id']}/invitations",
        json={"email": target.email, "role": "admin"},
    )
    admin_invites_member = client.post(
        f"/api/v1/organizations/{organization['id']}/invitations",
        json={"email": target.email, "role": "member"},
    )
    login_as(client, member)
    member_invites = client.post(
        f"/api/v1/organizations/{organization['id']}/invitations",
        json={"email": "another@example.com", "role": "member"},
    )

    assert_error(admin_invites_admin, 403, "insufficient_role")
    assert admin_invites_member.status_code == 201
    assert_error(member_invites, 403, "insufficient_role")


def test_invitation_decline_expiration_and_cancel(
    api_client: tuple[TestClient, Session],
) -> None:
    """Pending invitations can be declined, expired, or cancelled with terminal state."""
    client, session = api_client
    owner = create_user(client, session, "owner-state303@example.com")
    decline_target = create_user(client, session, "decline303@example.com")
    expire_target = create_user(client, session, "expire303@example.com")
    cancel_target = create_user(client, session, "cancel303@example.com")
    login_as(client, owner)
    organization = create_organization(client)
    declined_invite = client.post(
        f"/api/v1/organizations/{organization['id']}/invitations",
        json={"email": decline_target.email, "role": "member"},
    ).json()
    expired_invite = client.post(
        f"/api/v1/organizations/{organization['id']}/invitations",
        json={"email": expire_target.email, "role": "member"},
    ).json()
    cancelled_invite = client.post(
        f"/api/v1/organizations/{organization['id']}/invitations",
        json={"email": cancel_target.email, "role": "member"},
    ).json()
    expired = session.get(Invitation, uuid.UUID(expired_invite["id"]))
    assert expired is not None
    expired.expires_at = datetime.now(UTC) - timedelta(minutes=1)
    session.commit()

    login_as(client, decline_target)
    declined = client.post(f"/api/v1/invitations/{declined_invite['id']}/decline")
    login_as(client, expire_target)
    accepted_expired = client.post(f"/api/v1/invitations/{expired_invite['id']}/accept")
    login_as(client, owner)
    cancelled = client.delete(
        f"/api/v1/organizations/{organization['id']}/invitations/{cancelled_invite['id']}"
    )
    cancel_again = client.delete(
        f"/api/v1/organizations/{organization['id']}/invitations/{cancelled_invite['id']}"
    )

    assert declined.status_code == 200
    assert declined.json()["status"] == "declined"
    assert_error(accepted_expired, 400, "invalid_invitation")
    assert cancelled.status_code == 204
    assert_error(cancel_again, 409, "invitation_finalized")


def test_project_invitation_acceptance_listing_and_removal(
    api_client: tuple[TestClient, Session],
) -> None:
    """Project invitations grant explicit project membership only after acceptance."""
    client, session = api_client
    owner = create_user(client, session, "owner-project303@example.com")
    member = create_user(client, session, "project-member303@example.com")
    outsider = create_user(client, session, "project-outsider303@example.com")
    login_as(client, owner)
    organization = create_organization(client)
    add_membership(session, organization["id"], member, MembershipRole.MEMBER)
    project = create_project(client, organization["id"], "Restricted Project")

    invited = client.post(
        f"/api/v1/projects/{project['id']}/invitations",
        json={"user_id": str(member.id)},
    )
    duplicate = client.post(
        f"/api/v1/projects/{project['id']}/invitations",
        json={"user_id": str(member.id)},
    )
    outsider_invite = client.post(
        f"/api/v1/projects/{project['id']}/invitations",
        json={"user_id": str(outsider.id)},
    )
    login_as(client, member)
    hidden_before_accept = client.get(f"/api/v1/projects/{project['id']}")
    accepted = client.post(f"/api/v1/invitations/{invited.json()['id']}/accept")
    visible_after_accept = client.get(f"/api/v1/projects/{project['id']}")
    members = client.get(f"/api/v1/projects/{project['id']}/members")
    login_as(client, owner)
    removed = client.delete(f"/api/v1/projects/{project['id']}/members/{member.id}")

    assert invited.status_code == 201
    assert invited.json()["scope_type"] == "project"
    assert_error(duplicate, 409, "invitation_exists")
    assert_error(outsider_invite, 404, "membership_not_found")
    assert_error(hidden_before_accept, 404, "project_not_found")
    assert accepted.status_code == 200
    assert visible_after_accept.status_code == 200
    assert {item["user_id"] for item in members.json()["items"]} == {str(owner.id), str(member.id)}
    assert removed.status_code == 204


def test_regular_member_project_visibility_and_task_assignment(
    api_client: tuple[TestClient, Session],
) -> None:
    """Regular members see only joined projects and assignees must be project members."""
    client, session = api_client
    owner = create_user(client, session, "owner-visible303@example.com")
    member = create_user(client, session, "member-visible303@example.com")
    other_member = create_user(client, session, "other-visible303@example.com")
    login_as(client, owner)
    organization = create_organization(client)
    add_membership(session, organization["id"], member, MembershipRole.MEMBER)
    add_membership(session, organization["id"], other_member, MembershipRole.MEMBER)
    visible = create_project(client, organization["id"], "Visible")
    hidden = create_project(client, organization["id"], "Hidden")
    add_project_membership(session, organization["id"], visible["id"], member)

    invalid_assignee = client.post(
        f"/api/v1/projects/{visible['id']}/tasks",
        json={"title": "Bad assignee", "assignee_id": str(other_member.id)},
    )
    login_as(client, member)
    project_list = client.get(f"/api/v1/organizations/{organization['id']}/projects")
    hidden_detail = client.get(f"/api/v1/projects/{hidden['id']}")
    hidden_tasks = client.get(f"/api/v1/projects/{hidden['id']}/tasks")
    self_assigned = client.post(
        f"/api/v1/projects/{visible['id']}/tasks",
        json={"title": "Mine", "assignee_id": str(member.id)},
    )

    assert_error(invalid_assignee, 400, "invalid_task")
    assert project_list.status_code == 200
    assert [item["id"] for item in project_list.json()["items"]] == [visible["id"]]
    assert_error(hidden_detail, 404, "project_not_found")
    assert_error(hidden_tasks, 404, "project_not_found")
    assert self_assigned.status_code == 201


def test_removed_organization_member_loses_project_assignment_eligibility(
    api_client: tuple[TestClient, Session],
) -> None:
    """Removing organization membership also removes usable project assignment access."""
    client, session = api_client
    owner = create_user(client, session, "owner-remove303@example.com")
    member = create_user(client, session, "member-remove303@example.com")
    login_as(client, owner)
    organization = create_organization(client)
    add_membership(session, organization["id"], member, MembershipRole.MEMBER)
    project = create_project(client, organization["id"], "Cleanup Project")
    add_project_membership(session, organization["id"], project["id"], member)

    removed = client.delete(f"/api/v1/organizations/{organization['id']}/members/{member.id}")
    assigned = client.post(
        f"/api/v1/projects/{project['id']}/tasks",
        json={"title": "Invalid stale assignee", "assignee_id": str(member.id)},
    )

    assert removed.status_code == 204
    assert (
        session.scalar(
            select(ProjectMembership).where(
                ProjectMembership.organization_id == uuid.UUID(organization["id"]),
                ProjectMembership.user_id == member.id,
            )
        )
        is None
    )
    assert_error(assigned, 400, "invalid_task")
