# OpsDesk

OpsDesk is a spec-driven B2B SaaS portfolio project for operational work management.

## Current Scope

The current implementation covers `SPEC-010` and `SPEC-011`: backend scaffold, local PostgreSQL, Alembic, health checks, Docker Compose, validation harness, and a local-only database admin panel.

## Local Setup

Copy the example environment file if you want local overrides:

```bash
cp .env.example .env
```

Install backend dependencies:

```bash
cd backend
poetry install
```

Start the local container stack:

```bash
docker compose up -d --build
```

Check backend health:

```bash
curl -f http://localhost:8000/health
```

## Local Database Admin

The local Compose stack includes Adminer for direct PostgreSQL inspection during development and review. It is local tooling only and is not part of the production deployment.

Open Adminer after the stack is running:

```text
http://127.0.0.1:8080
```

Use these login values:

| Field | Value |
|---|---|
| System | `PostgreSQL` |
| Server | `postgres` |
| Username | `opdesk` or `POSTGRES_USER` from `.env` |
| Password | `opdesk_dev_password` or `POSTGRES_PASSWORD` from `.env` |
| Database | `opdesk` or `POSTGRES_DB` from `.env` |

If port `8080` is unavailable, set `ADMINER_PORT` in `.env` and restart the stack.

Direct database edits through Adminer bypass application validation and authorization. Use them only for local inspection/debugging, and reset local data through Docker/database reset commands when manual edits invalidate test assumptions.

## Validation

Use Make targets from the repository root:

```bash
make lint
make format-check
make test-backend
make migrations-check
make smoke
```

`DATABASE_URL` is intended for container-to-container access through the Compose `postgres` hostname. Host-side commands can use `LOCAL_DATABASE_URL` or the Makefile default pointing at `localhost:5432`.
