# SPEC-302 — Predeployment UI Stabilization

Status: Draft
Owner: Arquitecto de specs
Last updated: 2026-07-15

## Scope And Required Context

This spec governs:

- Frontend corrections and small additions needed before the public deployment handoff.
- Authenticated app shell navigation behavior for organizations, projects, and tasks.
- Frontend tests that prevent regressions in recruiter-visible MVP workflows.

Required context:

- `AGENTS.md`
- `docs/project-state.md`
- `specs/README.md`
- `specs/000-product-vision.md`
- `specs/001-api-conventions.md`
- `specs/harness/local-validation.md`
- `specs/features/104-frontend-app-shell-and-auth-ui.md`
- `specs/features/105-frontend-organizations-ui.md`
- `specs/features/106-frontend-projects-and-tasks-ui.md`

Memory updates:

- `docs/project-state.md` when current state, next work, known gaps, or validation baseline changes
- `docs/implementation-log.md` for meaningful spec-prep, implementation, review, validation, or merge events
- `specs/README.md` when status, dependencies, order, or primary surfaces change
- ADRs only if implementation introduces a durable cross-cutting frontend routing or state decision not already captured by existing specs

## Problem

Before public deployment, the authenticated frontend still has visible workflow defects. One confirmed defect is that after creating an organization, clicking the left-panel `Organizations`, `Projects`, or `Tasks` navigation entries routes the user to organizations and highlights all three entries at the same time. This makes the app shell misleading and blocks a clean recruiter-visible path through organizations, projects, and tasks.

More predeployment corrections and small additions may be added to this spec before implementation. Larger product additions are tracked separately so this spec can remain a narrow stabilization slice.

## Goals

- Correct left-panel navigation so Organizations, Projects, and Tasks route to their intended destinations after an organization exists.
- Ensure the active navigation state marks only the currently relevant top-level section.
- Preserve route-derived organization context from `SPEC-105`.
- Preserve project/task route behavior from `SPEC-106`.
- Capture additional small predeployment UI corrections before implementation begins.

## Non-Goals

- Backend API changes.
- Database schema or migration changes.
- Public VPS/domain deployment execution.
- Large new product areas such as comments, activity history, notification inbox UI, billing, or analytics.
- Organization member invitations, project access management, chat, client users, and client tickets; these belong to `SPEC-303`, `SPEC-304`, and `SPEC-305`.
- Replacing the existing app shell or routing architecture without a separate ADR-level decision.

## Actors And Permissions

| Actor | UI Permission | Backend Authority |
|---|---|---|
| Anonymous user | Cannot access authenticated app navigation | `SPEC-101` auth cookies |
| Authenticated user with no organizations | Can access organization creation/listing routes; project/task shortcuts must not imply fake data | `SPEC-105` organization API behavior |
| Organization owner/admin/member | Can navigate between organization, project, and task surfaces available to their backend permissions | `SPEC-102`, `SPEC-103` |
| Non-member | Must not receive leaked organization, project, or task data through navigation | Backend `404` tenant isolation policy |

Client-side routing and active-state checks are UX only. Backend authorization remains authoritative for data access.

## Business Rules

- BR-1: The app shell must derive active navigation from the current route, not from a broad prefix that causes unrelated top-level sections to appear active together.
- BR-2: The Organizations navigation entry must route to `/app/organizations` or the existing organization route selected by the implementation, but it must remain distinct from project and task navigation.
- BR-3: The Projects navigation entry must route to the active organization's project list when an active organization is known.
- BR-4: The Tasks navigation entry must route to a task working surface for the active organization or current project context when enough context exists; if no usable project/task context exists, the UI must show a safe empty or recovery state rather than silently routing to organizations.
- BR-5: Clicking Organizations, Projects, or Tasks must not highlight more than one of those top-level navigation entries at once.
- BR-6: Navigation must not create local-only organizations, projects, or tasks.

## Data Model Impact

No data model changes are expected. No Alembic migration is required unless future additions change backend persistence, which should move that work into a separate spec or explicitly update this section.

## API Contract

No new API endpoints are expected for the confirmed navigation bug. Frontend code must continue using the API contracts from `SPEC-105` and `SPEC-106`:

- `/api/v1/organizations*`
- `/api/v1/organizations/{organization_id}/projects`
- `/api/v1/projects*`
- `/api/v1/tasks*`

API errors must continue to follow `specs/001-api-conventions.md`.

## Frontend Impact

Likely surfaces:

- `frontend/src/app` app shell navigation, route registration, and active-link logic
- `frontend/src/features/organizations` active organization helpers or route context
- `frontend/src/features/projects` project list/detail route navigation
- `frontend/src/features/tasks` task list/detail route navigation
- Frontend route/component tests covering app-shell navigation state

The app shell must keep stable dimensions while navigation state changes. Labels must not overflow on mobile or desktop layouts.

## Acceptance Criteria

- AC-1: Given an authenticated user has created an organization, when they click `Organizations` in the left panel, then the app opens the organization surface and only `Organizations` is marked active among Organizations, Projects, and Tasks.
- AC-2: Given an authenticated user has an active organization, when they click `Projects` in the left panel, then the app opens that organization's projects surface and only `Projects` is marked active among Organizations, Projects, and Tasks.
- AC-3: Given an authenticated user is in a valid project/task context, when they click `Tasks` in the left panel, then the app opens the task working surface for that context and only `Tasks` is marked active among Organizations, Projects, and Tasks.
- AC-4: Given no active organization or project/task context is available, when the user clicks `Projects` or `Tasks`, then the UI shows a safe empty/recovery state or disabled navigation state without fake data and without marking unrelated sections active.
- AC-5: Given the current route is an organization route, project route, or task route, when the app shell renders, then active navigation state is deterministic after page refresh and deep linking.
- AC-6: Given backend `401`, `403`, or `404` responses occur during navigation-driven data loading, then the UI renders the existing safe auth, permission, or not-found recovery states from `SPEC-105` and `SPEC-106`.

## Harness Requirements

Required tests/checks:

- Frontend tests for left-panel Organizations, Projects, and Tasks click routing after organization creation.
- Frontend tests for mutually exclusive active states across Organizations, Projects, and Tasks.
- Frontend tests for no-context Projects/Tasks navigation behavior.
- Regression coverage should use the project's established Vitest and React Testing Library approach.

Required commands:

```bash
make test-frontend
make lint
make format-check
make typecheck
make smoke
make memory-check SPEC=SPEC-302
```

No migration checks are required for the confirmed frontend-only bug unless this spec gains backend persistence work.

## Observability And Failure Cases

- Do not log cookies, tokens, raw auth headers, task descriptions, or user secrets.
- Client-side development logs may include safe route/action names only.
- Navigation failures must recover through visible route states, not silent redirects to unrelated sections.
- Stale organization/project/task context must be corrected by backend `401`, `403`, or `404` handling.

## Open Questions

- [ ] Which additional predeployment corrections should be included in this spec before implementation?
- [ ] Should the Tasks left-panel entry target a global assigned-to-me task surface, the current project's task list, or remain context-dependent until a global task list spec exists?
- [ ] Should project/task shortcuts be disabled before the first project exists, or route to empty states?

## Implementation Notes

- Prefer route-derived context over persistent browser storage for active organization and active navigation state.
- Keep the fix narrowly scoped to navigation behavior unless more corrections are added before implementation.
- Do not add a global task list API or frontend route unless this spec is updated with an explicit contract.
