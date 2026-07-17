# SPEC-305 — Project Clients And Tickets

Status: Draft
Owner: Arquitecto de specs
Last updated: 2026-07-15

## Scope And Required Context

This spec governs:

- Adding clients to projects.
- Client access boundaries.
- Client-created tickets that are visible to project members.
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

Memory updates:

- `docs/project-state.md` when current state, next work, known gaps, or validation baseline changes
- `docs/implementation-log.md` for meaningful spec-prep, implementation, review, validation, or merge events
- `specs/README.md` when status, dependencies, order, or primary surfaces change
- ADRs if client identity, ticket/task inheritance, or external access policy becomes a durable cross-cutting decision

## Problem

Projects often include external clients who should be able to report work requests without seeing the full internal organization workspace. OpsDesk currently has only internal organization members and tasks, so there is no client-facing ticket workflow.

## Goals

- Let internal users record clients for a project as lightweight project contacts.
- Let clients submit tickets through a limited form with client name, subject, organization, and project.
- Make client tickets visible to project members.
- Store client tickets in the existing task model with a clear task type/source distinction.
- Visually distinguish tickets from internal tasks with a label and distinct color.
- Preserve internal task permissions and tenant isolation.

## Non-Goals

- Billing, SLAs, customer portal branding, or public anonymous ticket intake.
- Client access to all organization projects.
- Client access to organization member administration.
- Full client accounts or authenticated client portal in the first implementation.
- Client chat unless `SPEC-304` is explicitly expanded.
- Advanced ticket workflows such as queues, macros, forms, or attachments.

## Actors And Permissions

| Actor | Permission | Notes |
|---|---|---|
| Organization owner/admin | Add/remove project clients and manage client tickets | Existing organization RBAC |
| Project member | View client tickets for projects they can access and handle them as project work | Exact update rights remain Draft |
| Client | Submit a ticket form for an allowed organization/project | Lightweight contact, not an authenticated organization member |
| Non-member/non-client | No access | Tenant-safe `404` |

## Business Rules

- BR-1: Clients are lightweight project contacts and do not automatically become organization members or authenticated users.
- BR-2: Only owners/admins or authorized project managers may add clients to a project.
- BR-3: Client ticket submission requires client name, subject, organization, and project.
- BR-4: Tickets must be visible to project members who can access the project.
- BR-5: Tickets are stored as tasks with a `ticket` type/source and must be distinguishable from internal tasks in API payloads and UI.
- BR-6: Client-created tickets must record the client creator separately from internal task assignees.
- BR-7: Client contact removal prevents future association with that client but must not delete historical tickets unless explicitly specified.
- BR-8: Archived projects reject new client tickets consistently with internal task creation.

## Data Model Impact

Expected task change:

- Add a task type/source field to `tasks`, where `internal` is the default and `ticket` differentiates client-created tickets from internal tasks.
- Ticket tasks should retain existing task status, priority, assignee, due date, and project membership behavior unless this spec narrows it before implementation.

Expected client access table:

| Field | Type | Rules |
|---|---|---|
| id | UUID | Primary key |
| project_id | UUID | FK projects.id |
| organization_id | UUID | FK organizations.id |
| client_name | string | Required |
| contact_email | string/null | Optional if added before Ready |
| added_by_id | UUID | FK users.id |
| created_at | timestamp | UTC |

Migration required if implemented.

## API Contract

Exact endpoints remain Draft. Candidate endpoints:

- `GET /api/v1/projects/{project_id}/clients`
- `POST /api/v1/projects/{project_id}/clients`
- `DELETE /api/v1/projects/{project_id}/clients/{client_id}`
- `POST /api/v1/projects/{project_id}/tickets`
- `GET /api/v1/projects/{project_id}/tickets`
- `GET /api/v1/tickets/{ticket_id}`
- `PATCH /api/v1/tickets/{ticket_id}`

Errors must follow `specs/001-api-conventions.md`, including `403 insufficient_role`, `404 project_not_found`, `404 ticket_not_found`, `409 project_archived`, and `400 invalid_ticket`.

## Frontend Impact

- Project settings gains client management.
- Project task surfaces must distinguish internal tasks from client tickets.
- Client-facing routes expose only a limited ticket submission form.
- Internal project members need a visible ticket list or combined work list with clear ticket labels.
- Ticket rows/cards use a distinct color and `Ticket` label.

## Acceptance Criteria

- AC-1: Given an owner/admin adds a client contact to a project, then the contact is project-scoped and no user account or organization membership is created.
- AC-2: Given a client submits the limited form with client name, subject, organization, and project, then a ticket task is created for that project.
- AC-3: Given a client creates a ticket, then project members can see it as a ticket task distinct from internal tasks.
- AC-4: Given a non-client tries to access a project ticket, then the API returns a tenant-safe error.
- AC-5: Given a project is archived, when a client attempts to create a ticket, then the API returns `409 project_archived`.
- AC-6: Given client access is removed, then the client can no longer open the project or create new tickets.

## Harness Requirements

Required tests/checks:

- Backend API tests for client add/remove, client tenant isolation, ticket creation, archived project rejection, and project member visibility.
- Frontend tests for client management UI, client ticket creation, and internal ticket visibility.
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

- [x] Clients are lightweight project contacts, not full OpsDesk user accounts for the first implementation.
- [x] Tickets live in the existing `tasks` table with a type/source field and distinct UI label/color.
- [ ] Should unauthenticated client ticket submission require a signed project form link, or should internal users submit on behalf of clients?
- [ ] Can clients see submitted tickets after creation, or is submission one-way for now?
- [ ] Can clients comment on tickets in this spec, or are comments deferred?
- [ ] Should project members assign tickets to internal members using the existing task assignment model?
