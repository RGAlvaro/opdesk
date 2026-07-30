# SPEC-309 — Project Task Labels

Status: Ready
Owner: Arquitecto de specs
Last updated: 2026-07-28

## Scope And Required Context

This spec governs:

- Project-scoped task labels.
- Label creation, update, archive/delete behavior, color and description metadata.
- Applying and removing labels on tasks.
- Backend models, APIs, permissions, frontend UI, filters, and tests for task labels.

Required context:

- `AGENTS.md`
- `docs/project-state.md`
- `specs/README.md`
- `specs/000-product-vision.md`
- `specs/001-api-conventions.md`
- `specs/harness/local-validation.md`
- `specs/features/102-organizations-and-rbac.md`
- `specs/features/103-projects-and-tasks.md`
- `specs/features/106-frontend-projects-and-tasks-ui.md`
- `specs/features/303-member-invitations-and-project-access.md` if project membership has been implemented
- `specs/features/308-enriched-record-metadata.md`
- `docs/decisions/ADR-007-tenant-isolation-and-rbac-enforcement.md`

Memory updates:

- `docs/project-state.md` when current state, validation baseline, next work, or known gaps change
- `docs/implementation-log.md` for meaningful spec-prep, implementation, review, validation, or merge events
- `specs/README.md` when status, dependencies, order, or primary surfaces change
- ADRs if label taxonomy, cross-project reuse, or task search architecture becomes a durable cross-cutting decision

## Problem

Tasks need lightweight categorization so project teams can scan, filter, and group work beyond status, priority, and assignee. OpsDesk currently has no labels, and `SPEC-106` explicitly left labels outside the first project/task UI.

## Goals

- Let the team that belongs to a project create labels for that project.
- Store label name, color, description, creator, and archived state.
- Let permitted users apply and remove existing project labels on tasks.
- Let task lists filter by label.
- Render labels consistently in task lists, task detail, and task forms.
- Preserve tenant isolation and project/task permissions.

## Non-Goals

- Global organization-wide labels in the first implementation.
- Cross-project label reuse or synchronization.
- Free-form custom fields.
- Full-text search.
- Automatic label suggestions.
- Label analytics.

## Actors And Permissions

| Actor | Permission | Notes |
|---|---|---|
| Organization owner/admin | Create, update, archive/delete, and apply labels on any accessible project task | Existing org-level project/task authority |
| Project member | Create labels for projects they belong to and apply labels to tasks they may update | Before `SPEC-303`, project member means an organization member with project access under `SPEC-103` |
| Assigned member | Apply or remove labels on their own assigned tasks | Cannot bypass task update permission rules |
| Organization member not assigned to task | Read labels on visible tasks | Cannot apply labels unless task update is allowed |
| Non-member | No access | Receives tenant-safe `404` |

## Business Rules

- BR-1: Labels belong to exactly one project and inherit the project's organization scope.
- BR-2: Label names are required, trimmed, 1-60 characters, and unique per project case-insensitively among active labels.
- BR-3: Label colors are required hex colors in `#RRGGBB` format.
- BR-4: Label descriptions are optional and max 500 characters.
- BR-5: `created_by_id` records the project team member who created the label.
- BR-6: Labels are archived by default instead of physically deleted when they have historical task usage.
- BR-7: Archived labels cannot be newly applied to tasks but remain visible on historical tasks until removed.
- BR-8: Applying a label to a task requires the task to belong to the same project as the label.
- BR-9: A task cannot have the same label more than once.
- BR-10: Owner/admin users may manage labels and label assignments on all tasks they can manage.
- BR-11: Regular members may create project labels and may apply/remove labels only on tasks they are allowed to update under `SPEC-103` and `SPEC-303` if implemented.
- BR-12: Task list filtering by label must keep pagination shape from `SPEC-001`.
- BR-13: Label colors must be stored as explicit values rather than inferred from label name.

## Data Model Impact

Create `task_labels`:

| Field | Type | Rules |
|---|---|---|
| id | UUID | Primary key |
| organization_id | UUID | FK organizations.id, denormalized for isolation |
| project_id | UUID | FK projects.id |
| name | string | Required, 1-60 chars |
| color | string | Required `#RRGGBB` |
| description | text/null | Optional, max 500 chars |
| created_by_id | UUID | FK users.id |
| archived_at | timestamp/null | UTC, null means active |
| created_at | timestamp | UTC |
| updated_at | timestamp | UTC |

Create `task_label_assignments`:

| Field | Type | Rules |
|---|---|---|
| id | UUID | Primary key |
| organization_id | UUID | FK organizations.id |
| project_id | UUID | FK projects.id |
| task_id | UUID | FK tasks.id |
| label_id | UUID | FK task_labels.id |
| applied_by_id | UUID | FK users.id |
| created_at | timestamp | UTC |

Indexes:

- unique active label name per project, case-insensitive
- unique `(task_id, label_id)`
- `(project_id, archived_at)`
- `(task_id)`
- `(label_id)`
- `(organization_id, project_id)`

Migration required.

## API Contract

All endpoints require authentication.

### `GET /api/v1/projects/{project_id}/labels`

Project-visible users may list labels. Supports pagination and optional `include_archived=false` by default.

Response `200` uses the standard pagination envelope. Items include:

```json
{
  "id": "uuid",
  "organization_id": "uuid",
  "project_id": "uuid",
  "name": "Urgent customer",
  "color": "#D92D20",
  "description": "Customer-facing work that needs fast triage",
  "created_by_id": "uuid",
  "archived_at": null,
  "created_at": "2026-07-28T10:00:00Z",
  "updated_at": "2026-07-28T10:00:00Z"
}
```

### `POST /api/v1/projects/{project_id}/labels`

Project team members may create labels.

Request:

```json
{
  "name": "Urgent customer",
  "color": "#D92D20",
  "description": "Customer-facing work that needs fast triage"
}
```

Response `201`: label payload.

Errors:

| Status | Code | Condition |
|---:|---|---|
| 400 | `invalid_label` | Invalid name, color, or description |
| 403 | `insufficient_role` | User cannot create labels for this project |
| 404 | `project_not_found` | Missing or hidden project |
| 409 | `label_name_taken` | Active label name already exists in the project |

### `PATCH /api/v1/projects/{project_id}/labels/{label_id}`

Project team members may update label name, color, description, or archived state.

Request fields: `name`, `color`, `description`, `is_archived`.

Response `200`: updated label payload.

Errors include `400 invalid_label`, `403 insufficient_role`, `404 label_not_found`, and `409 label_name_taken`.

### `POST /api/v1/tasks/{task_id}/labels`

Applies an active project label to a task.

Request:

```json
{
  "label_id": "uuid"
}
```

Response `200`: updated task payload including labels.

Errors:

| Status | Code | Condition |
|---:|---|---|
| 400 | `invalid_label_assignment` | Label is archived or belongs to another project |
| 403 | `insufficient_role` | User cannot update labels on this task |
| 404 | `task_not_found` | Missing or hidden task |
| 404 | `label_not_found` | Missing or hidden label |
| 409 | `label_already_applied` | Task already has the label |

### `DELETE /api/v1/tasks/{task_id}/labels/{label_id}`

Removes a label from a task.

Response `204`.

Errors include `403 insufficient_role`, `404 task_not_found`, and `404 label_not_found`.

### Task List Filtering

`GET /api/v1/projects/{project_id}/tasks` adds:

- `label_id`

The response includes labels on task items.

## Frontend Impact

- Project settings or a project labels panel lets project team members create and manage labels.
- Label controls use color swatches and text labels.
- Task create/detail/update forms allow permitted users to apply active labels.
- Task rows/cards show assigned labels without causing layout shifts.
- Task list filter UI supports label filtering and stores `label_id` in URL query parameters.
- Archived labels remain readable on historical tasks but are visually subdued and not offered as new choices.
- Duplicate and invalid label errors render near the label form.

## Acceptance Criteria

- AC-1: Given a project team member, when they create a valid label, then the label is stored under that project with name, color, description, and creator.
- AC-2: Given a duplicate active label name in the same project, when creation or rename is attempted, then the API returns `409 label_name_taken`.
- AC-3: Given labels with the same name in different projects, when they are created, then both creations succeed.
- AC-4: Given a user can update a task, when they apply an active label from the same project, then the task response includes that label.
- AC-5: Given a label belongs to another project or is archived, when it is applied to a task, then the API rejects the assignment safely.
- AC-6: Given a member is not allowed to update a task, when they apply or remove a label, then the API returns `403 insufficient_role`.
- AC-7: Given a task list is filtered by label, then only matching tasks are returned with standard pagination.
- AC-8: Given a label is archived, then it is not offered for new assignment but remains visible where already applied.
- AC-9: Given a non-member requests project labels or labeled tasks, then the API returns tenant-safe `404`.

## Harness Requirements

Required tests/checks:

- Backend API tests for label create/list/update/archive and duplicate handling.
- Backend API tests for label assignment/removal permissions, cross-project rejection, archived-label rejection, and tenant isolation.
- Backend API tests for task list filtering by label.
- Frontend tests for label management UI, color validation, task label assignment, archived-label display, and label filter URL state.
- Migration checks.

Required commands:

```bash
make test-backend
make test-frontend
make migrations-check
make lint
make format-check
make typecheck
make memory-check SPEC=SPEC-309
```

## Observability And Failure Cases

- Log label creation, archival, and task label assignment changes with actor ID, project ID, task ID where applicable, and label ID.
- Do not log task descriptions, cookies, tokens, or secrets.
- Tenant isolation must hide labels and assignments for non-members.
- Concurrent duplicate label creation must be protected by a database uniqueness constraint.

## Open Questions

- [x] Labels are project-scoped and can be created by the project team.
- [x] Labels store name, color, description, creator, and archived state.
- [x] Members may apply labels to their own tasks when backend task-update permissions allow it.

## Implementation Notes

- Prefer archived labels over hard deletion to keep historical task displays stable.
- Keep label filtering compatible with existing task pagination and URL-backed frontend filters.
