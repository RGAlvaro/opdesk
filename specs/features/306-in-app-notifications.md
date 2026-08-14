# SPEC-306 — In-App Notifications

Status: Implemented
Owner: Arquitecto de specs
Last updated: 2026-08-14

## Scope And Required Context

This spec governs:

- Persistent in-app notifications.
- Notification inbox UI and read/unread state.
- Notification events for organization, project, and task activity.
- Integration of `SPEC-303` organization/project invitations into the full notification inbox after the minimal invitation flow exists.
- Backend notification models, APIs, services, and frontend notification surfaces.

Required context:

- `AGENTS.md`
- `docs/project-state.md`
- `specs/README.md`
- `specs/000-product-vision.md`
- `specs/001-api-conventions.md`
- `specs/harness/local-validation.md`
- `specs/features/102-organizations-and-rbac.md`
- `specs/features/103-projects-and-tasks.md`
- `specs/features/201-background-jobs-and-notifications.md`
- `specs/features/303-member-invitations-and-project-access.md`
- `specs/features/304-organization-member-chat.md` only for future chat integration context

Memory updates:

- `docs/project-state.md` when current state, next work, known gaps, or validation baseline changes
- `docs/implementation-log.md` for meaningful spec-prep, implementation, review, validation, or merge events
- `specs/README.md` when status, dependencies, order, or primary surfaces change
- ADRs if notification delivery, retention, fan-out, or real-time transport becomes a durable cross-cutting decision

## Problem

Background jobs currently support log-only notification delivery, but users have no in-app notification inbox. Invitations and project/task changes need a product-visible notification surface so users can accept invitations and catch up on work while they were away.

## Goals

- Store in-app notifications for authenticated users.
- Show a notification inbox or menu with unread state.
- Let users mark notifications as read.
- Surface actionable organization and project invitations created by `SPEC-303` in the notification inbox.
- Notify users when they are added to an organization, project, or task.
- Notify relevant users when a project or task changes state.
- Keep the first implementation polling-based and reusable by later chat or email delivery.

## Non-Goals

- External email, SMS, push notifications, or web push.
- User-configurable notification preferences in the first implementation.
- Guaranteed real-time delivery; the first implementation uses authenticated API polling.
- Full audit log. Notifications are user-facing events, not the canonical history of every change.
- Defining invitation persistence or accept/decline semantics. `SPEC-303` owns those rules and provides the initial “My invitations” flow.

## Actors And Permissions

| Actor | Permission | Notes |
|---|---|---|
| Authenticated user | Read and update their own notifications | Cannot read another user's notifications |
| Organization/project/task actor | Triggers notifications through domain actions | Persistence is service-owned |
| Non-recipient | No notification access | Receives tenant-safe `404` |

## Business Rules

- BR-1: Notifications belong to exactly one recipient user.
- BR-2: A recipient can list, read, and mark only their own notifications.
- BR-3: Invitation notifications must be actionable and must reuse `SPEC-303` invitation records and accept/decline endpoints rather than duplicating invitation state.
- BR-4: Creating an organization or project invitation through `SPEC-303` creates a notification for the invited user.
- BR-5: Accepting or declining an invitation marks the matching invitation notification read, while preserving the underlying invitation record as the source of truth.
- BR-6: Adding a user to a project creates a notification for the added user.
- BR-7: Project status, archive, owner, or visibility changes notify explicit project members except the actor who made the change. Owners/admins who are not explicit project members are not added only for notifications in this version.
- BR-8: Task creation or assignment creates a notification for the assignee when present and not equal to the actor.
- BR-9: Task status changes notify the assignee and task watchers except the actor who made the change.
- BR-10: A duplicate domain event should not create duplicate unread notifications for the same recipient, type, resource, and unread state when the prior unread notification is still current enough for the same action.
- BR-11: Notification payloads must avoid storing secrets, raw cookies, auth headers, or private token values.
- BR-12: Notifications are retained indefinitely in the first implementation and may be deleted only by tenant/resource cascade. A later retention spec may add cleanup.
- BR-13: Polling the notifications API is the only delivery mechanism in this version; WebSockets/SSE remain future scope.

## Data Model Impact

Expected new table:

| Field | Type | Rules |
|---|---|---|
| id | UUID | Primary key |
| recipient_user_id | UUID | FK users.id |
| type | enum/string | Stable notification type |
| title | string | Short safe summary |
| body | string/null | Optional safe detail |
| action_url | string/null | Relative app route only |
| resource_type | string/null | Organization/project/task/invitation |
| resource_id | UUID/null | Related public resource ID where safe |
| read_at | timestamp/null | UTC |
| created_at | timestamp | UTC |

Indexes:

- `(recipient_user_id, read_at, created_at)`
- `(recipient_user_id, created_at)`
- optional unique or partial index may be used to prevent duplicate unread actionable notifications for the same recipient/type/resource.

Migration required if implemented.

## API Contract

All endpoints require authentication.

### `GET /api/v1/notifications`

Lists notifications for the current authenticated user using API pagination.

Query parameters:

- `limit`, `offset` per `SPEC-001`
- optional `unread=true|false`

Response `200`:

```json
{
  "items": [
    {
      "id": "uuid",
      "recipient_user_id": "uuid",
      "type": "invitation.organization",
      "title": "Organization invitation",
      "body": "You were invited to Acme Ops.",
      "action_url": "/app/invitations",
      "resource_type": "invitation",
      "resource_id": "uuid",
      "read_at": null,
      "created_at": "2026-08-14T10:00:00Z"
    }
  ],
  "total": 1,
  "limit": 20,
  "offset": 0
}
```

### `GET /api/v1/notifications/unread-count`

Returns the unread notification count for the current authenticated user.

Response `200`:

```json
{
  "unread_count": 3
}
```

### `PATCH /api/v1/notifications/{notification_id}`

Marks one notification read or unread.

Request:

```json
{
  "read": true
}
```

Response `200`: updated notification.

### `POST /api/v1/notifications/mark-all-read`

Marks all current-user unread notifications read.

Response `204`: all current-user notifications marked read with no response body.

Errors must follow `specs/001-api-conventions.md`, including `401 not_authenticated` and `404 notification_not_found` for missing or non-recipient notifications.

## Frontend Impact

- Add a notification bell/menu or inbox in the authenticated app shell.
- Show unread count.
- Show notification list with safe title, body, timestamp, and action route.
- Support mark-as-read and mark-all-read.
- Invitation notifications route to the existing `SPEC-303` “My invitations” page for accept/decline actions.
- The existing `SPEC-303` “My invitations” page remains as the canonical actionable invitation page in this version; the notification inbox links to it and shares the same backend invitation state.

## Acceptance Criteria

- AC-1: Given a user has unread notifications, when the app shell renders, then unread state is visible.
- AC-2: Given a user opens notifications, then only their notifications are listed.
- AC-3: Given a user marks a notification read, then `read_at` is persisted and unread count updates.
- AC-4: Given a user is invited to an organization or project through `SPEC-303`, then the notification inbox shows an actionable notification backed by the same invitation state.
- AC-5: Given a project is added to, reassigned, archived, or changes visible state, then intended explicit project members receive in-app notifications.
- AC-6: Given a task is created, assigned, or changes status, then the assignee/watchers defined by the business rules receive in-app notifications.
- AC-7: Given a user tries to read another user's notification, then the API returns a tenant-safe not-found response.

## Harness Requirements

Required tests/checks:

- Backend API tests for notification list, mark-read, mark-all-read, and non-recipient isolation.
- Backend service tests for `SPEC-303` invitation notification integration, project membership, assignment, and state-change notification creation.
- Frontend tests for unread count, inbox list, mark-read, and action navigation.
- Migration checks.

Required commands:

```bash
make test-backend
make test-frontend
make migrations-check
make lint
make format-check
make typecheck
make memory-check SPEC=SPEC-306
```

## Resolved Questions

- Use polling first. Chat and notifications may share WebSockets/SSE later only after a separate ADR/spec update.
- Retain notifications indefinitely in the first implementation; no cleanup job is required yet.
- Project status/archive/owner/visibility changes notify explicit project members except the actor.
- Task creation/assignment notifies the assignee except the actor; task status changes notify assignee and watchers except the actor.
- Keep the `SPEC-303` “My invitations” view as a dedicated actionable page; notification items link there.
- Missed chat notifications are deferred until `SPEC-304` defines chat persistence and recipient state.
