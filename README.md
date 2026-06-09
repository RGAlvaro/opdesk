# OpsDesk

OpsDesk is a spec-driven B2B SaaS portfolio project for operational work management.

## Current Scope

The current implementation target is `SPEC-010`: backend scaffold, local PostgreSQL, Alembic, health checks, Docker Compose, and validation harness.

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
