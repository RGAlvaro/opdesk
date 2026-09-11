# SPEC-314 — External Notification Delivery

Status: Implemented
Owner: Arquitecto de specs
Last updated: 2026-09-09

## Scope And Required Context

This spec governs:

- External notification delivery channels, initially email.
- Provider adapter selection, delivery templates, background sending, retry behavior, delivery audit, user-safe content, and production configuration.
- `.env.example`, backend settings, Celery worker tasks, notification services, tests, deployment docs, and production release checks when external delivery is enabled.

Required context:

- `AGENTS.md`
- `docs/project-state.md`
- `specs/README.md`
- `specs/000-product-vision.md`
- `specs/001-api-conventions.md`
- `specs/harness/local-validation.md`
- `specs/features/201-background-jobs-and-notifications.md`
- `specs/features/303-member-invitations-and-project-access.md`
- `specs/features/305-project-clients-and-tickets.md`
- `specs/features/306-in-app-notifications.md`
- `specs/features/307-release-automation-and-safe-updates.md`
- `docs/decisions/ADR-010-background-jobs-and-notifications.md`
- `docs/decisions/ADR-013-resend-email-delivery.md`

Memory updates:

- `docs/project-state.md` when notification delivery readiness, validation baseline, next work, or known gaps change
- `docs/implementation-log.md` for meaningful spec-prep, implementation, review, validation, or merge events
- `specs/README.md` when status, dependencies, order, or primary surfaces change
- ADR required when the provider, local fake delivery strategy, retry policy, or delivery audit retention is chosen

## Problem

OpsDesk currently persists in-app notifications and has a log-only background notification adapter. That is enough for local demos, but real users do not receive alerts unless they are already in the app. Client tickets, invitations, assignment requests, and unread conversations need an external delivery path so recipients can return to OpsDesk.

## Goals

- Add an external email delivery channel for all first-slice high-value notification events.
- Keep API requests independent of provider latency by sending through Celery.
- Preserve in-app notifications as the canonical product notification surface.
- Add delivery audit records for provider status, retries, failures, and safe debugging.
- Provide local and CI-safe delivery behavior that does not require real provider credentials.
- Document production environment variables and operational checks without committing secrets.

## Non-Goals

- SMS, WhatsApp, Slack, Teams, or mobile push delivery.
- Marketing email, newsletters, or bulk campaigns.
- User-configurable notification preferences in the first implementation.
- Replacing the in-app notification inbox.
- Sending external messages for every notification type.
- Public anonymous ticket intake.

## Actors And Permissions

| Actor | Permission | Notes |
|---|---|---|
| Recipient user | Receives external messages for eligible notifications | Email address comes from the authenticated user record |
| Organization owner/admin | Triggers invitations/client access and project events | Does not see provider secrets |
| Project member/client | Triggers ticket/comment/assignment events | Delivery must not leak tenant data to unrelated users |
| Worker process | Sends external messages and records delivery state | Uses provider credentials from environment only |
| Developer/CI | Uses fake or console delivery | Must not contact real providers by default |

## Business Rules

- BR-1: In-app notification persistence remains the source of truth for notification content and unread state.
- BR-2: External delivery is best-effort and must not roll back successful domain actions.
- BR-3: Email delivery is enabled by default for all users in the first implementation.
- BR-4: External messages are sent only for explicitly eligible notification types.
- BR-5: Eligible first-slice notification types are organization invitations, project invitations, client ticket creation, ticket comments, ticket assignment requests, and missed chat/unread conversation summaries.
- BR-6: Message content must include safe summaries and relative or absolute app links, but must not include passwords, cookies, tokens, raw auth headers, or secret values.
- BR-7: Production email delivery uses Resend as the selected provider.
- BR-8: Provider credentials must come from environment variables or server-side secret files only.
- BR-9: Local and CI environments must default to fake/console delivery and must not require external network access.
- BR-10: Delivery retries must be bounded, idempotent by notification/channel/recipient where practical, and safe against duplicate provider sends.
- BR-11: Provider failures must be recorded without exposing secret request/response payloads.
- BR-12: Revoked access or deactivated users must suppress future external delivery where practical before the job sends.
- BR-13: Delivery audit rows are retained indefinitely until manually deleted by an explicit future admin/maintenance flow.

## Data Model Impact

Expected new table:

| Field | Type | Rules |
|---|---|---|
| id | UUID | Primary key |
| notification_id | UUID | FK notifications.id when delivery is tied to an in-app notification |
| recipient_user_id | UUID | FK users.id |
| channel | string/enum | Initially `email` |
| provider | string | Configured provider key, initially `resend` in production and `console`/`fake` locally |
| provider_message_id | string/null | Safe provider id when available |
| status | string/enum | `pending`, `sent`, `failed`, `suppressed` |
| attempt_count | integer | Starts at 0 |
| last_attempt_at | timestamp/null | UTC |
| next_attempt_at | timestamp/null | UTC if retry is scheduled |
| last_error_code | string/null | Safe error class/code |
| created_at | timestamp | UTC |
| updated_at | timestamp | UTC |

Indexes:

- `(recipient_user_id, created_at)`
- `(notification_id, channel)`
- `(status, next_attempt_at)`

Migration required if implemented.

## API Contract

No public user-facing delivery management API is required in the first implementation because email notifications are enabled by default and no user preferences are introduced.

If an internal diagnostic endpoint is added, it must be owner/admin-scoped and follow `specs/001-api-conventions.md`. This spec does not require such an endpoint.

## Frontend Impact

- No mandatory user-facing frontend changes for sending email.
- Do not add account-level email notification preferences in this spec.
- Optional: display a small user-safe delivery state in notification detail surfaces only if product value is clear and no provider-sensitive data is exposed.

## Acceptance Criteria

- AC-1: Given an eligible in-app notification is created, when email delivery is enabled by default, then an email delivery job is enqueued without delaying the API response.
- AC-2: Given the worker processes an eligible pending delivery in production configuration, then it sends through the Resend provider adapter and records `sent` or `failed`.
- AC-3: Given local or CI configuration, then delivery uses fake/console mode and no real provider credentials are required.
- AC-4: Given a provider returns a transient failure, then retry state is recorded and retry attempts are bounded.
- AC-5: Given a provider returns a permanent failure or the recipient is no longer eligible, then the delivery is marked `failed` or `suppressed` without retry loops.
- AC-6: Given a non-eligible notification type is created, then no external delivery is attempted.
- AC-7: Given logs or delivery audit rows are inspected, then secrets, passwords, cookies, and raw tokens are absent.
- AC-8: Given production deploy docs are read, then required provider variables and fake/local behavior are documented.
- AC-9: Given delivery audit rows exist, then they remain stored until a later manual deletion or retention feature explicitly removes them.

## Harness Requirements

Required tests/checks:

- Backend adapter tests for fake provider and Resend adapter using mocks only.
- Backend service tests for eligible event fan-out and suppression.
- Worker tests for success, transient failure retry, permanent failure, and idempotency.
- Migration checks for delivery audit table.
- Production config validation for required env variables when external delivery is enabled.
- Secret-pattern checks must remain passing.

Required commands:

```bash
make test-backend
make migrations-check
make lint
make format-check
make typecheck
make prod-config
make memory-check SPEC=SPEC-314
```

## Observability And Failure Cases

- Worker logs include delivery id, notification id, channel, provider key, recipient user id, status, and safe error code.
- Logs must not include full message bodies by default in production.
- Delivery audit state must distinguish `failed` from `suppressed`.
- Provider timeouts are retryable only within the bounded retry policy.

## Resolved Questions

- [x] Production email provider: Resend.
- [x] Email notifications are enabled by default for all users; preferences are future scope.
- [x] Day-one emailed notification types: organization invitations, project invitations, client ticket creation, ticket comments, ticket assignment requests, and missed chat/unread conversation summaries.
- [x] Delivery audit retention: indefinite until manually deleted by a later explicit admin/maintenance flow.

## Implementation Notes

- Implement a provider interface with fake/console and Resend adapters.
- Use `ADR-013` as the durable provider and retention decision.
- Keep templates plain, transactional, and tenant-safe; avoid marketing copy.
