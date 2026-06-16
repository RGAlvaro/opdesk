# SPEC-XXX — Feature Name

Status: Draft | Ready | Implemented | Deprecated  
Owner: Arquitecto de specs  
Last updated: YYYY-MM-DD

## Scope And Required Context

This spec governs:

- Path or subsystem:

Required context:

- `AGENTS.md`
- `docs/project-state.md`
- `specs/README.md`
- `specs/001-api-conventions.md` when API behavior is involved
- `specs/harness/local-validation.md` when validation, tests, Docker, migrations, or Make targets change
- Relevant ADRs:

Memory updates:

- `docs/project-state.md` when current state, next work, known gaps, or validation baseline changes
- `docs/implementation-log.md` for meaningful spec-prep, implementation, review, or merge events
- `specs/README.md` when status, dependencies, order, or primary surfaces change
- ADRs when durable cross-cutting decisions are introduced or changed

## Problem

Describe the user or system problem. Avoid implementation details here.

## Goals

- Goal 1
- Goal 2

## Non-Goals

- Non-goal 1
- Non-goal 2

## Actors And Permissions

| Actor | Permission | Notes |
|---|---|---|
| Anonymous user | | |
| Authenticated user | | |
| Organization owner | | |
| Organization admin | | |
| Organization member | | |

## Business Rules

- BR-1:
- BR-2:

## Data Model Impact

New tables, changed tables, indexes, constraints, enums, relationships, and migration notes.

## API Contract

Reference `specs/001-api-conventions.md`.

### `METHOD /api/v1/path`

Request:

```json
{}
```

Response:

```json
{}
```

Errors:

| Status | Code | Condition |
|---:|---|---|
| 400 | | |
| 401 | | |
| 403 | | |
| 404 | | |
| 409 | | |

## Frontend Impact

Routes, forms, states, validation, error rendering, loading behavior, and empty states.

## Acceptance Criteria

Use observable criteria.

- AC-1: Given ..., when ..., then ...
- AC-2: Given ..., when ..., then ...

## Harness Requirements

Required tests/checks:

- Unit tests:
- Integration tests:
- API tests:
- Frontend tests:
- E2E/smoke tests:
- Migration checks:
- Security/permission tests:

Required commands:

```bash
# Add exact commands once available
```

## Observability And Failure Cases

- Logs:
- Metrics-ready events:
- Expected failure paths:
- Retry behavior, if any:

## Open Questions

- [ ] Question 1

## Implementation Notes

Useful constraints for implementation. Do not over-prescribe internals unless necessary.
