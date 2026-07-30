# SPEC-106 — Frontend Projects and Tasks UI

Status: Implemented
Owner: Arquitecto de specs  
Last updated: 2026-07-28

## Scope And Required Context

This spec governs:

- Frontend project and task routes, lists, detail views, forms, filters, pagination, and role-aware controls.
- Frontend API client calls to `/api/v1/organizations/{organization_id}/projects`, `/api/v1/projects*`, and `/api/v1/tasks*`.
- Integration of project/task navigation into the authenticated app shell and organization context from `SPEC-105`.
- Frontend tests for project/task workflows, permission states, filters, and API error handling.

Required context:

- `AGENTS.md`
- `docs/project-state.md`
- `specs/README.md`
- `specs/001-api-conventions.md`
- `specs/harness/local-validation.md`
- `specs/features/102-organizations-and-rbac.md`
- `specs/features/103-projects-and-tasks.md`
- `specs/features/104-frontend-app-shell-and-auth-ui.md`
- `specs/features/105-frontend-organizations-ui.md`
- `docs/decisions/ADR-007-tenant-isolation-and-rbac-enforcement.md`

Memory updates:

- `docs/project-state.md` if frontend project/task state, validation baseline, next work, or known gaps change
- `docs/implementation-log.md` for meaningful spec-prep, implementation, review, validation, or merge events
- `specs/README.md` if status, dependencies, order, or primary surfaces change
- ADRs only if implementation introduces a durable frontend state/routing/workflow decision not already captured by existing specs

## Problem

The backend can manage projects and tasks, but the frontend does not expose the core operational workflow. Recruiters and users still cannot create a workspace project, add tasks, assign work, filter task lists, or update task status through the product UI.

## Goals

- Let organization members view projects and tasks for an organization.
- Let owner/admin users create, update, and archive projects.
- Let organization members create tasks in non-archived projects within backend permission limits.
- Let owner/admin users manage all tasks and assignments.
- Let regular members update tasks assigned to themselves without exposing unsupported reassignment controls.
- Support task filters and pagination from `SPEC-103`.
- Render archived project and tenant/RBAC errors safely.
- Provide a recruiter-visible end-to-end workflow from login to organization, project, task creation, and task completion.

## Non-Goals

- Kanban drag-and-drop.
- Comments, attachments, activity history, or audit timeline.
- Notifications or background jobs. Those belong to `SPEC-201`.
- Bulk editing.
- Saved views, custom fields, or advanced search.
- Task labels. Labels belong to `SPEC-309`.
- Changing backend project/task API behavior from `SPEC-103`.

## Dependencies

- Requires `SPEC-102` organizations and memberships.
- Requires `SPEC-103` projects and tasks backend APIs.
- Requires `SPEC-104` frontend shell/auth behavior.
- Requires `SPEC-105` organization UI and route-derived organization context.
- Must follow `specs/001-api-conventions.md` for error parsing, auth cookies, pagination, and tenant isolation.

## Actors And Permissions

| Actor | UI Permission | Backend Authority |
|---|---|---|
| Anonymous user | Cannot access project/task routes | `SPEC-101` auth cookies |
| Organization owner/admin | Create/update/archive projects; create/update/reassign any task in the organization | `SPEC-103` owner/admin project/task rules |
| Organization member | Read projects; create tasks unassigned or assigned to self; update tasks assigned to self except `assignee_id` | `SPEC-103` member task rules |
| Non-member | No project/task UI data | Backend returns `404` for hidden tenant resources |

Client-side controls are UX only. The backend remains authoritative for every permission.

## Product UX Contract

### Routes

Authenticated routes:

- `/app/organizations/:organizationId/projects`
- `/app/organizations/:organizationId/projects/new`
- `/app/projects/:projectId`
- `/app/projects/:projectId/settings`
- `/app/projects/:projectId/tasks`
- `/app/projects/:projectId/tasks/new`
- `/app/tasks/:taskId`

Navigation behavior:

- Organization detail from `SPEC-105` must link to the organization's projects route once this spec is implemented.
- Project detail must make the task list the primary working surface.
- Task detail should preserve a route back to its project task list.
- Route params must use UUID identifiers returned by the backend.
- The UI must not create local-only project or task records.

### Project List

Route: `/app/organizations/:organizationId/projects`

Behavior:

- Fetch `GET /api/v1/organizations/{organization_id}/projects` with pagination.
- Show loading, empty, error, and populated states.
- Show project name, description summary when present, archived state, and timestamps when available.
- Owner/admin users see create project action.
- Members can view projects but do not see create project controls when role is known.
- Empty state for owner/admin includes create action. Empty state for member is read-only.

### Project Creation

Route: `/app/organizations/:organizationId/projects/new`

Behavior:

- Owner/admin submits to `POST /api/v1/organizations/{organization_id}/projects`.
- Required field: `name`.
- Optional field: `description`.
- On success, update project list cache and navigate to the created project route.
- Render `400 invalid_project`, `403 insufficient_role`, and `404 organization_not_found` safely.

### Project Detail And Settings

Routes:

- `/app/projects/:projectId`
- `/app/projects/:projectId/settings`

Behavior:

- Fetch `GET /api/v1/projects/{project_id}`.
- Show name, description, archived state, created/updated timestamps, and task list entry.
- Owner/admin can update name, description, and archive state through `PATCH /api/v1/projects/{project_id}`.
- Member sees read-only project detail.
- Archive/unarchive control must clearly indicate that archived projects reject new task creation.
- On `404 project_not_found`, show a safe not-found state and recovery navigation to organizations/projects when possible.

### Task List

Route: `/app/projects/:projectId/tasks`

Behavior:

- Fetch `GET /api/v1/projects/{project_id}/tasks` with pagination.
- Support filters from `SPEC-103`: `status`, `assignee_id`, `priority`, `due_before`, `due_after`.
- Filter UI must keep URL query parameters in sync so filtered lists can be refreshed or shared.
- Show loading, empty, error, and populated states.
- Task rows/cards must show title, status, priority, assignee when available, due date when available, and completion state when available.
- Organization members can create tasks only when the project is not archived.
- Archived project state disables task creation and renders the backend conflict safely if the state changes concurrently.

### Task Creation

Route: `/app/projects/:projectId/tasks/new`

Behavior:

- Submit to `POST /api/v1/projects/{project_id}/tasks`.
- Required field: `title`.
- Optional fields: `description`, `priority`, `assignee_id`, `due_date`.
- Default status is backend-owned and should not be sent unless the API supports it.
- Owner/admin may select any organization member as assignee.
- Regular member may leave the task unassigned or assign it to self. The UI must not present other-assignee choices for regular members when role is known.
- Assignee selection must use organization member data from `SPEC-105` when the actor has access to that list; if member list is unavailable for regular members, the UI may offer only "Unassigned" and "Me".
- On `201`, update task list cache and navigate to task detail or the project task list.
- Render `400 invalid_task`, `403 insufficient_role`, `404 project_not_found`, and `409 project_archived` safely.

### Task Detail And Update

Route: `/app/tasks/:taskId`

Behavior:

- Fetch `GET /api/v1/tasks/{task_id}`.
- Show title, description, status, priority, assignee, due date, completed timestamp when present, created timestamp, and updated timestamp when present.
- Owner/admin can update title, description, status, priority, assignee, and due date.
- Regular member assigned to the task can update fields allowed by the backend except reassignment. The UI must not show assignee editing controls to regular members.
- Regular member not assigned to the task sees read-only detail when they can read it and backend `403` for forbidden update attempts.
- Status transitions must rely on backend returned data for `completed_at`; the frontend must not compute or persist completion timestamps locally.
- On successful update, refresh task detail and relevant task list caches.

## API Usage Contract

Frontend calls must use relative paths and include credentials.

| UI Flow | Method | Path |
|---|---|---|
| List organization projects | `GET` | `/api/v1/organizations/{organization_id}/projects` |
| Create project | `POST` | `/api/v1/organizations/{organization_id}/projects` |
| Read project | `GET` | `/api/v1/projects/{project_id}` |
| Update/archive project | `PATCH` | `/api/v1/projects/{project_id}` |
| List project tasks | `GET` | `/api/v1/projects/{project_id}/tasks` |
| Create task | `POST` | `/api/v1/projects/{project_id}/tasks` |
| Read task | `GET` | `/api/v1/tasks/{task_id}` |
| Update task | `PATCH` | `/api/v1/tasks/{task_id}` |

Error handling:

- `401 not_authenticated`: clear session query state and route to `/login`.
- `403 insufficient_role`: show a safe permission error and keep surrounding route context when possible.
- `404 organization_not_found`, `project_not_found`, or `task_not_found`: show safe not-found state without revealing tenant existence.
- `400 invalid_project` and `400 invalid_task`: show field-level or form-level safe errors.
- `409 project_archived`: disable task creation state and prompt the user to refresh or return to tasks.

## Frontend Structure

Expected feature grouping:

```text
frontend/src/features/projects/
frontend/src/features/tasks/
frontend/src/features/organizations/
frontend/src/app/
frontend/src/shared/
```

Expected responsibilities:

- `features/projects`: project queries, mutations, list/detail/settings/create pages, project tests.
- `features/tasks`: task queries, mutations, filters, list/detail/create/update forms, task tests.
- `features/organizations`: shared organization context/member helpers created by `SPEC-105`.
- `app`: route registration and shell navigation updates.
- `shared`: reusable API, pagination, date formatting, form, and error helpers.

## Accessibility And UX Requirements

- Project and task forms must use semantic labels.
- Status and priority controls should use option controls with clear selected states.
- Date filters and due date inputs must be keyboard accessible.
- Filter controls must not cause layout shifts when options are selected.
- Buttons and forms must expose loading/disabled states during requests.
- Long project/task titles must wrap without overflowing on mobile or desktop.
- The task list must remain scannable at mobile and desktop widths.
- Do not use visible instructional copy about query caches, API internals, backend authorization, or implementation details.

## Acceptance Criteria

- AC-1: Given an organization member, when they open the projects route, then the UI lists only backend-returned projects for that organization using pagination shape from API conventions.
- AC-2: Given an owner/admin, when they create a project with valid input, then the UI calls the create endpoint, refreshes project state, and navigates to the created project.
- AC-3: Given a regular member, when they view project routes, then project creation/update/archive controls are absent or disabled, and backend `403` is rendered safely if encountered.
- AC-4: Given an owner/admin, when they update or archive a project, then the UI persists the change through `PATCH /api/v1/projects/{project_id}` and refreshes displayed data.
- AC-5: Given a non-member or missing project, when a project route returns `404`, then the UI shows a safe not-found state without exposing tenant data.
- AC-6: Given a project with tasks, when a user opens the task list, then the UI displays backend-returned tasks with status, priority, assignee, due date, and pagination.
- AC-7: Given task filters, when a user changes status, assignee, priority, due-before, or due-after filters, then the UI requests filtered tasks and reflects filters in URL query parameters.
- AC-8: Given a non-archived project, when an organization member creates a valid task within their assignment permissions, then the UI calls the create endpoint and refreshes task state.
- AC-9: Given an archived project, when a user attempts to create a task or the backend returns `409 project_archived`, then the UI prevents or safely reports task creation failure.
- AC-10: Given an owner/admin, when they create or update a task, then the UI allows assignment to valid organization members and renders invalid-assignee backend errors safely.
- AC-11: Given a regular member, when they create a task, then the UI only allows unassigned or self-assigned task creation when role is known.
- AC-12: Given a regular member assigned to a task, when they update allowed fields, then the UI persists the update and does not expose reassignment controls.
- AC-13: Given a regular member not assigned to a task, when an update attempt returns `403`, then the UI shows a safe permission error.
- AC-14: Given a task status changes to or from `done`, when the backend response returns `completed_at`, then the UI displays the returned completion state without computing it locally.
- AC-15: Given no valid session, when a project or task route is opened, then the frontend redirects to `/login`.

## Harness Requirements

Frontend tests:

- Project list loading, empty, error, and populated states.
- Project create/update/archive success and error handling.
- Owner/admin/member role-aware project controls.
- Task list loading, empty, error, populated, pagination, and filter URL state.
- Task creation validation and success.
- Archived-project task creation disabled/conflict handling.
- Owner/admin assignee selection behavior.
- Regular member self/unassigned-only task creation behavior.
- Task detail/update success and `403`/`404`/`400` error handling.
- Auth guard behavior for project/task routes.

Recommended test approach:

- Use Vitest and React Testing Library.
- Mock HTTP at the API boundary using the project's established frontend test approach.
- Prefer component/route tests for the first implementation.
- Add Playwright critical path coverage after organization/project/task UI stabilizes: login, create organization, create project, create task, mark task done.

Required commands:

```bash
make test-frontend
make lint
make format-check
make typecheck
make smoke
```

No migration checks are required for this frontend-only spec unless implementation changes backend schema.

## Observability And Failure Cases

- Do not log cookies, tokens, raw auth headers, task descriptions, or sensitive user data.
- Client-side development logs may include safe route/action names only.
- Network failures should render retry-oriented safe messages.
- Stale role or archive state must be corrected by backend `403`, `404`, or `409` handling.
- Task and project mutations must invalidate or update relevant project detail, task list, and task detail caches.

## Implementation Notes

- Prefer TanStack Query for project/task list/detail queries and mutations.
- Prefer React Hook Form and Zod for project/task forms and filter validation.
- Use backend enum values exactly: task statuses `todo`, `in_progress`, `blocked`, `done`, `cancelled`; priorities `low`, `medium`, `high`, `urgent`.
- Keep task filters URL-backed so refresh and shared links preserve the list state.
- Do not add comments, attachments, notifications, or activity timelines in this spec.
