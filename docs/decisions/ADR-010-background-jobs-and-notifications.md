# ADR-010 — Background Jobs And Notification Delivery

Status: Accepted
Date: 2026-07-07
Related specs:
- SPEC-201
- SPEC-301

## Context

OpsDesk needs a background-job path for notification and maintenance work without making API
responses depend on external provider latency. The first concrete use case is task assignment
notification after `SPEC-103` introduced assignable tasks.

## Decision

Use Celery with Redis as both broker and result backend. Local and production Docker Compose include
private Redis and worker services once `SPEC-201` is implemented.

The first notification adapter writes structured log messages instead of sending email. Jobs carry
only safe identifiers: `task_id`, `assignee_id`, and an `assignment_version` derived from the task
`updated_at` value after the assignment transaction commits. The worker reloads the task from the
database and ignores stale payloads whose assignee no longer matches.

Worker retries are limited to unexpected processing failures. Stale or invalid task data is logged
and treated as a completed no-op, because retrying cannot make an obsolete assignment current again.

## Consequences

The app gains a real broker and worker topology without requiring email credentials for local demos
or CI. Future email, notification inbox, or audit features can replace or extend the adapter while
keeping service code behind the enqueue boundary.

API requests still need Redis to accept enqueue requests for the job to be delivered. Enqueue
failures are logged and do not roll back the already-successful task write.

## Alternatives Considered

- Mailpit for local delivery: useful for visual email testing, but unnecessary before real email
  templates exist.
- Persistent notification/job audit table: more recruiter-visible, but it would introduce product
  behavior and API/UI questions outside this first background-job slice.
- FastAPI background tasks: simpler, but they do not demonstrate worker isolation, retry policy, or
  Redis-backed operations expected by the product vision.
