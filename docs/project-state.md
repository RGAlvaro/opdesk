# Project State

Last updated: 2026-07-15

This file is the compact operational state for agents. Use it to orient quickly before reading detailed specs, ADRs, implementation history, or code.

## Current Work

- Active branch: `codex/spec-predeployment-planning`
- Active spec: `SPEC-302`
- Current state: `SPEC-302` is a new Draft predeployment UI stabilization spec. The first captured defect is that after creating an organization, left-panel `Organizations`, `Projects`, and `Tasks` clicks route to organizations and highlight all three entries instead of routing and marking active state independently. Draft follow-up product specs now capture member invites/project access (`SPEC-303`), Slack-like organization/project chat (`SPEC-304`), project clients/client tickets (`SPEC-305`), and in-app notifications (`SPEC-306`). This planning branch is based on `main`; the separate `SPEC-201` implementation branch remains outside this branch until merged.
- Documentation checkpoint: agent operational memory was restructured on 2026-06-16 with this file, central touch-to-spec routing, per-spec scope/context blocks, and `ADR-005`; on 2026-06-24 the base workflow added review-gated memory checks and implementation-log scaffolding targets; `ADR-009` records the managed-sandbox GitHub CLI policy
- Recent validation recorded in `docs/implementation-log.md`: PR #5 passed the full GitHub Actions `Verify` workflow before merging as `8225e6f`; PR #6 passed the complete workflow at final head `fb1f5a6` before merging as `c1a730b`.
- Current validation baseline: `SPEC-301` production and local Docker validation passed; the integrated repository passes `make verify` with PostgreSQL, frontend build, and production Compose config validation in CI.

## Next Handoff

- Next role: Arquitecto de specs
- Next likely integration work: decide whether only `SPEC-302` blocks deployment or whether `SPEC-303`/`SPEC-304`/`SPEC-305`/`SPEC-306` should also be implemented first. Then move the chosen active spec(s) from Draft to Ready before implementation.
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

| Spec | Scope | Primary surfaces | Latest state |
|---|---|---|---|
| `SPEC-201` | Background jobs and notifications | Redis/Celery worker, notification models, tests | Draft in the `main` base; implementation is isolated on `codex/spec-201-background-jobs` until merged |
| `SPEC-302` | Predeployment UI stabilization and small corrections/additions | App shell navigation, organization/project/task frontend routes, frontend regression tests | Draft created with left-panel Organizations/Projects/Tasks routing and active-state defect captured |
| `SPEC-303` | Member invitations by email and project-level access | Organization members, project members, invite APIs, migrations, frontend management UI | Draft updated: existing-user invitations require in-app acceptance; project membership restricts task assignment |
| `SPEC-304` | Organization member chat | Chat persistence, chat APIs, organization chat UI, shared-project member ordering | Draft updated for Slack-like direct, group, organization channel, and project channel chat |
| `SPEC-305` | Project clients and client-created tickets | Client project contacts, ticket-as-task API/UI, migrations | Draft updated: clients are lightweight contacts and tickets live in `tasks` with a type/source and distinct UI label/color |
| `SPEC-306` | In-app notifications | Notification models, APIs, inbox UI, invitation/state/chat notification fan-out | Draft created for persistent in-app notifications and actionable invitation notifications |

## Next Likely Work

1. Decide predeployment scope: `SPEC-302` only, or `SPEC-302` plus one or more product additions from `SPEC-303`/`SPEC-304`/`SPEC-305`/`SPEC-306`.
2. Resolve open questions and mark the chosen active spec Ready.
3. Implement the chosen active spec before public deployment.
4. Continue `SPEC-201` PR/CI integration on its separate implementation branch.
5. Execute the documented VPS/domain deployment when public launch work is prioritized.

## Known Gaps

- `SPEC-104` has no Playwright E2E tests yet; the spec intentionally recommends adding them after the frontend/local server harness stabilizes.
- `SPEC-106` has route-level/component coverage but still has no Playwright E2E critical path; the spec recommends adding Playwright after organization/project/task UI stabilizes.
- `SPEC-201` remains Draft in this branch because the reviewed implementation is isolated on `codex/spec-201-background-jobs`.
- `SPEC-302` is Draft; current open questions are additional predeployment corrections/additions, the intended Tasks left-panel target, and whether project/task shortcuts should disable or route to empty states before context exists.
- `SPEC-303`, `SPEC-304`, `SPEC-305`, and `SPEC-306` are Draft product additions with unresolved admin-invite permissions, project visibility, chat transport, client ticket form access, notification retention, and notification recipient rules.
- Public production deployment is documented but not yet executed against a real VPS/domain.
- Redis and worker production services remain deferred on this branch until `SPEC-201` is merged.

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
| `frontend/src/features/organizations` | Organization/workspace UI, member/admin UI, organization API hooks, and active organization route support for `SPEC-105` |
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
