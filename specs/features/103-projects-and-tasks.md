# SPEC-103 — Projects and Tasks

Status: Ready  
Owner: Arquitecto de specs  
Last updated: 2026-06-08

## Problem

Teams need to organize operational work into projects and track tasks with assignment, status, priority, due dates, and history-ready state transitions.

## Goals

- Create projects inside organizations.
- Create, update, list, and filter tasks inside projects.
- Assign tasks to organization members.
- Track task status, priority, due date, and completion timestamp.
- Enforce organization permissions.
- Provide recruiter-visible business logic beyond simple CRUD.

## Dependencies

- Requires `SPEC-101` authenticated user identity.
- Requires `SPEC-102` organizations, memberships, and role checks.

## Non-Goals

- Kanban drag-and-drop.
- Real-time collaboration.
- Workflow automation.
- File attachments.
- Comments and activity events. These belong to a later feature.

## Actors And Permissions

| Actor | Permission |
|---|---|
| Owner/Admin | Create/update/archive projects, manage all tasks |
| Member | Read projects, create tasks, update tasks assigned to self |
| Non-member | No access |

## Business Rules

- BR-1: Projects belong to exactly one organization.
- BR-2: Tasks belong to exactly one project and inherit its organization scope.
- BR-3: A task assignee must be a member of the same organization.
- BR-4: Task status values: `todo`, `in_progress`, `blocked`, `done`, `cancelled`.
- BR-5: Task priority values: `low`, `medium`, `high`, `urgent`.
- BR-6: When task status changes to `done`, `completed_at` is set.
- BR-7: When task status changes from `done` to another status, `completed_at` is cleared.
- BR-8: Task list supports pagination and filters: `status`, `assignee_id`, `priority`, `due_before`, `due_after`.
- BR-9: Archived projects cannot receive new tasks.
- BR-10: Non-members receive `404`; members lacking action permission receive `403`.
- BR-11: Regular members may assign newly created tasks only to themselves or leave them unassigned. Owner/admin may assign tasks to any organization member.
- BR-12: Regular members cannot change `assignee_id` on task update. Owner/admin may reassign tasks to any organization member.

## Data Model Impact

Create `projects`:

| Field | Type | Rules |
|---|---|---|
| id | UUID | Primary key |
| organization_id | UUID | FK organizations.id |
| name | string | Required, 1-160 chars |
| description | text/null | Optional |
| is_archived | boolean | Default false |
| created_at | timestamp | UTC |
| updated_at | timestamp | UTC |

Create `tasks`:

| Field | Type | Rules |
|---|---|---|
| id | UUID | Primary key |
| organization_id | UUID | FK organizations.id, denormalized for isolation |
| project_id | UUID | FK projects.id |
| title | string | Required, 1-200 chars |
| description | text/null | Optional |
| status | enum | Default `todo` |
| priority | enum | Default `medium` |
| assignee_id | UUID/null | FK users.id, must be org member |
| due_date | date/null | Optional |
| completed_at | timestamp/null | Set by status rules |
| created_by_id | UUID | FK users.id |
| created_at | timestamp | UTC |
| updated_at | timestamp | UTC |

Indexes:

- `projects.organization_id`
- `(tasks.organization_id, tasks.project_id)`
- `tasks.status`
- `tasks.assignee_id`
- `tasks.priority`
- `tasks.due_date`

Migration required.

## API Contract

All endpoints require authentication.

### `POST /api/v1/organizations/{organization_id}/projects`

Owner/admin only.

Request:

```json
{
  "name": "Customer Onboarding",
  "description": "Implementation work"
}
```

Response `201`: project payload.

Errors:

| Status | Code | Condition |
|---:|---|---|
| 400 | `invalid_project` | Name or description invalid |
| 403 | `insufficient_role` | Member attempts project creation |
| 404 | `organization_not_found` | Missing or non-member |

### `GET /api/v1/organizations/{organization_id}/projects`

Organization members may list projects. Supports pagination.

### `GET /api/v1/projects/{project_id}`

Organization members may read project detail.

### `PATCH /api/v1/projects/{project_id}`

Owner/admin only.

Request fields: `name`, `description`, `is_archived`.

Errors:

| Status | Code | Condition |
|---:|---|---|
| 400 | `invalid_project` | Invalid update payload |
| 403 | `insufficient_role` | Member attempts project update |
| 404 | `project_not_found` | Missing or non-member |

### `POST /api/v1/projects/{project_id}/tasks`

Organization members may create tasks in non-archived projects.

Request:

```json
{
  "title": "Call customer",
  "description": "Confirm kickoff agenda",
  "priority": "high",
  "assignee_id": "uuid",
  "due_date": "2026-06-20"
}
```

Response `201`: task payload.

Errors:

| Status | Code | Condition |
|---:|---|---|
| 400 | `invalid_task` | Invalid task fields or assignee is not an organization member |
| 403 | `insufficient_role` | Member attempts to assign task to another user |
| 404 | `project_not_found` | Missing or non-member |
| 409 | `project_archived` | Project is archived |

### `GET /api/v1/projects/{project_id}/tasks`

Organization members may list tasks. Supports API pagination plus filters:

- `status`
- `assignee_id`
- `priority`
- `due_before`
- `due_after`

### `GET /api/v1/tasks/{task_id}`

Organization members may read task detail.

### `PATCH /api/v1/tasks/{task_id}`

Owner/admin may update any task. Members may update tasks assigned to themselves.

Request fields: `title`, `description`, `status`, `priority`, `assignee_id`, `due_date`.

Errors:

| Status | Code | Condition |
|---:|---|---|
| 400 | `invalid_task` | Invalid task fields or assignee is not an organization member |
| 403 | `insufficient_role` | Member lacks permission for this update |
| 404 | `task_not_found` | Missing or non-member |

## Acceptance Criteria

- AC-1: Given an owner/admin, when they create a project in an organization, then the project is created under that organization.
- AC-2: Given a regular member, when they try to create a project, then the API returns `403`.
- AC-3: Given a non-member, when they access a project, then the API returns `404`.
- AC-4: Given a valid project and valid assignee, when a task is created, then the task is stored with correct organization scope.
- AC-5: Given an assignee from another organization, when task creation/update is attempted, then the API returns `400`.
- AC-6: Given an archived project, when task creation is attempted, then the API returns `409`.
- AC-7: Given task status changes to `done`, when the update succeeds, then `completed_at` is set.
- AC-8: Given task status changes from `done` to another status, when the update succeeds, then `completed_at` is cleared.
- AC-9: Given list filters, when tasks are requested, then the response includes only matching tasks and uses pagination shape from API conventions.
- AC-10: Given a member not assigned to a task, when they try to update it, then the API returns `403`.
- AC-11: Given a regular member, when they try to create a task assigned to another user, then the API returns `403`.
- AC-12: Given a regular member assigned to a task, when they try to change `assignee_id`, then the API returns `403`.

## Harness Requirements

Backend tests:

- Project creation permission tests.
- Project archive behavior.
- Task creation success.
- Cross-organization assignee rejection.
- Archived project task rejection.
- Status transition completion timestamp tests.
- Filtering and pagination tests.
- Tenant isolation tests.
- Member update permission tests.
- Member assignment/reassignment restriction tests.
- Migration checks.

Frontend tests after UI exists:

- Project list loading/empty/error states.
- Task creation form validation.
- Task list filter behavior.

Required commands once available:

```bash
make test-backend
make test-frontend
make migrations-check
make lint
```

## Observability And Failure Cases

- Log project archive changes and task assignment changes with actor ID and organization ID.
- Do not log task descriptions if logs may become public.
- Assignment validation errors must include safe IDs only.
