# SPEC-105 — Frontend Organizations UI

Status: Implemented  
Owner: Arquitecto de specs  
Last updated: 2026-06-24

## Scope And Required Context

This spec governs:

- Frontend organization/workspace routes, organization list/detail/create/edit UI, member list and owner-only organization administration UI.
- Frontend API client calls to `/api/v1/organizations*`.
- App shell organization navigation and active organization context.
- Frontend tests for organization UX, permission states, and API error handling.

Required context:

- `AGENTS.md`
- `docs/project-state.md`
- `specs/README.md`
- `specs/001-api-conventions.md`
- `specs/harness/local-validation.md`
- `specs/features/101-auth-and-users.md`
- `specs/features/102-organizations-and-rbac.md`
- `specs/features/104-frontend-app-shell-and-auth-ui.md`
- `docs/decisions/ADR-007-tenant-isolation-and-rbac-enforcement.md`

Memory updates:

- `docs/project-state.md` if frontend organization state, validation baseline, next work, or known gaps change
- `docs/implementation-log.md` for meaningful spec-prep, implementation, review, validation, or merge events
- `specs/README.md` if status, dependencies, order, or primary surfaces change
- ADRs only if implementation introduces a durable frontend state/routing decision not already captured by existing specs

## Problem

OpsDesk users can authenticate, but the frontend does not let them create, select, inspect, or administer organizations. Without organization UI, the project cannot expose the tenant boundary required for projects and tasks.

## Goals

- Let authenticated users create their first organization.
- Let users list and open organizations where they are members.
- Establish an active organization context for later project/task UI.
- Show organization details and current user's role.
- Let owners update organization name and slug.
- Let owners/admins list members.
- Let owners manage non-owner member roles, remove non-owner members, transfer ownership, and permanently delete an organization when supported by the backend API.
- Render permission-aware UI without relying on client checks for security.
- Preserve the app shell patterns from `SPEC-104`.

## Non-Goals

- Invitation or join-request flows.
- Creating users from the organization UI.
- Billing, departments, guests, or external identity providers.
- Project/task UI. That belongs to `SPEC-106`.
- Changing organization backend behavior from `SPEC-102`.
- Persistent client-side organization preference across devices.

## Dependencies

- Requires `SPEC-101` authentication/session behavior.
- Requires `SPEC-102` organization and RBAC APIs.
- Requires `SPEC-104` frontend shell, routing, auth guards, API client, and frontend test harness.
- Must follow `specs/001-api-conventions.md` for error parsing, auth cookies, pagination, and tenant isolation.

## Actors And Permissions

| Actor | UI Permission | Backend Authority |
|---|---|---|
| Anonymous user | Cannot access organization routes | `SPEC-101` auth cookies |
| Authenticated user with no organizations | Create organization and see first-workspace empty state | `POST /api/v1/organizations` |
| Organization owner | View/update/delete organization, list members, manage non-owner members, transfer ownership | `SPEC-102` owner endpoints |
| Organization admin | View organization and list members | `SPEC-102` admin permissions |
| Organization member | View organization summary only | `SPEC-102` member permissions |
| Non-member | No organization UI data | Backend returns `404` for hidden tenant resources |

Client-side permission checks are UX only. The frontend must render backend `403` and `404` responses safely and must not infer hidden resources.

## Product UX Contract

### Routes

Authenticated routes:

- `/app/organizations`
- `/app/organizations/new`
- `/app/organizations/:organizationId`
- `/app/organizations/:organizationId/settings`
- `/app/organizations/:organizationId/members`

App shell behavior:

- The primary navigation must include an Organizations entry once this spec is implemented.
- The shell may show an organization switcher or compact current-organization control after organizations load.
- The active organization must be derived from the current route when the route contains `organizationId`.
- If no route organization exists, the UI may default to the first organization returned by the list endpoint for navigation convenience, but it must not write that default to persistent browser storage.
- Organization navigation must not show fake organizations or seed data.

### Organization List

Route: `/app/organizations`

Behavior:

- Fetch `GET /api/v1/organizations` with API pagination.
- Show loading, empty, error, and populated states.
- Show organization name, slug, current user's role, and useful timestamps when available.
- Provide a create organization action for every authenticated user.
- Opening an organization routes to `/app/organizations/:organizationId`.
- Empty state must guide the user to create an organization without implying invitations exist.

### Organization Creation

Route: `/app/organizations/new`

Behavior:

- Submit to `POST /api/v1/organizations`.
- Required field: `name`.
- Optional field: `slug`.
- On success, update organization list cache and navigate to the created organization detail route.
- Render `400 invalid_organization` and `409 organization_slug_taken` near the form.
- Do not generate a client-only permanent slug that can drift from the backend. Client-side slug preview is allowed only if clearly derived from the current input and overwritten by the response.

### Organization Detail

Route: `/app/organizations/:organizationId`

Behavior:

- Fetch `GET /api/v1/organizations/{organization_id}`.
- Show name, slug, current user's role, created timestamp, and updated timestamp when provided.
- Owner sees settings and destructive-admin entry points.
- Owner/admin sees member list entry point.
- Member sees read-only organization context and project/task navigation only after `SPEC-106`.
- On `404 organization_not_found`, show a safe not-found state and a route back to the organization list.
- On `401 not_authenticated`, clear session state and route to login.

### Organization Settings

Route: `/app/organizations/:organizationId/settings`

Behavior:

- Owner can update `name` and `slug` through `PATCH /api/v1/organizations/{organization_id}`.
- Non-owner users should not see editable controls when role is known, but backend `403 insufficient_role` must still be handled.
- On successful update, refresh organization detail/list cache.
- Permanent deletion must require an explicit confirmation step including the organization name or slug.
- Deletion calls `DELETE /api/v1/organizations/{organization_id}` and, on `204`, clears related organization cache and routes to `/app/organizations`.
- The UI must state the product-level effect in user terms: deleting the organization removes its workspace data and memberships, while user accounts remain. It must not promise restore.

### Member List And Management

Route: `/app/organizations/:organizationId/members`

Behavior:

- Owner/admin fetches `GET /api/v1/organizations/{organization_id}/members` with pagination.
- Member list displays safe user fields from the backend response and each membership role.
- Admin can view the member list but cannot change roles, remove members, transfer ownership, or delete the organization.
- Owner can change non-owner memberships between `admin` and `member` through `PATCH /api/v1/organizations/{organization_id}/members/{user_id}`.
- Owner can remove non-owner members through `DELETE /api/v1/organizations/{organization_id}/members/{user_id}` with confirmation.
- Owner can transfer ownership through `POST /api/v1/organizations/{organization_id}/transfer-ownership` with confirmation.
- The current owner membership must not show generic role-change or removal actions.
- `409 ownership_transfer_required` and `409 ownership_transfer_not_required` must be rendered as safe actionable errors.
- The UI must not include an invite form until a future invitations spec exists.

## API Usage Contract

Frontend calls must use relative paths and include credentials.

| UI Flow | Method | Path |
|---|---|---|
| List organizations | `GET` | `/api/v1/organizations` |
| Create organization | `POST` | `/api/v1/organizations` |
| Read organization | `GET` | `/api/v1/organizations/{organization_id}` |
| Update organization | `PATCH` | `/api/v1/organizations/{organization_id}` |
| Delete organization | `DELETE` | `/api/v1/organizations/{organization_id}` |
| List members | `GET` | `/api/v1/organizations/{organization_id}/members` |
| Change member role | `PATCH` | `/api/v1/organizations/{organization_id}/members/{user_id}` |
| Remove member | `DELETE` | `/api/v1/organizations/{organization_id}/members/{user_id}` |
| Transfer ownership | `POST` | `/api/v1/organizations/{organization_id}/transfer-ownership` |

Error handling:

- `401 not_authenticated`: clear session query state and route to `/login`.
- `403 insufficient_role`: show a safe permission error without hiding the current organization shell.
- `404 organization_not_found`: show not-found and route recovery to organization list.
- `404 membership_not_found`: show a safe member-specific error and refresh the member list.
- `409 organization_slug_taken`: show form-level or slug-field error.
- `409 ownership_transfer_required`: explain that ownership must be transferred before that action.
- `409 ownership_transfer_not_required`: explain that the selected user is already owner.

## Frontend Structure

Expected feature grouping:

```text
frontend/src/features/organizations/
frontend/src/app/
frontend/src/shared/
```

Expected responsibilities:

- `features/organizations`: organization queries, mutations, forms, detail/settings/member pages, route-level tests.
- `app`: app shell navigation updates and route registration.
- `shared`: reusable API error helpers, pagination helpers, confirmation dialog primitives if they become shared.

## Accessibility And UX Requirements

- Organization and member forms must use semantic labels.
- Destructive actions must require explicit confirmation and have cancellable dialogs.
- Loading states must not resize major shell navigation areas.
- Empty states must be concise and action-oriented.
- Role labels must be readable and consistent: `Owner`, `Admin`, `Member`.
- Keyboard users must be able to create, update, delete, and navigate organizations and member actions.
- Do not use visible instructional copy about internal auth cookies, query caches, routing internals, or API implementation.

## Acceptance Criteria

- AC-1: Given an authenticated user with no organizations, when they open `/app/organizations`, then they see an empty state with a create organization action and no fake organizations.
- AC-2: Given an authenticated user, when they create an organization with valid input, then the UI calls `POST /api/v1/organizations`, refreshes organization state, and navigates to the new organization detail.
- AC-3: Given invalid organization input or a duplicate slug, when creation or update fails, then the UI displays the backend safe error without exposing internals.
- AC-4: Given a user who belongs to multiple organizations, when they open the organization list, then only backend-returned organizations are shown with each current role.
- AC-5: Given a member, when they open organization detail, then they see read-only organization context and no owner/admin-only controls.
- AC-6: Given an owner, when they update organization name or slug with valid input, then the UI persists the update and refreshes displayed organization data.
- AC-7: Given an owner, when they permanently delete an organization after confirmation, then the UI calls the delete endpoint, removes stale organization state, and returns to the organization list.
- AC-8: Given an admin, when they open the members route, then they can view paginated members but cannot edit roles, remove members, transfer ownership, or delete the organization.
- AC-9: Given an owner, when they update a non-owner member role, then the UI calls the role endpoint and refreshes the member list.
- AC-10: Given an owner, when they remove a non-owner member after confirmation, then the UI calls the member delete endpoint and refreshes the member list.
- AC-11: Given an owner and another existing member, when ownership is transferred after confirmation, then the UI calls the transfer endpoint, refreshes organization/member state, and reflects the actor's changed role.
- AC-12: Given backend `403` or `404` responses for organization or member actions, when the response is received, then the UI renders safe permission/not-found states consistent with tenant isolation.
- AC-13: Given no valid session, when an organization route is opened, then the frontend redirects to `/login`.
- AC-14: Given `SPEC-106` is not implemented, when organization pages render, then they do not show active project/task CRUD controls or fake project/task data.

## Harness Requirements

Frontend tests:

- Organization list loading, empty, error, and populated states.
- Organization creation success and `invalid_organization`/`organization_slug_taken` errors.
- Organization detail role-aware controls for owner/admin/member.
- Organization update success and `insufficient_role` error handling.
- Deletion confirmation and success routing.
- Member list loading and permission states.
- Owner role change, member removal, and ownership transfer success/error handling.
- Auth guard behavior for organization routes.
- Absence of project/task CRUD before `SPEC-106`.

Recommended test approach:

- Use Vitest and React Testing Library.
- Mock HTTP at the API boundary using the project's established frontend test approach.
- Add Playwright only after core organization/project/task UI stabilizes.

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

- Do not log cookies, tokens, raw auth headers, or user secrets.
- Client-side development logs may include safe route/action names only.
- Network failures should render retry-oriented safe messages.
- After role changes, removals, transfers, or deletion, stale cached organization/member data must be invalidated or updated.
- If a user loses access during an action, the UI must recover through backend `403`/`404` handling rather than assuming prior client role state remains true.

## Implementation Notes

- Prefer TanStack Query for organization list/detail/member list queries and mutations.
- Prefer React Hook Form and Zod for organization forms and confirmation input validation.
- Keep route params UUID-based, matching backend public identifiers.
- Keep organization context route-derived first so deep links remain reliable.
- Do not add invitation UI, mock member creation, or local-only organization datasets.
