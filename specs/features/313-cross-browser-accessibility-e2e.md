# SPEC-313 — Cross-Browser And Accessibility E2E Hardening

Status: Implemented
Owner: Arquitecto de specs
Last updated: 2026-09-07

## Scope And Required Context

This spec governs:

- Playwright browser coverage beyond Chromium-only execution.
- Accessibility checks for recruiter-visible and app-critical workflows.
- `frontend/e2e/`, `frontend/playwright.config.ts`, E2E helper code, CI E2E job configuration, Playwright artifacts, and harness documentation when E2E behavior changes.

Required context:

- `AGENTS.md`
- `docs/project-state.md`
- `specs/README.md`
- `specs/000-product-vision.md`
- `specs/001-api-conventions.md`
- `specs/harness/local-validation.md`
- `specs/features/104-frontend-app-shell-and-auth-ui.md`
- `specs/features/106-frontend-projects-and-tasks-ui.md`
- `specs/features/305-project-clients-and-tickets.md`
- `specs/features/306-in-app-notifications.md`
- `specs/features/311-public-portfolio-home.md`
- `specs/features/312-playwright-e2e-expansion.md`

Memory updates:

- `docs/project-state.md` when E2E coverage, validation baseline, next work, or known gaps change
- `docs/implementation-log.md` for meaningful spec-prep, implementation, review, validation, or merge events
- `specs/README.md` when status, dependencies, order, or primary surfaces change
- ADRs only if CI topology, browser support policy, or accessibility tooling strategy changes beyond this spec

## Problem

`SPEC-312` established useful browser coverage, but it intentionally left Firefox, WebKit, dedicated accessibility checks, and visual regression coverage outside scope. The portfolio app now has enough product surface that browser compatibility and accessibility regressions can reduce demo confidence even when unit tests pass.

## Goals

- Add Playwright smoke coverage for Firefox and WebKit on the highest-value user journeys.
- Add automated accessibility checks for public portfolio pages and authenticated app-critical pages.
- Keep Chromium as the full functional E2E project while adding smaller cross-browser coverage to control CI runtime.
- Preserve existing E2E artifact behavior and upload diagnostics on CI failure.
- Add a clear harness target or documented project selection for cross-browser/accessibility checks.

## Non-Goals

- Replacing component tests or existing Chromium E2E coverage.
- Guaranteeing pixel-perfect layout across browsers.
- Full WCAG certification or manual accessibility audit.
- Production-site monitoring against `https://rgalvaro.es/`.
- Adding broad visual snapshot testing in this spec.
- Changing product behavior solely to satisfy test selectors.

## Actors And Permissions

| Actor | Permission | Notes |
|---|---|---|
| Anonymous visitor | Exercise public home, changelog, login, and protected-route redirect checks | No privileged state |
| Authenticated internal user | Exercise core app shell, organization/project/task navigation, notifications, and logout | Test data must be unique per run |
| Authenticated client user | Exercise restricted client ticket shell in at least one Chromium accessibility path | Client setup may use existing product APIs through the UI when practical |
| CI runner | Run browser and accessibility checks without production secrets | Must preserve failure artifacts |
| Developer/review agent | Run the documented local E2E targets | Managed sandbox Docker execution requires elevation from the first attempt |

## Business Rules

- BR-1: Chromium remains the full-suite browser unless a later spec changes the cost/stability policy.
- BR-2: Firefox and WebKit run smoke journeys only: public route load, auth redirect, login/logout, and one core authenticated workflow.
- BR-3: Accessibility checks must run against rendered pages using browser automation, not static-only linting.
- BR-4: Accessibility failures must identify the route and rule violation in CI artifacts or test output.
- BR-5: Tests must use accessible selectors where available and must not depend on direct database writes.
- BR-6: E2E test data must use unique run identifiers and avoid leaking passwords, cookies, or tokens.
- BR-7: Visual snapshot testing remains future scope unless implementation proves it is stable, narrowly scoped, and separately documented.
- BR-8: Cross-browser checks may be excluded from default `make verify` if runtime is materially higher, but they must have a canonical local and CI entry point.

## Data Model Impact

No database schema changes are required.

## API Contract

No API endpoints are added or changed.

The tests continue to exercise existing public API behavior through the browser app. Any surfaced API errors must continue following `specs/001-api-conventions.md`.

## Frontend Impact

- Extend Playwright configuration with Firefox and WebKit projects.
- Add an accessibility helper using a proven browser accessibility tool such as `@axe-core/playwright`.
- Cover at minimum:
  - public portfolio home
  - public changelog
  - login page
  - authenticated app shell
  - organization/project/task critical path
  - notifications inbox
  - client ticket list or ticket creation path where practical
- Keep generated Playwright reports, traces, screenshots, videos, and accessibility artifacts uncommitted.

## Acceptance Criteria

- AC-1: Given the cross-browser E2E target runs, then Firefox and WebKit each complete public route, protected-route redirect, login, app-shell, and logout smoke coverage.
- AC-2: Given Chromium full-suite E2E runs, then the existing `SPEC-312` critical paths continue to pass.
- AC-3: Given accessibility checks run on public pages, then violations above the configured severity threshold fail the test with route-specific output.
- AC-4: Given accessibility checks run on authenticated app pages, then app shell, notifications, and task/project workflow pages are scanned after data has loaded.
- AC-5: Given E2E checks fail in CI, then Playwright artifacts are uploaded without exposing secrets.
- AC-6: Given a developer runs the documented command, then it executes the same browser/accessibility projects used by CI or documents any intentional local/CI split.
- AC-7: Given tests run on mobile Chromium, then existing mobile critical-path coverage remains active and text/control overflow regressions remain observable.

## Harness Requirements

Required tests/checks:

- Playwright projects for Firefox and WebKit smoke coverage.
- Playwright accessibility tests using rendered UI.
- Existing Chromium desktop and mobile E2E projects remain passing.
- Frontend unit tests remain passing.
- Harness docs updated if commands or CI jobs change.

Required commands:

```bash
make test-e2e
make test-frontend
make lint
make format-check
make typecheck
make memory-check SPEC=SPEC-313
```

If a new target is added, for example `make test-e2e-a11y` or `make test-e2e-cross-browser`, record it in `specs/harness/local-validation.md` and implementation memory.

## Observability And Failure Cases

- Accessibility output must identify route, browser project, rule id, and affected selector where the tool supports it.
- Browser-specific failures must be reported as product/test failures only after rerun or clear deterministic evidence.
- Docker socket, browser-image pull, or sandbox failures are environment constraints unless reproduced outside the sandbox.

## Open Questions

- [x] Should Firefox/WebKit run the full Chromium suite? No. Start with smoke coverage to limit CI runtime and flake rate.
- [x] Should visual snapshots be included now? No. Keep them future scope until the app has stable visual baselines and a narrower spec.
- [x] Should accessibility require manual WCAG certification? No. This spec adds automated checks only.

## Implementation Notes

- Prefer one shared helper for unique users and setup once multiple browser projects need the same data.
- Prefer severity filtering for accessibility checks only if noisy low-impact findings would otherwise block useful coverage; document the threshold.
- Keep CI artifacts on failure only unless an implementation needs temporary debugging output.
