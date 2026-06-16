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

## Consequences

Future agents can orient from a short current-state file before reading detailed specs or code.

The project now has two memory layers:

- `docs/project-state.md` for current operational truth.
- `docs/implementation-log.md` for historical evidence.

Agents and reviewers must keep both aligned when current state, validation baseline, known gaps, or spec readiness changes.

Feature specs confirm their own scope and required context, but discovery of which spec to read belongs in the central spec index.

## Alternatives Considered

- Keep using only `docs/implementation-log.md`: preserves history, but becomes inefficient and error-prone as entries accumulate.
- Put all state into `AGENTS.md`: makes the main instruction file too volatile and mixes workflow rules with changing project state.
- Rely on Git history and PRs only: useful for evidence, but too slow for agent orientation and not explicit enough about next work or known gaps.
