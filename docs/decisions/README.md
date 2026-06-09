# Architecture Decisions

This directory stores Architecture Decision Records (ADRs) for durable technical choices.

Specs define expected behavior. ADRs explain why an implementation direction was chosen when that choice affects future work.

## When To Add An ADR

Add an ADR when a decision:

- affects multiple specs or modules;
- changes setup, deployment, security, persistence, or testing strategy;
- is expensive to reverse later;
- may be unclear from code alone;
- resolves a meaningful tradeoff or open question.

Do not add ADRs for routine local implementation details that are obvious from code and isolated to one file.

## Naming

Use:

```text
ADR-XXX-short-title.md
```

Examples:

```text
ADR-001-python-package-manager.md
ADR-002-backend-module-layout.md
ADR-003-auth-cookie-token-strategy.md
```

## Template

```text
# ADR-XXX — Title

Status: Proposed | Accepted | Superseded
Date: YYYY-MM-DD
Related specs:
- SPEC-XXX

## Context

What problem or tradeoff forced the decision?

## Decision

What did we decide?

## Consequences

What becomes easier, harder, constrained, or deferred?

## Alternatives Considered

- Option: reason accepted/rejected.
```
