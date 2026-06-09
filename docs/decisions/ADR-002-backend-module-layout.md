# ADR-002 — Backend Module Layout

Status: Accepted
Date: 2026-06-09
Related specs:
- SPEC-010

## Context

Later specs need a predictable place for API routers, settings, database setup, services, repositories, and tests. The initial scaffold should avoid overbuilding while leaving clear extension points.

## Decision

Use `backend/app` as the Python package, with initial subpackages:

- `app/api` for FastAPI routers.
- `app/core` for settings and cross-cutting configuration.
- `app/db` for SQLAlchemy base, session setup, and database dependencies.
- `backend/tests` for backend tests.

Future specs may add `app/services`, `app/repositories`, `app/schemas`, and feature-specific modules as needed.

## Consequences

The backend starts small but has clear boundaries for route handlers, configuration, and persistence. Feature specs can add service/repository layers without moving the scaffold.

## Alternatives Considered

- Flat `main.py` only: simpler initially, but would force early churn once auth and organizations are added.
- Feature-only package layout from day one: useful later, but premature before the first domain feature exists.
