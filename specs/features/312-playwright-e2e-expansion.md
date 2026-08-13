# SPEC-312 — Playwright E2E Expansion

Status: Implemented
Owner: Ingeniero de software
Last updated: 2026-08-13

## Scope And Required Context

This spec governs:

- Expanding Playwright browser coverage beyond the initial critical path.
- `frontend/e2e/`, `frontend/playwright.config.ts`, frontend E2E test helpers, and E2E artifact handling.
- `Makefile`, Docker Compose E2E runner wiring, GitHub Actions verification, and harness documentation when E2E command behavior changes.
- Browser viewport/project selection for desktop and mobile E2E checks.

Required context:

- `AGENTS.md`
- `docs/project-state.md`
- `specs/README.md`
- `specs/000-product-vision.md`
- `specs/001-api-conventions.md`
- `specs/harness/local-validation.md`
- `specs/features/101-auth-and-users.md`
- `specs/features/104-frontend-app-shell-and-auth-ui.md`
- `specs/features/105-frontend-organizations-ui.md`
- `specs/features/106-frontend-projects-and-tasks-ui.md`
- `specs/features/309-project-task-labels.md`
- `specs/features/311-public-portfolio-home.md`

Memory updates:

- `docs/project-state.md` when E2E coverage, validation baseline, next work, or known gaps change
- `docs/implementation-log.md` for meaningful spec-prep, implementation, review, validation, or merge events
- `specs/README.md` when status, dependencies, order, or primary surfaces change
- ADRs only if CI topology, browser support policy, or test data strategy changes in a durable cross-cutting way

## Problem

OpsDesk now has one Playwright critical path that proves a signed-up user can create an organization, project, task, and mark that task done. That is useful but narrow. The frontend still lacks browser-level coverage for auth route protection, logout, profile editing, task filters, label filtering, mobile layout behavior, and CI integration. These are high-value regression surfaces because they combine routing, cookie-backed auth, backend APIs, Docker networking, and responsive UI behavior.

## Goals

- Add browser-level coverage for login/logout and protected-route behavior from `SPEC-104`.
- Add browser-level coverage for profile editing from `SPEC-104` and enriched metadata from `SPEC-308` where the current UI exposes it.
- Add browser-level coverage for task list filters, URL query persistence, and task label filtering from `SPEC-106` and `SPEC-309`.
- Run the existing critical path on both desktop Chromium and a mobile Chromium viewport.
- Keep E2E data isolated with unique test-run identifiers and avoid relying on manual database cleanup.
- Add an optional CI job or workflow step for E2E checks without making normal `make verify` unexpectedly slower or dependent on browser containers.
- Keep Playwright artifacts ignored locally and uploaded only on CI failure if CI integration is added.

## Non-Goals

- Replacing Vitest/React Testing Library route and component tests.
- Full cross-browser support for Firefox and WebKit in this phase.
- Visual snapshot testing.
- Accessibility audits beyond assertions naturally made through roles, labels, and keyboard-reachable controls.
- Testing production `https://rgalvaro.es/` directly.
- Adding seed-only or test-only product APIs.
- Solving npm audit advisories unless the implementation proves they affect production runtime or block CI.

## Actors And Permissions

| Actor | Permission | Notes |
|---|---|---|
| Anonymous visitor | Exercise public routes and protected-route redirects in E2E tests | No backend access beyond public endpoints |
| Authenticated user | Exercise profile, organization, project, task, label, and logout flows | Test users must be unique per run |
| Organization owner | Create and manage project/task/label test data | The first user in an empty local DB may be superuser, but E2E assertions must rely on organization role behavior, not superuser-only behavior |
| CI runner | Run optional E2E job against local Docker services | Must not require production secrets |
| Developer/review agent | Run `make test-e2e` locally with Docker access | Managed sandbox runs require elevated Docker execution from the first attempt |

## Business Rules

- BR-1: E2E tests must use the public browser UI and public backend API behavior; they must not mutate the database directly.
- BR-2: E2E test data must include a unique run suffix for user emails and user-created records.
- BR-3: E2E tests must not log passwords, cookies, tokens, raw auth headers, or sensitive request payloads.
- BR-4: E2E tests must assert user-visible outcomes, stable route changes, and safe errors rather than internal React Query state.
- BR-5: E2E tests must prefer accessible selectors such as roles, labels, headings, and navigation names.
- BR-6: The desktop and mobile projects must cover the same critical path unless implementation records a concrete unsupported mobile blocker.
- BR-7: CI E2E execution, if added, must be a distinct job or explicitly named step so browser failures are easy to diagnose separately from unit/backend verification.
- BR-8: `make verify` must not start running E2E by default in this spec unless the spec is explicitly updated after observed stability and runtime cost are acceptable.
- BR-9: Playwright reports, traces, screenshots, videos, and test results remain uncommitted artifacts.
- BR-10: E2E tests may leave uniquely named local records behind; they must not require destructive cleanup or assume an empty database.

## Data Model Impact

No database schema changes are required.

Implementation may create local test records through existing product APIs:

- Users through `POST /api/v1/auth/register`
- Organizations through existing organization UI/API
- Projects through existing project UI/API
- Tasks through existing task UI/API
- Labels through existing task label UI/API

No migrations are required.

## API Contract

No API endpoints are added or changed.

E2E implementation must continue to use existing API contracts through the browser app:

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/logout`
- `GET /api/v1/users/me`
- `PATCH /api/v1/users/me`
- Existing organization, project, task, and task-label APIs from `SPEC-102`, `SPEC-103`, `SPEC-308`, and `SPEC-309`

Errors must remain rendered according to `specs/001-api-conventions.md`.

## Frontend Impact

- Add focused Playwright specs under `frontend/e2e/`.
- Factor common E2E helpers only when it removes meaningful duplication across tests, such as unique user signup/login or common organization/project/task setup.
- Extend Playwright projects to include:
  - desktop Chromium
  - mobile Chromium viewport, for example a Pixel-class device profile
- Keep the E2E runner Dockerized through Compose unless a later ADR changes the browser execution strategy.
- If CI integration is added, store traces/screenshots/videos as CI artifacts only on failure.
- Do not add visible app text solely to make tests easier.

## Acceptance Criteria

- AC-1: Given an anonymous browser opens `/app`, `/app/profile`, and one project/task route with no session, then the UI redirects to `/login` without exposing protected content.
- AC-2: Given an existing E2E user logs in with valid credentials, then the app shell renders the user's safe identity context and reaches `/app`.
- AC-3: Given an authenticated E2E user logs out, then the UI returns to the public home and a subsequent protected route visit redirects to `/login`.
- AC-4: Given an authenticated E2E user updates their profile full name or currently implemented profile metadata, then the saved value is visible after navigation or refresh.
- AC-5: Given E2E-created project tasks with different status, priority, due date, and label values, when filters are applied from the task list, then only matching tasks are visible and the URL query parameters reflect the selected filters.
- AC-6: Given the filtered task list URL is reloaded, then the selected filters and filtered results persist.
- AC-7: Given the existing critical signup-to-completed-task flow runs on desktop Chromium, then it still passes.
- AC-8: Given the existing critical signup-to-completed-task flow runs on a mobile Chromium viewport, then primary actions remain reachable, text does not overflow materially, and the flow still passes.
- AC-9: Given E2E checks fail in CI, then Playwright artifacts are available for diagnosis without being committed to the repository.
- AC-10: Given a developer runs `make test-e2e`, then the command remains the canonical local E2E entry point and uses the Docker/local stack.

## Harness Requirements

Required tests/checks:

- Playwright E2E tests for auth protection, login, logout, and post-logout protected-route redirect.
- Playwright E2E test for profile update persistence.
- Playwright E2E test for task filter URL persistence, including label filtering if label UI is available in the current implementation.
- Playwright desktop and mobile projects for the existing critical path.
- Existing frontend unit/route tests must remain passing.
- No migration checks are required beyond the existing `make test-e2e` behavior that applies and checks Alembic inside Compose before browser execution.

Required commands:

```bash
make test-e2e
make test-frontend
make lint
make format-check
make typecheck
make smoke
make memory-check SPEC=SPEC-312
```

If CI integration is implemented:

```bash
# exact command or GitHub Actions run evidence from the implementation
```

## Observability And Failure Cases

- Playwright traces, screenshots, and videos should be retained on failure only unless debugging locally.
- CI failure artifacts must not include cookies, tokens, passwords, or raw auth headers.
- Network, Docker socket, or host PostgreSQL sandbox failures must be reported as environment constraints, not product regressions, unless reproduced outside the sandbox.
- E2E tests should fail with specific route, selector, or assertion context that identifies the affected flow.
- Browser checks must not depend on test execution order.

## Open Questions

- [x] Should Firefox/WebKit be added in this phase? No. Keep this phase focused on Chromium desktop and Chromium mobile viewport for stability and runtime.
- [x] Should E2E be added to `make verify` immediately? No. Keep `make test-e2e` separate while runtime and flake rate are still being observed.
- [x] Should E2E run in CI? Yes, but as a distinct optional job or explicitly named workflow step with artifacts on failure, not hidden inside the existing verify step.
- [x] Should E2E tests use direct database cleanup? No. Use unique test data and existing product APIs.

## Implementation Notes

- Prefer a small helper module such as `frontend/e2e/helpers.ts` only after at least two specs need the same setup.
- Use unique email prefixes like `e2e-<timestamp>-<random>@example.com`.
- Prefer route assertions with `expect(page).toHaveURL(...)` after major navigation.
- Prefer `getByRole`, `getByLabel`, and scoped `getByRole("navigation", { name: "Primary navigation" })` selectors.
- When adding CI, consider whether the Playwright Docker image should run through Compose or whether GitHub-hosted Ubuntu can run `npx playwright install --with-deps chromium`; document the chosen route in implementation memory.
