# SPEC-308 — Enriched Record Metadata

Status: Ready
Owner: Arquitecto de specs
Last updated: 2026-07-28

## Scope And Required Context

This spec governs:

- Additional profile fields for authenticated users.
- Email change with current-password confirmation as the first implementation.
- Additional organization, project, and task metadata fields.
- Backend models, schemas, migrations, APIs, frontend forms, display states, and tests for the metadata fields.
- Public API behavior around backend-generated, non-editable organization slugs.

Required context:

- `AGENTS.md`
- `docs/project-state.md`
- `specs/README.md`
- `specs/000-product-vision.md`
- `specs/001-api-conventions.md`
- `specs/harness/local-validation.md`
- `specs/features/101-auth-and-users.md`
- `specs/features/102-organizations-and-rbac.md`
- `specs/features/103-projects-and-tasks.md`
- `specs/features/104-frontend-app-shell-and-auth-ui.md`
- `specs/features/105-frontend-organizations-ui.md`
- `specs/features/106-frontend-projects-and-tasks-ui.md`
- `docs/decisions/ADR-007-tenant-isolation-and-rbac-enforcement.md`

Memory updates:

- `docs/project-state.md` when current state, validation baseline, next work, or known gaps change
- `docs/implementation-log.md` for meaningful spec-prep, implementation, review, validation, or merge events
- `specs/README.md` when status, dependencies, order, or primary surfaces change
- ADRs if email verification, file upload/storage, project visibility, or profile privacy becomes a durable cross-cutting decision

## Problem

OpsDesk currently exposes only minimal identity, organization, project, and task fields. The product works, but records look sparse for a recruiter-facing B2B SaaS demo and do not capture common business context such as contact details, company profile data, project ownership, budgets, task estimates, or blocker context.

## Goals

- Expand personal profiles with job title, phone, timezone, locale, avatar URL, and bio.
- Allow users to change their email after confirming their current password.
- Expand organizations with company profile and contact fields.
- Keep organization slug backend-generated and non-editable while preserving it as display metadata.
- Expand projects with lifecycle, ownership, budget, visibility, and date metadata.
- Expand tasks with estimates, actual effort, ordering, blocker reason, external reference, type, and watchers.
- Update frontend profile, organization, project, and task forms to display and edit the new fields.
- Preserve existing tenant isolation and RBAC rules.

## Non-Goals

- Email-delivered confirmation links. A future email delivery spec may replace password-only confirmation.
- File upload/storage for avatars or logos. This spec stores URL strings only.
- Billing, invoicing, or financial reporting based on project budget fields.
- Full custom field builders.
- Task labels. Labels belong to `SPEC-309`.
- Client ticket semantics. Ticket-specific task type/source behavior belongs to `SPEC-305`.
- Audit history for metadata changes.

## Actors And Permissions

| Actor | Permission | Notes |
|---|---|---|
| Anonymous user | None | Cannot access metadata APIs |
| Authenticated user | Read and update own profile fields | Email change requires current password |
| Organization owner | Update organization metadata | Backend remains authoritative |
| Organization admin | Read organization metadata, update project/task metadata within existing project/task permissions | Organization-level metadata update remains owner-only unless `SPEC-102` changes |
| Organization member | Read organization/project/task metadata they can access; update assigned task metadata allowed by `SPEC-103` | Cannot bypass existing task reassignment limits |
| Non-member | No tenant-scoped metadata access | Receives tenant-safe `404` |

## Business Rules

- BR-1: Public JSON field names use `snake_case`.
- BR-2: Metadata fields are optional unless an existing spec already requires the field.
- BR-3: Empty strings must be normalized to `null` for optional metadata fields unless a field has a documented empty-string meaning.
- BR-4: URL fields must be valid `http` or `https` URLs.
- BR-5: Email fields must be normalized lowercase where stored.
- BR-6: Phone fields are stored as trimmed strings and are not validated as globally deliverable phone numbers in this spec.
- BR-7: Organization slug is generated only by the backend from organization name and is never accepted from create or update forms.
- BR-8: Organization slug collision handling uses `slug`, `slug-2`, `slug-3`, and so on.
- BR-9: Updating an organization name does not require regenerating the slug unless a later spec explicitly introduces slug regeneration.
- BR-10: User email change through `PATCH /api/v1/users/me` requires the current password in the same request.
- BR-11: User email change must reject a duplicate email case-insensitively.
- BR-12: Project owner must be an organization member who can access the project under current project-access rules.
- BR-13: Project budget amount, when provided, must be non-negative and paired with a three-letter uppercase currency code.
- BR-14: Project date validation must reject an end date earlier than a start date.
- BR-15: Task estimates and actual effort are stored as decimal hours, must be non-negative, and may be updated independently.
- BR-16: Task `sort_order` is project-scoped ordering metadata. It must be stable and not required to be gapless.
- BR-17: Task `blocked_reason` is allowed only when status is `blocked`; leaving `blocked` clears it unless the update explicitly preserves it through a future history feature.
- BR-18: Task `external_reference` is a safe free-text reference for links to external systems. It is not dereferenced by the backend.
- BR-19: Task `task_type` values for this spec are `internal` by default and `operational`. `ticket` is reserved for `SPEC-305`.
- BR-20: Task watchers must be organization members and, after `SPEC-303`, must satisfy project membership visibility rules.

## Data Model Impact

Change `users`:

| Field | Type | Rules |
|---|---|---|
| job_title | string/null | Optional, max 120 chars |
| phone | string/null | Optional, max 40 chars |
| timezone | string/null | Optional IANA timezone name |
| locale | string/null | Optional BCP 47 style locale string |
| avatar_url | string/null | Optional http/https URL |
| bio | text/null | Optional, max 1000 chars |

Change `organizations`:

| Field | Type | Rules |
|---|---|---|
| employee_count | integer/null | Optional, non-negative |
| industry | string/null | Optional, max 120 chars |
| website | string/null | Optional http/https URL |
| contact_email | string/null | Optional email, lowercase |
| phone | string/null | Optional, max 40 chars |
| address_line1 | string/null | Optional, max 160 chars |
| address_line2 | string/null | Optional, max 160 chars |
| city | string/null | Optional, max 120 chars |
| region | string/null | Optional, max 120 chars |
| postal_code | string/null | Optional, max 40 chars |
| country | string/null | Optional, max 120 chars |
| tax_id | string/null | Optional, max 80 chars |
| logo_url | string/null | Optional http/https URL |
| description | text/null | Optional, max 2000 chars |

Change `projects`:

| Field | Type | Rules |
|---|---|---|
| status | enum | `planned`, `active`, `on_hold`, `completed`, `cancelled`; default `active` |
| start_date | date/null | Optional |
| end_date | date/null | Optional, must be on or after `start_date` when both are set |
| budget_amount | numeric/null | Optional, non-negative |
| budget_currency | string/null | Required when budget amount is set, three uppercase letters |
| visibility | enum | `organization`, `project_members`; default `organization` until `SPEC-303` narrows visibility |
| project_owner_id | UUID/null | FK users.id, must be an organization member |

Change `tasks`:

| Field | Type | Rules |
|---|---|---|
| estimated_hours | numeric/null | Optional, non-negative |
| actual_hours | numeric/null | Optional, non-negative |
| sort_order | integer/null | Optional, project-scoped ordering hint |
| blocked_reason | text/null | Optional, max 1000 chars, only valid with `blocked` status |
| external_reference | string/null | Optional, max 200 chars |
| task_type | enum/string | Default `internal`; `ticket` reserved for `SPEC-305` |

Expected new table for task watchers:

| Field | Type | Rules |
|---|---|---|
| id | UUID | Primary key |
| organization_id | UUID | FK organizations.id |
| project_id | UUID | FK projects.id |
| task_id | UUID | FK tasks.id |
| user_id | UUID | FK users.id |
| added_by_id | UUID | FK users.id |
| created_at | timestamp | UTC |

Indexes:

- `projects.status`
- `projects.project_owner_id`
- `projects.visibility`
- `(tasks.project_id, sort_order)`
- `tasks.task_type`
- unique `(task_id, user_id)` for watchers
- indexes on watcher `organization_id`, `project_id`, and `user_id`

Migration required.

## API Contract

Existing endpoints are extended. All endpoints require authentication unless inherited specs say otherwise.

### `GET /api/v1/users/me`

Response includes existing safe user fields plus profile metadata:

```json
{
  "id": "uuid",
  "email": "user@example.com",
  "full_name": "User Name",
  "job_title": "Operations Manager",
  "phone": "+34 600 000 000",
  "timezone": "Europe/Madrid",
  "locale": "es-ES",
  "avatar_url": "https://example.com/avatar.png",
  "bio": "Short profile summary",
  "is_active": true,
  "is_superuser": false,
  "created_at": "2026-07-28T10:00:00Z",
  "updated_at": "2026-07-28T10:00:00Z"
}
```

### `PATCH /api/v1/users/me`

Request fields: `full_name`, `email`, `current_password`, `job_title`, `phone`, `timezone`, `locale`, `avatar_url`, `bio`.

Rules:

- `current_password` is required only when `email` changes.
- `current_password` is never returned.

Errors:

| Status | Code | Condition |
|---:|---|---|
| 400 | `invalid_profile` | Invalid profile metadata |
| 401 | `not_authenticated` | Missing or invalid access cookie |
| 403 | `invalid_current_password` | Email change password confirmation failed |
| 409 | `email_already_registered` | Requested email already belongs to another user |

### Organization Endpoints

`POST /api/v1/organizations`, `GET /api/v1/organizations`, `GET /api/v1/organizations/{organization_id}`, and `PATCH /api/v1/organizations/{organization_id}` return organization metadata fields.

Create/update request fields:

- `name`
- `employee_count`
- `industry`
- `website`
- `contact_email`
- `phone`
- `address_line1`
- `address_line2`
- `city`
- `region`
- `postal_code`
- `country`
- `tax_id`
- `logo_url`
- `description`

Clients must not submit `slug`.

### Project Endpoints

`POST /api/v1/organizations/{organization_id}/projects`, `GET /api/v1/organizations/{organization_id}/projects`, `GET /api/v1/projects/{project_id}`, and `PATCH /api/v1/projects/{project_id}` include project metadata fields.

Create/update request fields add:

- `status`
- `start_date`
- `end_date`
- `budget_amount`
- `budget_currency`
- `visibility`
- `project_owner_id`

Errors add `400 invalid_project` for invalid metadata and invalid project owner.

### Task Endpoints

`POST /api/v1/projects/{project_id}/tasks`, `GET /api/v1/projects/{project_id}/tasks`, `GET /api/v1/tasks/{task_id}`, and `PATCH /api/v1/tasks/{task_id}` include task metadata fields.

Create/update request fields add:

- `estimated_hours`
- `actual_hours`
- `sort_order`
- `blocked_reason`
- `external_reference`
- `task_type`
- `watcher_ids`

Errors add `400 invalid_task` for invalid metadata or invalid watchers.

Task list supports additional filters:

- `task_type`
- `watcher_id`
- `external_reference`

## Frontend Impact

- Profile page displays and edits all user metadata fields.
- Email edit requires a current-password confirmation field and clearly reports duplicate or invalid-password errors.
- Organization create/settings forms display and edit organization metadata but never show an editable slug input.
- Organization detail displays company profile/contact metadata in a compact, scannable layout.
- Project create/settings/detail surfaces display lifecycle, date, budget, visibility, and project owner fields.
- Task create/detail/update surfaces display effort, ordering, blocker, external reference, type, and watchers.
- Watcher selection uses organization members the current actor is allowed to see.
- The frontend must continue to handle backend authorization errors as authoritative.

## Acceptance Criteria

- AC-1: Given an authenticated user, when they update profile metadata with valid data, then `/api/v1/users/me` returns the updated safe profile.
- AC-2: Given an authenticated user changes email with the correct current password, then the email is normalized, uniqueness is enforced, and the response returns the new safe email.
- AC-3: Given an authenticated user changes email without the current password or with an invalid password, then the API rejects the change and leaves the email unchanged.
- AC-4: Given a user creates or updates an organization, when slug is omitted, then the backend returns a generated slug.
- AC-5: Given a client submits a slug field for organization create or update, then the API rejects it with `400 invalid_organization`, and the frontend never sends it.
- AC-6: Given duplicate organization names, when organizations are created, then generated slugs receive numeric suffixes and both creations succeed.
- AC-7: Given an owner updates organization metadata with valid data, then detail/list responses expose the updated metadata.
- AC-8: Given organization metadata is invalid, then the API returns `400 invalid_organization` and the frontend renders safe form errors.
- AC-9: Given an owner/admin creates or updates project metadata with valid data, then project responses expose the updated metadata.
- AC-10: Given invalid project dates, budget, visibility, or owner, then the API returns `400 invalid_project`.
- AC-11: Given a user creates or updates task metadata within existing permissions, then task responses expose the updated metadata.
- AC-12: Given a task is marked `blocked` with a blocker reason, then the reason is stored; given the task leaves `blocked`, then the reason is cleared.
- AC-13: Given invalid task effort, type, watcher, or blocker metadata, then the API returns `400 invalid_task`.
- AC-14: Given task list filters include `task_type`, `watcher_id`, or `external_reference`, then pagination and tenant isolation still match `SPEC-001`.

## Harness Requirements

Required tests/checks:

- Backend API tests for profile metadata update, email change success, duplicate email, invalid current password, and invalid profile metadata.
- Backend API tests for organization slug generation without client input, collision suffixing, client-supplied slug rejection, and metadata validation.
- Backend API tests for project metadata validation, project owner validation, and tenant isolation.
- Backend API tests for task metadata validation, blocker clearing, watcher validation, and new task filters.
- Frontend tests for profile, organization, project, and task forms and safe error rendering.
- Migration checks for added columns and watcher table.

Required commands:

```bash
make test-backend
make test-frontend
make migrations-check
make lint
make format-check
make typecheck
make memory-check SPEC=SPEC-308
```

## Observability And Failure Cases

- Log email changes, organization metadata updates, project owner changes, project visibility changes, and task watcher changes with actor ID and resource ID.
- Do not log current passwords, raw profile bios, task descriptions, task blocker details, tokens, cookies, or secrets.
- Tenant isolation failures must keep returning `404` for non-members.
- Permission failures for known members must keep returning `403`.
- Email-change failure must not reveal whether the current password was close or which credential check failed beyond `invalid_current_password`.

## Open Questions

- [x] Email change uses current-password confirmation first; email-delivered confirmation is deferred until an email delivery spec exists.
- [x] Organization slug is backend-generated, non-editable, and collision-safe with numeric suffixes.

## Implementation Notes

- Keep this implementation in a single migration if practical, but separate watcher table creation from simple nullable column additions if reviewability suffers.
- Preserve existing API response fields so current frontend tests can be expanded rather than rewritten.
- Treat URL-based `avatar_url` and `logo_url` as references only; upload handling requires a later storage decision.
