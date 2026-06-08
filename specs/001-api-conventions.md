# SPEC-001 — API Conventions

Status: Ready  
Owner: Arquitecto de specs  
Last updated: 2026-06-08

## Purpose

This spec defines cross-feature API conventions. Feature specs inherit these rules unless they explicitly override them.

## Base Path And Versioning

- Public API endpoints use `/api/v1`.
- Health endpoints may live outside versioned API if useful for infrastructure, for example `/health`.
- Feature specs must write endpoint paths with the full public path, for example `GET /api/v1/users/me`.

## Identifiers

- Public resource identifiers are UUID strings.
- Organization slugs may be exposed as human-readable fields but are not the default primary URL identifier for MVP endpoints.
- Tenant-scoped resources must validate organization membership before returning data.

## Timestamps

- Store timestamps in UTC.
- Return timestamps as ISO 8601 strings.
- Include `created_at` and `updated_at` on persisted primary resources unless a feature spec says otherwise.

## Error Format

API errors return JSON:

```json
{
  "error": {
    "code": "string_code",
    "message": "Human-readable message",
    "details": {}
  }
}
```

Rules:

- `code` is stable and machine-readable.
- `message` is safe for end users.
- `details` may be empty.
- Authentication errors must not reveal whether an email exists.
- Authorization errors must not leak cross-tenant data.

Common status codes:

| Status | Use |
|---:|---|
| 400 | Invalid request shape or invalid business input |
| 401 | Missing or invalid authentication |
| 403 | Authenticated user lacks permission for a known accessible scope |
| 404 | Resource not found or hidden by tenant isolation policy |
| 409 | Unique constraint or state conflict |
| 422 | Framework-level validation error if FastAPI emits it |
| 500 | Unexpected server error |

Tenant isolation policy:

- Return `404` when a user is not a member of the organization that owns a requested resource.
- Return `403` when the user is a member but lacks the required role/action.

## Pagination

List endpoints use `limit` and `offset`.

Defaults:

- `limit`: 20
- `offset`: 0
- max `limit`: 100

Response shape:

```json
{
  "items": [],
  "total": 0,
  "limit": 20,
  "offset": 0
}
```

## Authentication

Browser authentication uses httpOnly cookies:

- `access_token`: short-lived signed JWT, httpOnly, SameSite=Lax.
- `refresh_token`: longer-lived signed JWT, httpOnly, SameSite=Lax.
- Cookies must be `Secure` in production.

Token policy:

- Access token expiry: 15 minutes.
- Refresh token expiry: 7 days.
- Logout clears both cookies.
- Refresh endpoint rotates or reissues tokens; exact persistence/revocation may be added in a later security hardening spec.

## Request And Response Naming

- JSON uses `snake_case`.
- API schemas should avoid exposing internal-only fields.
- Password hashes, token values, and cookie values must never appear in JSON responses.
- Empty successful responses should use `204` with no JSON body.
- Create endpoints should return `201` with the created resource or documented envelope.

## Validation Harness

Every API feature with endpoints must include:

- Success path API tests.
- Failure path API tests.
- Authentication and authorization tests when applicable.
- Tests for the documented error status and shape where practical.
