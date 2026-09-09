# ADR-014 — Celery Beat And Operational Audit

Status: Accepted
Date: 2026-09-07
Related specs:
- SPEC-316
- SPEC-301
- SPEC-201
- SPEC-314

## Context

OpsDesk already uses Celery and Redis for background work. The project needs periodic maintenance and an audit trail without hiding behavior in VPS cron entries or introducing an unrelated scheduler stack.

Scheduled jobs also need to remain visible enough for a recruiter/operator to verify that production-minded maintenance exists and fails safely.

## Decision

Use Celery beat as the scheduler for `SPEC-316`.

Add a persistent operational audit table for scheduled job runs. Audit rows are retained indefinitely until a later explicit manual deletion or retention feature removes them.

Expose operational audit in an owner/admin-visible app screen backed by a role-gated API. The screen shows safe job names, statuses, timestamps, counts, and sanitized error details only.

Implement scheduled jobs in this order:

1. Scheduler heartbeat/health audit.
2. External email delivery retry sweep.
3. Expired invitation state maintenance.
4. Stale ticket assignment request reminder creation.

Production V1 runs exactly one scheduler service. Multi-scheduler locking or horizontally scaled scheduler operation requires a later spec/ADR.

## Consequences

The scheduler fits the existing Redis/Celery topology and production Compose model. `SPEC-301` deployment docs and smoke checks must be updated when the scheduler service is added.

Operational audit becomes product-visible for owner/admin users, so API and frontend permissions need explicit tests. Audit rows must avoid secrets, raw provider payloads, tokens, cookies, and personal message bodies.

Indefinite retention simplifies the first implementation and preserves debugging evidence, but the database may grow over time. A later retention/manual deletion spec can address cleanup once real volume exists.

## Alternatives Considered

- VPS cron: simple, but hidden from Compose, harder to test, and easier for future agents to miss.
- APScheduler inside the backend: fewer containers, but couples scheduling to web process lifecycle and weakens worker separation.
- Celery beat with distributed locking from day one: more scalable, but unnecessary for the current single-scheduler VPS deployment.
