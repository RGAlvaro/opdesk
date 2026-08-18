# ADR-005 — Agent Operational Memory

Status: Accepted
Date: 2026-06-16
Related specs:
- Repository workflow
- All feature specs

## Context

OpsDesk is intentionally spec-driven and agent-assisted. As the number of specs, reviews, validation runs, and implementation-log entries grows, future agents need a compact way to understand current state without reading large amounts of code or the full historical log.

The repository already has strong durable memory in specs, tests, migrations, ADRs, and `docs/implementation-log.md`, but the implementation log is chronological evidence. It is not optimized as the first document for current operational orientation.

## Decision

Use `docs/project-state.md` as the compact current-state dashboard for agents.

It records:

- active branch/spec;
- implemented specs;
- ready and draft specs;
- next likely work;
- known gaps;
- latest validation baseline;
- high-level code map;
- recommended reading order.

Keep `docs/implementation-log.md` as chronological evidence of spec-prep, implementation, validation, review, and merge events.

Keep touch-to-spec discovery in `specs/README.md`, where agents can decide which spec to open before editing.

Add a `Scope And Required Context` section to feature specs and the feature-spec template so each opened spec states what it governs, which related documents matter, and which memory files must be updated after changes.

Use the Review agent's `APPROVED` decision as the canonical pre-merge operational-memory checkpoint.
A review cannot be approved while `docs/project-state.md` or `docs/implementation-log.md` is
materially stale for the active spec. Commit and push remain useful evidence checkpoints, but they
are not the primary trigger for creating project memory.

Use merge as a second operational-memory checkpoint. After a PR or branch is merged, the merge actor
must record the merged PR, merge commit, validation evidence, carried-forward review decision, known
gaps, and next work before moving to another spec. If the merge has already landed and memory is
stale on `main`, the actor must make a small follow-up memory commit.

Add lightweight harness helpers:

- `make memory-check SPEC=SPEC-XXX` verifies that the current-state and implementation-log files
  contain the active spec and required log sections before review approval.
- `make review-ready SPEC=SPEC-XXX` aliases the current memory readiness check so agents have a
  stable handoff target.
- `make merge-memory-check SPEC=SPEC-XXX` verifies that the newest log entry for the spec records
  merged state, PR, merge commit, validation evidence, and the approved review decision.
- `make memory-entry SPEC=SPEC-XXX` prints a paste-ready implementation-log template.

These helpers validate or scaffold memory only. They must not fabricate validation evidence, review
decisions, commits, gaps, or branch state.

## Consequences

Future agents can orient from a short current-state file before reading detailed specs or code.

The project now has two memory layers:

- `docs/project-state.md` for current operational truth.
- `docs/implementation-log.md` for historical evidence.

Agents and reviewers must keep both aligned when current state, validation baseline, known gaps, or spec readiness changes.

Review approval and merge handoff are stricter than commit or push: stale memory is a blocker even
if the code and tests are otherwise correct.

Feature specs confirm their own scope and required context, but discovery of which spec to read belongs in the central spec index.

## Alternatives Considered

- Keep using only `docs/implementation-log.md`: preserves history, but becomes inefficient and error-prone as entries accumulate.
- Put all state into `AGENTS.md`: makes the main instruction file too volatile and mixes workflow rules with changing project state.
- Rely on Git history and PRs only: useful for evidence, but too slow for agent orientation and not explicit enough about next work or known gaps.
- Auto-write memory on commit or push: rejected because hooks are local, easy to bypass, and cannot
  safely know whether validation evidence, known gaps, or review decisions are true.
