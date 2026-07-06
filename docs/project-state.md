# Project State

Last updated: 2026-07-06

This file is the compact operational state for agents. Use it to orient quickly before reading detailed specs, ADRs, implementation history, or code.

## Current Work

- Active branch: `codex/gh-outside-sandbox-policy`
- Active spec: no product spec; repository workflow policy for managed sandbox GitHub operations
- Current state: `SPEC-301` is merged into `main` through PR #5; PR #6 adds the managed-sandbox policy requiring network-backed `gh` commands to use outside-sandbox execution from the first attempt.
- Documentation checkpoint: agent operational memory was restructured on 2026-06-16 with this file, central touch-to-spec routing, per-spec scope/context blocks, and `ADR-005`; on 2026-06-24 the base workflow added review-gated memory checks and implementation-log scaffolding targets; `ADR-009` records the managed-sandbox GitHub CLI policy
- Recent validation recorded in `docs/implementation-log.md`: PR #5 passed the full GitHub Actions `Verify` workflow at memory checkpoint `99ee74d` before merging as `8225e6f`; the managed-sandbox policy passed its documentation reference checks, memory check, diff check, and elevated authentication/scope check.
- Current validation baseline: `SPEC-301` production and local Docker validation passed, and the merged workflow runs the complete `make verify` harness with PostgreSQL; PR #6 requires the same CI after this main reconciliation.

## Next Handoff

- Next role: Integrator
- Next likely integration work: validate and review the reconciled PR #6, confirm CI, then merge the repository workflow policy into `main`.
- Keep `SPEC-301` expanding when Redis/worker services become real through `SPEC-201`.

## Implemented Specs

| Spec | Scope | Primary surfaces | Latest state |
|---|---|---|---|
| `SPEC-010` | Backend scaffold, local PostgreSQL, Alembic, Make harness | `backend/`, `docker-compose.yml`, `Makefile`, `.env.example` | Implemented and approved through later validation |
| `SPEC-011` | Local Adminer database inspection | `docker-compose.yml`, `.env.example`, `README.md`, harness docs | Implemented and review approved |
| `SPEC-101` | Backend auth and users | `backend/app`, `backend/tests`, Alembic migration `0002`, `.env.example` | Implemented and review approved after endpoint-level API tests |
| `SPEC-002` | Human-readable code comments and initial comment pass | Existing backend/frontend source files, future source changes | Implemented and review approved |
| `SPEC-104` | React app shell and auth/profile UI | `frontend/`, `Makefile`, `docker-compose.yml`, `.env.example`, `README.md` | Implemented, reviewed, and merged locally to `main` |
| `SPEC-102` | Single-owner organizations, ownership transfer, permanent deletion, and RBAC | Organization backend, migrations `0003`/`0004`, tests, `ADR-007` | Implemented and review approved |
| `SPEC-103` | Projects and tasks backend | Project/task backend, migration `0005`, endpoint tests | Implemented and review approved |
| `SPEC-105` | Frontend organizations UI | Organization routes, shell navigation, organization API hooks, frontend tests | Implemented and review approved |
| `SPEC-106` | Frontend projects and tasks UI | Project/task routes, forms, filters, pagination, assignment UI, frontend tests | Implemented and review approved |
| `SPEC-301` | Production deployment and operations | Production Compose, Caddy, CI, isolated smoke, deployment docs, tested backup/restore, `ADR-008` | Implemented and review approved |

## Draft Specs

| Spec | Scope | Blocker |
|---|---|---|
| `SPEC-201` | Background jobs and notifications | Task assignment events now exist; broker, retry, local adapter, persistence, and Compose ownership decisions remain open |

## Next Likely Work

1. Merge PR #6 after its updated memory and GitHub Actions verification pass review.
2. Add Playwright coverage in a dedicated follow-up after the deployment harness is integrated.
3. Prepare `SPEC-201` decisions and move it to Ready before implementing Redis/Celery.

## Known Gaps

- `SPEC-104` has no Playwright E2E tests yet; the spec intentionally recommends adding them after the frontend/local server harness stabilizes.
- `SPEC-106` has route-level/component coverage but still has no Playwright E2E critical path; the spec recommends adding Playwright after organization/project/task UI stabilizes.
- `SPEC-201` remains Draft.
- Public production deployment is documented but not yet executed against a real VPS/domain.
- Redis and worker production services remain deferred until `SPEC-201`.

## Validation Baseline

- Latest recorded full local verification: `make verify` PASS for `SPEC-301` on 2026-06-30, run with elevated host PostgreSQL access after the sandboxed migration step failed to connect to localhost.
- Latest review-fix validation: `make prod-config`, `make prod-smoke`, `make prod-down`, `make smoke`, `make migrations-check-compose`, `make verify-no-db`, `npm run build` from `frontend/`, URL-encoded SQLAlchemy URL parse check, `make memory-check SPEC=SPEC-301`, and `git diff --check` PASS on 2026-07-06. The pushed GitHub Actions run then passed the complete `make verify` harness with PostgreSQL at commit `2a36558`.
- Latest recorded sandbox-friendly frontend validation: `make test-frontend`, `make lint`, `make format-check`, and `make typecheck` PASS for `SPEC-106` pagination review fix on 2026-06-30.
- Latest recorded smoke check: isolated `make prod-smoke` and `make prod-down` PASS for the completed `SPEC-301` review fix on 2026-07-02.
- Latest final review: `SPEC-301` APPROVED on 2026-07-06 after re-review of production database URL handling, full CI migration coverage, production/local Docker smoke, backup/restore smoke, validation evidence, ADR, and project memory.
- Memory harness baseline: `make memory-check SPEC=SPEC-301` verifies that project memory mentions the active spec and that the newest implementation-log entry includes required handoff sections.
- Use `specs/harness/local-validation.md` for current command meanings and expected coverage.

## Code Map

| Area | Purpose |
|---|---|
| `backend/app/api` | FastAPI routers and API entry points |
| `backend/app/core` | Settings and cross-cutting backend configuration |
| `backend/app/db` | SQLAlchemy base, engine/session, database dependencies |
| `backend/app/models` | SQLAlchemy persistence models |
| `backend/app/repositories` | Data access boundaries |
| `backend/app/schemas` | Pydantic request/response contracts |
| `backend/app/services` | Business logic and policy enforcement |
| `backend/tests` | Backend unit, integration, API, and migration-related tests |
| `frontend/src/app` | Router, app shell, providers, route guards |
| `frontend/src/features/auth` | Login, signup, session bootstrap, logout behavior |
| `frontend/src/features/organizations` | Organization/workspace UI, member/admin UI, API hooks, and active organization route support for `SPEC-105` |
| `frontend/src/features/projects` | Project API hooks, paginated list/detail/settings/create routes, and SPEC-106 route tests |
| `frontend/src/features/tasks` | Task API hooks, URL-backed pagination/filters, assignment controls, create/update forms, and SPEC-106 route tests |
| `frontend/src/features/profile` | Current-user profile display and update flow |
| `frontend/src/shared` | Shared API client, UI primitives, test helpers, utilities |

## Agent Reading Order

For implementation or review:

1. `AGENTS.md`
2. `docs/project-state.md`
3. `specs/README.md`
4. Relevant active feature spec
5. `specs/001-api-conventions.md` for API work
6. `specs/harness/local-validation.md`
7. Relevant ADRs from `docs/decisions/`
8. Recent entries in `docs/implementation-log.md` only when validation or history needs confirmation

## Related Decisions

- `docs/decisions/ADR-005-agent-operational-memory.md`
- `docs/decisions/ADR-006-human-readable-code-comments.md`
- `docs/decisions/ADR-007-tenant-isolation-and-rbac-enforcement.md`
- `docs/decisions/ADR-008-production-compose-and-caddy.md`
- `docs/decisions/ADR-009-managed-sandbox-github-cli.md`
