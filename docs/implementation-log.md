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
