# ADR-007 — Tenant Isolation And RBAC Enforcement

Status: Accepted
Date: 2026-06-18
Related specs:
- `SPEC-102`
- `SPEC-103`

## Context

Organizations establish the tenant boundary reused by projects, tasks, and later product features. Authorization checks spread across route handlers or unconstrained repository lookups would make it easy for later endpoints to expose cross-tenant records or return inconsistent `403` and `404` responses.

OpsDesk also needs an unambiguous ownership model. Allowing multiple owners complicates destructive actions and makes ownership transfer indistinguishable from ordinary role management.

## Decision

Enforce organization access through two complementary boundaries:

- repositories require an `organization_id` in every membership and tenant-owned lookup, and member-facing organization reads join against the actor's membership;
- services resolve membership before applying role policy, return `404` for non-members, and return `403` for known members without the required role;
- FastAPI route handlers remain transport adapters and do not own authorization decisions;
- reusable roles are represented by the shared `MembershipRole` enum;
- every organization has exactly one owner at committed transaction boundaries;
- ordinary membership role management cannot assign or remove the owner role;
- ownership changes only through a dedicated transfer service that locks the organization row, revalidates the actor, demotes and flushes the previous owner, and promotes an existing member atomically;
- a partial unique database index prevents multiple owner memberships for one organization;
- permanent organization deletion is owner-only, serializes on the same organization-row lock as transfer, removes memberships without deleting users, and requires later organization-owned models to define compatible deletion behavior;
- role-change, ownership-transfer, and organization-deletion audit logs contain actor, organization, target user, and role identifiers as applicable, but no sensitive user data.

Future tenant-owned repositories and services introduced by `SPEC-103` should follow the same lookup and error policy.

## Consequences

Tenant isolation and RBAC decisions remain testable independently of HTTP routing, and later features have a consistent policy to reuse.

Repository methods must avoid generic ID-only access for tenant-owned resources. Service methods need the actor and organization context even when the resource ID is globally unique.

The ownership lock and partial unique index depend on PostgreSQL transaction and index behavior. SQLite remains useful for most endpoint tests, while PostgreSQL integration coverage is required for concurrent ownership transfer and migration validation.

## Alternatives Considered

- Route-only authorization: rejected because later callers could bypass tenant and role checks.
- Repository-only authorization: rejected because repositories should scope data access but should not decide public error semantics or role policy.
- Global middleware for all tenant access: rejected because required roles and resource lookup order vary by operation.
- Multiple owners with last-owner protection: rejected for the MVP because it complicates ownership authority and destructive actions.
- Reusing generic membership role updates for ownership transfer: rejected because the two-role atomic transition and concurrency policy need an explicit contract.
