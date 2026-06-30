# `specs/` — Source of Truth

This directory defines OpsDesk behavior and validation.

Development workflow:

```text
Spec -> Plan -> Tasks -> Implement -> Validate -> Review -> Merge
```

Rules:

1. Do not implement a system feature without a `Ready` spec under `specs/features/`.
2. Specs define observable behavior, permissions, data rules, contracts, and validation.
3. `specs/001-api-conventions.md` applies to every API feature unless a feature spec explicitly overrides it.
4. Tests and harness commands are part of each feature contract.
5. If implementation and spec conflict, fix the spec first or change code to match the spec.
6. Review is performed against specs, not vague intent.

Feature specs should use `specs/_templates/feature-spec-template.md`.

## Spec Index

Use this index for routing. Use `docs/project-state.md` for the compact current operational state, including active branch, latest validation baseline, and known gaps.

| Spec | Status | Purpose | Depends on | Primary surfaces |
|---|---|---|---|---|
| `SPEC-000` | Ready | Product vision and MVP boundary | None | `specs/000-product-vision.md` |
| `SPEC-001` | Ready | Cross-feature API conventions | `SPEC-000` | `specs/001-api-conventions.md`, API tests |
| `SPEC-002` | Implemented | Human-readable code comments convention and initial comment pass | `SPEC-000` | `AGENTS.md`, source code files, `docs/decisions/ADR-006-human-readable-code-comments.md` |
| `SPEC-010` | Implemented | Backend scaffold and local PostgreSQL database | `SPEC-000`, `SPEC-001` | `backend/`, `docker-compose.yml`, `Makefile`, `.env.example` |
| `SPEC-011` | Implemented | Local database administration panel | `SPEC-010` | `docker-compose.yml`, `.env.example`, `README.md`, harness docs |
| `SPEC-101` | Implemented | Authentication and users | `SPEC-010`, `SPEC-001` | `backend/app`, `backend/tests`, Alembic migrations, `.env.example` |
| `SPEC-104` | Implemented | Frontend app shell and auth UI | `SPEC-101` | `frontend/`, `Makefile`, `docker-compose.yml`, `.env.example`, `README.md` |
| `SPEC-102` | Implemented | Organizations and RBAC | `SPEC-101` | Backend models, migration, APIs, services, tests |
| `SPEC-103` | Implemented | Projects and tasks | `SPEC-102` | Backend models, migration, APIs, services, tests |
| `SPEC-105` | Implemented | Frontend organizations UI | `SPEC-102`, `SPEC-104` | Organization routes, forms, member/admin UI, frontend tests |
| `SPEC-106` | Implemented | Frontend projects and tasks UI | `SPEC-103`, `SPEC-105` | Project/task routes, forms, filters, frontend tests |
| `SPEC-201` | Draft | Background jobs and notifications | `SPEC-103` | Redis/Celery worker, notification models, tests |
| `SPEC-301` | Ready | Production deployment and operations | Starts after `SPEC-010`; evolves with services | Production Compose, Caddy, deployment docs, backup/restore docs |

Implementation order should usually follow spec dependencies:

```text
SPEC-010 -> SPEC-011 -> SPEC-101 -> SPEC-104 -> SPEC-002 -> SPEC-102 -> SPEC-103 -> SPEC-105 -> SPEC-106 -> SPEC-201
SPEC-301 starts after SPEC-010 and should evolve as backend, frontend, Redis, and worker services exist.
```

## Agent Routing

- Start with `docs/project-state.md` to identify active work, current gaps, and the latest validation baseline.
- Read the active feature spec before touching implementation or tests.
- Read `SPEC-001` for any API endpoint, error, auth, pagination, or tenant-isolation work.
- Read `specs/harness/local-validation.md` before changing Make targets, Docker services, tests, migrations, or validation docs.
- Read related ADRs in `docs/decisions/` before changing package management, module layout, database topology, deployment topology, auth token strategy, or other durable cross-cutting decisions.
- Use `docs/implementation-log.md` for history and evidence, not as the first source for current state.

## Touch-To-Spec Routing

Use this table to decide which feature spec to open before editing.

| If touching... | Read spec |
|---|---|
| Product boundaries, MVP scope, recruiter/demo goals | `SPEC-000` |
| API paths, error shape, cookies, pagination, status codes, tenant-isolation conventions | `SPEC-001` |
| File-level comments, function/class comments, or repository-wide code readability comments | `SPEC-002` |
| Backend scaffold, settings, health endpoint, PostgreSQL, Alembic baseline, Make targets, local database env vars | `SPEC-010` |
| Adminer, local DB inspection, Adminer port, local database admin smoke checks | `SPEC-011` |
| Users, password hashing/policy, auth cookies/JWTs, `/api/v1/auth/*`, `/api/v1/users/me` | `SPEC-101` |
| React app shell, login/signup/profile UI, frontend session bootstrap, Vite proxy, frontend auth tests | `SPEC-104` |
| Organizations, memberships, roles, RBAC, tenant isolation helpers, `/api/v1/organizations*` | `SPEC-102` |
| Projects, tasks, assignment, status/priority rules, task filters, archive behavior | `SPEC-103` |
| Frontend organization/workspace routes, organization forms, member/admin UI, active organization context | `SPEC-105` |
| Frontend project/task routes, project forms, task forms, task filters, assignment UI | `SPEC-106` |
| Redis, Celery, workers, background jobs, task assignment notifications | `SPEC-201` |
| Production Compose, Caddy, public deployment, backup/restore, production smoke checks | `SPEC-301` |
