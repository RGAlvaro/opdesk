# Implementation Log

This file is the durable timeline for OpsDesk spec work. Keep entries short, factual, and linked to specs, commits, validation, and review outcomes.

## How To Use

- Add one entry per meaningful spec-prep, implementation, review, or merge event.
- Newest entries go at the top of `Entries`.
- Reference spec IDs exactly, for example `SPEC-010`.
- Record commands that were run and their result. If a command was not run, record why.
- Record known gaps only when they matter after the current step.

## Entry Template

```text
### YYYY-MM-DD — SPEC-XXX — Short title

Role: Arquitecto de specs | Ingeniero de software | Review agent
Branch: branch-name
Commit/PR: commit sha or PR URL
Status: Planned | Ready | Implemented | Reviewed | Merged | Blocked

Summary:
- ...

Validation:
- command: PASS/FAIL/NOT RUN — notes

Review:
- decision: APPROVED/CHANGES_REQUESTED/BLOCKED_BY_SPEC_GAP/N/A

Known gaps:
- None, or list remaining work.
```

## Entries

### 2026-06-30 — Repository workflow — Managed sandbox GitHub CLI policy

Role: Arquitecto de specs
Branch: codex/gh-outside-sandbox-policy
Commit/PR: `5491223` / PR pending
Status: Ready

Summary:
- Required network-backed `gh` commands to run outside managed sandboxes from the first attempt.
- Required narrowly scoped approvals and an outside-sandbox authentication check before publication.
- Added an explicit `workflow` token-scope check when publishing `.github/workflows/*`.
- Recorded the durable decision in `ADR-009`; no product spec status or behavior changed.

Validation:
- command: `git diff --check`: PASS.
- command: policy reference check with `rg`: PASS — mandatory outside-sandbox execution and `workflow` scope guidance are present in agent instructions, workflow notes, ADR, and project memory.
- command: `make memory-check SPEC=SPEC-106`: PASS — existing active product memory remains structurally valid; this policy does not introduce a product spec.
- command: elevated `gh auth status`: PASS — authenticated account exposes `repo` and `workflow` scopes outside the sandbox.

Review:
- decision: N/A — workflow policy awaits review.

Known gaps:
- Runtime approval remains environment-specific; the repository can require elevation but cannot pre-authorize it.

### 2026-06-30 — SPEC-106 — Pagination review fix approved

Role: Review agent
Branch: main
Commit/PR: `749c381`
Status: Reviewed

Summary:
- Re-reviewed the `SPEC-106` pagination review fix.
- Confirmed project and task list hooks send `limit`/`offset` and include pagination in query keys.
- Confirmed project and task list screens expose URL-backed previous/next pagination controls.
- Confirmed task filters reset offset to the first page and preserve filters when paginating.
- Confirmed tests assert paginated requests, shared pagination URLs, and filtered task pagination.
- Updated project memory to mark `SPEC-106` review approved.

Validation:
- command: `make test-frontend`: PASS — 3 frontend test files, 38 tests passed.
- command: `make lint`: PASS — backend Ruff and frontend ESLint passed.
- command: `make format-check`: PASS — backend Ruff format check and frontend Prettier passed.
- command: `make typecheck`: PASS — backend mypy and frontend TypeScript passed.
- command: `make smoke`: PASS — Docker Compose rebuilt/started backend, frontend, PostgreSQL, and Adminer; backend health, Adminer, and frontend HTTP checks passed after backend startup retries.
- command: `make memory-check SPEC=SPEC-106`: PASS.
- command: `git diff --check`: PASS.

Review:
- decision: APPROVED

Known gaps:
- No Playwright E2E critical path yet; `SPEC-106` explicitly recommends adding it after organization/project/task UI stabilizes.

### 2026-06-30 — SPEC-106 — Pagination review fix implemented

Role: Ingeniero de software
Branch: main
Commit/PR: `749c381`
Status: Implemented

Summary:
- Added `limit` and `offset` support to project and task list API hooks and query keys.
- Added URL-backed previous/next pagination controls to project and task list routes.
- Reset task pagination offset when filters change while preserving filter query parameters when paging.
- Added route tests that assert project/task list requests include `limit`/`offset`, that shared pagination URLs load the requested page, and that task filters are preserved while paginating.
- Updated project memory for re-review handoff.

Validation:
- command: `npm run test` from `frontend/`: PASS — 3 frontend test files, 38 tests passed.
- command: `npm run lint` from `frontend/`: PASS — frontend ESLint passed.
- command: `npm run format:check` from `frontend/`: PASS — frontend Prettier passed.
- command: `npm run typecheck` from `frontend/`: PASS — TypeScript project build passed.
- command: `make test-frontend`: PASS — 3 frontend test files, 38 tests passed.
- command: `make lint`: PASS — backend Ruff and frontend ESLint passed.
- command: `make format-check`: PASS — backend Ruff format check and frontend Prettier passed.
- command: `make typecheck`: PASS — backend mypy and frontend TypeScript passed.
- command: `make smoke`: PASS — Docker Compose rebuilt/started backend, frontend, PostgreSQL, and Adminer; backend health, Adminer, and frontend HTTP checks passed after backend startup retries.

Review:
- decision: N/A — review fix awaits re-review.

Known gaps:
- No Playwright E2E critical path yet; `SPEC-106` recommends adding it after organization/project/task UI stabilizes.

### 2026-06-24 — SPEC-106 — Review changes requested

Role: Review agent
Branch: main
Commit/PR: `749c381`
Status: Reviewed

Summary:
- Reviewed the `SPEC-106` frontend projects/tasks implementation against routes, API usage, filters, role-aware controls, tests, validation, and project memory.
- Confirmed required frontend validation and smoke checks pass.
- Found that project and task list API hooks and screens do not expose `limit`/`offset` pagination controls or request parameters, leaving AC-1, AC-6, and the harness pagination requirement only partially implemented.
- Updated project memory to reflect the review decision and next work.

Validation:
- command: `make test-frontend`: PASS — 3 frontend test files, 37 tests passed.
- command: `make lint`: PASS — backend Ruff and frontend ESLint passed.
- command: `make format-check`: PASS — backend Ruff format check and frontend Prettier passed.
- command: `make typecheck`: PASS — backend mypy and frontend TypeScript passed.
- command: `make smoke`: PASS — Docker Compose rebuilt/started backend, frontend, PostgreSQL, and Adminer; backend health, Adminer, and frontend HTTP checks passed after backend startup retries.
- command: `make memory-check SPEC=SPEC-106`: PASS.
- command: `git diff --check`: PASS.

Review:
- decision: CHANGES_REQUESTED

Known gaps:
- Project and task list pagination controls/request parameters are missing and must be implemented before approval.

### 2026-06-24 — SPEC-106 — Frontend projects and tasks UI implemented

Role: Ingeniero de software
Branch: main
Commit/PR: `749c381`
Status: Implemented

Summary:
- Added project API hooks, types, list route, creation route, detail route, owner/admin settings, archive toggles, and organization-detail project navigation.
- Added task API hooks, types, URL-backed task filters, task list route, task creation route, role-aware assignee controls, task detail/update route, and safe `401`/`403`/`404`/`409` handling.
- Updated authenticated shell and dashboard navigation now that project/task routes are implemented.
- Added route-level frontend coverage for project list/create/update/archive, role-aware controls, task filters, assignment behavior, archived projects, task update completion state, safe API errors, and auth guard behavior.
- Marked `SPEC-106` implemented in the spec index and updated project memory for review handoff.

Validation:
- command: `npm run typecheck` from `frontend/`: PASS — TypeScript project build passed after initial implementation fixes.
- command: `npm run test -- --runInBand` from `frontend/`: FAIL — Vitest does not support the Jest-style `--runInBand` option in this project.
- command: `npm run test` from `frontend/`: PASS — 3 frontend test files, 37 tests passed.
- command: `npm run lint` from `frontend/`: PASS — frontend ESLint passed after removing a dead import and Fast Refresh helper exports.
- command: `npm run format:check` from `frontend/`: PASS — frontend Prettier check passed after formatting touched files.
- command: `make test-frontend`: PASS — 3 frontend test files, 37 tests passed.
- command: `make lint`: PASS — backend Ruff and frontend ESLint passed.
- command: `make format-check`: PASS — backend Ruff format check and frontend Prettier passed.
- command: `make typecheck`: PASS — backend mypy and frontend TypeScript passed.
- command: `make smoke`: PASS — Docker Compose rebuilt/started backend, frontend, PostgreSQL, and Adminer; backend health, Adminer, and frontend HTTP checks passed after backend startup retries.

Review:
- decision: N/A — implementation awaits review.

Known gaps:
- No Playwright E2E critical path yet; `SPEC-106` recommends adding it after organization/project/task UI stabilizes.

### 2026-06-24 — SPEC-106 — Memory harness review approved

Role: Review agent
Branch: main
Commit/PR: Pending
Status: Reviewed

Summary:
- Reviewed the review-gated memory workflow changes against the requested points: review approval as the canonical checkpoint, memory verification targets, and implementation-log scaffolding.
- Confirmed the changes avoid commit/push hooks as the source of truth and keep generated memory factual.
- Confirmed new scripts use standard-library Python, include required reader comments/docstrings, and are wired through Make targets.
- Confirmed project memory and `ADR-005` reflect the durable workflow policy.

Validation:
- command: `git diff --check`: PASS.
- command: `make memory-check SPEC=SPEC-106`: PASS — project-state and implementation-log mention the active spec and required handoff sections.
- command: `make review-ready SPEC=SPEC-106`: PASS — memory readiness alias passed.
- command: `python3 scripts/memory_check.py --spec SPEC-106 --reviewed`: PASS — strict reviewed/approved memory check passed.
- command: `python3 -m compileall scripts`: PASS — both memory helper scripts compiled.

Review:
- decision: APPROVED

Known gaps:
- `SPEC-106` product UI remains unimplemented; this review only covers the base workflow and memory harness preparation.

### 2026-06-24 — SPEC-106 — Review-gated memory harness prepared

Role: Arquitecto de specs
Branch: main
Commit/PR: Pending
Status: Ready

Summary:
- Updated the base workflow so Review agent `APPROVED` is the canonical point where `docs/project-state.md` and `docs/implementation-log.md` must be current.
- Added `make memory-check SPEC=SPEC-XXX`, `make review-ready SPEC=SPEC-XXX`, and `make memory-entry SPEC=SPEC-XXX` as harness helpers for memory verification and log-entry scaffolding.
- Documented the helpers in the local validation harness and captured the durable policy in `ADR-005`.
- Kept the helpers factual: they validate or print templates, but do not auto-write validation evidence or review decisions.

Validation:
- command: `make memory-entry SPEC=SPEC-106 ROLE='Review agent' STATUS=Reviewed TITLE='Review approved' BRANCH=main`: PASS — printed a paste-ready reviewed-entry template.
- command: `make memory-check SPEC=SPEC-106`: PASS — verified project-state and implementation-log memory shape for the active spec.
- command: `make review-ready SPEC=SPEC-106`: PASS — ran the memory readiness alias successfully.
- command: `git diff --check`: PASS.

Review:
- decision: N/A

Known gaps:
- `SPEC-106` remains unimplemented.

### 2026-06-24 — SPEC-106 — Readiness audit for frontend projects and tasks UI

Role: Arquitecto de specs
Branch: main
Commit/PR: Pending
Status: Ready

Summary:
- Reviewed project memory, spec index, product/API conventions, local validation harness, `SPEC-103`, `SPEC-104`, `SPEC-105`, and `ADR-007` before implementation handoff.
- Confirmed `SPEC-106` is the next dependency-valid implementation target after merged `SPEC-105`.
- Checked backend project/task API contracts and frontend organization helper surfaces for obvious mismatches; no spec gap found.
- Updated project memory so the active branch and active spec reflect the merged `main` state.

Validation:
- command: `git status -sb`: PASS — repository is on `main` tracking `origin/main` before documentation updates.
- command: implementation harness NOT RUN — readiness/documentation review only; product code was not changed.

Review:
- decision: N/A

Known gaps:
- `SPEC-106` remains unimplemented.
- Full implementation validation is deferred to the `SPEC-106` engineer.

### 2026-06-24 — SPEC-105 — Review approved after auth-loss fix

Role: Review agent
Branch: codex/spec-105-frontend-organizations-ui
Commit/PR: Pending
Status: Reviewed

Summary:
- Re-reviewed the `SPEC-105` organization `401 not_authenticated` fix.
- Confirmed organization query and mutation auth-loss handling clears cached session state and navigates to `/login`.
- Confirmed updated frontend tests cover cached-session query `401` and mutation `401` flows.
- Updated project memory to mark `SPEC-105` review approved and route next work to `SPEC-106`.

Validation:
- command: `make test-frontend`: PASS — 2 frontend test files, 24 tests passed.
- command: `make lint`: PASS — backend Ruff and frontend ESLint passed.
- command: `make format-check`: PASS — backend Ruff format check and frontend Prettier passed.
- command: `make typecheck`: PASS — backend mypy and frontend TypeScript passed.
- command: prior `make verify-no-db`: PASS — lint, format, type checks, backend non-DB tests, and frontend tests passed for the review fix.
- command: prior `make smoke`: PASS — Docker Compose built/started backend, frontend, PostgreSQL, and Adminer; health/Adminer/frontend checks passed for the review fix.

Review:
- decision: APPROVED

Known gaps:
- `SPEC-106` project/task UI remains unimplemented.

### 2026-06-24 — SPEC-105 — Review fix implemented

Role: Ingeniero de software
Branch: codex/spec-105-frontend-organizations-ui
Commit/PR: Pending
Status: Implemented

Summary:
- Added organization auth-loss handling that cancels/removes the cached session query and navigates to `/login` when organization queries or mutations return `401 not_authenticated`.
- Applied the handling to organization list/detail/member query error branches and create/update/delete/member role/member removal/ownership transfer mutation failures.
- Added frontend tests for cached-session query `401` and mutation `401` flows to ensure the login route remains visible after session cache is cleared.
- Updated project memory for re-review handoff.

Validation:
- command: `cd frontend && npm run test -- OrganizationPages.test.tsx`: PASS — 12 organization tests passed.
- command: `cd frontend && npm run typecheck`: PASS.
- command: `cd frontend && npm run lint`: PASS.
- command: `make test-frontend`: PASS — 2 frontend test files, 24 tests passed.
- command: `make lint`: PASS — backend Ruff and frontend ESLint passed.
- command: `make format-check`: PASS — backend Ruff format check and frontend Prettier passed.
- command: `make typecheck`: PASS — backend mypy and frontend TypeScript passed.
- command: `make verify-no-db`: PASS — lint, format, type checks, backend non-DB tests, and frontend tests passed.
- command: `make smoke`: PASS — Docker Compose built/started backend, frontend, PostgreSQL, and Adminer; health/Adminer/frontend checks passed.

Review:
- decision: N/A — review fix awaits re-review.

Known gaps:
- `SPEC-105` re-review approval remains pending.
- `SPEC-106` project/task UI remains unimplemented.

### 2026-06-24 — SPEC-105 — Review changes requested

Role: Review agent
Branch: codex/spec-105-frontend-organizations-ui
Commit/PR: Pending
Status: Reviewed

Summary:
- Reviewed `SPEC-105` implementation against frontend organization routes, API usage, permission states, error handling, tests, and project memory.
- Found that organization `401 not_authenticated` handling does not clear cached session state and mutation `401` responses do not redirect to login, contrary to the spec's API usage contract.
- Updated project memory to reflect review changes requested.

Validation:
- command: `make test-frontend`: PASS — 2 frontend test files, 22 tests passed.
- command: `make lint`: PASS — backend Ruff and frontend ESLint passed.
- command: `make format-check`: PASS — backend Ruff format check and frontend Prettier passed.
- command: `make typecheck`: PASS — backend mypy and frontend TypeScript passed.

Review:
- decision: CHANGES_REQUESTED

Known gaps:
- Fix organization query and mutation `401 not_authenticated` handling so session cache is cleared and the user reaches `/login`.

### 2026-06-24 — SPEC-105 — Frontend organizations UI implemented

Role: Ingeniero de software
Branch: codex/spec-105-frontend-organizations-ui
Commit/PR: Pending
Status: Implemented

Summary:
- Implemented frontend organization routes for list, create, detail, settings, and members under the authenticated app shell.
- Added organization API hooks and types for `SPEC-102` endpoints, including create/update/delete, member listing, role changes, member removal, and ownership transfer.
- Updated app navigation and dashboard entry points so Organizations is active while Projects/Tasks remain unavailable until `SPEC-106`.
- Added route-level frontend tests for empty/list states, creation errors, role-aware detail/settings/member controls, destructive confirmation, owner member actions, safe `403`/`404` handling, and auth redirects.
- Updated `SPEC-105` status and project memory for review handoff.

Validation:
- command: `cd frontend && npm run test`: PASS — 2 files, 22 tests passed.
- command: `cd frontend && npm run typecheck`: PASS.
- command: `cd frontend && npm run lint`: PASS.
- command: `cd frontend && npm run format:check`: PASS.
- command: `make test-frontend`: PASS — 2 frontend test files, 22 tests passed.
- command: `make lint`: PASS — backend Ruff and frontend ESLint passed.
- command: `make format-check`: PASS — backend Ruff format check and frontend Prettier passed.
- command: `make typecheck`: PASS — backend mypy and frontend TypeScript passed.
- command: `make smoke`: PASS — Docker Compose built/started backend, frontend, PostgreSQL, and Adminer; health/Adminer/frontend checks passed.
- command: `make verify-no-db`: PASS — lint, format, type checks, backend non-DB tests, and frontend tests passed.

Review:
- decision: N/A — implementation awaits review.

Known gaps:
- `SPEC-105` review approval remains pending.
- `SPEC-106` project/task UI remains unimplemented.

### 2026-06-24 — SPEC-105/SPEC-106 — Frontend work specs prepared

Role: Arquitecto de specs
Branch: main
Commit/PR: Pending
Status: Ready

Summary:
- Added `SPEC-105` for frontend organization/workspace UI, including routes, active organization context, owner/admin/member states, member management, API usage, acceptance criteria, and frontend validation requirements.
- Added `SPEC-106` for frontend projects and tasks UI, including routes, project/task forms, filters, assignment controls, archived-project behavior, API usage, acceptance criteria, and frontend validation requirements.
- Updated project memory and spec index so the next implementation order is `SPEC-105` then `SPEC-106`, with `SPEC-201` remaining Draft and `SPEC-301` still Ready but lower priority than the core UI.

Validation:
- command: `git diff --check`: PASS
- command: implementation harness NOT RUN — spec/documentation changes only; product code was not changed.

Review:
- decision: N/A

Known gaps:
- `SPEC-105` and `SPEC-106` are ready but not implemented.
- `SPEC-201` remains Draft until notification-worthy task events are finalized.

### 2026-06-23 — SPEC-103 — Docker validation retried

Role: Ingeniero de software
Branch: main
Commit/PR: Pending
Status: Reviewed

Summary:
- Re-ran Docker-backed validation after Docker Desktop was started.
- Confirmed Docker Compose can build/start the stack and Alembic can validate migration `0005` from inside the backend container.
- Confirmed host-side Alembic access to `localhost:5432` still fails in this WSL environment, so `migrations-check-compose` remains the reliable DB validation path here.

Validation:
- command: `docker --version`: PASS — Docker CLI responded.
- command: `make smoke`: PASS — PostgreSQL, backend, Adminer, and frontend built, started, and responded.
- command: `make migrations-check-compose`: PASS — Alembic upgrade/check passed inside the backend container.
- command: `make migrations-check`: FAIL — host process could not connect to PostgreSQL at `localhost:5432`.
- command: `LOCAL_DATABASE_URL=postgresql+psycopg://opdesk:opdesk_dev_password@127.0.0.1:5432/opdesk poetry run alembic current`: FAIL — same host-to-PostgreSQL connection issue.
- command: `make verify-no-db`: PASS — lint, format, backend/frontend type checks, backend tests, and frontend tests passed.

Review:
- decision: APPROVED on 2026-06-23

Known gaps:
- None for `SPEC-103`; host-side PostgreSQL connectivity remains an environment limitation, covered by `migrations-check-compose`.

### 2026-06-23 — SPEC-103 — Integrated locally

Role: Ingeniero de software
Branch: main
Commit/PR: `d897f6c`
Status: Merged

Summary:
- Committed the review-approved `SPEC-103` backend projects/tasks implementation and harness updates to local `main`.
- Included migration `0005`, project/task API surfaces, endpoint tests, project memory, and the sandbox-friendly validation targets.

Validation:
- command: `make verify-no-db`: PASS — lint, format, backend/frontend type checks, backend tests, and frontend tests passed before commit.
- command: `make migrations-check-compose`: NOT RUN in final integration session — Docker CLI is not available in this WSL environment; prior `SPEC-103` migration validation passed outside sandbox and is recorded below.
- command: `git diff --cached --check`: PASS before commit.

Review:
- decision: APPROVED on 2026-06-23

Known gaps:
- Commit is local only; push/PR publication remains pending.

### 2026-06-23 — SPEC-103 — Harness sandbox targets added

Role: Ingeniero de software
Branch: main
Commit/PR: Pending
Status: Implemented

Summary:
- Added `make verify-no-db` for lint, format, type checks, and non-DB tests without Docker/PostgreSQL access.
- Kept `make verify` as the complete check by delegating to `verify-no-db` plus `migrations-check`.
- Added `make migrations-check-compose` to run Alembic upgrade/check from inside the backend container through Compose networking.
- Updated local validation docs to explain sandbox permission constraints for host PostgreSQL ports and Docker socket access.

Validation:
- command: `make verify-no-db`: PASS — lint, format, backend/frontend type checks, backend tests, and frontend tests passed.
- command: `make migrations-check-compose`: FAIL in sandbox — Docker socket access was denied before elevation.
- command: `make migrations-check-compose`: PASS outside sandbox — Alembic upgrade/check passed inside the backend container.
- command: `git diff --check`: PASS.

Review:
- decision: N/A — harness documentation/target refinement after `SPEC-103` review approval.

Known gaps:
- None.

### 2026-06-23 — SPEC-103 — Review approved

Role: Review agent
Branch: main
Commit/PR: Pending
Status: Reviewed

Summary:
- Reviewed `SPEC-103` implementation against the feature spec, `SPEC-001`, `ADR-002`, `ADR-007`, project memory, migration `0005`, routes, services, repositories, schemas, and endpoint tests.
- Confirmed tenant-aware project/task lookups hide non-member resources with `404`, known members without action permission receive `403`, task assignees are organization members, archived projects reject new tasks, and `completed_at` follows `done` transitions.
- Verified project memory reflects `SPEC-103` implementation and validation evidence.

Validation:
- command: `make test-backend`: PASS — 65 passed, 2 DB tests deselected.
- command: `make lint`: PASS — backend Ruff and frontend ESLint passed.
- command: `git diff --check`: PASS.
- command: prior `make verify`: PASS outside sandbox — lint, format, backend/frontend type checks, backend/frontend tests, migration upgrade, and Alembic check passed.
- command: prior `make smoke`: PASS — PostgreSQL, backend, Adminer, and frontend built, started, and responded.

Review:
- decision: APPROVED

Known gaps:
- None for `SPEC-103`; frontend organization/project/task UI remains future spec work.

### 2026-06-23 — SPEC-103 — Projects and tasks implemented

Role: Ingeniero de software
Branch: main
Commit/PR: Pending
Status: Implemented

Summary:
- Added project/task SQLAlchemy models, public enums, migration `0005`, schemas, repositories, services, and FastAPI routers.
- Registered project/task routes and implemented tenant-aware lookups that hide cross-tenant resources with `404` while returning `403` for known members without action permission.
- Enforced same-organization assignees, member self-assignment limits, owner/admin reassignment, archived-project task rejection, task filters, and `completed_at` transitions.
- Added endpoint-level tests for the `SPEC-103` acceptance criteria and updated project memory for review handoff.
- Fixed the initial PostgreSQL enum migration issue by creating enum types explicitly and reusing them with `create_type=False`.

Validation:
- command: `cd backend && poetry run ruff check .`: PASS.
- command: `cd backend && poetry run ruff format --check .`: PASS after formatting the new migration.
- command: `cd backend && poetry run pytest -m "not db"`: PASS — 65 passed, 2 DB tests deselected.
- command: `make typecheck`: PASS — backend mypy and frontend TypeScript checks passed.
- command: `make migrations-check`: PASS outside sandbox — migration `0005` applied and Alembic found no new upgrade operations.
- command: `docker compose exec backend poetry run alembic upgrade head`: PASS outside sandbox after rebuilding backend image with the corrected migration.
- command: `docker compose exec backend poetry run alembic check`: PASS outside sandbox — no new upgrade operations detected.
- command: `make verify`: PASS outside sandbox — lint, format, backend/frontend type checks, backend/frontend tests, migration upgrade, and Alembic check passed.
- command: `make smoke`: PASS — PostgreSQL, backend, Adminer, and frontend built, started, and responded.
- command: `git diff --check`: PASS before this memory update.

Review:
- decision: N/A — implementation awaits review.

Known gaps:
- `SPEC-103` review approval remains pending.
- Frontend organization/project/task UI remains intentionally outside `SPEC-103`.

### 2026-06-23 — SPEC-103 — Implementation handoff refreshed

Role: Arquitecto de specs
Branch: main
Commit/PR: Pending
Status: Ready

Summary:
- Reviewed agent-facing repository instructions, `docs/agent-workflow.md`, `docs/project-state.md`, spec index, current validation baseline, and relevant ADRs after the previous Codex session ended.
- Updated project state to reflect that `main` is current, `SPEC-102` is published and review approved, and `SPEC-103` is the next implementation target.
- Added a SPEC-103 implementation handoff with likely backend files, first implementation slice, and key tenant/RBAC/archive/status-transition risks.

Validation:
- command: `git status -sb`: PASS — clean before documentation edits.
- command: `git log --oneline --decorate -5`: PASS — confirmed HEAD is `da852c0` on `main` with `origin/main`.
- command: `git diff --check`: PASS — documentation/spec handoff edits have no whitespace errors.
- command: implementation harness NOT RUN — documentation/spec handoff only; product code was not changed.

Review:
- decision: N/A

Known gaps:
- `SPEC-103` still needs implementation and validation by Ingeniero de software.

### 2026-06-18 — SPEC-102 — AC-15 review fix approved

Role: Ingeniero de software and Review agent
Branch: codex/spec-102-organizations-rbac
Commit/PR: `7d404fd` / draft PR `#3`
Status: Reviewed

Summary:
- Added the missing endpoint assertion that an organization `member` receives `403 insufficient_role` when attempting permanent organization deletion.
- Re-reviewed AC-15 alongside the existing admin `403`, non-member `404`, owner deletion, user retention, membership cascade, and slug-reuse assertions.
- Updated project memory to mark `SPEC-102` implemented and review approved.

Validation:
- command: `make test-backend`: PASS — 53 passed, 2 DB tests deselected.
- command: `make smoke`: PASS — PostgreSQL, backend, Adminer, and frontend built, started, and responded.
- command: `make verify`: PASS outside sandbox — lint, format, backend/frontend type checks and tests, migration `0004`, and Alembic drift checks passed.
- command: `make test-backend-db`: PASS outside sandbox — 2 PostgreSQL tests passed, including concurrent ownership transfer.

Review:
- decision: APPROVED

Known gaps:
- None for `SPEC-102`; invitations remain explicitly outside its scope.

### 2026-06-18 — SPEC-102 — Single-owner revision changes requested

Role: Review agent
Branch: main
Commit/PR: Pending
Status: Reviewed

Summary:
- Reviewed the revised single-owner model, migration `0004`, generic role restrictions, ownership transfer, permanent deletion, tenant isolation, audit behavior, tests, and project memory against `SPEC-102`, `SPEC-001`, and `ADR-007`.
- Confirmed the implementation preserves one owner, serializes concurrent transfers/deletion, revalidates ownership after locking, rolls back failed transfers, retains users on deletion, and reuses deleted slugs.
- Found one acceptance-test gap: AC-15 requires both admin and member deletion attempts to return `403`, but the deletion test covers admin and non-member only.

Validation:
- command: `make test-backend`: PASS — 53 passed, 2 DB tests deselected.
- command: `make lint`: PASS.
- command: `make format-check`: PASS.
- command: `make typecheck`: PASS — backend and frontend checks passed.
- command: `make smoke test-backend-db migrations-check`: PASS — services responded, 2 PostgreSQL tests passed, migration `0004` was current, and Alembic found no new operations.
- command: `git diff --check`: PASS before this memory update.

Review:
- decision: CHANGES_REQUESTED

Known gaps:
- Add endpoint-level coverage asserting a `member` receives `403 insufficient_role` from `DELETE /api/v1/organizations/{organization_id}`, then rerun the affected tests and request re-review.

### 2026-06-18 — SPEC-102 — Single-owner revision implemented

Role: Ingeniero de software
Branch: main
Commit/PR: Pending
Status: Implemented

Summary:
- Added migration `0004` and matching SQLAlchemy metadata for a unique partial owner index per organization.
- Restricted generic membership role/removal operations from assigning, demoting, or removing the owner role.
- Added atomic ownership transfer with organization-row locking, post-lock owner revalidation, ordered demotion flush, rollback on persistence failure, and audit logging.
- Added owner-only permanent organization deletion with serialized locking, membership cleanup, retained user accounts, slug reuse, and audit logging.
- Expanded endpoint coverage and added a PostgreSQL concurrency test forcing two transfers to authorize before competing for the same organization lock.

Validation:
- command: `make verify`: PASS — lint, format, strict backend/frontend types, 53 backend tests, 12 frontend tests, `alembic upgrade head`, and `alembic check` passed.
- command: `make smoke`: PASS — PostgreSQL, backend, Adminer, and frontend built, started, and responded.
- command: `make test-backend-db`: PASS — 2 PostgreSQL tests passed, including concurrent ownership transfer.
- command: `make migrations-check`: PASS — migration `0004` applied and Alembic detected no new upgrade operations.
- command: `git diff --check`: PASS before this memory update.

Review:
- decision: N/A — revised implementation awaits review.

Known gaps:
- No implementation gaps identified; review approval remains pending.

### 2026-06-18 — SPEC-102 — Single-owner policy and organization deletion spec refresh

Role: Arquitecto de specs
Branch: main
Commit/PR: Pending
Status: Ready

Summary:
- Replaced multiple-owner/last-owner policy with exactly one owner per organization.
- Added a dedicated atomic ownership-transfer contract that promotes an existing member and demotes the previous owner to admin.
- Prevented generic membership role/removal endpoints from assigning, demoting, or removing the owner role.
- Added owner-only permanent organization deletion with membership cleanup, retained user accounts, and slug reuse.
- Added migration, PostgreSQL concurrency, audit, error, and acceptance requirements, and aligned `ADR-007` with the revised policy.

Validation:
- command: `git diff --check`: PASS.
- command: implementation harness NOT RUN — spec/ADR/project-memory-only change; implementation validation is required after code alignment.

Review:
- decision: N/A

Known gaps:
- Existing organization code, migration, and tests implement the superseded multiple-owner policy and must be updated before `SPEC-102` can return to review.

### 2026-06-18 — SPEC-102 — Review blocked by owner-removal policy gap

Role: Review agent
Branch: main
Commit/PR: Pending
Status: Blocked

Summary:
- Reviewed the complete implementation against `SPEC-102`, `SPEC-001`, `ADR-007`, migration `0003`, tests, and project memory.
- Found conflicting source-of-truth rules for deleting owners: the permissions table and endpoint description allow removing only non-owner members, while BR-10 and the documented `last_owner_required` delete error imply that a non-final owner may be removed.
- Confirmed the implementation permits deleting an owner whenever another owner remains, but no acceptance test covers that policy choice.

Validation:
- command: `make test-backend`: PASS — 47 passed, 1 DB test deselected.
- command: `make lint`: PASS.
- command: `make format-check`: PASS.
- command: `make typecheck`: PASS — backend and frontend checks passed.
- command: `make smoke migrations-check`: PASS — services responded, migration `0003` was current, and Alembic detected no new upgrade operations.
- command: `git diff --check`: PASS before this memory update.

Review:
- decision: BLOCKED_BY_SPEC_GAP

Known gaps:
- An Arquitecto de specs must decide whether deleting a non-final owner is allowed and document the expected status/error when it is not. Implementation and endpoint tests must then match that decision before re-review.

### 2026-06-18 — SPEC-102 — Review approved

Role: Review agent
Branch: main
Commit/PR: Pending
Status: Reviewed

Summary:
- Reviewed models, migration, repository scoping, service authorization, HTTP contracts, acceptance tests, project memory, and `ADR-007` against `SPEC-102` and `SPEC-001`.
- Confirmed all ten acceptance criteria have endpoint-level coverage and tenant access consistently returns `404` for non-members versus `403` for underprivileged members.
- Moved the final user lookup for role-change responses out of the route and behind the existing user repository boundary.

Validation:
- command: `make smoke`: PASS — PostgreSQL, backend, Adminer, and frontend built, started, and responded.
- command: `make verify`: PASS — lint, format, strict backend/frontend types, 47 backend tests, 12 frontend tests, live `alembic upgrade head`, and `alembic check` passed.
- command: `poetry run pytest tests/test_organizations_api.py -q`: PASS — 12 passed after the review adjustment.
- command: `poetry run ruff check . && poetry run ruff format --check .`: PASS.
- command: `poetry run mypy app`: PASS — no issues in 27 source files.
- command: `git diff --check`: PASS after removing modified Markdown trailing whitespace.

Review:
- decision: APPROVED

Known gaps:
- None for `SPEC-102`; invitations remain explicitly outside its scope.

### 2026-06-18 — SPEC-102 — Organizations and RBAC implemented

Role: Ingeniero de software
Branch: main
Commit/PR: Pending
Status: Implemented

Summary:
- Added organization and membership models with owner/admin/member roles, migration `0003`, uniqueness constraints, and tenant lookup indexes.
- Added organization schemas, tenant-scoped repository queries, service-owned isolation/RBAC policy, final-owner locking, role-change audit logging, and all specified organization/member routes.
- Added 12 endpoint-level tests covering creation, owner membership, slug behavior, tenant isolation, pagination, role permissions, final-owner protection, updates, safe member listing, and membership-only deletion.
- Added `ADR-007` to preserve the tenant isolation and RBAC enforcement pattern for `SPEC-103`.

Validation:
- command: `make test-backend`: PASS — 47 passed, 1 DB test deselected.
- command: `make typecheck`: PASS — backend strict mypy and frontend TypeScript checks passed.
- command: `poetry run alembic upgrade head --sql`: PASS — PostgreSQL DDL generated through migration `0003`.
- command: `make smoke`: PASS — PostgreSQL, backend, Adminer, and frontend started and responded.
- command: `make migrations-check`: PASS — migration `0003` applied to live PostgreSQL and Alembic detected no new upgrade operations.
- command: `make lint`: PASS after fixing one test import-order issue found by the initial run.
- command: `make format-check`: PASS after formatting migration `0003` following the initial run.
- command: `make verify`: PASS — all backend/frontend checks and live migration validation passed.

Review:
- decision: APPROVED on 2026-06-18.

Known gaps:
- None for `SPEC-102`; invitations remain explicitly outside its scope.

### 2026-06-17 — SPEC-002 — Review approved

Role: Review agent
Branch: main
Commit/PR: `86a1332`
Status: Reviewed

Summary:
- Reviewed `SPEC-002` implementation against the human-readable comment convention and source-of-truth caveat.
- Verified file-level comments/docstrings exist on source files under `backend/` and `frontend/` that are in scope.
- Verified representative function/class/component/hook/helper comments are concise and behavior-preserving.
- Updated project state to reflect successful Docker-backed validation and approval.

Validation:
- command: `make smoke`: PASS — Docker Compose built/started PostgreSQL, backend, Adminer, and frontend; health/Adminer/frontend checks succeeded.
- command: `make verify`: PASS outside sandbox — lint, format, typecheck, backend tests, frontend tests, `alembic upgrade head`, and `alembic check` passed.
- command: `git diff --check`: PASS

Review:
- decision: APPROVED

Known gaps:
- None for `SPEC-002`.

### 2026-06-17 — SPEC-002 — Human-readable code comments implemented

Role: Ingeniero de software
Branch: main
Commit/PR: `86a1332`
Status: Implemented

Summary:
- Added file-level comments/docstrings to existing backend, frontend, test, migration, and frontend configuration source files.
- Added concise explanatory comments/docstrings to backend functions/classes, test helpers/fixtures/cases, frontend components/hooks/helpers/types, and migration functions.
- Updated project memory and spec index so `SPEC-002` is implemented and awaiting review.

Validation:
- command: `make lint`: PASS
- command: `make format-check`: PASS
- command: `make test`: PASS — backend 35 passed, 1 DB test deselected; frontend 12 passed.
- command: `make typecheck`: PASS
- command: `make verify`: FAIL — lint, format, typecheck, backend tests, and frontend tests passed; Alembic migration check failed because local PostgreSQL was not accepting connections.
- command: `make verify` outside sandbox: FAIL — same non-Docker checks passed; Alembic failed with connection refused to `127.0.0.1:5432`.
- command: `make smoke`: FAIL — Docker is not installed in this WSL distro, so PostgreSQL/local services could not be started.
- command: `git diff --check`: PASS

Review:
- decision: APPROVED on 2026-06-17

Known gaps:
- Resolved by the review entry above.

### 2026-06-17 — SPEC-002 — Human-readable code comments spec

Role: Arquitecto de specs
Branch: main
Commit/PR: `86a1332`
Status: Ready

Summary:
- Added `SPEC-002` for repository-wide human-readable file/function/class comments and the initial existing-code comment pass.
- Updated `AGENTS.md` to make the convention mandatory for future source code while clarifying comments are reader support, not source-of-truth material for agents.
- Added `ADR-006` to record the durable decision and updated spec routing/project state so `SPEC-002` is the next implementation target.

Validation:
- command: NOT RUN — spec/documentation-only change.

Review:
- decision: N/A

Known gaps:
- Resolved by the implementation entry above.

### 2026-06-16 — SPEC-104 — Merged locally to main

Role: Ingeniero de software
Branch: main
Commit/PR: `5d019bd`, merge commit pending push
Status: Merged

Summary:
- Committed `SPEC-104` implementation as `5d019bd`.
- Pushed branch `spec-104-frontend-auth-shell` to origin.
- Merged `spec-104-frontend-auth-shell` into local `main`.
- Updated project state so future agents start from `main` and treat `SPEC-102` as the next likely implementation target.

Validation:
- command: NOT RUN after merge — merge was clean; pre-merge `make smoke` and `make verify` passed and are recorded below.

Review:
- decision: APPROVED

Known gaps:
- `main` push and feature-branch deletion still pending in this publishing step.

### 2026-06-16 — SPEC-104 — Final review approved

Role: Review agent
Branch: spec-104-frontend-auth-shell
Commit/PR: Pending
Status: Reviewed

Summary:
- Reviewed the profile `401` review fix for `SPEC-104`.
- Verified `PATCH /api/v1/users/me` now clears session state and redirects to `/login` on `401 not_authenticated`.
- Verified test coverage for profile update losing authentication.
- Verified project memory reflects the fixed state and validation baseline.

Validation:
- command: `cd frontend && npm run lint`: PASS
- command: `cd frontend && npm run test`: PASS — 12 passed.
- command: `cd frontend && npm run typecheck`: PASS
- command: `cd frontend && npm run build`: PASS
- command: `make test`: PASS — backend 35 passed, 1 DB test deselected; frontend 12 passed.
- command: `git diff --check`: PASS
- command: `make smoke`: PASS outside sandbox — recorded in the review-fix entry.
- command: `make verify`: PASS outside sandbox — recorded in the review-fix entry.

Review:
- decision: APPROVED

Known gaps:
- No E2E browser tests yet; `SPEC-104` recommends adding Playwright later after the frontend/local server harness stabilizes.

### 2026-06-16 — SPEC-104 — Profile 401 review fix

Role: Ingeniero de software
Branch: spec-104-frontend-auth-shell
Commit/PR: Pending
Status: Implemented

Summary:
- Fixed `PATCH /api/v1/users/me` profile update handling so `401 not_authenticated` clears the session query state and redirects to `/login`.
- Added frontend route test coverage for profile update losing authentication.
- Updated project memory to reflect the review fix and current validation baseline.

Validation:
- command: `cd frontend && npm run lint`: PASS
- command: `cd frontend && npm run format:check`: PASS
- command: `cd frontend && npm run typecheck`: PASS
- command: `cd frontend && npm run test`: PASS — 12 passed.
- command: `cd frontend && npm run build`: PASS
- command: `make lint`: PASS
- command: `make format-check`: PASS
- command: `make typecheck`: PASS
- command: `make test`: PASS — backend 35 passed, 1 DB test deselected; frontend 12 passed.
- command: `make smoke`: PASS outside sandbox — Docker Compose built/started backend, PostgreSQL, Adminer, and frontend; `/health`, Adminer, and `http://127.0.0.1:5173` responded.
- command: `make verify`: PASS outside sandbox — lint, format, typecheck, tests, Alembic upgrade, and Alembic check passed.

Review:
- decision: N/A

Known gaps:
- No E2E browser tests yet; `SPEC-104` recommends adding Playwright later after the frontend/local server harness stabilizes.

### 2026-06-16 — SPEC-104 — Review changes requested

Role: Review agent
Branch: spec-104-frontend-auth-shell
Commit/PR: Pending
Status: Reviewed

Summary:
- Reviewed `SPEC-104` frontend app shell/auth UI implementation against the spec, API conventions, project memory, and current diff.
- Verified the frontend app shell, public/auth routes, auth/profile forms, API client credential handling, future navigation unavailable state, Make/Compose integration, and memory updates.
- Found one required fix: profile update `401 not_authenticated` responses currently render an error instead of clearing session state and redirecting to `/login`, which conflicts with `SPEC-104` profile and failure-case requirements.

Validation:
- command: `cd frontend && npm run lint`: PASS
- command: `cd frontend && npm run format:check`: PASS
- command: `cd frontend && npm run typecheck`: PASS
- command: `cd frontend && npm run test`: PASS — 11 passed.
- command: `make lint`: PASS
- command: `make format-check`: PASS
- command: `make typecheck`: PASS
- command: `make test`: PASS — backend 35 passed, 1 DB test deselected; frontend 11 passed.
- command: `make smoke`: PASS — Docker Compose built/started backend, PostgreSQL, Adminer, and frontend; `/health`, Adminer, and `http://127.0.0.1:5173` responded.
- command: `make migrations-check`: PASS outside sandbox — sandboxed process could not connect to local `localhost:5432`.
- command: `make verify`: PASS outside sandbox — lint, format, typecheck, tests, Alembic upgrade, and Alembic check passed.

Review:
- decision: CHANGES_REQUESTED

Known gaps:
- Add/fix profile-call `401` handling and test coverage before push.

### 2026-06-16 — Repository memory — Agent operational state and routing

Role: Arquitecto de specs
Branch: spec-104-frontend-auth-shell
Commit/PR: Pending
Status: Ready

Summary:
- Added `docs/project-state.md` as the compact current-state dashboard for active work, implemented specs, next likely work, known gaps, validation baseline, code map, and reading order.
- Expanded `specs/README.md` into a richer routing index with dependencies, primary implementation surfaces, and a central touch-to-spec routing table.
- Updated `docs/agent-workflow.md` so agents start from `docs/project-state.md` and follow the current implementation order.
- Added `Scope And Required Context` sections to the feature spec template and existing feature specs.
- Updated `AGENTS.md` to make `docs/project-state.md` part of required project memory.
- Added `ADR-005` to capture the durable decision to split current operational memory from historical implementation evidence.

Validation:
- command: NOT RUN — documentation/process-only change.

Review:
- decision: N/A

Known gaps:
- `SPEC-104` implementation remains locally implemented with uncommitted changes and still needs review/commit.

### 2026-06-15 — SPEC-104 — Frontend auth shell implemented

Role: Ingeniero de software
Branch: spec-104-frontend-auth-shell
Commit/PR: Pending
Status: Implemented

Summary:
- Created the initial React TypeScript frontend under `frontend/` with Vite, React Router, TanStack Query, React Hook Form, Zod, Tailwind CSS, Vitest, and Testing Library.
- Implemented the public landing page, login, signup, authenticated app shell, protected/public route guards, logout, and profile view/update flows against the `SPEC-101` API contract.
- Added disabled/unavailable future navigation for organizations, projects, and tasks without fake backend data or unsupported CRUD.
- Integrated the frontend into Docker Compose, `.env.example`, README setup, local validation docs, and Make targets.
- Updated frontend dev dependencies to Vite `8.0.16`, Vitest `4.1.9`, and `@vitejs/plugin-react` `6.0.2`; `npm audit` reports 0 vulnerabilities.

Validation:
- command: `cd frontend && npm run lint`: PASS
- command: `cd frontend && npm run format:check`: PASS
- command: `cd frontend && npm run typecheck`: PASS
- command: `cd frontend && npm run test`: PASS — 11 passed.
- command: `cd frontend && npm run build`: PASS
- command: `cd frontend && npm audit --omit=dev`: PASS — 0 vulnerabilities.
- command: `cd frontend && npm audit`: PASS — 0 vulnerabilities after Vite/Vitest update.
- command: `make lint`: PASS
- command: `make format-check`: PASS
- command: `make typecheck`: PASS
- command: `make test`: PASS — backend 35 passed, 1 DB test deselected; frontend 11 passed.
- command: `make smoke`: PASS — Docker Compose built/started backend, PostgreSQL, Adminer, and frontend; `/health`, Adminer, and `http://127.0.0.1:5173` responded.
- command: `make verify`: PASS — required running outside the sandbox because the sandboxed process could not connect to local `localhost:5432`; lint, format, typecheck, tests, Alembic upgrade, and Alembic check passed.

Review:
- decision: N/A

Known gaps:
- No E2E browser tests yet; SPEC-104 recommends adding Playwright later after the frontend/local server harness stabilizes.
- Organization, project, and task UI remains intentionally unavailable until their frontend specs are active.

### 2026-06-15 — SPEC-104 — Frontend app shell and auth UI spec

Role: Arquitecto de specs
Branch: main
Commit/PR: Pending
Status: Ready

Summary:
- Reviewed current specs and completed backend `SPEC-101` work.
- Added `SPEC-104` for the initial React frontend, public landing page, login/signup flows, authenticated app shell, logout, and profile management.
- Reserved navigation/product structure for future organizations, projects, and tasks without allowing fake data or unsupported CRUD before `SPEC-102`/`SPEC-103` frontend work.
- Updated the spec index and dependency order so frontend auth shell follows backend auth and precedes future product UI expansion.

Validation:
- command: NOT RUN — spec/documentation-only change.

Review:
- decision: N/A

Known gaps:
- Frontend implementation pending.
- A frontend package-manager ADR may be needed during implementation if the project chooses anything other than npm.

### 2026-06-15 — SPEC-101 — Review approved after uvloop API tests

Role: Review agent
Branch: spec-011-local-database-admin
Commit/PR: Pending
Status: Reviewed

Summary:
- Reviewed SPEC-101 endpoint-level API test changes after Docker was available.
- Verified the auth API tests now exercise public HTTP endpoints with FastAPI `TestClient` and `uvloop`.
- Verified logout now returns a real `204` response through the HTTP layer.
- Verified migrations, Docker smoke checks, DB test, lint, formatting, typecheck, and backend tests.

Validation:
- command: `make smoke`: PASS — Compose built/started backend, PostgreSQL, and Adminer; backend `/health` and Adminer HTTP checks passed.
- command: `make verify`: PASS — lint, format-check, backend tests, Alembic upgrade, and Alembic check passed.
- command: `make typecheck`: PASS — no issues in 22 source files.
- command: `make test-backend-db`: PASS — 1 passed, 35 deselected.
- command: `docker compose exec -T postgres pg_isready -U opdesk -d opdesk`: PASS — PostgreSQL accepting connections.

Review:
- decision: APPROVED

Known gaps:
- None for the SPEC-101 backend/API test scope. Frontend auth screens remain pending until frontend scaffold exists.

### 2026-06-15 — SPEC-101 — Endpoint-level auth API tests with uvloop

Role: Ingeniero de software
Branch: spec-011-local-database-admin
Commit/PR: Pending
Status: Implemented

Summary:
- Added endpoint-level SPEC-101 API tests using FastAPI `TestClient` with `backend_options={"use_uvloop": True}`.
- Added test dependency overrides for isolated SQLite DB sessions and auth settings.
- Covered register success, duplicate email, weak password, first-user superuser, later-user non-superuser, login success/failure/inactive user, refresh success/failure, logout cookie clearing, `/api/v1/users/me` unauthenticated/authenticated, profile update, and invalid profile through public HTTP endpoints.
- Fixed `POST /api/v1/auth/logout` to return an actual `204` status when returning the injected FastAPI `Response`.

Validation:
- command: `cd backend && poetry run pytest tests/test_auth_and_users.py`: PASS — 31 passed
- command: `make test-backend`: PASS — 35 passed, 1 DB test deselected
- command: `make lint`: PASS
- command: `make format-check`: PASS
- command: `make typecheck`: PASS — no issues in 22 source files
- command: `make verify`: FAIL/ENV — lint, format, and backend tests passed, then `migrations-check` failed because PostgreSQL/Docker was unavailable from this WSL session.
- command: `docker compose ps`: FAIL/ENV — Docker CLI not available in this WSL distro.

Review:
- decision: N/A

Known gaps:
- Docker-backed migration, DB, smoke, and full verify checks remain unverified in this session until Docker is available from WSL again.

### 2026-06-15 — SPEC-101 — uvloop added to API test harness specs

Role: Arquitecto de specs
Branch: spec-011-local-database-admin
Commit/PR: Pending
Status: Ready

Summary:
- Reviewed API and validation specs after the ASGI client investigation.
- Added `uvloop` guidance to `specs/harness/local-validation.md` for in-process backend API tests using FastAPI `TestClient` or HTTPX `ASGITransport`.
- Updated `SPEC-101` to prefer `uvloop` for in-process ASGI tests when synchronous endpoints or dependencies hang under the default `asyncio` event loop.

Validation:
- command: NOT RUN — spec/documentation-only change.

Review:
- decision: N/A

Known gaps:
- Implementation still needs to update SPEC-101 API tests to use endpoint-level HTTP coverage.

### 2026-06-15 — SPEC-101 — ASGI investigation readability update

Role: Ingeniero de software
Branch: spec-011-local-database-admin
Commit/PR: Pending
Status: Implemented

Summary:
- Rewrote `docs/spec-101-asgi-client-investigation.md` command examples as readable multiline shell heredocs.
- Preserved the investigation results and recommendation to use `uvloop` for in-process API tests, with Docker/local HTTP as fallback.

Validation:
- command: NOT RUN — documentation-only readability change.

Review:
- decision: N/A

Known gaps:
- SPEC-101 still needs automated API tests that exercise public HTTP endpoints.

### 2026-06-15 — SPEC-101 — API test clarification and ASGI client investigation

Role: Arquitecto de specs / Ingeniero de software
Branch: spec-011-local-database-admin
Commit/PR: Pending
Status: Implemented

Summary:
- Clarified in `SPEC-101` that API tests may use in-process ASGI clients or local Docker HTTP, but must exercise public HTTP endpoints and cookie/error behavior.
- Investigated why FastAPI `TestClient` and HTTPX `ASGITransport` hang in the local environment.
- Added `docs/spec-101-asgi-client-investigation.md` with reproduction steps, command evidence, likely causes, and recommended solutions.
- Found that the hang reproduces below FastAPI in AnyIO/asyncio thread wakeups, and that `uvloop` resolves the minimal reproductions.

Validation:
- command: minimal FastAPI `TestClient` without `uvloop`: FAIL/REPRODUCED — request hangs until timeout.
- command: minimal HTTPX `ASGITransport` with async endpoint: PASS.
- command: minimal HTTPX `ASGITransport` with sync endpoint: FAIL/REPRODUCED — request hangs until timeout.
- command: isolated `anyio.to_thread.run_sync`: FAIL/REPRODUCED — hangs until timeout.
- command: Python `threading` and `ThreadPoolExecutor`: PASS — native threads work.
- command: `asyncio.call_soon_threadsafe` with default event loop: FAIL/REPRODUCED — worker runs but loop does not wake without another timer.
- command: `asyncio.call_soon_threadsafe`, `anyio.to_thread.run_sync`, FastAPI `TestClient`, and HTTPX `ASGITransport` with `uvloop`: PASS.

Review:
- decision: N/A

Known gaps:
- SPEC-101 still needs automated API tests that exercise public HTTP endpoints. Recommended next step is FastAPI `TestClient(app, backend_options={"use_uvloop": True})`, with Docker/local HTTP as fallback.

### 2026-06-11 — SPEC-101 — Backend auth and users implemented

Role: Ingeniero de software
Branch: spec-011-local-database-admin
Commit/PR: Pending
Status: Implemented

Summary:
- Implemented backend auth/user API endpoints for registration, login, refresh, logout, current user, and profile update.
- Added `users` SQLAlchemy model, repository/service layers, Pydantic schemas, API error shape, auth dependencies, Argon2 password hashing, and signed JWT cookies.
- Added Alembic migration `0002` for `users`.
- Added auth settings and safe local placeholders to `.env.example`.
- Added backend tests for password policy/hash, register/login/refresh/logout, current user, profile update, inactive user handling, duplicate email, and first-user superuser behavior.
- Updated README and spec index to reflect implemented backend auth scope.

Validation:
- command: `make lint`: PASS
- command: `make format-check`: PASS
- command: `make test-backend`: PASS — 21 passed, 1 DB test deselected
- command: `make typecheck`: PASS — no issues in 22 source files
- command: `make migrations-check`: PASS — migration `0002` applied and Alembic check found no new upgrade operations
- command: `make test-backend-db`: PASS — 1 passed, 21 deselected
- command: `make smoke`: PASS — backend and Adminer responded after Docker rebuild
- command: `make verify`: PASS
- command: direct `curl` register/login against Docker backend: PASS — registration returned safe user payload and login set httpOnly `access_token`/`refresh_token` cookies.

Review:
- decision: N/A

Known gaps:
- Frontend auth screens remain pending because the frontend scaffold does not exist yet.
- In-process HTTP client tests using FastAPI `TestClient`/HTTPX ASGI transport hang in this environment, so backend tests exercise route functions directly and Docker `curl` smoke covers real HTTP register/login.

### 2026-06-11 — SPEC-101 — Auth spec refresh after scaffold/admin tooling

Role: Arquitecto de specs
Branch: spec-011-local-database-admin
Commit/PR: Pending
Status: Ready

Summary:
- Reviewed `SPEC-101` after `SPEC-010` scaffold and `SPEC-011` local DB admin work.
- Clarified that Adminer is inspection-only and not a functional dependency for auth behavior.
- Added auth configuration contract for token/cookie settings and updated harness expectations to current Make targets.
- Added test-state guidance for first-user superuser bootstrap.

Validation:
- command: NOT RUN — spec/documentation-only change.

Review:
- decision: N/A

Known gaps:
- `SPEC-101` implementation still pending.

### 2026-06-11 — SPEC-011 — Review approved

Role: Review agent
Branch: spec-011-local-database-admin
Commit/PR: `269149c`, PR https://github.com/RGAlvaro/opdesk/pull/2
Status: Reviewed

Summary:
- Reviewed `SPEC-011` implementation after the Adminer port override fix.
- Verified local-only Adminer wiring, docs, ADR, harness updates, and implementation log evidence.

Validation:
- command: `make lint`: PASS
- command: `make format-check`: PASS
- command: `make test-backend`: PASS — 4 passed, 1 DB test deselected
- command: `docker compose config`: PASS — Adminer binds to localhost and uses the configured port.
- command: `make smoke`: PASS — verified both `.env` override path on `8081` during fix validation and default `8080` after removing temporary `.env`.

Review:
- decision: APPROVED

Known gaps:
- None.

### 2026-06-11 — SPEC-011 — Adminer port override review fix

Role: Ingeniero de software
Branch: spec-011-local-database-admin
Commit/PR: `ff11f48`, PR https://github.com/RGAlvaro/opdesk/pull/2
Status: Implemented

Summary:
- Updated `Makefile` so Make includes `.env` when present and exports its variables to recipes.
- Added a default `ADMINER_PORT ?= 8080` and made `make smoke` curl `$(ADMINER_PORT)`, aligning smoke checks with Docker Compose `.env` resolution.

Validation:
- command: `make -n smoke` without `.env`: PASS — Adminer curl resolves to `http://127.0.0.1:8080`.
- command: temporary `.env` with `ADMINER_PORT=8081` plus `make -n smoke`: PASS — Adminer curl resolves to `http://127.0.0.1:8081`.
- command: temporary `.env` with `ADMINER_PORT=8081` plus `docker compose config`: PASS — Adminer publishes `127.0.0.1:8081`.
- command: temporary `.env` with `ADMINER_PORT=8081` plus `make smoke`: PASS — backend health returned `{"status":"ok"}` and Adminer returned the login page on port `8081`.
- command: `make smoke` after removing temporary `.env`: PASS — backend health returned `{"status":"ok"}` and Adminer returned the login page on default port `8080`.
- command: `make lint`: PASS
- command: `make format-check`: PASS
- command: `make test-backend`: PASS — 4 passed, 1 DB test deselected
- command: `docker compose ps`: PASS — `adminer`, `backend`, and healthy `postgres` services are running.

Review:
- decision: N/A

Known gaps:
- None.

### 2026-06-10 — SPEC-011 — Local database admin implemented

Role: Ingeniero de software
Branch: spec-011-local-database-admin
Commit/PR: `d240330`, PR https://github.com/RGAlvaro/opdesk/pull/2
Status: Implemented

Summary:
- Added local-only Adminer service to Docker Compose with localhost host binding and default PostgreSQL server wiring.
- Documented Adminer URL, login values, local-only scope, and manual-edit caveat in README.
- Added `ADMINER_PORT` to `.env.example` and Adminer HTTP check to local smoke validation.

Validation:
- command: `make lint`: PASS
- command: `make format-check`: PASS
- command: `make test-backend`: PASS — 4 passed, 1 DB test deselected
- command: `rg -n "adminer|ADMINER" docker-compose.yml .env.example Makefile README.md specs/harness/local-validation.md specs/features/011-local-database-admin.md docs/decisions/ADR-004-local-database-admin-tool.md docs/implementation-log.md`: PASS — local Adminer wiring and docs present.
- command: `test -f docker-compose.prod.yml && rg -n "adminer|ADMINER" docker-compose.prod.yml || true`: PASS — no production Compose file exists yet, so Adminer is not present in production config.
- command: `docker compose config`: PASS — Adminer is configured on `127.0.0.1:8080` and depends on healthy PostgreSQL.
- command: `make smoke`: PASS — backend health returned `{"status":"ok"}` and Adminer returned the login page.
- command: `docker compose ps`: PASS — `adminer`, `backend`, and healthy `postgres` services are running.

Review:
- decision: N/A

Known gaps:
- None.

### 2026-06-10 — SPEC-011 — Local database admin spec

Role: Arquitecto de specs
Branch: main
Commit/PR: Pending
Status: Ready

Summary:
- Added `SPEC-011` for a local-only Adminer panel to inspect the Docker Compose PostgreSQL database.
- Updated the spec index and implementation order.
- Added ADR-004 to record the Adminer-over-pgAdmin local tooling decision and production exclusion.

Validation:
- command: NOT RUN — spec/documentation-only change.

Review:
- decision: N/A

Known gaps:
- `SPEC-011` implementation still pending.

### 2026-06-09 — SPEC-010 — Backend scaffold implemented

Role: Ingeniero de software
Branch: spec-010-backend-scaffold
Commit/PR: `be18383`, `36f9757`, `d97031d`, `ea31737`, `3c84c46`, PR https://github.com/RGAlvaro/opdesk/pull/1, merge `ac242cd`
Status: Merged

Summary:
- Implemented FastAPI backend scaffold with `/health`, settings, SQLAlchemy session setup, Alembic baseline wiring, empty baseline revision, and backend tests.
- Added local PostgreSQL and backend services through Docker Compose with named PostgreSQL volume and health gating.
- Added `.env.example`, `Makefile`, `README.md`, `backend/Dockerfile`, backend `.dockerignore`, and Poetry lockfile.
- Added ADRs for package manager choice, backend module layout, and local/container database URL strategy.
- Tightened `AGENTS.md` memory rules so review-fix commits and validation reruns must update this log before review.

Validation:
- command: `make lint`: PASS
- command: `make format-check`: PASS
- command: `make test-backend`: PASS — 4 passed, 1 DB test deselected
- command: `make typecheck`: PASS
- command: `make migrations-check`: PASS — no new upgrade operations detected
- command: `make test-backend-db`: PASS — 1 DB test passed against Docker PostgreSQL
- command: `make smoke`: PASS — Docker Compose backend/PostgreSQL started and `/health` returned `{"status":"ok"}`
- command: `make verify`: PASS — includes `alembic upgrade head` and `alembic check`

Review:
- decision: APPROVED

Known gaps:
- None.

### 2026-06-09 — SPEC-010 — ADR requirement before implementation

Role: Arquitecto de specs
Branch: main
Commit/PR: Pending
Status: Ready

Summary:
- Clarified that `SPEC-010` implementation must create ADRs for durable scaffold choices.
- Required ADR coverage for package manager choice, backend module layout, and local/container database configuration strategy.

Validation:
- command: NOT RUN — spec/documentation-only change.

Review:
- decision: N/A

Known gaps:
- `SPEC-010` implementation still pending.

### 2026-06-09 — SPEC-010 — Backend scaffold foundation spec

Role: Arquitecto de specs
Branch: main
Commit/PR: `fe4e493`
Status: Ready

Summary:
- Added `SPEC-010` for backend scaffold, local PostgreSQL, SQLAlchemy, Alembic, health checks, and harness.
- Updated dependency order so implementation starts with `SPEC-010` before auth, organizations, and tasks.
- Reframed `SPEC-301` as production deployment and operations built on top of the local scaffold.

Validation:
- command: NOT RUN — spec/documentation-only change.

Review:
- decision: N/A

Known gaps:
- `SPEC-201` remains Draft pending Redis/worker ownership and notification decisions.
- `SPEC-301` still needs final domain/DNS and VPS sizing decisions before production launch.
