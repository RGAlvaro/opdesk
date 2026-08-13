# Project State

Last updated: 2026-08-13

This file is the compact operational state for agents. Use it to orient quickly before reading detailed specs, ADRs, implementation history, or code.

## Current Work

- Active branch: `agent/spec-312-playwright-e2e-expansion`
- Active spec: `SPEC-312` Playwright E2E expansion is reviewed and approved, pending PR/CI.
- Current state: `SPEC-307` release automation was re-reviewed and approved on 2026-07-30 after the pre-backup data-service recreation fix; GitHub Actions production secrets were configured on 2026-08-03 and the first manual workflow execution completed successfully on 2026-08-11, first validation-only and then with production deploy enabled. `SPEC-308` was implemented, review-fixed, deployed to production, and smoke-checked on 2026-08-11 with migration `0006`, profile/email-change APIs, backend-owned organization slug suffixing, project/task metadata APIs, task watchers, frontend metadata forms/display states, and backend/frontend tests. `SPEC-309` was merged to `main` on 2026-08-12 with migration `0007`, project-scoped task label APIs, task label assignments, `label_id` task filtering, frontend label management/filtering/display, and backend/frontend tests. `SPEC-310` was merged to `main` through PR #11 on 2026-08-12 with root `CHANGELOG.md`, changelog format validation, production workflow changelog-entry enforcement before secrets/SSH, public `/changelog` route, landing-page release-notes link, frontend route coverage, deployment docs, and harness docs. `SPEC-311` was merged to `main` through PR #12 on 2026-08-12 with a static public portfolio home, recruiter-facing developer copy, OpsDesk available app card, ERP coming-soon card with no fake link, changelog navigation, generated portfolio hub bitmap asset, and frontend tests. An authenticated production smoke exposed a release-order bug where Alembic ran before the new backend image was built; production was manually recovered to `0006`, authenticated SPEC-308 smoke passed, and `scripts/prod_release.sh` now builds the backend image after backup and before migrations. Production is available at `https://rgalvaro.es/` and `https://www.rgalvaro.es/`; on 2026-08-12 the temporary `https://opdesk.51.255.202.88.sslip.io/` Caddy fallback was removed from the VPS and the pending Ubuntu kernel reboot was completed. `SPEC-312` expands the Playwright harness with auth protection/login/logout, profile persistence, task filter URL persistence, label filtering, desktop Chromium full-suite coverage, mobile Chromium critical-path coverage, and a separate GitHub Actions `e2e` job with failure artifacts.
- Documentation checkpoint: agent operational memory was restructured on 2026-06-16 with this file, central touch-to-spec routing, per-spec scope/context blocks, and `ADR-005`; on 2026-06-24 the base workflow added review-gated memory checks and implementation-log scaffolding targets; `ADR-009` records the managed-sandbox GitHub CLI policy.
- Recent validation recorded in `docs/implementation-log.md`: `SPEC-312` implementation passed `make test-e2e`, `make lint`, `make format-check`, `make typecheck`, `make test-frontend`, `make smoke`, `make prod-config`, and `cd frontend && npm run build` on 2026-08-13; review validation passed `make memory-check SPEC=SPEC-312` and `git diff --check`.
- Current validation baseline: `main` includes merged `SPEC-302`, reviewed-approved and production-executed `SPEC-307`, Draft `SPEC-303` to `SPEC-306`, implemented/review-approved and production-deployed `SPEC-308`, merged/review-approved `SPEC-309`, merged/review-approved `SPEC-310`, merged/review-approved `SPEC-311`, and reviewed-approved `SPEC-312` Playwright E2E expansion committed on branch `agent/spec-312-playwright-e2e-expansion` at `d088295`, pending PR/CI; the `SPEC-310` and `SPEC-311` GitHub `Verify` workflows passed on their 2026-08-12 merge commits.
- Harness note: managed-sandbox agents should run migration validation targets with elevated execution from the first attempt because host PostgreSQL TCP access and the Docker socket can be blocked by the sandbox even when services are healthy.
- CI harness note: GitHub official actions were updated to `@v6` in `verify.yml` and `production-release.yml`; GitHub Actions `Verify` run `31516781996` passed without the prior Node 20 deprecation annotation.

## Next Handoff

- Next role: Ingeniero de software to push `SPEC-312`, open PR, and validate the new GitHub Actions `e2e` job.
- Next likely integration work: merge `SPEC-312` after CI, then choose the next Ready product spec or refine the Draft product additions.
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
| `SPEC-307` | Release automation and safe production updates | Manual GitHub Actions release workflow, VPS release script, pre-deploy backup, migrations, post-deploy checks, rollback docs | Implemented, review approved, production secrets configured, and first manual production workflow execution passed |
| `SPEC-308` | Enriched profile, organization, project, and task metadata | User profile/email change, organization/project/task metadata, task watchers, migration `0006`, frontend metadata forms | Implemented, review approved, and production deployed on 2026-08-11 |
| `SPEC-309` | Project-scoped task labels | Label models/APIs, task label assignments, task filters, label UI, migration `0007` | Implemented, review approved, and merged to `main` |
| `SPEC-310` | Production release changelog | `CHANGELOG.md`, changelog validation, public changelog route/link | Implemented, review approved, CI passed, and merged through PR #11 |
| `SPEC-311` | Static public portfolio home | Public `/` route, OpsDesk app card, ERP coming-soon card, changelog link | Implemented, review approved, CI passed, and merged through PR #12 |
| `SPEC-312` | Expanded Playwright E2E coverage | Auth/profile/filter browser tests, mobile viewport, optional CI artifacts | Reviewed and approved; pending commit/PR/CI |

## Draft Specs

| Spec | Scope | Primary surfaces | Latest state |
|---|---|---|---|
| `SPEC-303` | Member invitations by email and project-level access | Organization members, project members, invite APIs, migrations, frontend management UI | Draft updated: existing-user invitations require in-app acceptance; project membership restricts task assignment |
| `SPEC-304` | Organization member chat | Chat persistence, chat APIs, organization chat UI, shared-project member ordering | Draft updated for Slack-like direct, group, organization channel, and project channel chat |
| `SPEC-305` | Project clients and client-created tickets | Client project contacts, ticket-as-task API/UI, migrations | Draft updated: clients are lightweight contacts and tickets live in `tasks` with a type/source and distinct UI label/color |
| `SPEC-306` | In-app notifications | Notification models, APIs, inbox UI, invitation/state/chat notification fan-out | Draft created for persistent in-app notifications and actionable invitation notifications |

## Next Likely Work

1. Select or ready the next product spec after `SPEC-311`.
2. Continue hardening production observability or E2E coverage if no product spec is selected.

## Known Gaps

- `SPEC-312` addressed the prior Playwright coverage gap for auth protection/login/logout, profile persistence, task filter URL persistence, label filtering, and mobile critical-path coverage; remaining E2E gaps are intentionally future scope: Firefox/WebKit, visual snapshots, and dedicated accessibility audits.
- `SPEC-303`, `SPEC-304`, `SPEC-305`, and `SPEC-306` are Draft product additions with unresolved admin-invite permissions, project visibility, chat transport, client ticket form access, notification retention, and notification recipient rules.
- `SPEC-307` is implemented, review approved, and the first real VPS workflow run passed on 2026-08-11.
- Production is currently deployed at `https://rgalvaro.es/` and `https://www.rgalvaro.es/`.
- `SPEC-201` uses a log-only notification adapter; real email delivery, notification inbox UI, scheduled jobs, and persistent job audit remain outside this spec.

## Validation Baseline

- Latest `SPEC-312` review validation: `make memory-check SPEC=SPEC-312` PASS and `git diff --check` PASS on 2026-08-13; review decision APPROVED. Implementation validation: `make test-e2e` PASS with Docker/local Compose build, backend Alembic upgrade/check, and 6 Playwright tests across desktop Chromium plus mobile Chromium critical path; `make lint` PASS; `make format-check` PASS; `make typecheck` PASS; `make test-frontend` PASS with 47 frontend tests; `make smoke` PASS; `make prod-config` PASS; `cd frontend && npm run build` PASS on 2026-08-13. The separate GitHub Actions `e2e` job is implemented but not yet run in CI.
- Latest `SPEC-104`/`SPEC-106` Playwright hardening validation: `make test-e2e` PASS with Docker/local Compose build, backend Alembic upgrade/check, and 1 Chromium critical-path test covering signup through completed task; `make lint` PASS; `make format-check` PASS; `make typecheck` PASS; `make test-frontend` PASS with 47 frontend tests; `make smoke` PASS; `make prod-config` PASS; `cd frontend && npm run build` PASS on 2026-08-12.
- Latest `SPEC-301` operational cleanup validation: `ssh opdesk-vps` confirmed pre-change `REBOOT_REQUIRED=yes` and `CADDY_SITE_ADDRESS=rgalvaro.es, www.rgalvaro.es, opdesk.51.255.202.88.sslip.io`; server-side `.env.production` was backed up to `.env.production.pre-hostname-cleanup-20260812-093900`, `CADDY_SITE_ADDRESS` was reduced to `rgalvaro.es, www.rgalvaro.es`, and Caddy was recreated. Post-change `curl -fsS https://rgalvaro.es/health`, `curl -I -fsS https://rgalvaro.es/`, `curl -fsS https://www.rgalvaro.es/health`, `curl -I -fsS https://www.rgalvaro.es/`, and unauthenticated `curl -i https://rgalvaro.es/api/v1/users/me` PASS on 2026-08-12; `curl -fsS --max-time 15 https://opdesk.51.255.202.88.sslip.io/health` EXPECTED FAIL with TLS internal alert after Caddy hostname removal. Controlled VPS reboot PASS with post-reboot uptime `2026-08-12 09:39:36`, `REBOOT_REQUIRED=no`, production Compose services running, backend/PostgreSQL/Redis healthy, Redis `PONG`, and worker running.
- Latest merge validation: `SPEC-311` PR #12 merged to `main` as `af9535e` on 2026-08-12, GitHub Actions `Verify` run `31581961980` PASS, local `main` fast-forwarded to `af9535e`, and local/remote `agent/spec-311-public-portfolio-home` branch deletion PASS. `SPEC-310` PR #11 merged to `main` as `f0849fe` on 2026-08-12, GitHub Actions `Verify` run `31581706174` PASS, and local/remote `agent/spec-310-release-changelog` branch deletion PASS.
- Latest `SPEC-311` review validation: `make test-frontend` PASS with 47 frontend tests; `make lint` PASS; `make format-check` PASS; `make typecheck` PASS; `make memory-check SPEC=SPEC-311` PASS; `make smoke` PASS with Docker/local backend health, Redis, worker, Adminer, and Vite frontend checks; `cd frontend && npm run build` PASS; `git diff --check agent/spec-310-release-changelog...HEAD` PASS on 2026-08-12.
- Latest `SPEC-310` review validation: `make release-workflow-check` PASS; `make test-frontend` PASS with 46 frontend tests; `make lint` PASS; `make format-check` PASS; `make typecheck` PASS; `make memory-check SPEC=SPEC-310` PASS; `git diff --check main...HEAD` PASS; `cd frontend && npm run build` PASS; `python3 scripts/validate_changelog.py --entry "2099-01-01 - Missing Release"` EXPECTED FAIL on 2026-08-12.
- Latest `SPEC-309` re-review validation: `make test-frontend` PASS with 45 frontend tests; `make test-backend` PASS with 83 selected backend tests and 2 deselected DB tests; `make lint` PASS; `make format-check` PASS; `make typecheck` PASS; `make memory-check SPEC=SPEC-309` PASS; `git diff --check` PASS on 2026-08-12. Earlier `SPEC-309` migration validation: elevated `make migrations-check` initially FAIL after applying `0007` because Alembic metadata lacked the new partial label-name index, then PASS after the model index was added and Alembic reported no new upgrade operations on 2026-08-11.
- Latest `SPEC-308` validation: `python3 -m compileall backend/app` PASS; `make test-backend` PASS with 80 selected non-DB tests and 2 deselected DB tests; `make test-frontend` PASS with 41 tests; `make lint` PASS; `make format-check` PASS; `make typecheck` PASS; `make migrations-check` PASS outside sandbox with Alembic upgrade/check through `0006`; `make migrations-check-compose` PASS with Alembic upgrade/check through `0006`; `git diff --check` PASS.
- Latest `SPEC-308` production validation: GitHub Actions `Verify` run `31475622515` PASS on `cb7692e`; `Production Release` run `31476539204` PASS deploying `cb7692e0d69f94f97e9883d6576c8719bfbbe8f5`; `curl -fsS https://rgalvaro.es/health` PASS; `curl -I -fsS https://rgalvaro.es/` PASS with `HTTP/2 200`; `curl -i -sS https://rgalvaro.es/api/v1/users/me` PASS with expected `401 not_authenticated` envelope.
- Latest `SPEC-308` authenticated production smoke: initial register returned `500` because production was still at Alembic `0005`; manual production `alembic upgrade head` PASS moved production to `0006`; authenticated smoke then PASS for register, login, profile metadata update, organization metadata create/delete, project metadata create, task metadata/watchers create, blocked reason update, task metadata filters, and smoke user cleanup.
- Latest `SPEC-307` release automation fix: `scripts/prod_release.sh` now builds the backend image after backup and before Alembic so new migrations are available before app containers are replaced; `make release-workflow-check`, `make prod-config`, `git diff --check`, GitHub Actions `Verify` run `31500412344`, and corrected `Production Release` run `31500572299` PASS. The production release manifest for `94dbb542e0fe71bcf223d0f576e8b5d4e52a4252` recorded `backend_image_build=PASS`, `migrations=PASS`, and `compose_update=PASS`.
- Latest `SPEC-307` migration drift hardening: `scripts/prod_release.sh` now runs `alembic check` and records `alembic_current` after `alembic upgrade head` but before replacing app containers; `make release-workflow-check`, `make prod-config`, `git diff --check`, GitHub Actions `Verify` run `31501963103`, and `Production Release` run `31502139076` PASS. The production release manifest for `5a36d8e10d9469c2b1d505b1f4da90a54c0add0f` recorded `backend_image_build=PASS`, `migrations=PASS`, `migration_drift_check=PASS`, `alembic_current=0006 (head)`, and `compose_update=PASS`.
- Latest harness clarification: `specs/harness/local-validation.md` now requires managed-sandbox agents to request elevated execution from the first attempt for host or Compose migration validation targets; sandboxed TCP/Docker permission failures are not migration evidence.
- Latest `SPEC-307` production workflow validation: `gh auth status` PASS with `repo` and `workflow` scopes; `Production Release` validation-only run `31471833191` PASS with deploy skipped; `Production Release` deploy run `31472041900` PASS at `a2dea58a70bef2aec98ef318ea6acc796099230f` with remote production update, backend health, frontend, Redis, and worker checks passing; `curl -fsS https://rgalvaro.es/health` PASS; `curl -I -fsS https://rgalvaro.es/` PASS with `HTTP/2 200` on 2026-08-11.
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
