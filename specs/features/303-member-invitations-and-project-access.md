# SPEC-303 — Member Invitations And Project Access

Status: Implemented
Owner: Arquitecto de specs
Last updated: 2026-08-14

## Scope And Required Context

This spec governs:

- Adding existing OpsDesk users to organizations by email through an invitation flow.
- Accepting or declining pending organization and project invitations inside the authenticated app.
- Assigning organization members to specific projects.
- Restricting regular member project visibility and task assignment by project membership.
- Backend models, APIs, permissions, migrations, and frontend UI for invite/member/project access management.

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
- `specs/features/105-frontend-organizations-ui.md`
- `specs/features/106-frontend-projects-and-tasks-ui.md`
- `specs/features/201-background-jobs-and-notifications.md`
- `docs/decisions/ADR-007-tenant-isolation-and-rbac-enforcement.md`

Memory updates:

- `docs/project-state.md` when current state, next work, known gaps, or validation baseline changes
- `docs/implementation-log.md` for meaningful spec-prep, implementation, review, validation, or merge events
- `specs/README.md` when status, dependencies, order, or primary surfaces change
- ADRs if invite/token policy, project-level access, or notification integration becomes a durable cross-cutting decision

## Problem

Organization owners and admins currently cannot add teammates from the product UI. Project work also treats every organization member as equally project-visible, which is too broad once organizations contain multiple teams or client-facing projects.

## Goals

- Let organization owners and admins invite existing OpsDesk users by email.
- Require the invited user to accept in the authenticated app before organization or project access is granted.
- Let owners/admins invite organization members to specific projects.
- Restrict regular organization members to projects where they have explicit project membership.
- Keep organization-level roles (`owner`, `admin`, `member`) separate from project participation.
- Preserve tenant isolation and existing owner-only role transfer rules.
- Provide a minimal in-app “My invitations” flow for `SPEC-303`, without waiting for the full notification inbox from `SPEC-306`.

## Non-Goals

- Public self-serve join links.
- Enterprise SSO or domain-based auto-join.
- Billing seats.
- Inviting emails that do not belong to an existing OpsDesk user.
- Real email provider integration.
- External email invitations.
- Full notification inbox, unread counts, notification preferences, or notification retention. These belong to `SPEC-306`.
- Client users. Client access belongs to `SPEC-305`.
- Task invitations. Task assignment uses normal task assignment rules after project membership exists.

## Actors And Permissions

| Actor | Permission | Notes |
|---|---|---|
| Organization owner | Invite organization members as `admin` or `member`, manage organization roles through existing `SPEC-102` endpoints, invite/remove project members, view all projects | Cannot create a second owner through generic membership endpoints |
| Organization admin | Invite organization members only as `member`, invite/remove project members, view all projects | Cannot invite admins, transfer ownership, delete the organization, or change organization roles |
| Organization member | View only projects where they have explicit project membership; view project membership for projects they can access | Cannot invite organization/project members |
| Invited existing user | List, accept, or decline their own pending invitations | Must already have an OpsDesk user account and must not gain access before acceptance |
| Non-member | No access | Receives tenant-safe `404` where applicable |

## Business Rules

- BR-1: Owners and admins may invite existing users to an organization by email.
- BR-2: The invited email must match an existing user account after normalization to lowercase; unknown emails are rejected safely and do not create placeholder users.
- BR-3: Email-add flows create pending invitations, not immediate organization memberships or project memberships.
- BR-4: Organization owners may invite a user as `admin` or `member`; organization admins may invite only `member`.
- BR-5: Ownership still changes only through the `SPEC-102` ownership-transfer endpoint. Invitation endpoints cannot create, transfer, or remove the `owner` role.
- BR-6: A user cannot have duplicate memberships in the same organization.
- BR-7: A user cannot have more than one active pending invitation for the same organization or project scope.
- BR-8: Pending invitations expire after 7 days. Expired invitations cannot be accepted or declined and return `400 invalid_invitation`.
- BR-8a: The service marks expired pending invitations as `expired` before creating a replacement invitation for the same user and scope.
- BR-9: Organization invitation acceptance creates the organization membership with the invited role.
- BR-10: Organization invitation decline records `declined_at` and grants no access.
- BR-11: Project invitations can target only users who are already members of the project’s organization.
- BR-12: Project invitations create pending project access; project membership is created only after acceptance.
- BR-13: Project member removal deletes only project membership. It does not remove organization membership or the user account.
- BR-14: Owners/admins have organization-wide project management rights and can view/manage all projects, even when they do not have explicit rows in `project_memberships`.
- BR-15: Regular members can list, read, and work only in projects where they have explicit project membership.
- BR-16: Project list endpoints must return all organization projects for owners/admins and only explicitly joined projects for regular members.
- BR-17: Project detail and task endpoints must return tenant-safe `404` to regular organization members who are not project members.
- BR-18: Task assignees must be explicit project members of the task’s project. Owners/admins may manage tasks but still cannot assign a task to a user who lacks project membership.
- BR-19: Existing projects must keep current behavior after migration by backfilling `project_memberships` for all current organization members on each existing project.
- BR-20: New projects created after this spec is implemented must automatically add the creator as a project member. Owner/admin visibility still does not depend on this row.
- BR-21: Invitation listing and accept/decline endpoints expose only invitations addressed to the current user, plus organization-scoped management lists for owner/admin inviters.
- BR-22: Invitation responses must not expose whether an unrelated tenant, project, or invitation exists.

## Data Model Impact

Create `invitations`:

| Field | Type | Rules |
|---|---|---|
| id | UUID | Primary key |
| organization_id | UUID | FK organizations.id |
| target_email | string | Required, normalized lowercase, must match an existing user |
| target_user_id | UUID | FK users.id |
| role | enum/null | `admin` or `member` for organization invitations; null for project invitations |
| scope_type | enum | `organization` or `project` |
| project_id | UUID/null | FK projects.id for project invitations |
| invited_by_id | UUID | FK users.id |
| status | enum | `pending`, `accepted`, `declined`, `cancelled`, or `expired` |
| accepted_at | timestamp/null | UTC |
| declined_at | timestamp/null | UTC |
| cancelled_at | timestamp/null | UTC |
| expires_at | timestamp | UTC, default now plus 7 days |
| created_at | timestamp | UTC |
| updated_at | timestamp | UTC |

Create `project_memberships`:

| Field | Type | Rules |
|---|---|---|
| id | UUID | Primary key |
| organization_id | UUID | FK organizations.id |
| project_id | UUID | FK projects.id |
| user_id | UUID | FK users.id |
| added_by_id | UUID/null | FK users.id; nullable for migration backfill |
| created_at | timestamp | UTC |

Indexes:

- unique pending organization invitation per `(organization_id, target_user_id)` where `scope_type = 'organization'` and `status = 'pending'`
- unique pending project invitation per `(project_id, target_user_id)` where `scope_type = 'project'` and `status = 'pending'`
- unique `(project_id, user_id)` for project members
- indexes on `invitations.organization_id`, `invitations.target_user_id`, `invitations.project_id`, `project_memberships.organization_id`, `project_memberships.project_id`, and `project_memberships.user_id`

Migration required:

- Add `invitations`.
- Add `project_memberships`.
- Backfill `project_memberships` so every current organization member is a project member for every current project in that organization.
- Preserve deterministic migration behavior and avoid relying on application services during migration.

## API Contract

All endpoints require authentication.

### `POST /api/v1/organizations/{organization_id}/invitations`

Owner/admin only. Creates a pending organization invitation for an existing user.

Request:

```json
{
  "email": "teammate@example.com",
  "role": "member"
}
```

Response `201`:

```json
{
  "id": "uuid",
  "organization_id": "uuid",
  "target_email": "teammate@example.com",
  "target_user_id": "uuid",
  "role": "member",
  "scope_type": "organization",
  "project_id": null,
  "status": "pending",
  "accepted_at": null,
  "declined_at": null,
  "cancelled_at": null,
  "expires_at": "2026-08-21T10:00:00Z",
  "created_at": "2026-08-14T10:00:00Z",
  "updated_at": "2026-08-14T10:00:00Z"
}
```

Errors:

| Status | Code | Condition |
|---:|---|---|
| 400 | `invalid_invitation` | Invalid role, self-invite, expired target state, or malformed business input |
| 403 | `insufficient_role` | Member attempts invite, or admin attempts to invite another admin |
| 404 | `organization_not_found` | Missing organization or non-member |
| 404 | `user_not_found` | Email does not match an existing user |
| 409 | `membership_exists` | Target user is already an organization member |
| 409 | `invitation_exists` | Matching active pending invitation already exists |

### `GET /api/v1/organizations/{organization_id}/invitations`

Owner/admin only. Lists pending, accepted, declined, and expired invitations for the organization using API pagination. Supports optional `status=pending|accepted|declined|expired`.

### `DELETE /api/v1/organizations/{organization_id}/invitations/{invitation_id}`

Owner/admin only. Cancels a pending organization or project invitation in the organization by setting `status` to `cancelled`.

Response `204`: invitation cancelled with no response body.

Errors:

| Status | Code | Condition |
|---:|---|---|
| 403 | `insufficient_role` | Member attempts cancellation |
| 404 | `organization_not_found` | Missing organization or non-member |
| 404 | `invitation_not_found` | Missing invitation or invitation outside the organization |
| 409 | `invitation_finalized` | Invitation is already accepted, declined, expired, or cancelled |

### `GET /api/v1/invitations`

Lists invitations addressed to the current user using API pagination. Supports optional `status=pending|accepted|declined|expired`.

Response `200`: paginated invitation summaries with safe organization/project display names.

### `POST /api/v1/invitations/{invitation_id}/accept`

Accepts a pending invitation addressed to the current user.

Behavior:

- Organization invitation: creates organization membership with the invited role and sets `status` to `accepted`.
- Project invitation: creates project membership if the user is still an organization member and sets `status` to `accepted`.

Response `200`: accepted invitation summary.

Errors:

| Status | Code | Condition |
|---:|---|---|
| 400 | `invalid_invitation` | Invitation expired or no longer valid |
| 404 | `invitation_not_found` | Missing invitation or not the target user |
| 409 | `membership_exists` | Membership already exists |

### `POST /api/v1/invitations/{invitation_id}/decline`

Declines a pending invitation addressed to the current user by setting `status` to `declined`.

Response `200`: declined invitation summary.

Errors follow accept semantics.

### `GET /api/v1/projects/{project_id}/members`

Owners/admins and project members may list project members using API pagination. Regular organization members who are not project members receive `404 project_not_found`.

### `POST /api/v1/projects/{project_id}/invitations`

Owner/admin only. Invites an existing organization member to join a project.

Request:

```json
{
  "user_id": "uuid"
}
```

Response `201`: project invitation summary.

Errors:

| Status | Code | Condition |
|---:|---|---|
| 400 | `invalid_invitation` | Target is the inviter or invalid for project invitation |
| 403 | `insufficient_role` | Regular member attempts project invite |
| 404 | `project_not_found` | Missing project, non-member organization, or hidden project |
| 404 | `membership_not_found` | Target user is not an organization member |
| 409 | `project_membership_exists` | Target user is already a project member |
| 409 | `invitation_exists` | Matching active pending project invitation already exists |

### `DELETE /api/v1/projects/{project_id}/members/{user_id}`

Owner/admin only. Removes explicit project membership.

Response `204`: project membership removed.

Errors:

| Status | Code | Condition |
|---:|---|---|
| 403 | `insufficient_role` | Regular member attempts project member removal |
| 404 | `project_not_found` | Missing project, non-member organization, or hidden project |
| 404 | `project_membership_not_found` | User is not a project member |

### Existing Endpoint Changes

- `GET /api/v1/organizations/{organization_id}/projects`: owners/admins receive all projects; regular members receive only projects with explicit project membership.
- `GET /api/v1/projects/{project_id}`: owners/admins may read any organization project; regular members must have explicit project membership.
- `PATCH /api/v1/projects/{project_id}`: remains owner/admin only.
- `POST /api/v1/projects/{project_id}/tasks`: owners/admins may create tasks in any organization project; regular members must have explicit project membership. `assignee_id`, when present, must be an explicit project member.
- `GET /api/v1/projects/{project_id}/tasks`: owners/admins may list any organization project tasks; regular members must have explicit project membership.
- `GET /api/v1/tasks/{task_id}` and `PATCH /api/v1/tasks/{task_id}`: regular members must have explicit membership in the task’s project. Owner/admin project management rights remain organization-wide, but assignee changes still require the target assignee to be an explicit project member.

Errors must follow `specs/001-api-conventions.md`, including `403 insufficient_role`, tenant-safe `404 organization_not_found`/`project_not_found`/`task_not_found`, `409 membership_exists`, and `400 invalid_invitation`.

## Frontend Impact

- Organization members page gains an invite-by-email form for owners/admins.
- The organization invitation form allows owner users to choose `admin` or `member`; admin users may invite only `member`.
- Organization members page shows organization invitation state and lets owners/admins cancel pending invitations.
- Project settings or project members page gains project invitation controls for owners/admins.
- Project member UI clearly distinguishes organization membership from project participation.
- Regular members see only projects where they have explicit access.
- Authenticated app gains a minimal “My invitations” view or panel where the current user can see pending organization/project invitations and accept or decline them.
- Duplicate member/invite conflicts must render safe actionable errors.
- The minimal invitation UI is intentionally separate from the future `SPEC-306` notification inbox; `SPEC-306` must later surface these same invitations through the general notification UI without changing invitation semantics.

## Acceptance Criteria

- AC-1: Given an owner/admin enters an existing user's email, when they invite the user to an organization, then a pending organization invitation is created and no membership exists before acceptance.
- AC-2: Given an owner/admin enters an unknown email, when they submit the invitation, then the API rejects it safely and does not create a placeholder user.
- AC-3: Given an owner invites a user as `admin`, when the user accepts, then the user becomes an organization admin.
- AC-4: Given an admin attempts to invite a user as `admin`, then the API returns `403 insufficient_role`.
- AC-5: Given a member tries to invite a user by email, then the API returns `403 insufficient_role`.
- AC-6: Given an invited user views “My invitations”, then they can see only their own invitations.
- AC-7: Given an invited user accepts an organization invitation, then the organization membership is created with the invited role.
- AC-8: Given an invited user declines an organization invitation, then no membership is created.
- AC-9: Given an owner/admin invites an organization member to a project, when the recipient accepts, then the user appears in that project's member list.
- AC-10: Given a user is not an organization member, when they are invited to a project, then the API rejects the request safely.
- AC-11: Given a regular organization member has no explicit membership in a project, when they list projects or access that project/tasks, then the project is hidden with tenant-safe behavior.
- AC-12: Given an owner/admin lists projects, then all organization projects remain visible regardless of explicit project membership rows.
- AC-13: Given a project has explicit members, when a task is assigned, then the assignee must be an explicit project member and invalid assignees are rejected.
- AC-14: Given the migration runs on existing data, then all current organization members retain access to current organization projects through backfilled project memberships.
- AC-15: Given a new project is created, then the creator is added as an explicit project member.

## Harness Requirements

Required tests/checks:

- Backend API tests for organization invite-by-email success, unknown-email rejection, duplicate invitation, existing membership conflict, forbidden member invite, admin-inviting-admin rejection, accept, decline, expiration, and cancellation cases.
- Backend API tests for project invitation success, target-not-organization-member rejection, duplicate invitation, existing project membership conflict, accept, decline, and removal cases.
- Backend API tests for project visibility and tenant isolation across owner/admin/member/non-member cases.
- Backend API tests for task assignment rejection when the target user is not an explicit project member.
- Migration test or migration validation evidence proving existing organization members are backfilled into current project memberships.
- Frontend tests for owner/admin/member invitation UI permissions, “My invitations” accept/decline behavior, project visibility, and safe duplicate/unknown-email errors.
- Existing Playwright E2E can remain unchanged for this spec unless implementation touches critical navigation in a way that requires focused E2E coverage.
- Migration checks.

Required commands:

```bash
make test-backend
make test-frontend
make migrations-check
make lint
make format-check
make typecheck
make memory-check SPEC=SPEC-303
```

## Resolved Questions

- Adding an existing user by email always requires invitation acceptance through a minimal in-app invitation flow.
- Unknown-email invitations are rejected; no external email invitation is sent.
- Project membership restricts regular member project visibility and task assignment eligibility.
- Organization owners may invite admins or members; organization admins may invite only members.
- Existing projects are backfilled with all current organization members during migration to preserve current access.
- Project invitations reject users who are not already organization members. Organization and project invitations are not combined in this spec.
- Task invitations are removed from `SPEC-303`; task assignment remains available only after project membership exists.
- `SPEC-306` is not a prerequisite for `SPEC-303`. `SPEC-306` must later integrate the `SPEC-303` invitation model into the full in-app notification inbox.
