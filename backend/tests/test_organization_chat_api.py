"""Endpoint-level and WebSocket coverage for SPEC-304 organization chat."""

import uuid
from collections.abc import Generator
from typing import Any

import pytest
from argon2 import PasswordHasher
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.websockets import WebSocketDisconnect

import app.services.security as security_service
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
    """Keep multi-user chat scenarios fast while preserving password behavior."""
    monkeypatch.setattr(
        security_service,
        "password_hasher",
        PasswordHasher(time_cost=1, memory_cost=512, parallelism=1),
    )


@pytest.fixture
def api_client() -> Generator[tuple[TestClient, Session], None, None]:
    """Run SPEC-304 endpoints against one isolated in-memory database."""
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
        """Supply the same test database session to API and WebSocket handlers."""
        yield session

    def override_get_settings() -> Settings:
        """Supply deterministic auth settings to chat API tests."""
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
    """Register one internal user through the public auth API."""
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


def create_organization(client: TestClient, name: str = "Chat Ops") -> dict[str, Any]:
    """Create one organization through the public API."""
    response = client.post("/api/v1/organizations", json={"name": name})
    assert response.status_code == 201
    return response.json()


def add_membership(
    session: Session, organization_id: str, user: User, role: MembershipRole
) -> None:
    """Seed organization membership for chat scenarios."""
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
    """Seed explicit project access for shared-project and channel checks."""
    session.add(
        ProjectMembership(
            organization_id=uuid.UUID(organization_id),
            project_id=uuid.UUID(project_id),
            user_id=user.id,
            added_by_id=None,
        )
    )
    session.commit()


def create_project(
    client: TestClient, organization_id: str, name: str = "Chat Project"
) -> dict[str, Any]:
    """Create one project through the public project API."""
    response = client.post(
        f"/api/v1/organizations/{organization_id}/projects",
        json={"name": name},
    )
    assert response.status_code == 201
    return response.json()


def grant_client(client: TestClient, project_id: str) -> dict[str, Any]:
    """Create a restricted client account for client-exclusion checks."""
    response = client.post(
        f"/api/v1/projects/{project_id}/clients",
        json={
            "email": "chat-client@example.com",
            "full_name": "Chat Client",
            "password": "Example1234",
        },
    )
    assert response.status_code == 201
    return response.json()


def test_chat_members_exclude_clients_and_prioritize_shared_project(
    api_client: tuple[TestClient, Session],
) -> None:
    """The chat member list contains internal members with shared-project users first."""
    client, session = api_client
    owner = create_user(client, session, "owner304@example.com")
    shared = create_user(client, session, "shared304@example.com")
    other = create_user(client, session, "other304@example.com")
    login_as(client, owner.email)
    organization = create_organization(client)
    add_membership(session, organization["id"], shared, MembershipRole.MEMBER)
    add_membership(session, organization["id"], other, MembershipRole.MEMBER)
    project = create_project(client, organization["id"])
    add_project_membership(session, organization["id"], project["id"], shared)
    grant_client(client, project["id"])

    response = client.get(f"/api/v1/organizations/{organization['id']}/chat/members")

    assert response.status_code == 200
    items = response.json()["items"]
    assert [item["email"] for item in items] == [shared.email, other.email, owner.email]
    assert items[0]["shares_project"] is True
    assert "chat-client@example.com" not in {item["email"] for item in items}


def test_direct_message_persists_history_unread_notification_and_clear(
    api_client: tuple[TestClient, Session],
) -> None:
    """Direct messages persist, notify the recipient once, and respect personal clearing."""
    client, session = api_client
    owner = create_user(client, session, "owner-dm304@example.com")
    member = create_user(client, session, "member-dm304@example.com")
    outsider = create_user(client, session, "outsider-dm304@example.com")
    login_as(client, owner.email)
    organization = create_organization(client)
    add_membership(session, organization["id"], member, MembershipRole.MEMBER)

    direct = client.post(
        f"/api/v1/organizations/{organization['id']}/chat/direct-conversations",
        json={"target_user_id": str(member.id)},
    )
    message = client.post(
        f"/api/v1/chat/conversations/{direct.json()['id']}/messages",
        json={"body": "Hello from operations"},
    )
    second_message = client.post(
        f"/api/v1/chat/conversations/{direct.json()['id']}/messages",
        json={"body": "Another unread ping"},
    )
    login_as(client, member.email)
    conversations = client.get(f"/api/v1/organizations/{organization['id']}/chat/conversations")
    history = client.get(f"/api/v1/chat/conversations/{direct.json()['id']}/messages")
    cleared = client.post(f"/api/v1/chat/conversations/{direct.json()['id']}/clear")
    history_after_clear = client.get(f"/api/v1/chat/conversations/{direct.json()['id']}/messages")
    login_as(client, outsider.email)
    outsider_read = client.get(f"/api/v1/chat/conversations/{direct.json()['id']}/messages")

    notification = session.scalar(
        select(Notification).where(
            Notification.recipient_user_id == member.id,
            Notification.type == NotificationType.CHAT_UNREAD,
        )
    )
    assert direct.status_code == 201
    assert message.status_code == 201
    assert second_message.status_code == 201
    assert notification is not None
    assert conversations.json()["items"][0]["unread_count"] == 2
    assert history.json()["total"] == 2
    assert cleared.status_code == 200
    assert history_after_clear.json()["total"] == 0
    assert_error(outsider_read, 404, "conversation_not_found")


def test_rest_message_validation_returns_invalid_message(
    api_client: tuple[TestClient, Session],
) -> None:
    """Invalid REST message bodies use the SPEC-304 error envelope."""
    client, session = api_client
    owner = create_user(client, session, "owner-invalid304@example.com")
    member = create_user(client, session, "member-invalid304@example.com")
    login_as(client, owner.email)
    organization = create_organization(client)
    add_membership(session, organization["id"], member, MembershipRole.MEMBER)
    direct = client.post(
        f"/api/v1/organizations/{organization['id']}/chat/direct-conversations",
        json={"target_user_id": str(member.id)},
    ).json()

    empty = client.post(
        f"/api/v1/chat/conversations/{direct['id']}/messages",
        json={"body": ""},
    )
    too_long = client.post(
        f"/api/v1/chat/conversations/{direct['id']}/messages",
        json={"body": "x" * 4001},
    )

    assert_error(empty, 400, "invalid_message")
    assert_error(too_long, 400, "invalid_message")


def test_project_channel_enforces_project_membership(
    api_client: tuple[TestClient, Session],
) -> None:
    """Regular members can use only project channels for explicit project access."""
    client, session = api_client
    owner = create_user(client, session, "owner-project304@example.com")
    project_member = create_user(client, session, "member-project304@example.com")
    blocked_member = create_user(client, session, "blocked-project304@example.com")
    login_as(client, owner.email)
    organization = create_organization(client)
    add_membership(session, organization["id"], project_member, MembershipRole.MEMBER)
    add_membership(session, organization["id"], blocked_member, MembershipRole.MEMBER)
    project = create_project(client, organization["id"])
    add_project_membership(session, organization["id"], project["id"], project_member)

    login_as(client, project_member.email)
    allowed = client.get(f"/api/v1/projects/{project['id']}/chat/channel")
    sent = client.post(
        f"/api/v1/chat/conversations/{allowed.json()['id']}/messages",
        json={"body": "Project channel message"},
    )
    login_as(client, blocked_member.email)
    blocked = client.get(f"/api/v1/projects/{project['id']}/chat/channel")

    assert allowed.status_code == 200
    assert allowed.json()["conversation_type"] == "project_channel"
    assert sent.status_code == 201
    assert_error(blocked, 404, "project_not_found")


def test_client_account_cannot_use_organization_chat(
    api_client: tuple[TestClient, Session],
) -> None:
    """Restricted client accounts are rejected from internal chat surfaces."""
    client, session = api_client
    owner = create_user(client, session, "owner-client304@example.com")
    login_as(client, owner.email)
    organization = create_organization(client)
    project = create_project(client, organization["id"])
    grant_client(client, project["id"])

    login_as(client, "chat-client@example.com")
    members = client.get(f"/api/v1/organizations/{organization['id']}/chat/members")

    assert_error(members, 403, "internal_member_required")
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect("/api/v1/chat/ws"):
            pass


def test_websocket_persists_before_fanout(api_client: tuple[TestClient, Session]) -> None:
    """WebSocket sends persist messages before broadcasting created events."""
    client, session = api_client
    owner = create_user(client, session, "owner-ws304@example.com")
    member = create_user(client, session, "member-ws304@example.com")
    login_as(client, owner.email)
    organization = create_organization(client)
    add_membership(session, organization["id"], member, MembershipRole.MEMBER)
    direct = client.post(
        f"/api/v1/organizations/{organization['id']}/chat/direct-conversations",
        json={"target_user_id": str(member.id)},
    ).json()

    with client.websocket_connect("/api/v1/chat/ws") as websocket:
        websocket.send_json({"type": "subscribe", "conversation_id": direct["id"]})
        assert websocket.receive_json()["type"] == "subscribed"
        websocket.send_json(
            {
                "type": "message.send",
                "conversation_id": direct["id"],
                "body": "Realtime hello",
            }
        )
        event = websocket.receive_json()

    assert event["type"] == "message.created"
    persisted = client.get(f"/api/v1/chat/conversations/{direct['id']}/messages")
    assert persisted.json()["items"][0]["body"] == "Realtime hello"
