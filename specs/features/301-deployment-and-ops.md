# SPEC-301 — Deployment and Operations

Status: Ready  
Owner: Arquitecto de specs  
Last updated: 2026-06-08

## Problem

The project should be demonstrable through a real public URL without recruiters needing to run it locally. It must have a credible deployment path on a rented VPS.

## Goals

- Provide local Docker Compose setup.
- Provide production Docker Compose setup.
- Use Caddy as reverse proxy with automatic TLS.
- Document environment variables.
- Provide health checks.
- Provide PostgreSQL backup and restore procedures.
- Keep deployment simple enough for a solo developer portfolio project.

## Non-Goals

- Kubernetes.
- Cloud-managed PostgreSQL in first deployment.
- Multi-region deployment.
- Enterprise observability stack.

## Operational Rules

- BR-1: Production must not run with debug settings.
- BR-2: Secrets come from environment variables or server-side secret files, never Git.
- BR-3: Persistent services use named volumes by default.
- BR-4: Deployment docs must include backup and restore before public launch.
- BR-5: Health endpoint must not expose secrets or sensitive internals.
- BR-6: Caddy terminates TLS and proxies to frontend/backend services.
- BR-7: Local Compose must support running without production-only TLS or domain settings.
- BR-8: Production deployment must document which services are exposed publicly and which remain private on the Docker network.

## Target Services

- `backend`
- `frontend`
- `postgres`
- `redis`
- `worker` after SPEC-201
- `beat` only if scheduled jobs exist
- `caddy`

## Required Files

- `docker-compose.yml`
- `docker-compose.prod.yml`
- `.env.example`
- backend `Dockerfile`
- frontend `Dockerfile`
- Caddy config
- `docs/deployment.md`
- backup/restore scripts or documented commands

## Acceptance Criteria

- AC-1: Given Docker is installed locally, when local setup instructions are followed, then the app starts successfully.
- AC-2: Given production env variables, when production Compose starts, then backend, frontend, database, Redis, and Caddy start successfully.
- AC-3: Given `/health` is requested, when backend dependencies are healthy enough for traffic, then it returns success without sensitive details.
- AC-4: Given the documented PostgreSQL backup command, when it is run, then a restorable backup is produced.
- AC-5: Given `.env.example`, when a developer reads it, then all required variables are documented without real secrets.
- AC-6: Given CI runs, when the project is in a valid state, then lint/tests/build checks pass.
- AC-7: Given production Compose is used, when services start, then PostgreSQL and Redis are not publicly exposed by default.

## Harness Requirements

- Docker build check.
- Local smoke test.
- Backend health endpoint test.
- CI check for common committed secret patterns if practical.

Required commands once available:

```bash
make smoke
make verify
```

## Deployment Defaults

- Reverse proxy: Caddy.
- Production database persistence: named Docker volume unless a VPS-specific host path is documented.
- Backup frequency recommendation: daily before public demo; exact automation may be manual for first release.

## Deployment-Time Questions

- [ ] Final domain and DNS provider.
- [ ] VPS provider and host sizing.
