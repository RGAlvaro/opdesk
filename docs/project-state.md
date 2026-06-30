# Project State

Last updated: 2026-06-30

This file is the compact operational state for agents. Use it to orient quickly before reading detailed specs, ADRs, implementation history, or code.

## Current Work

- Active branch: `main`
- Active spec: `SPEC-106` frontend projects and tasks UI is review approved
- Current state: `SPEC-106` adds project/task routes, forms, filters, assignment UI, route navigation, cache handling, frontend tests, and URL-backed project/task pagination with `limit`/`offset` request parameters; pagination review fix has been re-reviewed and approved
- Documentation checkpoint: agent operational memory was restructured on 2026-06-16 with this file, central touch-to-spec routing, per-spec scope/context blocks, and `ADR-005`; on 2026-06-24 the base workflow added review-gated memory checks and implementation-log scaffolding targets
- Recent validation recorded in `docs/implementation-log.md`: `SPEC-106` pagination review fix re-review passed `make test-frontend`, `make lint`, `make format-check`, `make typecheck`, `make smoke`, `make memory-check SPEC=SPEC-106`, and `git diff --check` on 2026-06-30
- Current validation baseline: required frontend implementation checks and Docker smoke passed for `SPEC-106` on 2026-06-30; latest live migration validation remains the `SPEC-103` baseline from 2026-06-23 because `SPEC-106` is frontend-only

## Next Handoff

- Next role: Arquitecto de specs or Ingeniero de software
- Next likely implementation work: revisit `SPEC-201` after task assignment notification events are available, or continue `SPEC-301` deployment work.
- Keep `SPEC-301` expanding as deployment surfaces become real.

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

## Ready Specs Not Yet Implemented

| Spec | Scope | Depends on | Expected next surfaces |
|---|---|---|---|
| `SPEC-301` | Production deployment and operations | `SPEC-010`, then evolving services | Production Compose, Caddy, deployment docs, backup/restore docs |

## Draft Specs

| Spec | Scope | Blocker |
|---|---|---|
| `SPEC-201` | Background jobs and notifications | Should wait until task assignment and notification-worthy events exist |

## Next Likely Work

1. Revisit `SPEC-201` after task assignment notification events are specified through the task UI.
2. Expand `SPEC-301` as frontend, backend, database, Redis, and worker services become real.

## Known Gaps

- `SPEC-104` has no Playwright E2E tests yet; the spec intentionally recommends adding them after the frontend/local server harness stabilizes.
- `SPEC-106` has route-level/component coverage but still has no Playwright E2E critical path; the spec recommends adding Playwright after organization/project/task UI stabilizes.
- `SPEC-201` remains Draft.
- CI and public production deployment are not complete yet.

## Validation Baseline

- Latest recorded full local verification: `make verify` PASS for `SPEC-103` on 2026-06-23, run outside sandbox for PostgreSQL migration access.
- Latest recorded sandbox-friendly frontend validation: `make test-frontend`, `make lint`, `make format-check`, and `make typecheck` PASS for `SPEC-106` pagination review fix on 2026-06-30.
- Latest recorded smoke check: `make smoke` PASS for `SPEC-106` pagination review fix on 2026-06-30.
- Latest final review: `SPEC-106` APPROVED on 2026-06-30 after re-review of project/task pagination hooks, controls, URL state, tests, validation evidence, and project memory.
- Memory harness baseline: `make memory-check SPEC=SPEC-106` verifies that project memory mentions the active spec and that the newest implementation-log entry includes required handoff sections.
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
