# SPEC-102 — Organizations and RBAC

Status: Ready  
Owner: Arquitecto de specs  
Last updated: 2026-06-08

## Problem

Users must work inside organizations/workspaces, and every tenant-scoped resource must be isolated by organization.

## Goals

- Allow authenticated users to create organizations.
- Create owner membership for the creator.
- Support roles: `owner`, `admin`, `member`.
- Enforce tenant isolation on organization-scoped resources.
- Establish reusable permission checks for later specs.

## Dependencies

- Requires `SPEC-010` backend scaffold, PostgreSQL service, SQLAlchemy session setup, and Alembic baseline.
- Requires `SPEC-101` user identity and authenticated session behavior.

## Non-Goals

- Billing.
- Enterprise departments.
- External guest users.
- Invitations. Invitations belong to a later feature.
- SSO.

## Actors And Permissions

| Actor | Permission |
|---|---|
| Authenticated user | Create organization |
| Owner | Read/update organization, list members, change member roles, remove non-owner members |
| Admin | Read organization, list members, manage projects/tasks |
| Member | Read organization and participate in visible tasks |
| Non-member | No access to organization data |

## Business Rules

- BR-1: Every organization must have at least one owner.
- BR-2: The creator automatically becomes owner.
- BR-3: Organization slug is unique, lowercase, URL-safe, and generated from name unless supplied.
- BR-4: Public organization URLs use UUID `organization_id`; slug is display/search metadata.
- BR-5: A user can belong to multiple organizations.
- BR-6: Tenant-scoped queries must always filter by organization ID.
- BR-7: Non-members receive `404` for organization-owned resources.
- BR-8: Members receive `403` when they are in the organization but lack the required role.
- BR-9: Members cannot escalate their own role.
- BR-10: The last owner cannot be removed or demoted.
- BR-11: Organization name and slug updates are owner-only.
- BR-12: Removing a member deletes their membership only; it does not delete the user account.

## Data Model Impact

Create `organizations`:

| Field | Type | Rules |
|---|---|---|
| id | UUID | Primary key |
| name | string | Required, 1-120 chars |
| slug | string | Required, unique, lowercase |
| created_at | timestamp | UTC |
| updated_at | timestamp | UTC |

Create `organization_memberships`:

| Field | Type | Rules |
|---|---|---|
| id | UUID | Primary key |
| user_id | UUID | FK users.id |
| organization_id | UUID | FK organizations.id |
| role | enum | owner/admin/member |
| created_at | timestamp | UTC |
| updated_at | timestamp | UTC |

Indexes:

- unique `organizations.slug`
- unique `(user_id, organization_id)`
- index `(organization_id, role)`
- index `(user_id)`

Migration required.

## API Contract

All endpoints require authentication.

### `POST /api/v1/organizations`

Request:

```json
{
  "name": "Acme Ops",
  "slug": "acme-ops"
}
```

`slug` is optional. If omitted, backend generates it from `name`.

Response `201`:

```json
{
  "id": "uuid",
  "name": "Acme Ops",
  "slug": "acme-ops",
  "role": "owner",
  "created_at": "2026-06-07T10:00:00Z",
  "updated_at": "2026-06-07T10:00:00Z"
}
```

Errors:

| Status | Code | Condition |
|---:|---|---|
| 400 | `invalid_organization` | Name or slug invalid |
| 401 | `not_authenticated` | Missing or invalid access cookie |
| 409 | `organization_slug_taken` | Slug already exists |

### `GET /api/v1/organizations`

Response `200` paginated using API conventions. `items` contain organization summary plus current user's role.

### `GET /api/v1/organizations/{organization_id}`

Response `200`: organization detail plus current user's role.

Errors:

| Status | Code | Condition |
|---:|---|---|
| 404 | `organization_not_found` | Missing or non-member |

### `PATCH /api/v1/organizations/{organization_id}`

Owner only.

Request fields: `name`, `slug`.

Response `200`: updated organization detail plus current user's role.

Errors:

| Status | Code | Condition |
|---:|---|---|
| 400 | `invalid_organization` | Name or slug invalid |
| 403 | `insufficient_role` | Non-owner attempts organization update |
| 404 | `organization_not_found` | Missing or non-member |
| 409 | `organization_slug_taken` | Slug already exists |

### `GET /api/v1/organizations/{organization_id}/members`

Owner/admin only.

Response `200` paginated list of memberships with safe user fields.

Errors:

| Status | Code | Condition |
|---:|---|---|
| 403 | `insufficient_role` | Member without admin/owner role attempts member listing |
| 404 | `organization_not_found` | Missing or non-member |

### `PATCH /api/v1/organizations/{organization_id}/members/{user_id}`

Owner only.

Request:

```json
{
  "role": "admin"
}
```

Response `200`: updated membership.

Errors:

| Status | Code | Condition |
|---:|---|---|
| 403 | `insufficient_role` | Non-owner attempts role change |
| 404 | `membership_not_found` | User is not a member of the organization |
| 409 | `last_owner_required` | Would remove/demote final owner |

### `DELETE /api/v1/organizations/{organization_id}/members/{user_id}`

Owner only. Removes a non-owner member from the organization.

Response `204`: membership removed.

Errors:

| Status | Code | Condition |
|---:|---|---|
| 403 | `insufficient_role` | Non-owner attempts member removal |
| 404 | `membership_not_found` | User is not a member of the organization |
| 409 | `last_owner_required` | Would remove final owner |

## Acceptance Criteria

- AC-1: Given an authenticated user, when they create an organization, then the organization is created and the user becomes owner.
- AC-2: Given an unauthenticated user, when they create an organization, then the API returns `401`.
- AC-3: Given a duplicate slug, when organization creation is attempted, then the API returns `409`.
- AC-4: Given a non-member, when they request organization details by UUID, then the API returns `404`.
- AC-5: Given a member, when they request organizations list, then only organizations where they are a member are returned.
- AC-6: Given a member without owner role, when they attempt role management, then the API returns `403`.
- AC-7: Given an owner, when they attempt to demote/remove the last owner, then the API returns `409`.
- AC-8: Given an owner, when they update organization name or slug with valid data, then the organization is updated.
- AC-9: Given an owner, when they remove a non-owner member, then that membership is deleted and the user account remains.
- AC-10: Given an admin, when they list members, then the API returns memberships with safe user fields.

## Harness Requirements

Backend tests:

- Organization creation success.
- Owner membership creation.
- Slug generation and duplicate slug conflict.
- Tenant isolation negative tests.
- Permission tests for owner/admin/member/non-member.
- Last-owner protection.
- Organization update tests.
- Member removal tests.
- Migration check.

Required commands once available:

```bash
make test-backend
make migrations-check
make lint
```

## Observability And Failure Cases

- Log membership role changes with actor ID and organization ID.
- Do not log sensitive user data.
- Tenant access denials should be testable and consistent with API conventions.
