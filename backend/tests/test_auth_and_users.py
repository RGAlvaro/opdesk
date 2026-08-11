"""Backend auth and current-user API coverage for SPEC-101."""

from collections.abc import Generator
from http.cookies import SimpleCookie
from typing import Any

import pytest
from argon2 import PasswordHasher
from fastapi import Response
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import app.services.security as security_service
from app.api.auth import login, logout, refresh, register
from app.api.deps import get_current_user
from app.api.errors import APIError
from app.api.users import read_me, update_me
from app.core.config import Settings, get_settings
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.user import User
from app.schemas.users import LoginRequest, RegisterRequest, UserUpdateRequest
from app.services.security import hash_password, verify_password
from app.services.users import normalize_email, validate_password_policy


class RequestStub:
    """Minimal request double that carries cookies into dependency tests."""

    def __init__(self, cookies: dict[str, str] | None = None) -> None:
        """Store cookie values with an empty default for unauthenticated cases."""
        self.cookies = cookies or {}


def assert_api_error(exc: APIError, status_code: int, code: str) -> None:
    """Assert the stable fields on an application APIError."""
    assert exc.status_code == status_code
    assert exc.code == code


def extract_cookie(response: Response, cookie_name: str) -> str:
    """Read one cookie value from FastAPI response headers."""
    cookie = SimpleCookie()
    for header, value in response.raw_headers:
        if header == b"set-cookie":
            cookie.load(value.decode())
    morsel = cookie[cookie_name]
    return morsel.value


@pytest.fixture(autouse=True)
def fast_password_hasher(monkeypatch: pytest.MonkeyPatch) -> None:
    """Speed up password hashing so auth tests stay focused on behavior."""
    monkeypatch.setattr(
        security_service,
        "password_hasher",
        PasswordHasher(time_cost=1, memory_cost=512, parallelism=1),
    )


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """Provide an isolated in-memory database session for service-level tests."""
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


@pytest.fixture
def settings() -> Settings:
    """Return deterministic auth settings for token and cookie assertions."""
    return Settings(
        auth_secret_key="test_secret_key_minimum_32_chars",
        auth_cookie_secure=False,
    )


@pytest.fixture
def api_client(settings: Settings) -> Generator[tuple[TestClient, Session], None, None]:
    """Run the FastAPI app against an isolated in-memory database."""
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = session_factory()

    def override_get_db() -> Generator[Session, None, None]:
        """Inject the test database session into API routes."""
        yield session

    def override_get_settings() -> Settings:
        """Inject deterministic settings into API routes."""
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


def register_payload(
    email: str = "User@Example.com",
    password: str = "Example1234",
    full_name: str = "User Name",
) -> RegisterRequest:
    """Build a service-level registration payload with useful defaults."""
    return RegisterRequest(email=email, password=password, full_name=full_name)


def register_user(db_session: Session, payload: RegisterRequest | None = None) -> Any:
    """Register a user through the route function for direct behavior tests."""
    return register(payload or register_payload(), db_session)


def login_user(db_session: Session, settings: Settings) -> tuple[Any, Response]:
    """Log in the default user through the route function and keep cookies."""
    response = Response()
    result = login(
        LoginRequest(email="user@example.com", password="Example1234"),
        response,
        db_session,
        settings,
    )
    return result, response


def api_register_payload(
    email: str = "User@Example.com",
    password: str = "Example1234",
    full_name: str = "User Name",
) -> dict[str, str]:
    """Build a JSON registration payload with useful API defaults."""
    return {
        "email": email,
        "password": password,
        "full_name": full_name,
    }


def api_login_payload(
    email: str = "user@example.com",
    password: str = "Example1234",
) -> dict[str, str]:
    """Build a JSON login payload with useful API defaults."""
    return {
        "email": email,
        "password": password,
    }


def assert_error_response(response: Any, status_code: int, code: str) -> None:
    """Assert the API error response envelope and expected status code."""
    assert response.status_code == status_code
    body = response.json()
    assert body["error"]["code"] == code
    assert isinstance(body["error"]["message"], str)
    assert body["error"]["details"] == {}


def api_register_user(client: TestClient, payload: dict[str, str] | None = None) -> Any:
    """Register a user through HTTP and assert the creation succeeded."""
    response = client.post("/api/v1/auth/register", json=payload or api_register_payload())
    assert response.status_code == 201
    return response


def test_normalize_email_lowercases_and_trims() -> None:
    """Email normalization removes spacing and case variance."""
    assert normalize_email("  USER@Example.COM ") == "user@example.com"


def test_password_policy_rejects_weak_password() -> None:
    """Weak passwords are rejected with the documented API error."""
    with pytest.raises(APIError) as exc_info:
        validate_password_policy("short1")

    assert_api_error(exc_info.value, 400, "weak_password")


def test_password_hashing_and_verification() -> None:
    """Password hashing stores non-plaintext hashes and verifies candidates."""
    password_hash = hash_password("Example1234")

    assert password_hash != "Example1234"
    assert verify_password("Example1234", password_hash)
    assert not verify_password("Wrong1234", password_hash)


def test_register_creates_first_superuser_and_excludes_sensitive_fields(
    db_session: Session,
) -> None:
    """The first service-level registration becomes superuser and hides secrets."""
    user = register_user(db_session)
    data = user.model_dump()

    assert data["email"] == "user@example.com"
    assert data["full_name"] == "User Name"
    assert data["is_active"] is True
    assert data["is_superuser"] is True
    assert "password_hash" not in data
    assert "access_token" not in data


def test_api_register_creates_first_superuser_and_excludes_sensitive_fields(
    api_client: tuple[TestClient, Session],
) -> None:
    """The first API registration becomes superuser and hides secrets."""
    client, _ = api_client

    response = client.post("/api/v1/auth/register", json=api_register_payload())

    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "user@example.com"
    assert data["full_name"] == "User Name"
    assert data["is_active"] is True
    assert data["is_superuser"] is True
    assert "password_hash" not in data
    assert "access_token" not in data
    assert "refresh_token" not in data


def test_register_duplicate_email_is_case_insensitive(db_session: Session) -> None:
    """Duplicate registration checks normalized email addresses."""
    register_user(db_session, register_payload(email="user@example.com"))

    with pytest.raises(APIError) as exc_info:
        register_user(db_session, register_payload(email="USER@example.com"))

    assert_api_error(exc_info.value, 409, "email_already_registered")


def test_api_register_duplicate_email_is_case_insensitive(
    api_client: tuple[TestClient, Session],
) -> None:
    """The API rejects duplicate email addresses regardless of case."""
    client, _ = api_client
    api_register_user(client, api_register_payload(email="user@example.com"))

    response = client.post(
        "/api/v1/auth/register",
        json=api_register_payload(email="USER@example.com"),
    )

    assert_error_response(response, 409, "email_already_registered")


def test_register_rejects_weak_password(db_session: Session) -> None:
    """Service-level registration applies the password policy."""
    with pytest.raises(APIError) as exc_info:
        register_user(db_session, register_payload(password="weak"))

    assert_api_error(exc_info.value, 400, "weak_password")


def test_api_register_rejects_weak_password(api_client: tuple[TestClient, Session]) -> None:
    """The registration API returns the documented weak-password error."""
    client, _ = api_client

    response = client.post(
        "/api/v1/auth/register",
        json=api_register_payload(password="weak"),
    )

    assert_error_response(response, 400, "weak_password")


def test_later_registered_users_are_not_superusers(db_session: Session) -> None:
    """Only the first registered user receives bootstrap superuser status."""
    first = register_user(db_session, register_payload(email="one@example.com"))
    second = register_user(db_session, register_payload(email="two@example.com"))

    assert first.is_superuser is True
    assert second.is_superuser is False


def test_api_later_registered_users_are_not_superusers(
    api_client: tuple[TestClient, Session],
) -> None:
    """The API keeps bootstrap superuser status limited to the first account."""
    client, _ = api_client

    first = api_register_user(client, api_register_payload(email="one@example.com"))
    second = api_register_user(client, api_register_payload(email="two@example.com"))

    assert first.json()["is_superuser"] is True
    assert second.json()["is_superuser"] is False


def test_login_sets_auth_cookies_and_returns_safe_user(
    db_session: Session, settings: Settings
) -> None:
    """Service-level login returns a safe user and sets httpOnly cookies."""
    register_user(db_session)

    result, response = login_user(db_session, settings)

    assert result.user.email == "user@example.com"
    assert not hasattr(result.user, "password_hash")
    access_token = extract_cookie(response, "access_token")
    refresh_token = extract_cookie(response, "refresh_token")
    assert access_token
    assert refresh_token
    set_cookie = ",".join(
        value.decode() for header, value in response.raw_headers if header == b"set-cookie"
    )
    assert "HttpOnly" in set_cookie


def test_api_login_sets_auth_cookies_and_returns_safe_user(
    api_client: tuple[TestClient, Session],
) -> None:
    """The login API returns a safe user and browser auth cookies."""
    client, _ = api_client
    api_register_user(client)

    response = client.post("/api/v1/auth/login", json=api_login_payload())

    assert response.status_code == 200
    assert response.json()["user"]["email"] == "user@example.com"
    assert "password_hash" not in response.json()["user"]
    assert "access_token" in response.cookies
    assert "refresh_token" in response.cookies
    set_cookie = ",".join(response.headers.get_list("set-cookie"))
    assert "HttpOnly" in set_cookie
    assert "SameSite=lax" in set_cookie


def test_login_invalid_credentials_returns_generic_error(
    db_session: Session, settings: Settings
) -> None:
    """Invalid service-level login attempts use a generic credentials error."""
    register_user(db_session)

    with pytest.raises(APIError) as exc_info:
        login(
            LoginRequest(email="missing@example.com", password="Wrong1234"),
            Response(),
            db_session,
            settings,
        )

    assert_api_error(exc_info.value, 401, "invalid_credentials")


def test_api_login_invalid_credentials_returns_generic_error(
    api_client: tuple[TestClient, Session],
) -> None:
    """The login API does not reveal whether email or password failed."""
    client, _ = api_client
    api_register_user(client)

    response = client.post(
        "/api/v1/auth/login",
        json=api_login_payload(email="missing@example.com", password="Wrong1234"),
    )
    wrong_password_response = client.post(
        "/api/v1/auth/login",
        json=api_login_payload(email="user@example.com", password="Wrong1234"),
    )

    assert_error_response(response, 401, "invalid_credentials")
    assert_error_response(wrong_password_response, 401, "invalid_credentials")
    assert response.json()["error"]["message"] == wrong_password_response.json()["error"]["message"]


def test_inactive_user_cannot_login(db_session: Session, settings: Settings) -> None:
    """Inactive users are blocked after credential verification succeeds."""
    user = User(
        email="inactive@example.com",
        password_hash=hash_password("Example1234"),
        full_name="Inactive User",
        is_active=False,
    )
    db_session.add(user)
    db_session.commit()

    with pytest.raises(APIError) as exc_info:
        login(
            LoginRequest(email="inactive@example.com", password="Example1234"),
            Response(),
            db_session,
            settings,
        )

    assert_api_error(exc_info.value, 403, "inactive_user")


def test_api_inactive_user_cannot_login(api_client: tuple[TestClient, Session]) -> None:
    """The login API returns the inactive-user error for disabled accounts."""
    client, session = api_client
    user = User(
        email="inactive@example.com",
        password_hash=hash_password("Example1234"),
        full_name="Inactive User",
        is_active=False,
    )
    session.add(user)
    session.commit()

    response = client.post(
        "/api/v1/auth/login",
        json=api_login_payload(email="inactive@example.com", password="Example1234"),
    )

    assert_error_response(response, 403, "inactive_user")


def test_refresh_with_valid_cookie_sets_new_access_cookie(
    db_session: Session, settings: Settings
) -> None:
    """A valid refresh cookie produces a new access cookie."""
    register_user(db_session)
    _, login_response = login_user(db_session, settings)
    refresh_token = extract_cookie(login_response, "refresh_token")

    response = Response()
    result = refresh(RequestStub({"refresh_token": refresh_token}), response, db_session, settings)

    assert result.status == "ok"
    assert extract_cookie(response, "access_token")


def test_api_refresh_with_valid_cookie_sets_new_access_cookie(
    api_client: tuple[TestClient, Session],
) -> None:
    """The refresh API renews access cookies for valid sessions."""
    client, _ = api_client
    api_register_user(client)
    client.post("/api/v1/auth/login", json=api_login_payload())

    response = client.post("/api/v1/auth/refresh")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert "access_token" in response.cookies


def test_refresh_without_cookie_fails(db_session: Session, settings: Settings) -> None:
    """Missing refresh cookies fail with the documented auth error."""
    with pytest.raises(APIError) as exc_info:
        refresh(RequestStub(), Response(), db_session, settings)

    assert_api_error(exc_info.value, 401, "invalid_refresh_token")


def test_api_refresh_without_cookie_fails(api_client: tuple[TestClient, Session]) -> None:
    """The refresh API rejects unauthenticated refresh requests."""
    client, _ = api_client

    response = client.post("/api/v1/auth/refresh")

    assert_error_response(response, 401, "invalid_refresh_token")


def test_logout_clears_auth_cookies(settings: Settings) -> None:
    """Service-level logout expires both auth cookies."""
    response = logout(Response(), settings)

    set_cookie = ",".join(
        value.decode() for header, value in response.raw_headers if header == b"set-cookie"
    )
    assert "access_token=" in set_cookie
    assert "refresh_token=" in set_cookie
    assert "Max-Age=0" in set_cookie


def test_api_logout_clears_auth_cookies(api_client: tuple[TestClient, Session]) -> None:
    """The logout API expires both auth cookies with a 204 response."""
    client, _ = api_client
    api_register_user(client)
    client.post("/api/v1/auth/login", json=api_login_payload())

    response = client.post("/api/v1/auth/logout")

    assert response.status_code == 204
    set_cookie = ",".join(response.headers.get_list("set-cookie"))
    assert "access_token=" in set_cookie
    assert "refresh_token=" in set_cookie
    assert "Max-Age=0" in set_cookie


def test_users_me_requires_authentication(db_session: Session, settings: Settings) -> None:
    """Current-user dependency rejects requests without auth cookies."""
    with pytest.raises(APIError) as exc_info:
        get_current_user(RequestStub(), db_session, settings)

    assert_api_error(exc_info.value, 401, "not_authenticated")


def test_api_users_me_requires_authentication(api_client: tuple[TestClient, Session]) -> None:
    """The current-user API requires authentication."""
    client, _ = api_client

    response = client.get("/api/v1/users/me")

    assert_error_response(response, 401, "not_authenticated")


def test_users_me_returns_current_user(db_session: Session, settings: Settings) -> None:
    """Current-user route function returns the authenticated user's profile."""
    register_user(db_session)
    _, login_response = login_user(db_session, settings)
    access_token = extract_cookie(login_response, "access_token")

    current_user = get_current_user(
        RequestStub({"access_token": access_token}), db_session, settings
    )
    result = read_me(current_user)

    assert result.email == "user@example.com"


def test_api_users_me_returns_current_user(api_client: tuple[TestClient, Session]) -> None:
    """The current-user API returns the safe authenticated profile."""
    client, _ = api_client
    api_register_user(client)
    client.post("/api/v1/auth/login", json=api_login_payload())

    response = client.get("/api/v1/users/me")

    assert response.status_code == 200
    assert response.json()["email"] == "user@example.com"
    assert "password_hash" not in response.json()


def test_users_me_updates_only_current_profile(db_session: Session, settings: Settings) -> None:
    """Profile update normalizes and persists the current user's name."""
    register_user(db_session)
    _, login_response = login_user(db_session, settings)
    access_token = extract_cookie(login_response, "access_token")
    current_user = get_current_user(
        RequestStub({"access_token": access_token}), db_session, settings
    )

    result = update_me(UserUpdateRequest(full_name="  Updated   Name  "), current_user, db_session)

    assert result.full_name == "Updated Name"


def test_api_users_me_updates_only_current_profile(
    api_client: tuple[TestClient, Session],
) -> None:
    """The profile API updates only the authenticated user's mutable fields."""
    client, _ = api_client
    api_register_user(client)
    client.post("/api/v1/auth/login", json=api_login_payload())

    response = client.patch("/api/v1/users/me", json={"full_name": "  Updated   Name  "})

    assert response.status_code == 200
    assert response.json()["full_name"] == "Updated Name"


def test_api_users_me_updates_profile_metadata(
    api_client: tuple[TestClient, Session],
) -> None:
    """The profile API stores optional SPEC-308 metadata and normalizes blanks."""
    client, _ = api_client
    api_register_user(client)
    client.post("/api/v1/auth/login", json=api_login_payload())

    response = client.patch(
        "/api/v1/users/me",
        json={
            "job_title": "  Operations Manager  ",
            "phone": " +34 600 000 000 ",
            "timezone": "Europe/Madrid",
            "locale": "es_ES",
            "avatar_url": "https://example.com/avatar.png",
            "bio": "  Keeps the workflow moving.  ",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["job_title"] == "Operations Manager"
    assert body["phone"] == "+34 600 000 000"
    assert body["timezone"] == "Europe/Madrid"
    assert body["locale"] == "es-ES"
    assert body["avatar_url"] == "https://example.com/avatar.png"
    assert body["bio"] == "Keeps the workflow moving."


def test_api_users_me_changes_email_with_current_password(
    api_client: tuple[TestClient, Session],
) -> None:
    """Email changes require the current password and store normalized email."""
    client, _ = api_client
    api_register_user(client)
    client.post("/api/v1/auth/login", json=api_login_payload())

    response = client.patch(
        "/api/v1/users/me",
        json={"email": " NEW@Example.COM ", "current_password": "Example1234"},
    )

    assert response.status_code == 200
    assert response.json()["email"] == "new@example.com"


def test_api_users_me_rejects_email_change_without_valid_password(
    api_client: tuple[TestClient, Session],
) -> None:
    """Missing or invalid password confirmation leaves the email unchanged."""
    client, _ = api_client
    api_register_user(client)
    client.post("/api/v1/auth/login", json=api_login_payload())

    response = client.patch("/api/v1/users/me", json={"email": "new@example.com"})
    after = client.get("/api/v1/users/me")

    assert_error_response(response, 403, "invalid_current_password")
    assert after.json()["email"] == "user@example.com"


def test_api_users_me_rejects_duplicate_email_change(
    api_client: tuple[TestClient, Session],
) -> None:
    """Email changes enforce case-insensitive uniqueness across accounts."""
    client, _ = api_client
    api_register_user(client, api_register_payload(email="first@example.com"))
    api_register_user(client, api_register_payload(email="taken@example.com"))
    client.post(
        "/api/v1/auth/login",
        json=api_login_payload(email="first@example.com"),
    )

    response = client.patch(
        "/api/v1/users/me",
        json={"email": "TAKEN@example.com", "current_password": "Example1234"},
    )

    assert_error_response(response, 409, "email_already_registered")


def test_users_me_rejects_invalid_profile(db_session: Session, settings: Settings) -> None:
    """Service-level profile update rejects invalid names."""
    register_user(db_session)
    _, login_response = login_user(db_session, settings)
    access_token = extract_cookie(login_response, "access_token")
    current_user = get_current_user(
        RequestStub({"access_token": access_token}), db_session, settings
    )

    with pytest.raises(APIError) as exc_info:
        update_me(UserUpdateRequest(full_name=""), current_user, db_session)

    assert_api_error(exc_info.value, 400, "invalid_profile")


def test_api_users_me_rejects_invalid_profile(api_client: tuple[TestClient, Session]) -> None:
    """The profile API returns the documented invalid-profile error."""
    client, _ = api_client
    api_register_user(client)
    client.post("/api/v1/auth/login", json=api_login_payload())

    response = client.patch("/api/v1/users/me", json={"full_name": ""})

    assert_error_response(response, 400, "invalid_profile")


def test_api_users_me_rejects_invalid_profile_metadata(
    api_client: tuple[TestClient, Session],
) -> None:
    """Invalid profile metadata returns the documented profile error."""
    client, _ = api_client
    api_register_user(client)
    client.post("/api/v1/auth/login", json=api_login_payload())

    response = client.patch("/api/v1/users/me", json={"avatar_url": "ftp://example.com/me.png"})

    assert_error_response(response, 400, "invalid_profile")
