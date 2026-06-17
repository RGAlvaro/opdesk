# ADR-006 — Human-Readable Code Comments

Status: Accepted
Date: 2026-06-17
Related specs:
- `SPEC-002`
- Repository workflow
- All future implementation specs

## Context

OpsDesk is intended to be inspected by the repository owner, recruiters, and future agents. Specs, tests, migrations, and ADRs already define behavior and durable decisions, but source files can still be hard to scan quickly without local explanatory context.

Adding comments everywhere creates a risk: agents and reviewers might start treating comments as an informal contract, or comments might drift from specs and executable behavior.

## Decision

Adopt a repository-wide convention for human-readable code comments:

- every source code file starts with a concise responsibility comment or language-native docstring;
- every function, class, component, hook, service, repository, schema, model, fixture, and significant helper includes one or two explanatory lines;
- comments explain purpose, ownership, constraints, or non-obvious behavior rather than narrating obvious code.

These comments are explicitly reader support. They do not replace or override specs, tests, migrations, ADRs, API contracts, or `AGENTS.md`.

Agents may use comments as orientation hints, but comments are not mandatory reading and should not be treated as source-of-truth material. If a comment conflicts with a governing spec or executable test, the comment is stale and must be corrected.

## Consequences

Code should become easier for humans to inspect during portfolio review and future maintenance.

Future code additions have a small documentation cost at creation time.

Reviewers should check that comments exist and are not misleading, but they should continue reviewing behavior against specs and tests.

The initial repository-wide comment pass can be implemented as documentation-only work under `SPEC-002`.

## Alternatives Considered

- No repository-wide comment convention: avoids maintenance cost, but leaves readability dependent on implicit module knowledge.
- Require comments only for complex code: lower noise, but does not satisfy the portfolio readability goal for every source file.
- Make comments source-of-truth: rejected because it conflicts with OpsDesk's spec-driven workflow and would create ambiguous authority.
