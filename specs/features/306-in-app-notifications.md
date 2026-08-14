# SPEC-306 — In-App Notifications

Status: Draft
Owner: Arquitecto de specs
Last updated: 2026-08-14

## Scope And Required Context

This spec governs:

- Persistent in-app notifications.
- Notification inbox UI and read/unread state.
- Notification events for organization, project, task, and chat activity.
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
- `specs/features/304-organization-member-chat.md`

Memory updates:

- `docs/project-state.md` when current state, next work, known gaps, or validation baseline changes
- `docs/implementation-log.md` for meaningful spec-prep, implementation, review, validation, or merge events
- `specs/README.md` when status, dependencies, order, or primary surfaces change
- ADRs if notification delivery, retention, fan-out, or real-time transport becomes a durable cross-cutting decision

## Problem

Background jobs currently support log-only notification delivery, but users have no in-app notification inbox. Invitations, project/task changes, and missed chat messages need a product-visible notification surface so users can accept invitations and catch up on work while they were disconnected.

## Goals

- Store in-app notifications for authenticated users.
- Show a notification inbox or menu with unread state.
- Let users mark notifications as read.
- Surface actionable organization and project invitations created by `SPEC-303` in the notification inbox.
- Notify users when they are added to an organization, project, or task.
- Notify relevant users when a project or task changes state.
- Notify users about missed chat messages while they are disconnected or not viewing the conversation.
- Build on `SPEC-201` background job infrastructure where asynchronous dispatch is useful.

## Non-Goals

- External email, SMS, push notifications, or web push.
- User-configurable notification preferences in the first implementation.
- Guaranteed real-time delivery unless a later ADR selects WebSockets/SSE.
- Full audit log. Notifications are user-facing events, not the canonical history of every change.
- Defining invitation persistence or accept/decline semantics. `SPEC-303` owns those rules and provides the initial “My invitations” flow.

## Actors And Permissions

| Actor | Permission | Notes |
|---|---|---|
| Authenticated user | Read and update their own notifications | Cannot read another user's notifications |
| Organization/project/task actor | Triggers notifications through domain actions | Delivery is service-owned |
| Non-recipient | No notification access | Receives tenant-safe `404` |

## Business Rules

- BR-1: Notifications belong to exactly one recipient user.
- BR-2: A recipient can list, read, and mark only their own notifications.
- BR-3: Invitation notifications must be actionable and must reuse `SPEC-303` invitation records and accept/decline endpoints rather than duplicating invitation state.
- BR-4: Adding a user to an organization or project through `SPEC-303` creates or surfaces a notification for that user once this spec is implemented.
- BR-5: Project state changes notify project members who should see that project.
- BR-6: Task state changes notify the assignee and any other explicitly configured recipients.
- BR-7: Missed chat messages notify recipients who are offline or not actively viewing the relevant conversation.
- BR-8: Notification payloads must avoid storing secrets, raw cookies, auth headers, or private token values.

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
| resource_type | string/null | Organization/project/task/chat/invitation |
| resource_id | UUID/null | Related public resource ID where safe |
| read_at | timestamp/null | UTC |
| created_at | timestamp | UTC |

Indexes:

- `(recipient_user_id, read_at, created_at)`
- `(recipient_user_id, created_at)`

Migration required if implemented.

## API Contract

Exact endpoints remain Draft. Candidate endpoints:

- `GET /api/v1/notifications`
- `PATCH /api/v1/notifications/{notification_id}`
- `POST /api/v1/notifications/mark-all-read`

Errors must follow `specs/001-api-conventions.md`, including `401 not_authenticated` and `404 notification_not_found` for missing or non-recipient notifications.

## Frontend Impact

- Add a notification bell/menu or inbox in the authenticated app shell.
- Show unread count.
- Show notification list with safe title, body, timestamp, and action route.
- Support mark-as-read and mark-all-read.
- Invitation notifications must route to or embed the accept/decline flow from `SPEC-303`.
- The existing `SPEC-303` “My invitations” surface remains valid until this notification inbox ships; after `SPEC-306`, both surfaces must use the same backend invitation state.

## Acceptance Criteria

- AC-1: Given a user has unread notifications, when the app shell renders, then unread state is visible.
- AC-2: Given a user opens notifications, then only their notifications are listed.
- AC-3: Given a user marks a notification read, then `read_at` is persisted and unread count updates.
- AC-4: Given a user is invited to an organization or project through `SPEC-303`, then the notification inbox shows an actionable notification backed by the same invitation state.
- AC-5: Given a project or task changes state, then intended recipients receive in-app notifications.
- AC-6: Given a user receives chat messages while disconnected or away from the conversation, then they receive an in-app notification.
- AC-7: Given a user tries to read another user's notification, then the API returns a tenant-safe not-found response.

## Harness Requirements

Required tests/checks:

- Backend API tests for notification list, mark-read, mark-all-read, and non-recipient isolation.
- Backend service tests for `SPEC-303` invitation notification integration, assignment, state-change, and chat notification creation.
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

## Open Questions

- [ ] Should notification delivery use polling first, or should chat/notifications share a WebSocket/SSE transport later?
- [ ] What notification retention policy should apply?
- [ ] Which project/task state changes notify all project members versus only assignees/watchers?
- [ ] Should the `SPEC-303` “My invitations” view remain as a dedicated page after the full notification inbox ships, or should it become a filtered notifications view?
