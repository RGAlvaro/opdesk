# ADR-004 — Local Database Admin Tool

Status: Accepted
Date: 2026-06-10
Related specs:
- SPEC-011
- SPEC-010

## Context

OpsDesk needs a convenient way to inspect local PostgreSQL state while implementing migrations and CRUD-oriented features. The tool should be simple enough for a portfolio project, require minimal configuration, and avoid creating a production administration surface.

## Decision

Use Adminer as a local-only Docker Compose service for direct PostgreSQL inspection.

The service is limited to local Compose, binds to localhost, and is intentionally absent from production Compose. It uses the existing local PostgreSQL credentials documented for development.

## Consequences

Developers and review agents can inspect schemas, tables, rows, constraints, and migration state from a browser without installing a separate desktop client.

The tool must be documented as local-only because it can bypass application authorization and service-layer validation. Direct DB edits are acceptable for local debugging but cannot replace migrations, tests, fixtures, or product APIs.

Production deployment remains simpler and safer because no database admin panel is exposed publicly.

## Alternatives Considered

- pgAdmin: more feature-rich, but heavier and usually needs persistent configuration, login setup, and more documentation for a solo local workflow.
- Desktop database client only: keeps Compose smaller, but makes review/setup less reproducible and depends on each developer's machine.
- No DB admin panel: safest operationally, but slows local inspection and manual verification during early data-model work.
