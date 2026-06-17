# SPEC-002 — Human-Readable Code Comments

Status: Implemented  
Owner: Arquitecto de specs  
Last updated: 2026-06-17

## Scope And Required Context

This spec governs:

- Repository-wide source code documentation comments for files, functions, classes, and equivalent frontend/backend constructs.
- The initial implementation pass that adds these comments to existing source code.
- Future coding expectations for newly created or modified source code.

Required context:

- `AGENTS.md`
- `docs/project-state.md`
- `specs/README.md`
- `specs/harness/local-validation.md` when validation commands are reported
- `docs/decisions/ADR-006-human-readable-code-comments.md`

Memory updates:

- `docs/project-state.md` when the comment pass becomes active, implemented, reviewed, or no longer next work
- `docs/implementation-log.md` for spec-prep, implementation, review, and validation events
- `specs/README.md` when status, ordering, or primary surfaces change

## Problem

OpsDesk is both a product implementation and a portfolio artifact. The code should be easier for the repository owner and recruiters to inspect without requiring deep context switching across modules.

At the same time, the repository is spec-driven. Comments must not become an informal, divergent contract for agents or reviewers.

## Goals

- Add a short human-readable responsibility comment at the beginning of each source code file.
- Add one or two concise explanatory lines for each function, class, component, hook, service, repository, schema, model, fixture, and test helper.
- Establish the same expectation for future code additions.
- Make clear that these comments are reader support, not source of truth for agents, behavior, permissions, API contracts, data shape, or validation.

## Non-Goals

- Do not change runtime behavior.
- Do not change public API contracts, database schema, permissions, or validation harness behavior.
- Do not add comments to generated artifacts, dependency directories, build output, lockfiles, or non-source documentation files.
- Do not use comments to restate every line of code mechanically.
- Do not require agents to read every comment before implementation or review.

## Commenting Rules

- Source code files must begin with a file-level comment or language-native docstring that explains the file's responsibility.
- Each function or class-like construct must include a short comment, docstring, or JSDoc-style block explaining why it exists or what role it plays.
- Comments should be written for humans inspecting the repository, including recruiters.
- Comments should be concise and stable. Prefer purpose, ownership, constraints, and non-obvious behavior over implementation narration.
- If a comment conflicts with a spec, test, migration, ADR, or API contract, the comment is stale and must be corrected.
- Agents may use comments as orientation hints, but comments are not mandatory context and do not override `AGENTS.md`, specs, tests, migrations, or ADRs.

Language guidance:

- Python files should usually use module, class, and function docstrings.
- TypeScript and TSX files should usually use file header comments and JSDoc-style comments for exported or locally significant functions, classes, hooks, and components.
- Test files should explain the test module's target and any helper or fixture that is not self-evident.
- Alembic migrations should keep their generated revision metadata and add comments only where they improve human review without disrupting Alembic conventions.

## Acceptance Criteria

- AC-1: Given an existing source code file in `backend/` or `frontend/`, when the comment pass is complete, then the file begins with a concise responsibility comment or docstring unless it is generated, vendored, build output, or otherwise explicitly out of scope.
- AC-2: Given an existing function, class, component, hook, service, repository, schema, model, fixture, or helper in source code, when the comment pass is complete, then it has one or two human-readable explanatory lines unless a documented exception applies.
- AC-3: Given a future source code change, when a new file, function, class, or equivalent construct is added, then it includes the required explanatory comment at creation time.
- AC-4: Given an agent preparing implementation or review, when reading repository instructions, then the agent can identify that comments are helpful orientation but not source-of-truth contract material.
- AC-5: Given a conflict between a comment and a spec or executable test, when reviewing, then the spec or test governs and the comment is treated as stale documentation.

## Harness Requirements

Required tests/checks:

- No new product behavior tests are required because the implementation is documentation-only.
- Run formatting, lint, and relevant existing tests after the comment pass to ensure comments did not break syntax or style.

Required commands after implementation:

```bash
make lint
make format-check
make test
```

If a full local verification is practical, also run:

```bash
make verify
```

## Open Questions

- [ ] Whether to add an automated custom check for missing comments after the initial manual pass. This is intentionally deferred until the convention has proven useful without excessive noise.

## Implementation Notes

- Keep the first implementation pass mechanical and behavior-preserving.
- Prefer small batches by subsystem if the repository has grown enough that one large diff would be hard to review.
- Do not weaken lint, type, formatting, or tests to accommodate comments.
