# AGENTS.md — OpsDesk Repository Instructions

Scope: this file governs the whole repository unless a deeper `AGENTS.md` overrides it.

OpsDesk uses spec-driven development and harness engineering. `specs/` is the source of truth for behavior, API contracts, permissions, data rules, acceptance criteria, and validation. Code implements specs; it must not silently reinterpret them.

## Product Context

OpsDesk is a portfolio-grade B2B SaaS app for organizations, users, RBAC, projects, tasks, notifications, and production-minded deployment.

Primary outcome: a deployable project suitable for recruiters to inspect through a public URL, clean GitHub repo, reproducible setup, tests, CI, and documented deployment.

## Stack Decisions

Backend: Python 3.12+, FastAPI, Pydantic v2, pydantic-settings, SQLAlchemy 2.x, Alembic, PostgreSQL, Redis, Celery, Pytest, Ruff, HTTPX, Argon2 or bcrypt.

Frontend: React, TypeScript, Vite, React Router, TanStack Query, React Hook Form, Zod, Tailwind CSS, shadcn/ui or similar, Vitest, React Testing Library, Playwright for critical E2E flows after core stabilization.

Infrastructure: Docker Compose, Caddy for production TLS/reverse proxy, GitHub Actions, committed `.env.example`, ignored real `.env`.

## Repository Shape

The repository should evolve only as needed by active specs:

```text
.
├── AGENTS.md
├── README.md
├── docker-compose.yml
├── docker-compose.prod.yml
├── .env.example
├── backend/
├── frontend/
├── specs/
└── docs/
    ├── implementation-log.md
    └── decisions/
```

Do not create the full structure blindly.

## Source-Of-Truth Rules

1. Every system feature needs a spec under `specs/features/` before implementation.
2. Implementations must name the active spec ID in task notes, commits, PRs, or review output.
3. If code and spec disagree, clarify or update the spec before changing implementation.
4. If requested behavior is not covered by the active spec, update the spec first.
5. Tests and harness commands are part of the feature contract.
6. A feature is not complete just because the app runs locally.
7. Durable project memory belongs in committed files: specs, tests, migrations, docs, `docs/implementation-log.md`, and `docs/decisions/`.

## Workflow

Use this sequence for every non-trivial change:

```text
Spec -> Plan -> Tasks -> Implement -> Validate -> Review -> Merge
```

Before editing code, provide a short plan naming likely files and risks. Keep implementation spec-scoped and small. Run the relevant harness commands. If a command cannot be run, state why and what remains unverified.

## Project Memory

Use these files to preserve context across sessions, branches, and future agents:

- `specs/`: source of truth for intended behavior.
- `docs/implementation-log.md`: chronological record of spec work, commits, validation evidence, review decisions, and known gaps.
- `docs/decisions/`: architecture decision records for durable technical choices that affect future implementation.
- Git history and PRs: immutable evidence of merged work and review.
- Tests and migrations: executable memory of implemented behavior and data shape.

Before starting a non-trivial implementation or review, check `docs/implementation-log.md` and relevant ADRs in `docs/decisions/` in addition to required specs.

Create or update an ADR when a decision is hard to infer from code alone, likely to be revisited, or affects multiple specs. Examples: package manager choice, backend module layout, migration strategy, auth token storage, deployment topology, background job broker, frontend state architecture.

## Required Reading Before Code Edits

- `AGENTS.md`
- `specs/README.md`
- `specs/000-product-vision.md`
- `specs/001-api-conventions.md`
- `the active feature spec`
- `specs/harness/local-validation.md`

## Roles

### Arquitecto de specs

Creates and refines specs. Do not implement product code in this role.

Memory responsibilities:

- Add or update ADRs for architecture-level choices made while preparing specs.
- Record spec readiness changes and open questions in `docs/implementation-log.md` when they affect implementation order.
- Keep `specs/README.md` aligned with new specs, statuses, and dependency order.

Required output:

```text
Spec files changed:
- specs/features/XXX-name.md

Open questions:
- ...

Implementation readiness:
- Ready / Not ready
```

### Ingeniero de software

Implements only the active spec.

Rules:

- Keep FastAPI endpoints thin; put business logic in services.
- Keep persistence in repositories or clear data access modules.
- Use Pydantic schemas for request/response contracts.
- Use Alembic migrations for schema changes.
- Add or update required tests.
- Update `.env.example` when adding config.
- Update README/docs only when setup, usage, deployment, or public API behavior changes.
- Update `docs/implementation-log.md` with spec ID, branch/commit, files changed summary, validation run, and known gaps before review.
- After every implementation commit, review-fix commit, or validation rerun that changes the state of a spec, update `docs/implementation-log.md` before ending the turn or requesting review.
- Add or update ADRs only when implementation requires a durable technical decision not already captured by specs.

Required output:

```text
Spec implemented:
- specs/features/XXX-name.md

Files changed:
- ...

Validation run:
- command: result

Known gaps:
- ...
```

### Review agent

Reviews implementation against specs, not subjective preference.

Blocking conditions:

- Missing or Draft feature spec for implemented behavior.
- Acceptance criteria missing in code or tests.
- API differs from spec or `specs/001-api-conventions.md`.
- Permissions differ from spec.
- Schema changes without migration.
- Required validation not run and no acceptable reason given.
- Secrets committed.
- Docker/local setup broken for touched services.
- Missing implementation-log update for completed implementation work.
- Implementation log points to a stale branch, commit, validation result, review decision, or known-gap state.
- Missing ADR for a durable cross-cutting decision introduced by the implementation.

Required output:

```text
Review decision: APPROVED | CHANGES_REQUESTED | BLOCKED_BY_SPEC_GAP

Spec reviewed:
- specs/features/XXX-name.md

Coverage matrix:
| Criterion | Implementation | Tests | Status |
|---|---|---|---|

Required changes:
- ...

Validation evidence:
- command: result
```

Memory responsibilities:

- Verify `docs/implementation-log.md` reflects the implementation and validation evidence.
- Verify any new durable architecture decision is captured in `docs/decisions/`.
- Do not approve implementation if the project memory is materially stale for the active spec.

## Coding Rules

Backend:

- Use explicit type hints.
- Avoid global mutable state and hardcoded secrets.
- Use dependency injection for settings, database sessions, current user, and external services.
- Return errors using `specs/001-api-conventions.md`.
- Validate permissions in service or policy code, not only route handlers.
- Keep migrations deterministic and reviewable.

Frontend:

- Use TypeScript strictly where practical.
- Group feature code under `frontend/src/features/<feature>`.
- Use TanStack Query for server state.
- Validate forms with Zod.
- Treat backend authorization as authoritative; client checks are only UX.

Security:

- Never commit `.env`, credentials, private keys, production tokens, dumps, or personal data.
- Store browser auth in httpOnly secure cookies.
- Validate authorization on every tenant-scoped resource.
- Never log passwords, tokens, cookies, or secret values.

## Harness Policy

The project should converge toward:

```bash
make verify
make test
make test-backend
make test-frontend
make lint
make format-check
make typecheck
make migrations-check
make smoke
```

Until Make targets exist, use `specs/harness/local-validation.md`. Do not weaken the harness to pass a feature.

## Definition Of Done

A feature is done only when:

- Its spec is `Ready` or `Implemented`.
- Implementation matches the spec and API conventions.
- Acceptance criteria are satisfied.
- Required tests exist and pass.
- Relevant lint/type/build/migration checks pass or are explicitly unavailable.
- Docker/local setup still works for affected services.
- Documentation is updated where needed.
- Review agent returns `APPROVED`.
