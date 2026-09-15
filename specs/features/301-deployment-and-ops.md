# SPEC-301 — Production Deployment and Operations

Status: Implemented
Owner: Arquitecto de specs  
Last updated: 2026-07-07

## Scope And Required Context

This spec governs:

- Production Compose, Caddy, public deployment docs, production environment variables, production smoke checks, backup/restore procedures, frontend production serving, Redis/worker production wiring, or CI deployment checks.

Required context:

- `AGENTS.md`
- `docs/project-state.md`
- `specs/README.md`
- `specs/harness/local-validation.md`
- `specs/features/010-backend-scaffold-and-local-database.md`
- Current implemented service specs, such as `SPEC-101`, `SPEC-104`, and later `SPEC-102`, `SPEC-103`, or `SPEC-201`
- Relevant ADRs for database, deployment, auth cookies, frontend build/serving, Redis, and worker topology

Memory updates:

- `docs/project-state.md` if deployment readiness, validation baseline, next work, or known gaps change
- `docs/implementation-log.md` for meaningful spec-prep, implementation, review, or validation events
- `specs/README.md` if status, dependencies, order, or primary surfaces change
- ADRs if deployment topology, backup strategy, service exposure, or production runtime strategy changes

## Problem

The project should be demonstrable through a real public URL without recruiters needing to run it locally. It must have a credible production deployment path on a rented VPS, building on the local backend/database foundation from `SPEC-010`.

## Goals

- Provide production Docker Compose setup.
- Use Caddy as reverse proxy with automatic TLS.
- Document production environment variables.
- Provide production health checks and smoke checks.
- Provide PostgreSQL backup and restore procedures.
- Keep deployment simple enough for a solo developer portfolio project.

## Dependencies

- Requires `SPEC-010` local backend scaffold, PostgreSQL service, health endpoint, and `.env.example` foundation.
- Expands as frontend, Redis, worker, and background-job specs become implemented.

## Non-Goals

- Defining the initial local PostgreSQL/backend scaffold. That belongs to `SPEC-010`.
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
- BR-7: Production deployment must document which services are exposed publicly and which remain private on the Docker network.
- BR-8: Production Compose must not expose PostgreSQL or Redis publicly by default.
- BR-9: Production settings must override local debug and cookie/security defaults where applicable.
- BR-10: Production database connection settings must not construct connection URLs by interpolating raw secrets. Use an explicitly documented, URL-encoded connection URL or construct the URL through a parser-safe mechanism.

## Target Services

Current production services:

- `backend`
- `postgres`
- `caddy`
- `frontend`
- `redis`
- `worker`
- `scheduler`

## Required Files

- `docker-compose.prod.yml`
- production `.env.example` additions or deployment docs for production-only variables
- backend production `Dockerfile` behavior if different from local
- frontend `Dockerfile` after frontend exists
- Caddy config
- `docs/deployment.md`
- backup/restore scripts or documented commands

## Acceptance Criteria

- AC-1: Given production env variables, when production Compose starts, then backend, database, and Caddy start successfully; frontend, Redis, and worker are included once their specs are implemented.
- AC-2: Given Caddy is configured with a domain, when public traffic reaches the VPS, then Caddy terminates TLS and routes frontend/API traffic correctly.
- AC-3: Given `/health` is requested, when backend dependencies are healthy enough for traffic, then it returns success without sensitive details.
- AC-4: Given the documented PostgreSQL backup command, when it is run, then a restorable backup is produced.
- AC-5: Given deployment docs and `.env.example`, when a developer reads them, then all production-required variables are documented without real secrets.
- AC-6: Given CI runs, when the project is in a valid state, then the full verification harness, including migration validation, passes.
- AC-7: Given production Compose is used, when services start, then PostgreSQL and Redis are not publicly exposed by default.

## Harness Requirements

- Docker build check.
- Production Compose config validation when possible.
- Production smoke test.
- Backend health endpoint test through Caddy when production proxy exists.
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
- Local Compose and baseline backend/database behavior are owned by `SPEC-010`.

## Deployment-Time Questions

- [ ] Final domain and DNS provider.
- [ ] VPS provider and host sizing.
