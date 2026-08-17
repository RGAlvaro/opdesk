# SPEC-305 — Project Clients And Tickets

Status: Implemented
Owner: Arquitecto de specs
Last updated: 2026-08-17

## Scope And Required Context

This spec governs:

- Special OpsDesk client accounts with restricted project-ticket access.
- Adding client accounts to projects.
- Client-created tickets that are visible to project members.
- Ticket detail conversations for the client, assigned worker, and project lead/owner-admin context.
- Backend models, APIs, permissions, frontend UI, and tests for client tickets.

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
- `specs/features/106-frontend-projects-and-tasks-ui.md`
- `specs/features/303-member-invitations-and-project-access.md`
- `specs/features/306-in-app-notifications.md`
- `docs/decisions/ADR-011-client-accounts-and-ticket-access.md`

Memory updates:

- `docs/project-state.md` when current state, next work, known gaps, or validation baseline changes
- `docs/implementation-log.md` for meaningful spec-prep, implementation, review, validation, or merge events
- `specs/README.md` when status, dependencies, order, or primary surfaces change
- ADRs if client identity, ticket/task inheritance, or external access policy changes

## Problem

Projects often include external clients who should be able to report work requests and follow their progress without seeing the internal organization workspace. OpsDesk currently has only internal organization members and tasks, so there is no client-facing ticket workflow.

## Goals

- Let owner/admin users create or invite restricted client accounts for a project.
- Let clients log in to OpsDesk with a special client experience.
- Let clients create tickets only for projects where they have client access.
- Let clients see their own tickets and follow ticket status.
- Store client tickets in the existing task model with a clear task type/source distinction.
- Let the assigned worker, the project lead context, and the client discuss the ticket in a ticket detail conversation.
- Visually distinguish tickets from internal tasks with a label and distinct color.
- Preserve internal task permissions and tenant isolation.

## Non-Goals

- Billing, SLAs, customer portal branding, or public anonymous ticket intake.
- Client access to all organization projects.
- Client access to organization member administration, internal project settings, internal tasks, or organization chat.
- Client participation in `SPEC-304` chat.
- Advanced ticket workflows such as queues, macros, custom forms, or attachments.

## Actors And Permissions

| Actor | Permission | Notes |
|---|---|---|
| Organization owner/admin | Create client accounts, grant/revoke project client access, manage client tickets | Existing organization RBAC |
| Project member | View client tickets for projects they can access and handle them as project work | Assignment/update rights follow the existing project/task policy unless narrowed below |
| Assigned worker | Update assigned ticket fields, request reassignment to another eligible worker, and participate in the ticket detail conversation | Reassignment initiated by the assigned worker requires notification and acceptance by the new assignee before `assignee_id` changes |
| Project lead context | Participate in ticket detail conversations for tickets in accessible projects | In V1 this maps to organization owner/admin and any later explicit project-lead role must update this spec |
| Client account | Create tickets in projects where client access is granted, view own tickets, view status, and comment on own ticket detail pages | Client accounts are not organization members |
| Non-member/non-client | No access | Tenant-safe `404` |

## Business Rules

- BR-1: Clients are authenticated OpsDesk users with a restricted client account mode; they do not become organization members.
- BR-2: Only organization owners/admins may create client accounts or grant/revoke project client access.
- BR-3: A client account may be granted access to one or more projects, but sees only its own tickets within those projects.
- BR-4: Client ticket creation requires a project with active client access, a subject, and a bounded description/body.
- BR-5: Tickets are stored as tasks with a `ticket` type/source and must be distinguishable from internal tasks in API payloads and UI.
- BR-6: Client-created tickets must record the client creator separately from internal task assignees.
- BR-7: Project members can see ticket tasks for projects they can access.
- BR-8: Tickets can be assigned to internal project members using the existing task assignment model.
- BR-9: Archived projects reject new client tickets consistently with internal task creation.
- BR-10: Revoking a client's project access prevents new tickets for that project and prevents access to project-level client surfaces; historical tickets remain visible to internal project members.
- BR-11: A client may continue to view and comment on tickets they created unless the client account is deactivated or the ticket is explicitly closed from client visibility by a later spec.
- BR-12: Ticket detail conversations are scoped to one ticket and include comments/feedback from the client, assigned worker, and project lead context.
- BR-13: Ticket comments use persistent storage, bounded body length, author identity, timestamps, and tenant-safe access checks.
- BR-14: Ticket-comment unread notifications should summarize unread ticket conversation activity instead of creating one notification per individual comment.
- BR-15: Organization owners/admins may assign or reassign ticket `assignee_id` directly to an eligible internal project member.
- BR-16: The currently assigned worker may request reassignment to another eligible internal project member, but the ticket `assignee_id` must not change until the target worker accepts.
- BR-17: A reassignment request must notify the target worker, persist its pending/accepted/declined state, and be tenant-safe so only the target worker can accept or decline it.

## Data Model Impact

Expected user/account change:

- Add a durable way to identify restricted client accounts, for example a user account type or role separate from organization membership.
- Client accounts authenticate through the existing browser session model but are routed to client-only surfaces.

Expected client access table:

| Field | Type | Rules |
|---|---|---|
| id | UUID | Primary key |
| project_id | UUID | FK projects.id |
| organization_id | UUID | FK organizations.id |
| client_user_id | UUID | FK users.id, restricted client account |
| granted_by_id | UUID | FK users.id |
| created_at | timestamp | UTC |
| revoked_at | timestamp/null | Null while active |

Expected task change:

- Add a task type/source field to `tasks`, where `internal` is the default and `ticket` differentiates client-created tickets from internal tasks.
- Ticket tasks retain existing task status, priority, assignee, due date, and project membership behavior unless this spec narrows it before implementation.
- Ticket tasks include `client_user_id` or equivalent creator reference for client visibility and audit.

Expected ticket comment table:

| Field | Type | Rules |
|---|---|---|
| id | UUID | Primary key |
| task_id | UUID | FK tasks.id, must be a ticket task |
| organization_id | UUID | Denormalized tenant scope |
| project_id | UUID | Denormalized project scope |
| author_user_id | UUID | FK users.id |
| body | string | Required, bounded length |
| created_at | timestamp | UTC |
| updated_at | timestamp | UTC |
| deleted_at | timestamp/null | Optional soft-delete for author/admin moderation if implemented |

Migration required if implemented.

Expected ticket assignment request table:

| Field | Type | Rules |
|---|---|---|
| id | UUID | Primary key |
| task_id | UUID | FK tasks.id, must be a ticket task |
| organization_id | UUID | Denormalized tenant scope |
| project_id | UUID | Denormalized project scope |
| requested_by_id | UUID | FK users.id, must be the current ticket assignee at request time |
| target_user_id | UUID | FK users.id, must be an eligible internal project member |
| status | enum/string | `pending`, `accepted`, or `declined` |
| created_at | timestamp | UTC |
| responded_at | timestamp/null | Set when accepted or declined |

## API Contract

Exact schema fields may be refined during implementation, but endpoint behavior must preserve the rules below.

Candidate internal endpoints:

- `GET /api/v1/projects/{project_id}/clients`
- `POST /api/v1/projects/{project_id}/clients`
- `DELETE /api/v1/projects/{project_id}/clients/{client_access_id}`
- `GET /api/v1/projects/{project_id}/tickets`
- `GET /api/v1/tickets/{ticket_id}`
- `PATCH /api/v1/tickets/{ticket_id}`
- `GET /api/v1/tickets/{ticket_id}/comments`
- `POST /api/v1/tickets/{ticket_id}/comments`
- `POST /api/v1/tickets/{ticket_id}/assignment-requests`
- `GET /api/v1/ticket-assignment-requests`
- `POST /api/v1/ticket-assignment-requests/{request_id}/accept`
- `POST /api/v1/ticket-assignment-requests/{request_id}/decline`

Candidate client endpoints:

- `GET /api/v1/client/projects`
- `POST /api/v1/client/projects/{project_id}/tickets`
- `GET /api/v1/client/tickets`
- `GET /api/v1/client/tickets/{ticket_id}`
- `GET /api/v1/client/tickets/{ticket_id}/comments`
- `POST /api/v1/client/tickets/{ticket_id}/comments`

Errors must follow `specs/001-api-conventions.md`, including:

- `401 not_authenticated`
- `403 insufficient_role`
- `403 client_account_required`
- `404 project_not_found`
- `404 ticket_not_found`
- `409 project_archived`
- `409 client_access_revoked`
- `400 invalid_ticket`
- `400 invalid_comment`
- `400 invalid_assignment_request`
- `404 assignment_request_not_found`

## Frontend Impact

- Project settings gains owner/admin-only client account and project access management.
- Project task surfaces distinguish internal tasks from client tickets.
- Client users land in a restricted client app shell rather than the internal organization workspace.
- Client routes show accessible projects, the client's own tickets, ticket status, and ticket detail conversations.
- Internal project members need a visible ticket list or combined work list with clear ticket labels.
- Ticket rows/cards use a distinct color and `Ticket` label.
- Ticket detail pages show status, assignment, metadata, and a comment/feedback thread.
- Internal assigned workers can request reassignment from the ticket detail page.
- Internal workers can see pending assignment requests addressed to them and accept or decline them.

## Acceptance Criteria

- AC-1: Given an owner/admin creates or grants a client account access to a project, then the account can authenticate but is not an organization member.
- AC-2: Given a client creates a ticket for an accessible active project, then a ticket task is created for that project.
- AC-3: Given a client opens their ticket list, then they see only tickets they created.
- AC-4: Given a client opens one of their tickets, then they can see status, assignment state safe for clients, and the ticket conversation.
- AC-5: Given a client comments on their ticket, then the assigned worker and project lead context can see the comment.
- AC-6: Given an assigned worker or project lead context comments on the ticket, then the client can see the reply.
- AC-7: Given a client creates a ticket, then project members can see it as a ticket task distinct from internal tasks.
- AC-8: Given a non-client or unrelated client tries to access a project ticket, then the API returns a tenant-safe error.
- AC-9: Given a project is archived, when a client attempts to create a ticket, then the API returns `409 project_archived`.
- AC-10: Given client project access is revoked, then the client can no longer create tickets for that project.
- AC-11: Given a ticket is assigned, then the assignee must be an eligible internal project member.
- AC-12: Given ticket comments create unread activity, then in-app notifications summarize unread ticket conversation activity without one notification per individual comment.
- AC-13: Given an assigned worker requests reassignment to another eligible project member, then the ticket assignee remains unchanged, the target worker receives one pending assignment notification, and the target worker can accept to become the assignee.
- AC-14: Given a worker declines a pending reassignment request, then the ticket assignee remains unchanged and the request is no longer pending.

## Harness Requirements

Required tests/checks:

- Backend API tests for client account creation/access grant, tenant isolation, ticket creation, ticket status visibility, comment permissions, archived project rejection, revoked access, assignment eligibility, assignment request acceptance/decline, and project member visibility.
- Frontend tests for client management UI in project settings, restricted client shell, client ticket creation, client ticket detail/comments, assignment state, reassignment requests, and internal ticket visibility.
- Migration checks.

Required commands:

```bash
make test-backend
make test-frontend
make migrations-check
make lint
make format-check
make typecheck
make memory-check SPEC=SPEC-305
```

## Open Questions

- None. This spec is ready for implementation planning.
