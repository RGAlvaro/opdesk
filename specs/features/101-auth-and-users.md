# SPEC-101 — Authentication and Users

Status: Implemented  
Owner: Arquitecto de specs  
Last updated: 2026-06-16

## Scope And Required Context

This spec governs:

- User model, password handling, auth services, auth cookies/JWTs, `/api/v1/auth/*`, `/api/v1/users/me`, auth tests, or auth-related `.env.example` settings.

Required context:

- `AGENTS.md`
- `docs/project-state.md`
- `specs/README.md`
- `specs/001-api-conventions.md`
- `specs/harness/local-validation.md`
- `docs/decisions/ADR-001-python-package-manager.md`
- `docs/decisions/ADR-002-backend-module-layout.md`

Memory updates:

- `docs/project-state.md` if auth state, validation baseline, or known gaps change
- `docs/implementation-log.md` for meaningful implementation, review, or validation events
- `specs/README.md` if status, dependencies, order, or primary surfaces change
- ADRs if auth token storage, cookie strategy, or user bootstrap policy changes

## Problem

Users need secure access to OpsDesk before organizations, projects, tasks, and permissions can be implemented.

## Goals

- Allow users to register, log in, refresh session, log out, and retrieve their own profile.
- Store passwords securely.
- Provide browser-authenticated API access through httpOnly cookies.
- Establish the identity foundation for organization membership and RBAC.
- Provide tests for success, failure, and security-sensitive paths.

## Non-Goals

- Enterprise SSO.
- OAuth login.
- Password reset email flow.
- Two-factor authentication.
- Persistent refresh token revocation list.
- Billing-related identity.

## Dependencies

- Requires `SPEC-010` backend scaffold, PostgreSQL service, SQLAlchemy session setup, and Alembic baseline.
- `SPEC-011` local database admin may be used for local inspection during development/review, but it is not a functional dependency and must not replace API tests or migrations.

## Actors And Permissions

| Actor | Permission | Notes |
|---|---|---|
| Anonymous user | Register, log in, refresh with valid refresh cookie | Cannot access protected resources |
| Authenticated user | Retrieve and update own basic profile, log out | Cannot access other users directly |
| Superuser | Internal flag only | Bootstrap behavior defined below |

## Business Rules

- BR-1: Email must be unique case-insensitively.
- BR-2: Email must be stored normalized in lowercase.
- BR-3: Password must never be stored in plain text.
- BR-4: Password hashing must use Argon2id or bcrypt with production-safe parameters.
- BR-5: Password policy: minimum 10 characters, at least one letter, at least one number.
- BR-6: Inactive users cannot authenticate or refresh sessions.
- BR-7: Protected endpoints reject unauthenticated requests with `401`.
- BR-8: API responses must not expose password hashes or token values.
- BR-9: Browser auth uses httpOnly cookies as defined in `specs/001-api-conventions.md`.
- BR-10: The first registered user becomes `is_superuser=true`; later users default to `false`. If this behavior changes, a separate admin bootstrap spec is required.
- BR-11: Invalid credential responses must be generic and must not reveal whether the email exists.
- BR-12: Direct local database edits through Adminer or other database tools must not be used to satisfy auth behavior. Manual DB inspection is allowed for debugging only.
- BR-13: First-user bootstrap tests must control database state explicitly so local manual rows or previous development data cannot change expected `is_superuser` behavior.

## Data Model Impact

Create `users` table:

| Field | Type | Rules |
|---|---|---|
| id | UUID | Primary key |
| email | string | Required, unique, indexed, lowercase |
| password_hash | string | Required |
| full_name | string | Required, trimmed, 1-120 chars |
| is_active | boolean | Default true |
| is_superuser | boolean | Default false except first registered user |
| created_at | timestamp | UTC |
| updated_at | timestamp | UTC |

Migration required.

## Configuration Contract

`.env.example` must add safe local placeholders for auth configuration introduced by this spec.

Required variables:

| Variable | Purpose | Example |
|---|---|---|
| `AUTH_SECRET_KEY` | Signing key for auth tokens | `local_dev_change_me_min_32_chars` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token lifetime | `15` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token lifetime | `7` |
| `ACCESS_TOKEN_COOKIE_NAME` | Browser cookie name for access token | `access_token` |
| `REFRESH_TOKEN_COOKIE_NAME` | Browser cookie name for refresh token | `refresh_token` |
| `AUTH_COOKIE_SECURE` | Whether auth cookies require HTTPS | `false` locally |
| `AUTH_COOKIE_SAMESITE` | SameSite policy for auth cookies | `lax` |

Rules:

- Production must override `AUTH_SECRET_KEY` with a strong secret and must not reuse local placeholders.
- `AUTH_COOKIE_SECURE=false` is allowed only for local development.
- Cookie expiry values must match `specs/001-api-conventions.md` unless that convention is updated first.
- Auth settings must be loaded through the existing settings pattern from `SPEC-010`.

## API Contract

All endpoints use `/api/v1`.

### `POST /api/v1/auth/register`

Request:

```json
{
  "email": "user@example.com",
  "password": "Example1234",
  "full_name": "User Name"
}
```

Response `201`:

```json
{
  "id": "uuid",
  "email": "user@example.com",
  "full_name": "User Name",
  "is_active": true,
  "is_superuser": true,
  "created_at": "2026-06-07T10:00:00Z",
  "updated_at": "2026-06-07T10:00:00Z"
}
```

Errors:

| Status | Code | Condition |
|---:|---|---|
| 400 | `weak_password` | Password policy not met |
| 409 | `email_already_registered` | Email already registered, case-insensitive |

### `POST /api/v1/auth/login`

Request:

```json
{
  "email": "user@example.com",
  "password": "Example1234"
}
```

Response `200` sets `access_token` and `refresh_token` httpOnly cookies and returns:

```json
{
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "full_name": "User Name",
    "is_active": true,
    "is_superuser": false,
    "created_at": "2026-06-07T10:00:00Z",
    "updated_at": "2026-06-07T10:00:00Z"
  }
}
```

Errors:

| Status | Code | Condition |
|---:|---|---|
| 401 | `invalid_credentials` | Email/password invalid |
| 403 | `inactive_user` | User exists but is inactive |

### `POST /api/v1/auth/refresh`

Request: no JSON body. Uses `refresh_token` cookie.

Response `200` sets a fresh `access_token` cookie:

```json
{
  "status": "ok"
}
```

Errors:

| Status | Code | Condition |
|---:|---|---|
| 401 | `invalid_refresh_token` | Missing, expired, malformed, or inactive-user refresh token |

### `POST /api/v1/auth/logout`

Request: no JSON body.

Response `204`: clears `access_token` and `refresh_token` cookies.

### `GET /api/v1/users/me`

Response `200`:

```json
{
  "id": "uuid",
  "email": "user@example.com",
  "full_name": "User Name",
  "is_active": true,
  "is_superuser": false,
  "created_at": "2026-06-07T10:00:00Z",
  "updated_at": "2026-06-07T10:00:00Z"
}
```

Errors:

| Status | Code | Condition |
|---:|---|---|
| 401 | `not_authenticated` | Missing or invalid access cookie |

### `PATCH /api/v1/users/me`

Request:

```json
{
  "full_name": "Updated Name"
}
```

Response `200`: updated safe user profile.

Errors:

| Status | Code | Condition |
|---:|---|---|
| 400 | `invalid_profile` | Empty or too-long name |
| 401 | `not_authenticated` | Missing or invalid access cookie |

## Frontend Impact

- Signup page.
- Login page.
- Session bootstrap query using `GET /api/v1/users/me`.
- Protected route guard.
- Logout action.
- Profile display/edit for `full_name`.
- Forms render server errors without exposing tokens.

## Acceptance Criteria

- AC-1: Given a valid new email and valid password, when the user registers, then a user is created, the email is stored lowercase, and the response excludes password and token data.
- AC-2: Given an already registered email with different casing, when registration is attempted, then the API returns `409`.
- AC-3: Given a weak password, when registration is attempted, then the API returns `400`.
- AC-4: Given the first registered user, when registration succeeds, then the user is marked `is_superuser=true`.
- AC-5: Given valid credentials for an active user, when login is requested, then httpOnly auth cookies are set and a safe user payload is returned.
- AC-6: Given invalid credentials, when login is requested, then the API returns `401` with generic error text.
- AC-7: Given an inactive user, when login is requested, then the API returns `403`.
- AC-8: Given a valid refresh cookie, when refresh is requested, then a fresh access cookie is set.
- AC-9: Given logout, when the request succeeds, then auth cookies are cleared.
- AC-10: Given an unauthenticated request, when `/api/v1/users/me` is requested, then the API returns `401`.
- AC-11: Given an authenticated request, when `/api/v1/users/me` is requested, then the API returns the current user's safe profile.
- AC-12: Given an authenticated user, when they update `full_name`, then only their own profile is updated.

## Harness Requirements

Backend tests:

- Unit test email normalization.
- Unit test password policy.
- Unit or integration test password hashing/verification.
- API tests for register success, duplicate email, weak password, first-user superuser, login success, login failure, inactive login, refresh success/failure, logout cookie clearing, `/api/v1/users/me` unauthenticated/authenticated, profile update.
- Migration check for `users` table.
- Test setup must isolate or reset user table state for first-user superuser assertions.

API test clarification:

- API tests may run through an in-process ASGI client, such as FastAPI `TestClient` or HTTPX `ASGITransport`, or through the local Docker backend using HTTP requests.
- In-process ASGI API tests should use `uvloop` as defined in `specs/harness/local-validation.md` when synchronous endpoints or dependencies otherwise hang under the default `asyncio` event loop.
- API tests must exercise the public HTTP endpoints, not only route functions or services called directly.
- API tests must validate status codes, documented error shape where practical, and cookie behavior for login, refresh, and logout.
- If an in-process ASGI client is unavailable or unreliable in the local environment, the Docker/local-backend HTTP path is acceptable only when it is automated and covers the same acceptance criteria.

Frontend tests after UI exists:

- Login form validation.
- Signup form validation.
- Protected route redirects unauthenticated users.
- Logout clears session state.

Required commands once available:

```bash
make test-backend
make lint
make format-check
make typecheck
make migrations-check
make smoke
```

`make smoke` includes local Docker services from `SPEC-010` and `SPEC-011`. Adminer availability may be checked as part of smoke validation, but auth acceptance criteria still require API tests.

## Observability And Failure Cases

- Log failed authentication attempts with email hash or normalized email only if safe; never log passwords or tokens.
- Invalid credential responses remain generic.
- Expired token failures should be visible in debug/test logs but not noisy in production logs.

## Implementation Notes

- Prefer dependency-injected settings for cookie names, token secret, expiry values, and secure cookie mode.
- Use `Secure=false` only in local development.
- Do not add password reset in this spec.
- Adminer from `SPEC-011` can help inspect local `users` rows during debugging, but implementation and review must validate behavior through APIs, tests, and migrations.
