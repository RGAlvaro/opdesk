# SPEC-201 — Background Jobs and Notifications

Status: Draft  
Owner: Arquitecto de specs  
Last updated: 2026-06-08

## Problem

Some actions should not block API responses. OpsDesk needs background jobs for email, notifications, cleanup, and scheduled maintenance, but only after the core MVP has actions worth notifying about.

## Goals

- Add Celery worker using Redis as broker.
- Provide a safe pattern for enqueueing jobs from service code.
- Implement one concrete MVP-adjacent use case: task assignment notification.
- Support local development without a real email provider.
- Track important job failures through structured logs.

## Dependencies

- Requires `SPEC-103` task assignment and update behavior to be implemented first.
- Requires Redis service configuration from `SPEC-301` local/production Compose work.

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

To be finalized before implementation.

Default first version should avoid persistent notification tables unless needed. If job audit persistence is added, define schema here first.

## API Impact

No direct public API for the first version.

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

## Open Questions Before Ready

- [ ] Use console adapter only or Mailpit locally?
- [ ] Is persistent job audit needed for portfolio value?
- [ ] Exact Celery configuration and retry policy.
- [ ] Should task assignment notification be email-only, log-only for demo, or both?
