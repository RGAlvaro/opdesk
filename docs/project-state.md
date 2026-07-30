# Project State

Last updated: 2026-07-30

This file is the compact operational state for agents. Use it to orient quickly before reading detailed specs, ADRs, implementation history, or code.

## Current Work

- Active branch: `main`
- Active spec: `SPEC-307` reviewed; `SPEC-308`, `SPEC-309`, `SPEC-310`, and `SPEC-311` planning
- Current state: `SPEC-307` release automation was re-reviewed and approved on 2026-07-30 after the pre-backup data-service recreation fix; first real workflow run remains pending until GitHub Actions production secrets are configured. Product follow-up planning on 2026-07-28 added Ready specs for enriched profile/company/project/task metadata (`SPEC-308`), project-scoped task labels (`SPEC-309`), and production release changelog (`SPEC-310`), plus Draft static portfolio home planning (`SPEC-311`). `SPEC-102`/`SPEC-105` now define organization slug as backend-generated and non-editable with numeric collision suffixing. Production is available at `https://rgalvaro.es/` and `https://www.rgalvaro.es/`; the temporary `https://opdesk.51.255.202.88.sslip.io/` hostname remains configured as a fallback.
- Documentation checkpoint: agent operational memory was restructured on 2026-06-16 with this file, central touch-to-spec routing, per-spec scope/context blocks, and `ADR-005`; on 2026-06-24 the base workflow added review-gated memory checks and implementation-log scaffolding targets; `ADR-009` records the managed-sandbox GitHub CLI policy.
- Recent validation recorded in `docs/implementation-log.md`: `SPEC-307` re-review validation on 2026-07-30 passed `make release-workflow-check`, `make memory-check SPEC=SPEC-307`, `git diff --check`, `make prod-config`, `make verify-no-db`, elevated `make prod-data-smoke`, elevated `make prod-smoke`, and elevated `make prod-down`.
- Current validation baseline: `main` includes merged `SPEC-302`, reviewed-approved `SPEC-307`, Draft `SPEC-303` to `SPEC-306`, Ready `SPEC-308` to `SPEC-310`, and Draft `SPEC-311`; release automation checks and Docker-backed smoke checks passed on 2026-07-30 except the known host-local PostgreSQL migration connection limitation covered by prior `make migrations-check-compose` and elevated production-smoke migration validation.

## Next Handoff

- Next role: Ingeniero de software for production release execution or `SPEC-308` implementation.
- Next likely integration work: configure required GitHub Actions secrets and run the first manual `Production Release` workflow against `https://rgalvaro.es/`; then implement `SPEC-308`, followed by `SPEC-309` and `SPEC-310`. Resolve `SPEC-311` personal-copy and OpsDesk action-route questions before implementation.
- Keep `SPEC-301` production docs aligned if future scheduled jobs or a Celery beat service are added.

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
| `SPEC-201` | Background jobs and notifications | Redis/Celery worker, task assignment notification enqueueing, logging adapter, Compose wiring, `ADR-010` | Implemented, CI passed, and merged through PR #7 |
| `SPEC-301` | Production deployment and operations | Production Compose, Caddy, CI, isolated smoke, deployment docs, tested backup/restore, `ADR-008`, public VPS deployment | Implemented, review approved, and initially deployed to `https://rgalvaro.es/` |
| `SPEC-302` | Predeployment UI stabilization | App shell navigation, organization/project/task frontend route tests | Implemented, review approved, CI passed, and merged through PR #9 |
| `SPEC-307` | Release automation and safe production updates | Manual GitHub Actions release workflow, VPS release script, pre-deploy backup, migrations, post-deploy checks, rollback docs | Implemented locally and review approved; first real production workflow run pending |

## Draft Specs

| Spec | Scope | Primary surfaces | Latest state |
|---|---|---|---|
| `SPEC-303` | Member invitations by email and project-level access | Organization members, project members, invite APIs, migrations, frontend management UI | Draft updated: existing-user invitations require in-app acceptance; project membership restricts task assignment |
| `SPEC-304` | Organization member chat | Chat persistence, chat APIs, organization chat UI, shared-project member ordering | Draft updated for Slack-like direct, group, organization channel, and project channel chat |
| `SPEC-305` | Project clients and client-created tickets | Client project contacts, ticket-as-task API/UI, migrations | Draft updated: clients are lightweight contacts and tickets live in `tasks` with a type/source and distinct UI label/color |
| `SPEC-306` | In-app notifications | Notification models, APIs, inbox UI, invitation/state/chat notification fan-out | Draft created for persistent in-app notifications and actionable invitation notifications |
| `SPEC-311` | Static public portfolio home | Public `/` route, OpsDesk app card, ERP coming-soon card, changelog link | Draft: personal/developer copy and primary OpsDesk action route still need implementation-time answers |

## Ready Specs

| Spec | Scope | Primary surfaces | Latest state |
|---|---|---|---|
| `SPEC-308` | Enriched profile, organization, project, and task metadata | User profile, email change with password confirmation, company metadata, project/task metadata, migrations, frontend forms | Ready for first implementation slice |
| `SPEC-309` | Project-scoped task labels | Label models/APIs, task label assignments, task filters, label UI, migrations | Ready after `SPEC-308` |
| `SPEC-310` | Production release changelog | `CHANGELOG.md`, changelog validation, public changelog route/link | Ready after `SPEC-307`; public link should coordinate with `SPEC-311` |

## Next Likely Work

1. Configure GitHub Actions production secrets and run one manual `Production Release` workflow for `SPEC-307`.
2. Implement `SPEC-308` enriched metadata and backend-owned organization slug behavior.
3. Implement `SPEC-309` project-scoped task labels.
4. Implement `SPEC-310` release changelog.
5. Resolve `SPEC-311` personal-copy and OpsDesk action-route questions, then implement the static public portfolio home.
6. Decide when to remove the temporary `opdesk.51.255.202.88.sslip.io` fallback hostname.
7. Schedule a controlled VPS reboot for the pending Ubuntu kernel upgrade.

## Known Gaps

- `SPEC-104` has no Playwright E2E tests yet; the spec intentionally recommends adding them after the frontend/local server harness stabilizes.
- `SPEC-106` has route-level/component coverage but still has no Playwright E2E critical path; the spec recommends adding Playwright after organization/project/task UI stabilizes.
- `SPEC-303`, `SPEC-304`, `SPEC-305`, and `SPEC-306` are Draft product additions with unresolved admin-invite permissions, project visibility, chat transport, client ticket form access, notification retention, and notification recipient rules.
- `SPEC-311` is Draft because the public home still needs personal/developer description inputs and a final OpsDesk action route decision before implementation.
- `SPEC-308`, `SPEC-309`, and `SPEC-310` are Ready but not implemented.
- `SPEC-307` is implemented locally and review approved; GitHub Actions production secrets and the first real VPS workflow run are still pending.
- Production is currently deployed at `https://rgalvaro.es/` and `https://www.rgalvaro.es/`; the temporary `https://opdesk.51.255.202.88.sslip.io/` hostname remains configured as a fallback.
- The VPS reported a pending Ubuntu kernel upgrade after Docker installation; schedule a controlled reboot.
- `SPEC-201` uses a log-only notification adapter; real email delivery, notification inbox UI, scheduled jobs, and persistent job audit remain outside this spec.

## Validation Baseline

- Latest `SPEC-307` review validation: `make release-workflow-check` PASS; `make memory-check SPEC=SPEC-307` PASS; `git diff --check` PASS; `make prod-config` PASS and confirms only Caddy has host ports while PostgreSQL/Redis remain private; `make verify-no-db` PASS; sandboxed `make prod-data-smoke` FAIL due Docker socket access then elevated rerun PASS; elevated `make prod-smoke` PASS; elevated `make prod-down` PASS on 2026-07-30.
- Latest spec-planning memory validation: `make memory-check SPEC=SPEC-308` PASS on 2026-07-28.
- Latest `SPEC-301` production deployment validation: `make prod-config` PASS; `make verify` partial PASS then FAIL at host-local `migrations-check`; `make migrations-check-compose` PASS; elevated `make prod-data-smoke` PASS; VPS production Compose config PASS; backup `/srv/opdesk/backups/opdesk-initial-20260722-182637.dump` created; production migrations PASS through `0005`; production `docker compose up -d --build` PASS; `https://opdesk.51.255.202.88.sslip.io/health` PASS; `https://opdesk.51.255.202.88.sslip.io/` PASS; Redis `PONG`, worker running, and private PostgreSQL/Redis exposure checks PASS on 2026-07-22.
- Latest `SPEC-301` production domain validation: `dig @1.1.1.1` confirms `rgalvaro.es` A `51.255.202.88` and AAAA `2001:41d0:305:2100::1:1f66`; `curl -I https://rgalvaro.es/`, `curl https://rgalvaro.es/health`, `curl -I https://www.rgalvaro.es/`, and `curl https://www.rgalvaro.es/health` PASS on 2026-07-22.
- Latest `SPEC-302` review validation: `make test-frontend`, `make lint`, `make format-check`, `make typecheck`, `make memory-check SPEC=SPEC-302`, `git diff --check`, and `make smoke` PASS on 2026-07-22.
- Latest `SPEC-302` CI validation: GitHub Actions `Verify / verify` PASS on PR #9 before merge commit `6f0a49b` on 2026-07-22.
- Latest `SPEC-201` CI validation: GitHub Actions `Verify / verify` PASS on PR #7 at merge commit `ad90534` on 2026-07-16.
- Latest planning-spec CI validation: GitHub Actions `Verify / verify` PASS on PR #8 at merge commit `5c1a205` on 2026-07-17.
- Latest recorded review-fix validation for `SPEC-201`: `make verify-no-db` PASS with 71 backend non-DB tests and 38 frontend tests, `make smoke` PASS with Redis `PONG` and worker running, and elevated `make migrations-check` PASS on 2026-07-08. A full `make verify` rerun on 2026-07-08 passed no-DB checks but failed at migrations before Compose PostgreSQL was started; the subsequent smoke plus elevated migration check covered the failed step.
- Latest `SPEC-201` review decision: APPROVED on 2026-07-08 after focused stale-version worker test, memory check, and whitespace check passed.
- Latest recorded full local verification for `SPEC-201`: elevated `make verify` PASS on 2026-07-07; earlier sandboxed `make migrations-check` failed due localhost PostgreSQL access and the elevated rerun passed.
- Latest `SPEC-201` Compose validation: `make prod-config` PASS; `make smoke` PASS with Redis `PONG` and worker running; sandboxed `make prod-smoke` FAIL due Docker socket access, elevated `make prod-smoke` PASS, elevated `make prod-down` PASS on 2026-07-07.
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
| `backend/app/jobs` | Celery app, worker tasks, and request-time enqueue helpers |
| `backend/app/models` | SQLAlchemy persistence models |
| `backend/app/notifications` | Notification payloads and local-safe delivery adapters |
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
- `docs/decisions/ADR-010-background-jobs-and-notifications.md`
