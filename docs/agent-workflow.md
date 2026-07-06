# Agent Workflow Notes

Use these role prompts when asking Codex to work in this repository.

Before any non-trivial work, read `docs/project-state.md` to identify the active branch/spec, current known gaps, and latest validation baseline. Use `docs/implementation-log.md` as historical evidence, not as the first current-state dashboard.

## GitHub CLI In Managed Sandboxes

Run network-backed `gh` commands outside the restricted sandbox from the first attempt. This includes authentication checks, repository metadata, pull requests, Actions runs, and workflow operations. A sandboxed `gh auth status` can report a valid host token as invalid when GitHub is unreachable.

Use the runtime's elevated execution option with a narrowly scoped approval or prefix. Before pushing `.github/workflows/*`, check outside the sandbox that `gh auth status` includes the `workflow` scope. Local read-only Git commands remain sandboxed unless repository metadata permissions require elevation.

## Spec Architecture

```text
Act as Arquitecto de specs. Read AGENTS.md, docs/project-state.md, specs/README.md, docs/decisions/, docs/implementation-log.md as needed, and the relevant specs. Create or update the spec for [feature]. Do not implement code. Ensure the spec includes Scope And Required Context, business rules, acceptance criteria, API impact, data impact, permission rules, and harness requirements. Update specs/README.md, docs/project-state.md, implementation-log, or ADRs if spec readiness, current state, or durable decisions change.
```

## Implementation

```text
Act as Ingeniero de software. Read AGENTS.md, docs/project-state.md, specs/README.md, relevant docs/decisions/, specs/001-api-conventions.md when API behavior is involved, specs/harness/local-validation.md, and specs/features/[SPEC_FILE]. Implement only this spec. Before editing, provide a short plan. Add or update required tests and run the relevant harness commands. Update docs/project-state.md and docs/implementation-log.md before review.
```

## Current Handoff

As of 2026-07-06, `main` includes the review-approved implementation through `SPEC-301`, including production Compose, CI, backup/restore validation, deployment documentation, and the managed-sandbox GitHub CLI policy. No integration work remains; product known gaps are intentionally deferred to later sessions.

Use this prompt when one of the deferred product gaps is selected:

```text
Act as Arquitecto de specs. Read AGENTS.md, docs/project-state.md, specs/README.md, docs/implementation-log.md, relevant ADRs, and the implemented feature specs. Select one documented known gap, refine its owning spec and acceptance criteria, and update project memory. Do not implement product code.
```

## Review

```text
Act as Review agent. Read AGENTS.md, docs/project-state.md, specs/README.md, docs/implementation-log.md, relevant docs/decisions/, specs/features/[SPEC_FILE], specs/001-api-conventions.md when API behavior is involved, specs/harness/local-validation.md, and the current diff. Review implementation against the spec. Verify project memory is current. Produce a coverage matrix and return APPROVED, CHANGES_REQUESTED, or BLOCKED_BY_SPEC_GAP.
```

## Suggested First Sequence

1. Scaffold backend, database, health endpoint, Makefile, and Docker basics under `SPEC-010`.
2. Add local database inspection under `SPEC-011`.
3. Implement backend auth/users under `SPEC-101`.
4. Scaffold frontend app shell and auth/profile UI under `SPEC-104`.
5. Implement backend organizations/RBAC under `SPEC-102`.
6. Backend projects/tasks under `SPEC-103` is review approved.
7. Add frontend organization/project/task flows through new or updated frontend specs after backend APIs exist.
8. Return to `SPEC-201` for background jobs once task assignment exists.
9. Expand `SPEC-301` production deployment as services become real.
