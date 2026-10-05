# SPEC-319 — EventFlow portfolio card

Status: Implemented
Owner: Arquitecto de specs
Last updated: 2026-10-05

## Scope

Replace the second project panel on the public `/` portfolio page with EventFlow. This spec supersedes SPEC-318's ERP-specific copy and link requirements for that panel; the rest of SPEC-318's layout and public navigation remain in force.

## Evidence and truthful presentation

The `RGAlvaro/eventflow` repository is the source for project claims. Its `docs/project-state.md` and implemented code/tests show event ingestion, a PostgreSQL outbox, Celery/Redis delivery, recovery, HTTPS destination checks, and HMAC-signed webhooks as of 2026-10-05. Its README lags that state. There is no frontend or public demo. Link to `https://github.com/RGAlvaro/eventflow` as source code only.

## Requirements

- Keep the second panel smaller than the featured OpsDesk panel, after the process strip and before the footer.
- Show the name EventFlow, a brief English description of the implemented event-to-webhook path, and a clear `Code available` status. Do not imply that a live app is available.
- Include a small conceptual thumbnail illustrating event ingestion, durable storage, worker delivery, and a signed webhook. It must read as an illustration rather than an actual interface screenshot. Provide decorative-image accessibility treatment.
- Keep the existing portfolio visual language, keyboard focus, and responsive layout at 390, 768, and 1440 px without horizontal overflow.
- Preserve OpsDesk actions and public changelog/legal links.

## Acceptance criteria

- AC-1: The second project region is named EventFlow and follows the process section.
- AC-2: Its copy mentions event ingestion and signed webhook delivery, with current state accurately described; it does not claim a frontend or public demo.
- AC-3: The conceptual thumbnail is present, decorative for assistive technology, and readable at mobile and desktop sizes.
- AC-4: `View repository` points to the public EventFlow repository; no live-demo link appears.
- AC-5: Existing public routes and OpsDesk entry points still work, with no horizontal overflow at 390, 768, or 1440 px.

## Validation

Update the landing route test and browser portfolio test. Run frontend tests, lint, format, typecheck, build, browser checks where available, `make memory-check SPEC=SPEC-319`, and `git diff --check`. Record unrun checks explicitly.

No backend, schema, environment, or deployment-topology change is required. Production publication follows the existing SPEC-307 release workflow and changelog gate.
