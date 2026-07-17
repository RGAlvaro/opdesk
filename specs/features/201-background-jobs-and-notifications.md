# SPEC-201 — Background Jobs and Notifications

Status: Implemented
Owner: Arquitecto de specs  
Last updated: 2026-07-07

## Scope And Required Context

This spec governs:

- Redis, Celery, worker services, background job enqueueing, notification delivery, task assignment notification hooks, worker tests, or worker/Redis Docker Compose wiring.

Required context:

- `AGENTS.md`
- `docs/project-state.md`
- `specs/README.md`
- `specs/harness/local-validation.md`
- `specs/features/103-projects-and-tasks.md`
- `specs/features/301-deployment-and-ops.md` when production worker/Redis behavior is involved

Memory updates:

- `docs/project-state.md` if background-job readiness, validation baseline, next work, or known gaps change
- `docs/implementation-log.md` for meaningful spec-prep, implementation, review, or validation events
- `specs/README.md` if status, dependencies, order, or primary surfaces change
- ADRs if broker, retry, notification persistence, or email adapter strategy is chosen

## Problem

Some actions should not block API responses. OpsDesk needs background jobs for email, notifications, cleanup, and scheduled maintenance, but only after the core MVP has actions worth notifying about.

## Goals

- Add Celery worker using Redis as broker.
- Provide a safe pattern for enqueueing jobs from service code.
- Implement one concrete MVP-adjacent use case: task assignment notification.
- Support local development without a real email provider.
- Track important job failures through structured logs.

## Dependencies

- Requires `SPEC-010` backend scaffold and local Docker Compose foundation.
- Requires `SPEC-103` task assignment and update behavior to be implemented first.
- Requires Redis service configuration through `CELERY_BROKER_URL` and
  `CELERY_RESULT_BACKEND`, defaulting to the local Compose `redis` service.

## Non-Goals

- Paid email provider integration.
- Workflow engine.
- User-configurable notification preferences.
- Notification inbox UI.

## Business Rules

- BR-1: API requests must not depend on email provider latency.
- BR-2: Job payloads must be minimal and must not include secrets.
- BR-3: Task assignment notification jobs are idempotent by `(task_id, assignee_id, assignment_version)` where practical.
- BR-4: Failed jobs must log job name, safe resource IDs, and error class.
- BR-5: Local development uses console logging or Mailpit; no real email credentials required.

## Data Model Impact

No persistent notification or job audit tables in the first version. Job execution is observable
through structured application logs. A later notification inbox or audit feature must introduce its
own schema before implementation.

## API Impact

No direct public API for the first version.

## Worker And Delivery Decisions

- Redis is the Celery broker and result backend for local and production Compose.
- The first delivery adapter is a console/logging adapter. It records the intended notification
  recipient and safe task identifiers without contacting an external email provider.
- Task assignment notification jobs carry only `task_id`, `assignee_id`, and
  `assignment_version`. `assignment_version` is the task `updated_at` timestamp after the
  assignment write succeeds.
- Worker processing validates that the task still exists and is still assigned to the payload
  assignee. Stale payloads are logged and ignored.
- Worker retries are limited to transient processing failures using Celery retry behavior with a
  short backoff. Stale or invalid assignment data is not retried.
- Local tests may enable Celery eager mode instead of requiring a Redis broker.

## Acceptance Criteria

- AC-1: Given a task is assigned or reassigned, when the main API action succeeds, then a task assignment notification job is enqueued.
- AC-2: Given the worker receives a valid job, when it processes the job, then it sends through the configured local-safe adapter.
- AC-3: Given invalid or stale task data, when the worker processes the job, then it fails safely and logs enough safe context to debug.
- AC-4: Given local development without email credentials, when notification logic runs, then no external email provider is required.

## Harness Requirements

Backend tests:

- Unit test job payload creation.
- Integration test task update enqueues job.
- Worker task test using eager/synchronous mode or fake broker.
- Docker Compose check includes Redis and worker service.

Required commands once available:

```bash
make test-backend
make smoke
```

## Resolved Questions

- Use console/logging adapter only for this first version; no Mailpit or external email provider.
- Do not add persistent job audit tables in this spec.
- Use Redis-backed Celery with eager mode for tests, retry backoff, and limited retries for
  unexpected worker errors.
- Task assignment notification is log-only for the first version.
- Local and production Redis/worker Compose wiring is owned by this spec and extends `SPEC-301`.
