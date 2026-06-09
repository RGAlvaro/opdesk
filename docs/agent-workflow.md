# Agent Workflow Notes

Use these role prompts when asking Codex to work in this repository.

## Spec Architecture

```text
Act as Arquitecto de specs. Read AGENTS.md, docs/implementation-log.md, docs/decisions/, and the relevant specs. Create or update the spec for [feature]. Do not implement code. Ensure the spec includes business rules, acceptance criteria, API impact, data impact, permission rules, and harness requirements. Update implementation-log or ADRs if spec readiness or durable decisions change.
```

## Implementation

```text
Act as Ingeniero de software. Read AGENTS.md, docs/implementation-log.md, relevant docs/decisions/, specs/README.md, specs/001-api-conventions.md, and specs/features/[SPEC_FILE]. Implement only this spec. Before editing, provide a short plan. Add or update required tests and run the relevant harness commands. Update docs/implementation-log.md before review.
```

## Review

```text
Act as Review agent. Read AGENTS.md, docs/implementation-log.md, relevant docs/decisions/, specs/features/[SPEC_FILE], specs/001-api-conventions.md, and the current diff. Review implementation against the spec. Verify project memory is current. Produce a coverage matrix and return APPROVED, CHANGES_REQUESTED, or BLOCKED_BY_SPEC_GAP.
```

## Suggested First Sequence

1. Scaffold backend, database, health endpoint, Makefile, and Docker basics under SPEC-010.
2. Implement SPEC-101 auth backend and tests.
3. Implement SPEC-102 organizations/RBAC backend and tests.
4. Implement SPEC-103 projects/tasks backend and tests.
5. Scaffold frontend app shell and implement critical auth/org/task UI flows.
6. Return to SPEC-201 for background jobs once task assignment exists.
7. Expand SPEC-301 production deployment as services become real.
