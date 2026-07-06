# ADR-009 — Managed Sandbox GitHub CLI Execution

Status: Accepted
Date: 2026-06-30
Related specs:
- Repository workflow
- SPEC-301

## Context

Managed agent sandboxes may block outbound GitHub access while still exposing the host's GitHub CLI configuration. In that state, a sandboxed `gh auth status` can report a valid token as invalid. This creates unnecessary authentication prompts and delays automated publication, PR, and CI operations.

Publishing workflow files adds a second constraint: GitHub rejects pushes that create or modify `.github/workflows/*` when the active token lacks the `workflow` scope.

## Decision

Agents running in managed sandboxes execute every network-backed `gh` command with the runtime's elevated or outside-sandbox mode from the first attempt. They request the narrowest practical approval and reusable command prefix instead of probing GitHub from the restricted sandbox first.

Before publishing, agents verify authentication in that same execution context. If the diff touches `.github/workflows/*`, they also verify that the active token includes the `workflow` scope.

Local read-only Git inspection remains sandboxed. Git commands are elevated only when repository metadata permissions or remote network access require it.

## Consequences

- Valid host credentials are no longer misdiagnosed because of sandbox network restrictions.
- GitHub publication can proceed automatically after the required scoped approval exists.
- Workflow-file pushes fail earlier with a clear scope check instead of at the remote push.
- The policy remains runtime-aware: environments without a managed sandbox execute `gh` normally.
- Agents must continue to avoid printing or persisting unmasked credentials.

## Alternatives Considered

- Try `gh` inside the sandbox first and retry after failure: rejected because the known failure is noisy and can be misreported as an authentication problem.
- Always execute all Git commands outside the sandbox: rejected because local inspection does not need network access or broader privileges.
- Replace `gh` with manual browser operations: rejected because it weakens automation and reproducibility.
