# SPEC-101 — Authentication and Users

Status: Ready  
Owner: Arquitecto de specs  
Last updated: 2026-06-08

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

Frontend tests after UI exists:

- Login form validation.
- Signup form validation.
- Protected route redirects unauthenticated users.
- Logout clears session state.

Required commands once available:

```bash
make test-backend
make lint
make migrations-check
```

## Observability And Failure Cases

- Log failed authentication attempts with email hash or normalized email only if safe; never log passwords or tokens.
- Invalid credential responses remain generic.
- Expired token failures should be visible in debug/test logs but not noisy in production logs.

## Implementation Notes

- Prefer dependency-injected settings for cookie names, token secret, expiry values, and secure cookie mode.
- Use `Secure=false` only in local development.
- Do not add password reset in this spec.
