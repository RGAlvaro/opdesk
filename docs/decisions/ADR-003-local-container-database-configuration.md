# ADR-003 — Local And Container Database Configuration

Status: Accepted
Date: 2026-06-09
Related specs:
- SPEC-010

## Context

The backend runs inside Docker Compose for smoke checks, while developers and validation commands may also run from the host. The PostgreSQL hostname differs in those two contexts.

## Decision

Use `DATABASE_URL` for the runtime backend/Alembic connection and document it with the Compose service hostname `postgres`. Also document `LOCAL_DATABASE_URL` for host-side commands that connect through `localhost`.

The Makefile uses `LOCAL_DATABASE_URL` for host-side migration checks when present, while Docker Compose passes `DATABASE_URL` to the backend container.

## Consequences

Container and host workflows are both explicit. This avoids hardcoding one hostname that only works in one context.

## Alternatives Considered

- Use only `DATABASE_URL=localhost`: host commands work, but backend containers cannot resolve the database correctly.
- Use only `DATABASE_URL=postgres`: containers work, but host commands fail unless the user overrides the variable manually.
