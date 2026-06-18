# Project State

Last updated: 2026-06-18

This file is the compact operational state for agents. Use it to orient quickly before reading detailed specs, ADRs, implementation history, or code.

## Current Work

- Active branch: `codex/spec-102-organizations-rbac`
- Active spec: `SPEC-102` organizations and RBAC revision is implemented and review approved
- Current state: `SPEC-102` enforces one owner, atomic ownership transfer, owner-only permanent deletion, and tenant-isolated RBAC APIs
- Documentation checkpoint: agent operational memory was restructured on 2026-06-16 with this file, central touch-to-spec routing, per-spec scope/context blocks, and `ADR-005`
- Recent validation recorded in `docs/implementation-log.md`: `SPEC-102` passed `make smoke` and full `make verify` with live PostgreSQL migration checks
- Current `SPEC-102` validation: full `make verify`, live migration `0004`, Docker smoke, and PostgreSQL concurrent-transfer coverage pass

## Implemented Specs

| Spec | Scope | Primary surfaces | Latest state |
|---|---|---|---|
| `SPEC-010` | Backend scaffold, local PostgreSQL, Alembic, Make harness | `backend/`, `docker-compose.yml`, `Makefile`, `.env.example` | Implemented and approved through later validation |
| `SPEC-011` | Local Adminer database inspection | `docker-compose.yml`, `.env.example`, `README.md`, harness docs | Implemented and review approved |
| `SPEC-101` | Backend auth and users | `backend/app`, `backend/tests`, Alembic migration `0002`, `.env.example` | Implemented and review approved after endpoint-level API tests |
| `SPEC-002` | Human-readable code comments and initial comment pass | Existing backend/frontend source files, future source changes | Implemented and review approved |
| `SPEC-104` | React app shell and auth/profile UI | `frontend/`, `Makefile`, `docker-compose.yml`, `.env.example`, `README.md` | Implemented, reviewed, and merged locally to `main` |
| `SPEC-102` | Single-owner organizations, ownership transfer, permanent deletion, and RBAC | Organization backend, migrations `0003`/`0004`, tests, `ADR-007` | Implemented and review approved |

## Ready Specs Not Yet Implemented

| Spec | Scope | Depends on | Expected next surfaces |
|---|---|---|---|
| `SPEC-103` | Projects and tasks backend | `SPEC-102` | Backend models, migration, task/project services, API routes, tests |
| `SPEC-301` | Production deployment and operations | `SPEC-010`, then evolving services | Production Compose, Caddy, deployment docs, backup/restore docs |

## Draft Specs

| Spec | Scope | Blocker |
|---|---|---|
| `SPEC-201` | Background jobs and notifications | Should wait until task assignment and notification-worthy events exist |

## Next Likely Work

1. Implement `SPEC-103` backend projects and tasks.
2. Prepare frontend organization/product UI specs after project/task APIs exist.
3. Expand `SPEC-301` as frontend, backend, database, Redis, and worker services become real.

## Known Gaps

- `SPEC-104` has no Playwright E2E tests yet; the spec intentionally recommends adding them after the frontend/local server harness stabilizes.
- Organization, project, and task UI is intentionally unavailable until backend APIs and frontend specs support it.
- `SPEC-201` remains Draft.
- CI and public production deployment are not complete yet.

## Validation Baseline

- Latest recorded full local verification: `make verify` PASS for `SPEC-102` on 2026-06-18, run with Docker/PostgreSQL access.
- Latest recorded smoke check: `make smoke` PASS for `SPEC-102` on 2026-06-18.
- Latest final review: `SPEC-102` APPROVED on 2026-06-18 after adding AC-15 member deletion coverage.
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
