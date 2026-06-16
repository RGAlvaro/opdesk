# SPEC-010 — Backend Scaffold and Local Database

Status: Implemented  
Owner: Arquitecto de specs  
Last updated: 2026-06-16

## Scope And Required Context

This spec governs:

- Backend scaffold, settings, health endpoint, database session setup, Alembic baseline, Docker Compose PostgreSQL, Make harness, or `.env.example` database settings.

Required context:

- `AGENTS.md`
- `docs/project-state.md`
- `specs/README.md`
- `specs/001-api-conventions.md` for health/API behavior
- `specs/harness/local-validation.md`
- `docs/decisions/ADR-001-python-package-manager.md`
- `docs/decisions/ADR-002-backend-module-layout.md`
- `docs/decisions/ADR-003-local-container-database-configuration.md`

Memory updates:

- `docs/project-state.md` if scaffold state, validation baseline, or known gaps change
- `docs/implementation-log.md` for meaningful implementation, review, or validation events
- `specs/README.md` if status, dependencies, order, or primary surfaces change
- ADRs if package management, module layout, or database topology changes

## Problem

OpsDesk needs a reproducible backend foundation before feature models are implemented. Authentication, organizations, projects, tasks, migrations, tests, and deployment all depend on a working FastAPI scaffold, PostgreSQL service, SQLAlchemy session setup, Alembic baseline, and local validation commands.

## Goals

- Create the minimum backend scaffold needed for later API specs.
- Provide local PostgreSQL through Docker Compose.
- Configure application settings through environment variables and `.env.example`.
- Configure SQLAlchemy 2.x database access and Alembic migrations.
- Provide a health endpoint suitable for local smoke checks.
- Establish initial backend tests, linting, formatting, and migration validation.
- Add Make targets or documented direct commands for the backend/local database harness.

## Dependencies

- Inherits repository stack and source-of-truth rules from `AGENTS.md`.
- Inherits API conventions from `SPEC-001`.
- Supports later data-model specs: `SPEC-101`, `SPEC-102`, `SPEC-103`, and future backend features.

## Non-Goals

- User, organization, project, task, or notification business models.
- Authentication, authorization, or cookie behavior.
- Frontend scaffold.
- Production TLS/reverse proxy deployment. That belongs to `SPEC-301`.
- Redis, Celery, worker services, or background jobs. Those belong to `SPEC-201` and production wiring in `SPEC-301`.
- Kubernetes or cloud-managed database setup.

## Actors And Permissions

| Actor | Permission | Notes |
|---|---|---|
| Developer | Run backend locally, run tests, run migrations | Uses local environment only |
| Review agent | Validate scaffold and database harness | Uses documented commands |
| Anonymous HTTP client | Read health endpoint | Health response exposes no secrets |

## Business Rules

- BR-1: Local development uses PostgreSQL in Docker Compose, not SQLite, for parity with feature migrations.
- BR-2: Real secrets must not be committed. `.env.example` documents required variables with safe placeholder values only.
- BR-3: Backend configuration must use dependency-injected settings or import-safe settings objects, not hardcoded credentials.
- BR-4: Database access must use SQLAlchemy 2.x patterns and explicit session lifecycle management.
- BR-5: Alembic must be initialized before feature tables are added.
- BR-6: The initial Alembic baseline must be deterministic and reviewable, even if it creates no feature tables.
- BR-7: `/health` must return success without exposing database URLs, passwords, host internals, tokens, or stack traces.
- BR-8: Local Docker Compose must define persistent PostgreSQL storage with a named volume.
- BR-9: The backend must be runnable locally without production-only TLS, domain, or Caddy settings.
- BR-10: Harness commands must not weaken validation to pass; missing tools or unavailable services must be reported explicitly.

## Required Repository Impact

Create only the structure needed for this spec:

```text
.
├── .env.example
├── Makefile
├── docker-compose.yml
├── backend/
│   ├── Dockerfile
│   ├── alembic.ini
│   ├── pyproject.toml
│   ├── alembic/
│   ├── app/
│   └── tests/
└── docs/
```

`README.md` may be created or updated if setup commands are documented there. Do not scaffold frontend files in this spec.

## Configuration Contract

`.env.example` must document at least:

| Variable | Purpose | Example |
|---|---|---|
| `APP_ENV` | Runtime environment | `local` |
| `DEBUG` | Enables local debug behavior only | `true` |
| `DATABASE_URL` | SQLAlchemy database URL used by backend/Alembic | `postgresql+psycopg://opdesk:opdesk_dev_password@postgres:5432/opdesk` |
| `POSTGRES_USER` | Local PostgreSQL user | `opdesk` |
| `POSTGRES_PASSWORD` | Local PostgreSQL password placeholder | `opdesk_dev_password` |
| `POSTGRES_DB` | Local PostgreSQL database | `opdesk` |

Rules:

- `DATABASE_URL` may use the Compose service hostname for containerized backend runs.
- If direct host commands are supported, docs must explain the host-side database URL or env override.
- Placeholder values are acceptable for local development only and must not be reused as production secrets.

## Docker Compose Contract

`docker-compose.yml` must include:

- `postgres` service using a stable PostgreSQL image.
- PostgreSQL env wired from `.env`/`.env.example` variables.
- Named PostgreSQL data volume.
- Health check or readiness behavior sufficient for local smoke checks.
- `backend` service once backend Dockerfile exists.

Local Compose may expose PostgreSQL to localhost for developer tooling. Production exposure rules belong to `SPEC-301`.

## Backend Contract

Backend scaffold must include:

- FastAPI application object.
- Settings module using `pydantic-settings`.
- SQLAlchemy engine/session setup.
- Dependency for database sessions.
- Alembic environment wired to application metadata and `DATABASE_URL`.
- `GET /health` endpoint.

### `GET /health`

Response `200`:

```json
{
  "status": "ok"
}
```

The health endpoint may include a database readiness check if implemented without leaking sensitive internals. If database readiness is included, transient database failures should return a non-2xx status with a safe error shape or safe plain health response documented in implementation notes.

## Data Model Impact

No feature tables are created by this spec.

Expected migration impact:

- Alembic is initialized.
- Baseline migration state exists and can be inspected.
- Later feature specs add feature tables through new migrations.

## Frontend Impact

None.

## Acceptance Criteria

- AC-1: Given a fresh checkout, when documented setup commands are followed, then PostgreSQL starts through Docker Compose with a named volume.
- AC-2: Given backend dependencies are installed, when the backend starts, then `GET /health` returns `200` and no sensitive configuration.
- AC-3: Given `.env.example`, when a developer reads it, then required local database variables are documented with safe placeholders.
- AC-4: Given Alembic is configured, when migration validation runs, then the baseline state is valid before feature tables are introduced.
- AC-5: Given backend tests run, when the scaffold is valid, then the health endpoint test passes.
- AC-6: Given lint and format checks run, when scaffold code is valid, then backend checks pass.
- AC-7: Given Docker Compose starts the backend and PostgreSQL, when smoke checks run, then backend health succeeds against the containerized stack.
- AC-8: Given repository review, when files are inspected, then no `.env`, real secret, token, database dump, or generated dependency directory is committed.

## Harness Requirements

Backend tests:

- Health endpoint success.
- Settings load from environment with safe test values.
- Database session dependency can connect when PostgreSQL is available.
- Alembic configuration points at application metadata.

Required commands once available:

```bash
make test-backend
make lint
make format-check
make migrations-check
make smoke
```

Before Make targets exist, use exact direct commands documented in `specs/harness/local-validation.md` and update that file if the package manager or command shape changes during scaffold.

## Observability And Failure Cases

- Health logs should be minimal and must not include `DATABASE_URL` or credentials.
- Database connection failures should be debuggable locally through safe service names and error classes.
- Docker startup failures should be reported through smoke checks rather than hidden by retries.

## Implementation Notes

- Prefer Poetry unless the implementation explicitly updates setup docs and harness commands to another package manager.
- Use PostgreSQL-compatible types from the start, especially for UUID and timestamp behavior expected by later specs.
- Keep route handlers thin even for health checks.
- Create ADRs for durable scaffold choices introduced by this spec, at minimum package manager choice, backend module layout, and local/container database configuration strategy.
- Do not add auth, users, organizations, projects, tasks, Redis, Celery, or frontend code in this spec.
