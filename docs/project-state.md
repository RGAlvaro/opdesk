# Project State

Last updated: 2026-09-15

This file is the compact operational state for agents. Use it to orient quickly before reading detailed specs, ADRs, implementation history, or code.

## Current Work

- Active branch: `agent/spec-316-scheduled-audit`
- Current state: `SPEC-307` release automation was re-reviewed and approved on 2026-07-30 after the pre-backup data-service recreation fix; GitHub Actions production secrets were configured on 2026-08-03 and the first manual workflow execution completed successfully on 2026-08-11, first validation-only and then with production deploy enabled. `SPEC-308` was implemented, review-fixed, deployed to production, and smoke-checked on 2026-08-11 with migration `0006`, profile/email-change APIs, backend-owned organization slug suffixing, project/task metadata APIs, task watchers, frontend metadata forms/display states, and backend/frontend tests. `SPEC-309` was merged to `main` on 2026-08-12 with migration `0007`, project-scoped task label APIs, task label assignments, `label_id` task filtering, frontend label management/filtering/display, and backend tests. `SPEC-310` was merged to `main` through PR #11 on 2026-08-12 with root `CHANGELOG.md`, changelog format validation, production workflow changelog-entry enforcement before secrets/SSH, public `/changelog` route, landing-page release-notes link, frontend route coverage, deployment docs, and harness docs. `SPEC-311` was merged to `main` through PR #12 on 2026-08-12 with a static public portfolio home, recruiter-facing developer copy, OpsDesk available app card, ERP coming-soon card with no fake link, changelog navigation, generated portfolio hub bitmap asset, and frontend tests. Production is available at `https://rgalvaro.es/` and `https://www.rgalvaro.es/`. `SPEC-303`, `SPEC-306`, `SPEC-305`, and `SPEC-304` are merged and deployed through the 2026-08-18 Collaboration Release at app revision `cc354148dee2d1f69b3d99d34b3f0aaced3f06b6`, Alembic `0012 (head)`. On 2026-09-07 the known gaps were converted into Ready specs: `SPEC-313`, `SPEC-314`, `SPEC-315`, and `SPEC-316`. `SPEC-313` is now merged to `main` through PR #18 at merge commit `8006844` with `@axe-core/playwright`, Firefox/WebKit smoke projects, Chromium accessibility scans for public/authenticated/client surfaces, updated Playwright config, harness docs, local validation passing, and GitHub Actions `Verify` run `34325273247` passing on the final PR head.
- Current local `SPEC-314` state: merged to `main` through PR #19 at merge commit `70fcbee` on 2026-09-11 with Resend/console email delivery, delivery audit migration `0013`, Celery delivery tasks, `ticket.created` notification fan-out, production env/docs, safer delivery logs, and GitHub Actions `Verify` run `34577119234` passing before merge.
- Active spec: `SPEC-316` implemented locally on `agent/spec-316-scheduled-audit` and pending review.
- Current local `SPEC-315` state: merged to `main` with authenticated notification WebSockets, in-process recipient fan-out, unread/list cache updates, REST polling fallback, review approval, and GitHub Actions `Verify` run `34943597736` passing before merge.
- Current local `SPEC-316` state: implemented with Celery beat scheduler service, persistent operational audit run records, owner/admin audit API and UI, scheduled external delivery retry sweeps, expired invitation maintenance, stale ticket assignment reminder re-emits, migration `0014`, production Compose/docs updates, and local validation passing.
- Documentation checkpoint: agent operational memory was restructured on 2026-06-16 with this file, central touch-to-spec routing, per-spec scope/context blocks, and `ADR-005`; on 2026-06-24 the base workflow added review-gated memory checks and implementation-log scaffolding targets; on 2026-08-18 merge memory became an explicit checkpoint with `make merge-memory-check SPEC=SPEC-XXX`; `ADR-009` records the managed-sandbox GitHub CLI policy.
- Recent validation recorded in `docs/implementation-log.md`: the 2026-08-18 Collaboration Release deployed merged `SPEC-305` and `SPEC-304` to production through Production Release run `32133588953` after local changelog/test/lint/format/typecheck validation, GitHub Actions `Verify` run `32127831767`, backup, migrations, drift check, compose update, public smoke checks, and direct VPS manifest/Alembic checks passed.
- Current validation baseline: `SPEC-316` local implementation validation passed focused backend/frontend tests, full backend/frontend suites, lint, format, typecheck, migrations, production config rendering, and Docker/local smoke with scheduler running. Production remains deployed at app revision `cc354148dee2d1f69b3d99d34b3f0aaced3f06b6` with Alembic `0012 (head)`, including merged `SPEC-305` and merged `SPEC-304`.
- Harness note: managed-sandbox agents should run migration validation targets with elevated execution from the first attempt because host PostgreSQL TCP access and the Docker socket can be blocked by the sandbox even when services are healthy.
- CI harness note: GitHub official actions were updated to `@v6` in `verify.yml` and `production-release.yml`; GitHub Actions `Verify` run `31516781996` passed without the prior Node 20 deprecation annotation.

## Next Handoff

- Next role: Review agent for `SPEC-316`.
- Next likely integration work: review `SPEC-316`, then commit/PR if approved.
- Keep `SPEC-301` production docs aligned if future scheduled jobs or scheduler topology changes are added.

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
| `SPEC-312` | Expanded Playwright E2E coverage | Auth/profile/filter browser tests, mobile viewport, optional CI artifacts | Implemented, review approved, CI passed, and merged through PR #13 |
| `SPEC-303` | Member invitations by email and project-level access | Organization invitations, project invitations/memberships, project visibility, invite APIs, migration `0008`, frontend management UI | Merged and review approved through PR #14 |
| `SPEC-306` | In-app notifications | Notification models, APIs, inbox UI, invitation/project/task notification fan-out | Merged, review approved, and production deployed with migration `0009` |
| `SPEC-305` | Restricted client accounts, project tickets, status tracking, ticket comments, and accepted handoff requests | Client account access, ticket APIs, ticket comments, client shell, migrations `0010`/`0011` | Implemented, review approved, merged through PR #16, and production deployed |
| `SPEC-304` | Internal organization member chat | Chat persistence, REST/WebSocket chat APIs, organization chat UI, aggregate unread chat notifications, migration `0012` | Implemented, review approved, merged through PR #17, and production deployed |
| `SPEC-313` | Cross-browser and accessibility E2E hardening | `frontend/e2e/`, `frontend/playwright.config.ts`, `@axe-core/playwright`, harness docs | Implemented, review approved, CI passed, and merged through PR #18 |
| `SPEC-314` | External notification delivery | Resend/console email provider, Celery delivery jobs, delivery audit migration `0013`, production env/docs | Merged through PR #19 at `70fcbee`; GitHub Actions passed before merge |
| `SPEC-315` | Real-time notification inbox | Notification WebSocket endpoint, unread-count live updates, polling fallback, frontend cache updates | Merged through PR #20 at `cac6268`; GitHub Actions passed before merge |
| `SPEC-316` | Scheduled jobs and operational audit | Celery beat scheduler service, scheduled job audit table, admin audit UI, production Compose/docs | Implemented locally on `agent/spec-316-scheduled-audit`; pending review |

## Ready Specs

| Spec | Scope | Primary surfaces | Readiness notes |
|---|---|---|---|
| None | None | None | No Ready spec selected after `SPEC-316`; choose the next scope after review/merge |

## Next Likely Work

1. Review `SPEC-316` and open a PR if approved.
2. Keep production release memory current after any future deploy, rollback, or branch cleanup.

## Known Gaps

- `SPEC-312` addressed the prior Playwright coverage gap for auth protection/login/logout, profile persistence, task filter URL persistence, label filtering, and mobile critical-path coverage. `SPEC-313` now addresses Firefox/WebKit smoke coverage and automated accessibility audits; visual snapshots remain future scope.
- `SPEC-303` host PostgreSQL and Compose migration validations passed after the `membership_role` enum reuse fix and backend/worker image rebuild.
- `SPEC-305` and `SPEC-304` are deployed to production. Pending ticket assignment request listing revalidates current organization/project access, and accepting a pending assignment request revalidates current explicit assignment eligibility before setting `assignee_id`. Worker-initiated reassignment uses persisted target-accepted handoff requests. `SPEC-315` now implements notification WebSocket delivery with REST polling fallback; Redis pub/sub fan-out remains future scope before horizontal backend scaling.
- `SPEC-307` is implemented, review approved, and the first real VPS workflow run passed on 2026-08-11.
- Production is currently deployed at `https://rgalvaro.es/` and `https://www.rgalvaro.es/`.
- `SPEC-314` implements Resend-backed real email delivery and delivery audit with indefinite retention. `SPEC-316` now implements Celery beat scheduled jobs and persistent operational audit with owner/admin UI and indefinite retention. Production must run exactly one scheduler instance; horizontal scheduler locking remains future scope if multiple scheduler replicas are ever needed.

## Validation Baseline

- Latest `SPEC-316` implementation validation: `cd backend && poetry run pytest tests/test_operational_audit.py` PASS with 6 focused scheduled-job/audit tests; `cd frontend && npm run test -- AppRouter.test.tsx` PASS with focused router/audit UI coverage; `make test-backend` PASS with 124 backend tests and 2 DB tests deselected; `make test-frontend` PASS with 67 frontend tests; `make lint` PASS; `make format-check` PASS; `make typecheck` PASS; `make migrations-check` PASS with Alembic upgrade through `0014` and no new upgrade operations; `make prod-config` PASS with private scheduler service rendering; `make smoke` PASS with Docker/local backend health, Redis `PONG`, worker, scheduler, Adminer, and Vite frontend checks.
- Latest `SPEC-314` implementation validation: `make test-backend` PASS with 115 selected backend tests and 2 DB tests deselected; `make migrations-check` PASS with Alembic upgrade through `0013` and no new upgrade operations; `make lint` PASS; `make format-check` PASS; `make typecheck` PASS; `make prod-config` PASS with backend/worker Resend env wiring.
- Latest `SPEC-314` review validation: `make test-backend` PASS with 115 selected backend tests and 2 DB tests deselected; `make lint` PASS; `make format-check` PASS; `make typecheck` PASS; `make memory-check SPEC=SPEC-314` PASS; `git diff --check` PASS. Elevated `make migrations-check` could not connect to PostgreSQL at `127.0.0.1:5432`, and elevated `make prod-config` could not find `docker` in this WSL distro; both had passed before the review-only logging adjustment.
- Latest `SPEC-314` PR validation: GitHub Actions run `34576823985` passed `verify` in 2m1s and `e2e` in 2m41s on PR #19 before this evidence-memory update.
- Latest `SPEC-314` merge validation: PR #19 merged to `main` as `70fcbee` on 2026-09-11 after GitHub Actions `Verify` run `34577119234` passed with `verify` in 1m54s and `e2e` in 3m10s.
- Latest `SPEC-313` implementation validation: `make test-e2e` PASS with Docker/local Compose build, backend Alembic upgrade/check, Chromium desktop full suite, mobile Chromium critical path, Firefox/WebKit smoke coverage, and Chromium accessibility scans; `make test-frontend` PASS with 63 frontend tests; `make lint` PASS; `make format-check` PASS; `make typecheck` PASS; elevated `make smoke` PASS with backend health, Redis `PONG`, worker running, Adminer, and frontend checks.
- Latest `SPEC-313` review validation: `make memory-check SPEC=SPEC-313` PASS; `git diff --check` PASS; `cd frontend && npm run typecheck` PASS; `cd frontend && npm run format:check` PASS; `cd frontend && npm run lint` PASS. Review decision APPROVED on 2026-09-07.
- Latest `SPEC-313` merge validation: PR #18 merged to `main` as `8006844` on 2026-09-09 after GitHub Actions `Verify` run `34325273247` passed with `verify` in 1m57s and `e2e` in 2m52s.
- Latest `SPEC-315` implementation validation: `cd backend && poetry run pytest tests/test_in_app_notifications_api.py` PASS with 6 notification API/WebSocket tests; `cd frontend && npm run test -- NotificationsPage.test.tsx` PASS with 3 notification UI/WebSocket tests; `make test-backend` PASS with 109 selected backend tests and 2 DB tests deselected; `make test-frontend` PASS with 65 frontend tests; `make lint` PASS; `make format-check` PASS; `make typecheck` PASS; elevated `make smoke` PASS with Docker/local backend health, Redis `PONG`, worker running, Adminer, and Vite frontend checks.
- Latest `SPEC-315` review validation: `make test-backend` PASS with 118 selected backend tests and 2 DB tests deselected; `make test-frontend` PASS with 65 frontend tests; `make lint` PASS; `make format-check` PASS; `make typecheck` PASS; `make smoke` PASS with Docker/local backend health, Redis `PONG`, worker running, Adminer, and Vite frontend checks; `make memory-check SPEC=SPEC-315` PASS; `git diff --check` PASS.
- Latest `SPEC-315` PR validation: GitHub Actions run `34943274026` passed `verify` in 1m56s and `e2e` in 2m52s on PR #20 before this evidence-memory update.
- Latest `SPEC-315` merge validation: PR #20 merged to `main` as `cac6268` on 2026-09-15 after GitHub Actions `Verify` run `34943597736` passed with `verify` in 1m47s and `e2e` in 3m7s.
- Latest `SPEC-304` implementation validation: `make test-backend` PASS with 105 selected backend tests and 2 DB tests deselected; `make test-frontend` PASS with 61 frontend tests; `make lint` PASS; `make format-check` PASS; `make typecheck` PASS; elevated `make migrations-check` PASS with Alembic upgrade through `0012` and no new upgrade operations.
- Latest `SPEC-304` review-fix validation: `make test-backend` PASS with 106 selected backend tests and 2 DB tests deselected; `make test-frontend` PASS with 63 frontend tests; `make lint` PASS; `make format-check` PASS; `make typecheck` PASS; `make memory-check SPEC=SPEC-304` PASS; `git diff --check` PASS. `make migrations-check` was not rerun after review fixes because no migrations or SQLAlchemy models changed after the prior elevated `0012` pass.
- Latest `SPEC-304` review approval validation: `make test-backend` PASS with 106 selected backend tests and 2 DB tests deselected; `make test-frontend` PASS with 63 frontend tests; `make lint` PASS; `make format-check` PASS; `make typecheck` PASS; elevated `make migrations-check` PASS with Alembic reporting no new upgrade operations; `make memory-check SPEC=SPEC-304` PASS; `git diff --check` PASS.
- Latest `SPEC-304` merge validation: PR #17 merged to `main` as `6aea60e` on 2026-08-18 after GitHub Actions `Verify` run `32125728030` passed both `verify` in 1m47s and `e2e` in 2m9s; local `main` fast-forwarded to `6aea60e`.
- Latest production deployment validation: Collaboration Release deployed app revision `cc354148dee2d1f69b3d99d34b3f0aaced3f06b6` through Production Release run `32133588953` on 2026-08-18 in 2m58s. The release manifest recorded backup `/srv/opdesk/backups/opdesk-20260818-115050-cc354148dee2d1f69b3d99d34b3f0aac.dump`, `backend_image_build=PASS`, `migrations=PASS`, `migration_drift_check=PASS`, `alembic_current=0012 (head)`, `compose_update=PASS`, `backend_health=PASS`, `frontend=PASS`, `redis=PASS`, and `worker=PASS`. External checks passed for `curl -fsS https://rgalvaro.es/health`, `curl -I -fsS https://rgalvaro.es/`, `curl -I -fsS https://rgalvaro.es/changelog`, and unauthenticated `curl -i -sS https://rgalvaro.es/api/v1/users/me` returned the expected `401 not_authenticated` envelope. An earlier Production Release run `32128264461` failed before validation or deployment because an incorrect target SHA was supplied.
- Latest `SPEC-305` merge validation: PR #16 merged to `main` as `ba140d3` on 2026-08-17 after GitHub Actions `Verify` run `32010096770` passed both `verify` and `e2e`; local `main` is clean and aligned with `origin/main`. Earlier review validation passed `make test-backend`, `make test-frontend`, `make lint`, `make format-check`, `make typecheck`, elevated `make migrations-check`, `make memory-check SPEC=SPEC-305`, and `git diff --check`.
- Latest `SPEC-312` merge validation: PR #13 merged to `main` as `9b020cc` on 2026-08-13 after GitHub Actions `Verify` run `31686532597` passed both `verify` and `e2e` jobs; local `main` fast-forwarded to `9b020cc`; memory commit `5c1dac0` was pushed to `main`; GitHub Actions `Verify` run `31687118950` initially failed `e2e` because Docker Hub returned `500 Internal Server Error` while fetching image auth tokens for `python:3.12-slim` and `node:24-alpine`, then rerun passed with `e2e` in 2m15s and `verify` in 1m50s; memory commit `6422080` then passed GitHub Actions `Verify` run `31691528101` with `e2e` in 2m18s and `verify` in 1m40s. Earlier review validation: `make memory-check SPEC=SPEC-312` PASS and `git diff --check` PASS; implementation validation: `make test-e2e` PASS with Docker/local Compose build, backend Alembic upgrade/check, and 6 Playwright tests across desktop Chromium plus mobile Chromium critical path; `make lint` PASS; `make format-check` PASS; `make typecheck` PASS; `make test-frontend` PASS with 47 frontend tests; `make smoke` PASS; `make prod-config` PASS; `cd frontend && npm run build` PASS on 2026-08-13.
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
- `docs/decisions/ADR-011-client-accounts-and-ticket-access.md`
- `docs/decisions/ADR-012-websocket-chat-transport.md`
- `docs/decisions/ADR-013-resend-email-delivery.md`
- `docs/decisions/ADR-014-celery-beat-and-operational-audit.md`
