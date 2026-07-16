# SPEC-303 — Member Invitations And Project Access

Status: Draft
Owner: Arquitecto de specs
Last updated: 2026-07-15

## Scope And Required Context

This spec governs:

- Adding organization members by email.
- Assigning organization members to specific projects.
- Backend models, APIs, permissions, and frontend UI for invite/member/project access management.

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
- `specs/features/201-background-jobs-and-notifications.md`
- `specs/features/105-frontend-organizations-ui.md`
- `specs/features/106-frontend-projects-and-tasks-ui.md`
- `specs/features/306-in-app-notifications.md`
- `docs/decisions/ADR-007-tenant-isolation-and-rbac-enforcement.md`

Memory updates:

- `docs/project-state.md` when current state, next work, known gaps, or validation baseline changes
- `docs/implementation-log.md` for meaningful spec-prep, implementation, review, validation, or merge events
- `specs/README.md` when status, dependencies, order, or primary surfaces change
- ADRs if invite/token policy, project-level access, or email delivery becomes a durable cross-cutting decision

## Problem

Organization owners and admins currently cannot add teammates from the product UI. Project work also treats every organization member as equally project-visible, which is too broad once organizations contain multiple teams or client-facing projects.

## Goals

- Let organization owners and admins add members by email.
- Invite only existing OpsDesk users by email.
- Require the invited user to accept an in-app notification before organization, project, or task access is granted.
- Let owners/admins assign organization members to specific projects.
- Keep organization-level roles (`owner`, `admin`, `member`) separate from project-level participation.
- Preserve tenant isolation and existing owner-only role transfer rules.

## Non-Goals

- Public self-serve join links.
- Enterprise SSO or domain-based auto-join.
- Billing seats.
- Inviting emails that do not belong to an existing OpsDesk user.
- Real email provider integration.
- External email invitations. Invitations are delivered through in-app notifications from `SPEC-306`.
- Client users. Client access belongs to `SPEC-305`.

## Actors And Permissions

| Actor | Permission | Notes |
|---|---|---|
| Organization owner | Add members by email, manage organization roles, assign project members | Cannot create a second owner through generic membership endpoints |
| Organization admin | Add members by email and assign project members | Cannot transfer ownership or delete the organization |
| Organization member | View project membership for projects they can access | Cannot add organization/project members |
| Invited email recipient | Accept or decline an in-app invitation notification | Must already have an OpsDesk user account and must not gain access before acceptance |
| Non-member | No access | Receives tenant-safe `404` where applicable |

## Business Rules

- BR-1: Owners and admins may add organization members by email.
- BR-2: The invited email must match an existing user account; unknown emails are rejected safely and do not create placeholder users.
- BR-3: Adding by email creates a pending invitation and an in-app notification, not an immediate membership or project/task assignment.
- BR-4: Generic email-add flows can grant only `admin` or `member`; ownership still changes only through the `SPEC-102` transfer endpoint.
- BR-5: A user cannot have duplicate memberships in the same organization.
- BR-6: Project membership can include only users who are already organization members.
- BR-7: Project member removal does not remove organization membership or the user account.
- BR-8: Task assignment must reject assignees who are not members of the task's project, except organization owners/admins if the Ready spec explicitly preserves their override.
- BR-9: Owners/admins keep organization-wide project management rights unless this spec explicitly narrows them before implementation.
- BR-10: Accepted project invitations create project membership but do not change organization role.
- BR-11: Accepted task invitations may assign or add the user to the task only when they are already allowed by organization and project membership rules.

## Data Model Impact

Expected new table:

| Field | Type | Rules |
|---|---|---|
| id | UUID | Primary key |
| organization_id | UUID | FK organizations.id |
| target_email | string | Required, normalized lowercase, must match an existing user |
| target_user_id | UUID | FK users.id |
| role | enum | `admin` or `member` |
| scope_type | enum | `organization`, `project`, or `task` |
| project_id | UUID/null | FK projects.id for project/task invitations |
| task_id | UUID/null | FK tasks.id for task invitations |
| invited_by_id | UUID | FK users.id |
| accepted_at | timestamp/null | UTC |
| declined_at | timestamp/null | UTC |
| expires_at | timestamp | UTC |
| created_at | timestamp | UTC |
| updated_at | timestamp | UTC |

Expected new table for project access:

| Field | Type | Rules |
|---|---|---|
| id | UUID | Primary key |
| organization_id | UUID | FK organizations.id |
| project_id | UUID | FK projects.id |
| user_id | UUID | FK users.id |
| added_by_id | UUID | FK users.id |
| created_at | timestamp | UTC |

Indexes:

- unique pending invitation per `(organization_id, target_user_id, scope_type, project_id, task_id)` when not accepted or declined
- unique `(project_id, user_id)` for project members
- indexes on `organization_id`, `project_id`, and `user_id`

Migration required if implemented.

## API Contract

Exact endpoints remain Draft. Candidate endpoints:

- `POST /api/v1/organizations/{organization_id}/members/by-email`
- `GET /api/v1/organizations/{organization_id}/invitations`
- `DELETE /api/v1/organizations/{organization_id}/invitations/{invitation_id}`
- `POST /api/v1/invitations/{invitation_id}/accept`
- `POST /api/v1/invitations/{invitation_id}/decline`
- `GET /api/v1/projects/{project_id}/members`
- `POST /api/v1/projects/{project_id}/members`
- `DELETE /api/v1/projects/{project_id}/members/{user_id}`
- `POST /api/v1/tasks/{task_id}/assignee-invitations`

Errors must follow `specs/001-api-conventions.md`, including `403 insufficient_role`, `404 organization_not_found`, `404 project_not_found`, `409 membership_exists`, and `400 invalid_invitation`.

## Frontend Impact

- Organization members page gains an invite-by-email flow for owners/admins.
- Project settings or project members page gains project invitation by email.
- Task assignment controls may create an invitation when the target user exists but must accept before being assigned.
- Invitation notifications appear through the in-app notification UI from `SPEC-306`.
- The UI must clearly distinguish organization membership from project participation.
- Duplicate member/invite conflicts must render safe actionable errors.

## Acceptance Criteria

- AC-1: Given an owner/admin enters an existing user's email, when they invite the user to an organization, then a pending invitation and in-app notification are created and no membership exists before acceptance.
- AC-2: Given an owner/admin enters an unknown email, when they submit the invitation, then the API rejects it safely and does not create a placeholder user.
- AC-3: Given a member tries to add a user by email, then the API returns `403 insufficient_role`.
- AC-4: Given an owner/admin invites an organization member to a project, when the recipient accepts, then the user appears in that project's member list.
- AC-5: Given a user is not an organization member, when they are added to a project, then the API rejects the request safely.
- AC-6: Given a project has explicit members, when a task is assigned, then the assignee must be a project member and invalid assignees are rejected.
- AC-7: Given a user receives an organization, project, or task invitation, when they accept from the notification flow, then the corresponding access or assignment is applied.

## Harness Requirements

Required tests/checks:

- Backend API tests for invite-by-email success, unknown-email rejection, duplicate, forbidden, and non-member cases.
- Backend tests for accept/decline flows and notification creation.
- Backend API tests for project member add/remove and tenant isolation.
- Frontend tests for owner/admin/member UI permissions.
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

## Open Questions

- [x] Adding an existing user by email always requires invitation acceptance through in-app notifications.
- [x] Unknown-email invitations are rejected; no external email invitation is sent.
- [x] Project membership restricts task assignment.
- [ ] Can organization admins add other admins, or only regular members?
- [ ] Should project membership also restrict project visibility, or only assignment?
