"""Endpoint-level organizations and RBAC coverage for SPEC-102."""

import uuid
from collections.abc import Generator
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from typing import Any

import pytest
from argon2 import PasswordHasher
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, delete, func, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import app.services.security as security_service
from app.api.errors import APIError
from app.core.config import Settings, get_settings
from app.db.base import Base
from app.db.session import create_database_engine, get_db
from app.main import app
from app.models.organization import MembershipRole, Organization, OrganizationMembership
from app.models.user import User
from app.repositories.organizations import OrganizationRepository
from app.services.organizations import OrganizationService


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
    """Run organization endpoints against one isolated in-memory database."""
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
        """Supply deterministic auth settings to organization API tests."""
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
    """Seed a membership because invitations are explicitly outside SPEC-102."""
    membership = OrganizationMembership(
        organization_id=uuid.UUID(organization_id),
        user_id=user.id,
        role=role,
    )
    session.add(membership)
    session.commit()
    session.refresh(membership)
    return membership


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


def test_create_requires_authentication(api_client: tuple[TestClient, Session]) -> None:
    """Unauthenticated organization creation returns the documented 401 error."""
    client, _ = api_client

    response = client.post("/api/v1/organizations", json={"name": "Acme Ops"})

    assert_error(response, 401, "not_authenticated")


def test_create_generates_slug_and_owner_membership(
    api_client: tuple[TestClient, Session],
) -> None:
    """Organization creation generates a slug and atomically assigns ownership."""
    client, session = api_client
    owner = create_user(client, session, "owner@example.com")
    login_as(client, owner)

    response = client.post("/api/v1/organizations", json={"name": "  Álvaro  Field Ops  "})

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Álvaro Field Ops"
    assert body["slug"] == "alvaro-field-ops"
    assert body["role"] == "owner"
    membership = session.scalar(
        select(OrganizationMembership).where(
            OrganizationMembership.organization_id == uuid.UUID(body["id"]),
            OrganizationMembership.user_id == owner.id,
        )
    )
    assert membership is not None
    assert membership.role == MembershipRole.OWNER


def test_duplicate_and_invalid_slugs_return_documented_errors(
    api_client: tuple[TestClient, Session],
) -> None:
    """Slug uniqueness and URL-safe validation use stable business errors."""
    client, session = api_client
    owner = create_user(client, session, "owner@example.com")
    login_as(client, owner)
    first = client.post("/api/v1/organizations", json={"name": "Acme", "slug": "shared-slug"})

    duplicate = client.post("/api/v1/organizations", json={"name": "Other", "slug": "shared-slug"})
    invalid = client.post("/api/v1/organizations", json={"name": "Other", "slug": "Not URL Safe"})

    assert first.status_code == 201
    assert_error(duplicate, 409, "organization_slug_taken")
    assert_error(invalid, 400, "invalid_organization")


def test_list_is_paginated_and_tenant_isolated(
    api_client: tuple[TestClient, Session],
) -> None:
    """Organization listing includes only the actor's memberships and pagination metadata."""
    client, session = api_client
    first_user = create_user(client, session, "first@example.com")
    second_user = create_user(client, session, "second@example.com")
    login_as(client, first_user)
    first = create_organization(client, "First Org")
    second = create_organization(client, "Second Org")
    login_as(client, second_user)
    create_organization(client, "Hidden Org")
    login_as(client, first_user)

    response = client.get("/api/v1/organizations", params={"limit": 1, "offset": 1})

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    assert body["limit"] == 1
    assert body["offset"] == 1
    assert body["items"][0]["id"] in {first["id"], second["id"]}
    assert first["id"] != second["id"]


def test_non_member_cannot_discover_organization(
    api_client: tuple[TestClient, Session],
) -> None:
    """Organization detail hides an existing tenant from a non-member with 404."""
    client, session = api_client
    organization, _, _, _, outsider = organization_team(client, session)
    login_as(client, outsider)

    response = client.get(f"/api/v1/organizations/{organization['id']}")

    assert_error(response, 404, "organization_not_found")


def test_owner_updates_organization_but_admin_cannot(
    api_client: tuple[TestClient, Session],
) -> None:
    """Only owners can update organization names and slugs."""
    client, session = api_client
    organization, owner, admin, _, _ = organization_team(client, session)
    login_as(client, owner)

    updated = client.patch(
        f"/api/v1/organizations/{organization['id']}",
        json={"name": "Updated Ops", "slug": "updated-ops"},
    )
    login_as(client, admin)
    forbidden = client.patch(
        f"/api/v1/organizations/{organization['id']}", json={"name": "Admin Edit"}
    )

    assert updated.status_code == 200
    assert updated.json()["name"] == "Updated Ops"
    assert updated.json()["slug"] == "updated-ops"
    assert_error(forbidden, 403, "insufficient_role")


def test_update_rejects_duplicate_slug(api_client: tuple[TestClient, Session]) -> None:
    """Owner updates cannot claim a slug already used by another organization."""
    client, session = api_client
    owner = create_user(client, session, "owner@example.com")
    login_as(client, owner)
    first = create_organization(client, "First Org")
    second = create_organization(client, "Second Org")

    response = client.patch(f"/api/v1/organizations/{second['id']}", json={"slug": first["slug"]})

    assert_error(response, 409, "organization_slug_taken")


def test_admin_lists_members_with_safe_user_fields(
    api_client: tuple[TestClient, Session],
) -> None:
    """Admins can list tenant memberships without receiving credential fields."""
    client, session = api_client
    organization, _, admin, _, _ = organization_team(client, session)
    login_as(client, admin)

    response = client.get(f"/api/v1/organizations/{organization['id']}/members")

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 3
    assert {item["role"] for item in body["items"]} == {"owner", "admin", "member"}
    for item in body["items"]:
        assert set(item["user"]) == {"id", "email", "full_name", "is_active"}
        assert "password_hash" not in item["user"]
        assert "is_superuser" not in item["user"]


def test_member_and_non_member_receive_distinct_member_list_errors(
    api_client: tuple[TestClient, Session],
) -> None:
    """Known members receive 403 while outsiders receive tenant-hiding 404."""
    client, session = api_client
    organization, _, _, member, outsider = organization_team(client, session)
    login_as(client, member)
    forbidden = client.get(f"/api/v1/organizations/{organization['id']}/members")
    login_as(client, outsider)
    hidden = client.get(f"/api/v1/organizations/{organization['id']}/members")

    assert_error(forbidden, 403, "insufficient_role")
    assert_error(hidden, 404, "organization_not_found")


def test_owner_changes_role_but_member_cannot_escalate(
    api_client: tuple[TestClient, Session],
) -> None:
    """Role management is owner-only and members cannot elevate themselves."""
    client, session = api_client
    organization, owner, _, member, _ = organization_team(client, session)
    login_as(client, member)
    escalation = client.patch(
        f"/api/v1/organizations/{organization['id']}/members/{member.id}",
        json={"role": "admin"},
    )
    login_as(client, owner)
    update = client.patch(
        f"/api/v1/organizations/{organization['id']}/members/{member.id}",
        json={"role": "admin"},
    )

    assert_error(escalation, 403, "insufficient_role")
    assert update.status_code == 200
    assert update.json()["role"] == "admin"


def test_owner_role_requires_transfer_and_cannot_be_removed(
    api_client: tuple[TestClient, Session],
) -> None:
    """Generic membership endpoints cannot assign, demote, or remove ownership."""
    client, session = api_client
    organization, owner, _, member, _ = organization_team(client, session)
    login_as(client, owner)

    demotion = client.patch(
        f"/api/v1/organizations/{organization['id']}/members/{owner.id}",
        json={"role": "admin"},
    )
    promotion = client.patch(
        f"/api/v1/organizations/{organization['id']}/members/{member.id}",
        json={"role": "owner"},
    )
    removal = client.delete(f"/api/v1/organizations/{organization['id']}/members/{owner.id}")

    assert_error(demotion, 409, "ownership_transfer_required")
    assert_error(promotion, 409, "ownership_transfer_required")
    assert_error(removal, 409, "ownership_transfer_required")


def test_database_rejects_second_owner(api_client: tuple[TestClient, Session]) -> None:
    """The persistence constraint prevents two owners in one organization."""
    client, session = api_client
    organization, _, admin, _, _ = organization_team(client, session)
    admin_membership = session.scalar(
        select(OrganizationMembership).where(
            OrganizationMembership.organization_id == uuid.UUID(organization["id"]),
            OrganizationMembership.user_id == admin.id,
        )
    )
    assert admin_membership is not None
    admin_membership.role = MembershipRole.OWNER

    with pytest.raises(IntegrityError):
        session.commit()

    session.rollback()


def test_owner_transfers_ownership_atomically(api_client: tuple[TestClient, Session]) -> None:
    """Transfer promotes the target and demotes the previous owner in one request."""
    client, session = api_client
    organization, owner, _, member, _ = organization_team(client, session)
    login_as(client, owner)

    response = client.post(
        f"/api/v1/organizations/{organization['id']}/transfer-ownership",
        json={"new_owner_user_id": str(member.id)},
    )

    assert response.status_code == 204
    assert response.content == b""
    session.expire_all()
    memberships = list(
        session.scalars(
            select(OrganizationMembership).where(
                OrganizationMembership.organization_id == uuid.UUID(organization["id"])
            )
        )
    )
    roles = {membership.user_id: membership.role for membership in memberships}
    assert roles[owner.id] == MembershipRole.ADMIN
    assert roles[member.id] == MembershipRole.OWNER
    assert sum(role == MembershipRole.OWNER for role in roles.values()) == 1


def test_transfer_rolls_back_both_roles_when_commit_fails(
    api_client: tuple[TestClient, Session], monkeypatch: pytest.MonkeyPatch
) -> None:
    """A persistence failure leaves the previous ownership state intact."""
    client, session = api_client
    organization, owner, _, member, _ = organization_team(client, session)

    def fail_commit() -> None:
        """Simulate a database failure after the ordered ownership writes."""
        raise SQLAlchemyError("simulated transfer failure")

    monkeypatch.setattr(session, "commit", fail_commit)

    with pytest.raises(SQLAlchemyError):
        OrganizationService(session).transfer_ownership(
            owner, uuid.UUID(organization["id"]), member.id
        )

    session.expire_all()
    roles = dict(
        session.execute(
            select(OrganizationMembership.user_id, OrganizationMembership.role).where(
                OrganizationMembership.organization_id == uuid.UUID(organization["id"])
            )
        )
        .tuples()
        .all()
    )
    assert roles[owner.id] == MembershipRole.OWNER
    assert roles[member.id] == MembershipRole.MEMBER


def test_transfer_rejects_non_owners_and_non_members(
    api_client: tuple[TestClient, Session],
) -> None:
    """Known non-owners receive 403 while outsiders receive tenant-hiding 404."""
    client, session = api_client
    organization, _, admin, member, outsider = organization_team(client, session)

    for actor in (admin, member):
        login_as(client, actor)
        response = client.post(
            f"/api/v1/organizations/{organization['id']}/transfer-ownership",
            json={"new_owner_user_id": str(member.id)},
        )
        assert_error(response, 403, "insufficient_role")

    login_as(client, outsider)
    hidden = client.post(
        f"/api/v1/organizations/{organization['id']}/transfer-ownership",
        json={"new_owner_user_id": str(member.id)},
    )
    assert_error(hidden, 404, "organization_not_found")


def test_transfer_rejects_missing_or_current_owner_target(
    api_client: tuple[TestClient, Session],
) -> None:
    """Transfer requires another existing organization member as its target."""
    client, session = api_client
    organization, owner, _, _, outsider = organization_team(client, session)
    login_as(client, owner)

    missing = client.post(
        f"/api/v1/organizations/{organization['id']}/transfer-ownership",
        json={"new_owner_user_id": str(outsider.id)},
    )
    unchanged = client.post(
        f"/api/v1/organizations/{organization['id']}/transfer-ownership",
        json={"new_owner_user_id": str(owner.id)},
    )

    assert_error(missing, 404, "membership_not_found")
    assert_error(unchanged, 409, "ownership_transfer_not_required")


def test_remove_member_preserves_user_account(api_client: tuple[TestClient, Session]) -> None:
    """Removing a non-owner deletes only membership and leaves the user intact."""
    client, session = api_client
    organization, owner, _, member, _ = organization_team(client, session)
    login_as(client, owner)

    response = client.delete(f"/api/v1/organizations/{organization['id']}/members/{member.id}")

    assert response.status_code == 204
    assert response.content == b""
    assert session.get(User, member.id) is not None
    membership = session.scalar(
        select(OrganizationMembership).where(
            OrganizationMembership.organization_id == uuid.UUID(organization["id"]),
            OrganizationMembership.user_id == member.id,
        )
    )
    assert membership is None


def test_only_owner_can_delete_organization_and_slug_is_reusable(
    api_client: tuple[TestClient, Session],
) -> None:
    """Permanent deletion is owner-only and retains users while releasing the slug."""
    client, session = api_client
    organization, owner, admin, member, outsider = organization_team(client, session)
    organization_id = uuid.UUID(organization["id"])
    user_ids = list(session.scalars(select(User.id)))

    login_as(client, admin)
    admin_forbidden = client.delete(f"/api/v1/organizations/{organization['id']}")
    login_as(client, member)
    member_forbidden = client.delete(f"/api/v1/organizations/{organization['id']}")
    login_as(client, outsider)
    hidden = client.delete(f"/api/v1/organizations/{organization['id']}")
    login_as(client, owner)
    deleted = client.delete(f"/api/v1/organizations/{organization['id']}")

    assert_error(admin_forbidden, 403, "insufficient_role")
    assert_error(member_forbidden, 403, "insufficient_role")
    assert_error(hidden, 404, "organization_not_found")
    assert deleted.status_code == 204
    assert deleted.content == b""
    assert session.get(Organization, organization_id) is None
    membership_total = session.scalar(
        select(func.count(OrganizationMembership.id)).where(
            OrganizationMembership.organization_id == organization_id
        )
    )
    assert membership_total == 0
    assert set(session.scalars(select(User.id))) == set(user_ids)

    replacement = client.post(
        "/api/v1/organizations",
        json={"name": "Replacement Ops", "slug": organization["slug"]},
    )
    assert replacement.status_code == 201


@pytest.mark.db
def test_concurrent_transfers_leave_exactly_one_owner(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """PostgreSQL row locking lets only one transfer use the original owner state."""
    engine = create_database_engine()
    suffix = uuid.uuid4().hex
    organization_id: uuid.UUID | None = None
    user_ids: list[uuid.UUID] = []
    try:
        with Session(engine) as session:
            owner = User(
                email=f"owner-{suffix}@example.com",
                password_hash="not-used",
                full_name="Concurrent Owner",
            )
            first_target = User(
                email=f"first-{suffix}@example.com",
                password_hash="not-used",
                full_name="First Target",
            )
            second_target = User(
                email=f"second-{suffix}@example.com",
                password_hash="not-used",
                full_name="Second Target",
            )
            session.add_all([owner, first_target, second_target])
            session.flush()
            organization = Organization(name="Concurrent Ops", slug=f"concurrent-{suffix}")
            session.add(organization)
            session.flush()
            session.add_all(
                [
                    OrganizationMembership(
                        organization_id=organization.id,
                        user_id=owner.id,
                        role=MembershipRole.OWNER,
                    ),
                    OrganizationMembership(
                        organization_id=organization.id,
                        user_id=first_target.id,
                        role=MembershipRole.MEMBER,
                    ),
                    OrganizationMembership(
                        organization_id=organization.id,
                        user_id=second_target.id,
                        role=MembershipRole.MEMBER,
                    ),
                ]
            )
            session.commit()
            organization_id = organization.id
            owner_id = owner.id
            target_ids = [first_target.id, second_target.id]
            user_ids = [owner_id, *target_ids]

        barrier = Barrier(2)
        original_lock = OrganizationRepository.lock_organization

        def synchronized_lock(
            repository: OrganizationRepository, target_organization_id: uuid.UUID
        ) -> Organization | None:
            """Ensure both workers authorize before either takes the row lock."""
            barrier.wait(timeout=10)
            return original_lock(repository, target_organization_id)

        monkeypatch.setattr(OrganizationRepository, "lock_organization", synchronized_lock)

        def transfer(target_user_id: uuid.UUID) -> str:
            """Attempt one ownership transfer in an independent transaction."""
            with Session(engine) as session:
                actor = session.get(User, owner_id)
                assert actor is not None
                try:
                    OrganizationService(session).transfer_ownership(
                        actor, organization_id, target_user_id
                    )
                except APIError as exc:
                    session.rollback()
                    return exc.code
                return "success"

        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(transfer, target_ids))

        assert sorted(results) == ["insufficient_role", "success"]
        with Session(engine) as session:
            owner_count = session.scalar(
                select(func.count(OrganizationMembership.id)).where(
                    OrganizationMembership.organization_id == organization_id,
                    OrganizationMembership.role == MembershipRole.OWNER,
                )
            )
            assert owner_count == 1
    finally:
        with Session(engine) as session:
            if organization_id is not None:
                session.execute(
                    delete(OrganizationMembership).where(
                        OrganizationMembership.organization_id == organization_id
                    )
                )
                session.execute(delete(Organization).where(Organization.id == organization_id))
            if user_ids:
                session.execute(delete(User).where(User.id.in_(user_ids)))
            session.commit()
        engine.dispose()
