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

### 2026-06-09 — SPEC-010 — Backend scaffold implemented

Role: Ingeniero de software
Branch: spec-010-backend-scaffold
Commit/PR: `be18383`, `36f9757`, `d97031d`, `ea31737`, PR https://github.com/RGAlvaro/opdesk/pull/1
Status: Implemented

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
