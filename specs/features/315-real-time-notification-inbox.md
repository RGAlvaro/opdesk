# SPEC-315 — Real-Time Notification Inbox

Status: Implemented
Owner: Arquitecto de specs
Last updated: 2026-09-09

## Scope And Required Context

This spec governs:

- Real-time notification inbox updates for unread count and newly created notifications.
- WebSocket or SSE transport for notification delivery to authenticated browser sessions.
- Frontend connection states, fallback polling, reconnect behavior, and backend tests.

Required context:

- `AGENTS.md`
- `docs/project-state.md`
- `specs/README.md`
- `specs/000-product-vision.md`
- `specs/001-api-conventions.md`
- `specs/harness/local-validation.md`
- `specs/features/306-in-app-notifications.md`
- `specs/features/304-organization-member-chat.md`
- `specs/features/307-release-automation-and-safe-updates.md`
- `docs/decisions/ADR-012-websocket-chat-transport.md`

Memory updates:

- `docs/project-state.md` when notification delivery mode, validation baseline, next work, or known gaps change
- `docs/implementation-log.md` for meaningful spec-prep, implementation, review, validation, or merge events
- `specs/README.md` when status, dependencies, order, or primary surfaces change
- ADR update required if notification real-time transport differs materially from chat transport or adds Redis pub/sub fan-out

## Problem

`SPEC-306` intentionally uses polling for the notification inbox. Polling works, but unread counts and notification lists can feel stale compared with the real-time chat behavior implemented in `SPEC-304`. OpsDesk needs a focused real-time notification layer while preserving REST as the source of truth.

## Goals

- Deliver newly created in-app notifications to active browser sessions without waiting for the next poll.
- Update app-shell unread counts promptly when notifications are created, marked read, or marked all read.
- Keep REST endpoints as the canonical source for list, count, and read state recovery.
- Keep polling as a fallback for reconnect and unsupported/failed real-time sessions.
- Reuse the session-cookie authentication approach already used by chat WebSockets.

## Non-Goals

- External email/SMS/push delivery.
- Replacing the existing notification REST APIs.
- Multi-replica Redis pub/sub fan-out unless production topology requires it.
- Browser push notifications through the Notifications API or service workers.
- Real-time admin dashboards or analytics.

## Actors And Permissions

| Actor | Permission | Notes |
|---|---|---|
| Authenticated user | Receives only their own notification events | Session-cookie auth required |
| Non-recipient user | No access to another user's events | Must not learn resource existence |
| Client account | Receives own client-relevant notifications | Must remain outside internal-only chat surfaces |
| Backend notification service | Publishes events after persistence | Persistence remains source of truth |
| Browser app | Maintains connection and falls back to polling | Must expose clear failed/reconnecting state only where useful |

## Business Rules

- BR-1: Notification rows must be persisted before real-time fan-out.
- BR-2: Real-time payloads must contain only data the recipient can already read via `GET /api/v1/notifications`.
- BR-3: A user receives only events for their own `recipient_user_id`.
- BR-4: The app shell unread count must update when new notification, mark-read, and mark-all-read events affect the current user.
- BR-5: REST list/count endpoints remain required for initial load and reconnect recovery.
- BR-6: If the real-time connection fails, the frontend falls back to the existing polling behavior.
- BR-7: V1 may use in-process connection management for the current single-backend production topology.
- BR-8: Any multi-backend production scaling must add Redis pub/sub or equivalent fan-out through a later spec/ADR before deployment.
- BR-9: Real-time delivery is best-effort; missing an event must not corrupt read/unread state because REST recovery remains available.

## Data Model Impact

No database schema changes are required.

## API Contract

Existing REST endpoints from `SPEC-306` remain unchanged:

- `GET /api/v1/notifications`
- `GET /api/v1/notifications/unread-count`
- `PATCH /api/v1/notifications/{notification_id}`
- `POST /api/v1/notifications/mark-all-read`

Expected real-time endpoint:

### `GET /api/v1/notifications/ws`

Authenticated WebSocket endpoint.

Connection rules:

- Requires valid browser session cookie.
- Rejects unauthenticated connections.
- Sends only current-user notification events.

Example event payload:

```json
{
  "type": "notification.created",
  "notification": {
    "id": "uuid",
    "recipient_user_id": "uuid",
    "type": "ticket.comment",
    "title": "Ticket updated",
    "body": "New feedback was added.",
    "action_url": "/app/client/tickets/uuid",
    "resource_type": "ticket",
    "resource_id": "uuid",
    "read_at": null,
    "created_at": "2026-09-07T10:00:00Z"
  },
  "unread_count": 4
}
```

Additional events:

- `notification.read`
- `notifications.mark_all_read`
- optional `notification.deleted` only if deletion exists in a later spec

Errors must follow existing WebSocket close behavior used by `SPEC-304` where practical; REST errors continue following `specs/001-api-conventions.md`.

## Frontend Impact

- Add notification real-time client wiring near the authenticated app shell or notification feature.
- On connection open, load current notification count/list through REST.
- On `notification.created`, update unread count and invalidate or patch notification list cache.
- On read/mark-all-read events, update unread count and list cache for the current user.
- Show no intrusive real-time status by default; use existing loaded/error states unless a persistent outage affects the inbox.
- Preserve polling fallback with a documented interval when WebSocket is unavailable.

## Acceptance Criteria

- AC-1: Given an authenticated user has an active notification WebSocket, when a notification is created for that user, then the app-shell unread count updates without waiting for polling.
- AC-2: Given a notification is created for another user, then the current user's WebSocket receives no event.
- AC-3: Given a user marks one notification read in one active session, then another active session for the same user updates unread state or recovers it on the next REST refresh.
- AC-4: Given the WebSocket disconnects, then the frontend falls back to polling and later reconnects without duplicate visible notifications.
- AC-5: Given an unauthenticated browser attempts to connect, then the backend rejects the connection.
- AC-6: Given REST notification endpoints are called, then their behavior remains compatible with `SPEC-306`.

## Harness Requirements

Required tests/checks:

- Backend WebSocket tests for authentication, recipient isolation, created events, and read-state events.
- Backend notification service tests proving persistence happens before fan-out.
- Frontend tests for unread count update, list invalidation/cache patching, fallback polling, and reconnect behavior.
- Existing notification API tests remain passing.
- Caddy/production smoke checks continue to support WebSocket upgrades through `/api/v1/notifications/ws`.

Required commands:

```bash
make test-backend
make test-frontend
make lint
make format-check
make typecheck
make smoke
make memory-check SPEC=SPEC-315
```

## Observability And Failure Cases

- Backend logs connection open/close counts and safe user ids only when useful for debugging.
- WebSocket payloads must not include cookies, tokens, provider secrets, or private credentials.
- Reconnect loops must use bounded backoff to avoid hammering the backend.
- If Redis pub/sub is introduced later, delivery must remain tenant-safe across processes.

## Open Questions

- [x] Should this use polling only? No. Polling remains fallback, but real-time delivery uses WebSockets to align with chat.
- [x] Should browser push notifications be included? No. Browser push/service workers remain a separate future spec.
- [x] Should Redis pub/sub be required now? No. Current production is single backend; document the scaling constraint.

## Implementation Notes

- Reuse the `SPEC-304` session-cookie WebSocket authentication pattern where practical.
- Keep REST query invalidation simple before optimizing client-side cache patching.
- If chat and notifications start duplicating transport code heavily, extract a small shared connection helper during implementation.
