# SPEC-316 — Scheduled Jobs And Operational Audit

Status: Ready
Owner: Arquitecto de specs
Last updated: 2026-09-07

## Scope And Required Context

This spec governs:

- Periodic background jobs, scheduler service topology, and operational audit records.
- Celery beat or equivalent scheduler, idempotent job behavior, retention/cleanup tasks, delivery retry sweeps, and production deployment updates.
- Backend models/services, worker/scheduler Compose wiring, harness checks, and deployment docs for scheduled maintenance.

Required context:

- `AGENTS.md`
- `docs/project-state.md`
- `specs/README.md`
- `specs/000-product-vision.md`
- `specs/001-api-conventions.md`
- `specs/harness/local-validation.md`
- `specs/features/201-background-jobs-and-notifications.md`
- `specs/features/301-deployment-and-ops.md`
- `specs/features/306-in-app-notifications.md`
- `specs/features/307-release-automation-and-safe-updates.md`
- `specs/features/314-external-notification-delivery.md`
- `docs/decisions/ADR-010-background-jobs-and-notifications.md`
- `docs/decisions/ADR-014-celery-beat-and-operational-audit.md`

Memory updates:

- `docs/project-state.md` when scheduled-job readiness, validation baseline, next work, or known gaps change
- `docs/implementation-log.md` for meaningful spec-prep, implementation, review, validation, or merge events
- `specs/README.md` when status, dependencies, order, or primary surfaces change
- ADR required if scheduler topology, audit retention, or job idempotency policy changes cross-cutting operations

## Problem

OpsDesk has a Celery worker, but no scheduler or persistent operational audit. Future production behavior needs reliable periodic tasks for cleanup, retry sweeps, stale invitation handling, and maintenance checks. Without explicit scheduled-job specs, these behaviors risk becoming hidden cron-like work with weak evidence and unclear production ownership.

## Goals

- Add a scheduler service for periodic jobs using Celery beat or a documented equivalent.
- Add persistent operational audit records for scheduled job runs and important background maintenance outcomes.
- Define the first scheduled jobs with clear idempotency and safety rules.
- Keep production Compose, smoke checks, and deployment docs aligned with the new scheduler service.
- Make job failures visible through logs and persisted audit rows.
- Provide an owner/admin-visible operational audit screen.

## Non-Goals

- Full workflow engine.
- User-facing analytics dashboards beyond the focused operational audit screen.
- Enterprise observability stack, metrics backend, or alerting vendor integration.
- Running arbitrary admin-defined jobs.
- Long-running distributed locks beyond what is needed for single-scheduler production.

## Actors And Permissions

| Actor | Permission | Notes |
|---|---|---|
| Scheduler service | Enqueues configured periodic jobs | Exactly one active scheduler in production V1 |
| Worker service | Executes scheduled jobs | Must use idempotent job handlers |
| Organization owner/admin | Reads operational audit rows from an admin screen | Audit is operational status, not analytics |
| Developer/operator | Reads logs and audit rows during troubleshooting | No secrets or raw payloads in logs/API |
| CI/review agent | Validates scheduler config and job behavior | Must not depend on wall-clock waiting |

## Business Rules

- BR-1: Scheduled jobs must be idempotent by resource and time window where practical.
- BR-2: Production V1 runs exactly one scheduler service; multiple schedulers require a later locking/scaling spec.
- BR-3: Scheduled jobs must not require direct manual database mutation.
- BR-4: Job handlers must log safe resource identifiers and error classes, not secrets or raw payloads.
- BR-5: Each scheduled run must record an audit entry with job name, status, start/end timestamps, safe counts, and safe error summary when failed.
- BR-6: Failed scheduled jobs must not block the scheduler from enqueueing later runs.
- BR-7: Scheduler configuration must be deterministic and documented in code/config, not hidden in a VPS crontab.
- BR-8: Cleanup jobs must have explicit retention rules before deleting or mutating durable user-facing records.
- BR-9: Delivery retry sweeps are included after `SPEC-314` defines external delivery audit state.
- BR-10: Notification rows, delivery audit rows, and scheduled job audit rows are retained indefinitely until manually deleted by an explicit future admin/maintenance flow.
- BR-11: The first scheduled jobs are implemented in this order: scheduler heartbeat/health audit, external email delivery retry sweep, expired invitation state maintenance, and stale ticket assignment request reminder creation.
- BR-12: Cleanup in this spec must mark or summarize state rather than physically deleting user-facing notifications, delivery audit, or operational audit rows.
- BR-13: The admin audit screen is visible only to organization owners/admins and must not expose secrets, raw provider payloads, cookies, tokens, or personal message bodies.

## Data Model Impact

Expected new table:

| Field | Type | Rules |
|---|---|---|
| id | UUID | Primary key |
| job_name | string | Stable scheduled job identifier |
| scheduled_for | timestamp/null | UTC scheduled time/window when known |
| started_at | timestamp | UTC |
| finished_at | timestamp/null | UTC |
| status | string/enum | `started`, `succeeded`, `failed`, `skipped` |
| records_seen | integer/null | Safe count when applicable |
| records_changed | integer/null | Safe count when applicable |
| error_code | string/null | Safe exception class/code |
| error_message | string/null | Sanitized short message |
| created_at | timestamp | UTC |
| updated_at | timestamp | UTC |

Indexes:

- `(job_name, started_at)`
- `(status, started_at)`

Migration required if implemented.

## API Contract

All operational audit endpoints require authentication and must follow `specs/001-api-conventions.md`.

### `GET /api/v1/admin/operational-audit`

Lists scheduled job audit rows for organization owner/admin users.

Query parameters:

- `limit`, `offset` per `SPEC-001`
- optional `job_name`
- optional `status`

Response `200`:

```json
{
  "items": [
    {
      "id": "uuid",
      "job_name": "external_delivery_retry_sweep",
      "scheduled_for": "2026-09-07T10:00:00Z",
      "started_at": "2026-09-07T10:00:01Z",
      "finished_at": "2026-09-07T10:00:03Z",
      "status": "succeeded",
      "records_seen": 4,
      "records_changed": 2,
      "error_code": null,
      "error_message": null,
      "created_at": "2026-09-07T10:00:01Z",
      "updated_at": "2026-09-07T10:00:03Z"
    }
  ],
  "total": 1,
  "limit": 20,
  "offset": 0
}
```

Errors:

| Status | Code | Condition |
|---:|---|---|
| 401 | `not_authenticated` | Missing or invalid session |
| 403 | `insufficient_role` | Authenticated user is not an owner/admin in the selected administrative context |

## Frontend Impact

- Add an owner/admin-visible operational audit route under the authenticated app shell.
- Show scheduled job audit rows with filters for job name and status.
- Show job name, status, start/finish timestamps, safe counts, and sanitized error code/message.
- Include loading, empty, and error states.
- Hide the audit navigation item from regular members and client accounts.

## Acceptance Criteria

- AC-1: Given production Compose starts, then backend, worker, Redis, and exactly one scheduler service are configured for scheduled jobs.
- AC-2: Given the scheduler tick occurs, then configured jobs are enqueued without requiring manual VPS cron configuration.
- AC-3: Given a scheduled job succeeds, then an audit row records job name, timestamps, status, and safe counts.
- AC-4: Given a scheduled job fails, then an audit row records failure status and sanitized error details while the scheduler remains able to enqueue future runs.
- AC-5: Given a cleanup job mutates records, then the mutation follows an explicit retention/state rule documented in this spec or a dependent spec.
- AC-6: Given tests run, then scheduled job behavior is exercised without waiting for real wall-clock intervals.
- AC-7: Given deployment docs are read, then scheduler service operation, logs, and rollback considerations are documented.
- AC-8: Given an owner/admin opens the operational audit screen, then scheduled job audit rows are visible with safe status and count information.
- AC-9: Given a regular member or client account attempts to open operational audit, then the UI/API deny access without exposing audit rows.
- AC-10: Given delivery audit or scheduled job audit rows exist, then they are retained indefinitely until a later manual deletion feature explicitly removes them.

## Harness Requirements

Required tests/checks:

- Backend tests for audit row creation on success/failure.
- Scheduler configuration test proving expected jobs are registered.
- Worker tests for scheduler heartbeat/health audit, external delivery retry sweep, expired invitation state maintenance, and stale ticket assignment request reminders.
- Backend API tests for owner/admin operational audit list, filtering, pagination, and role denial.
- Frontend tests for operational audit route visibility, list rendering, filters, empty/error states, and role-gated navigation.
- Migration checks for audit table.
- Compose smoke check includes scheduler service when implemented.
- Production config validation confirms scheduler is private and uses Redis/backend settings safely.

Required commands:

```bash
make test-backend
make test-frontend
make migrations-check
make smoke
make prod-config
make lint
make format-check
make typecheck
make memory-check SPEC=SPEC-316
```

## Observability And Failure Cases

- Logs include job name, audit id, status, safe counts, and safe error code.
- Audit records must not store secrets, tokens, cookies, email provider payloads, or personal message bodies.
- Repeated failures should be visible through audit rows and logs; alerting is future scope unless explicitly added.
- If the scheduler is not running, production smoke should expose the missing service once this spec is implemented.

## Resolved Questions

- [x] First scheduled jobs and implementation order: scheduler heartbeat/health audit, external delivery retry sweep, expired invitation state maintenance, stale ticket assignment request reminders.
- [x] Retention policy: notifications, delivery audit, and scheduled job audit rows are retained indefinitely until manually deleted by a later explicit feature.
- [x] Operational audit is visible in an owner/admin screen.
- [x] Scheduler mechanism: Celery beat.

## Implementation Notes

- Celery beat is selected because the project already uses Celery and Redis.
- Keep first implementation order incremental: prove scheduler/audit with heartbeat first, then add delivery retry, then invitation state maintenance, then assignment reminders.
- Avoid destructive cleanup; this spec retains audit and notification data indefinitely.
