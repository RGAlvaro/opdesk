# ADR-001 — Python Package Manager

Status: Accepted
Date: 2026-06-09
Related specs:
- SPEC-010

## Context

The backend needs reproducible dependency installation, local commands, Docker builds, and a harness that future agents can run consistently.

## Decision

Use Poetry for the backend Python package manager.

## Consequences

Poetry commands become the default for backend validation and Docker dependency installation. Harness documentation can use `poetry run` consistently until a future ADR supersedes this decision.

## Alternatives Considered

- uv: fast and viable, but the repository already names Poetry as the initial harness default.
- pip requirements files: simple, but weaker for dependency grouping and lockfile workflow.
