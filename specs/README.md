# `specs/` — Source of Truth

This directory defines OpsDesk behavior and validation.

Development workflow:

```text
Spec -> Plan -> Tasks -> Implement -> Validate -> Review -> Merge
```

Rules:

1. Do not implement a system feature without a `Ready` spec under `specs/features/`.
2. Specs define observable behavior, permissions, data rules, contracts, and validation.
3. `specs/001-api-conventions.md` applies to every API feature unless a feature spec explicitly overrides it.
4. Tests and harness commands are part of each feature contract.
5. If implementation and spec conflict, fix the spec first or change code to match the spec.
6. Review is performed against specs, not vague intent.

Feature specs should use `specs/_templates/feature-spec-template.md`.

## Spec Index

| Spec | Status | Purpose |
|---|---|---|
| `SPEC-000` | Ready | Product vision and MVP boundary |
| `SPEC-001` | Ready | Cross-feature API conventions |
| `SPEC-101` | Ready | Authentication and users |
| `SPEC-102` | Ready | Organizations and RBAC |
| `SPEC-103` | Ready | Projects and tasks |
| `SPEC-201` | Draft | Background jobs and notifications |
| `SPEC-301` | Ready | Deployment and operations |

Implementation order should usually follow spec dependencies:

```text
SPEC-101 -> SPEC-102 -> SPEC-103 -> SPEC-201
SPEC-301 can start after backend/frontend scaffolding exists and should evolve with each service.
```
