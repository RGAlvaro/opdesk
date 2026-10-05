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

Use this index for routing. Use `docs/project-state.md` for the compact current operational state, including active branch, latest validation baseline, and known gaps.

| Spec | Status | Purpose | Depends on | Primary surfaces |
|---|---|---|---|---|
| `SPEC-000` | Ready | Product vision and MVP boundary | None | `specs/000-product-vision.md` |
| `SPEC-001` | Ready | Cross-feature API conventions | `SPEC-000` | `specs/001-api-conventions.md`, API tests |
| `SPEC-002` | Implemented | Human-readable code comments convention and initial comment pass | `SPEC-000` | `AGENTS.md`, source code files, `docs/decisions/ADR-006-human-readable-code-comments.md` |
| `SPEC-010` | Implemented | Backend scaffold and local PostgreSQL database | `SPEC-000`, `SPEC-001` | `backend/`, `docker-compose.yml`, `Makefile`, `.env.example` |
| `SPEC-011` | Implemented | Local database administration panel | `SPEC-010` | `docker-compose.yml`, `.env.example`, `README.md`, harness docs |
| `SPEC-101` | Implemented | Authentication and users | `SPEC-010`, `SPEC-001` | `backend/app`, `backend/tests`, Alembic migrations, `.env.example` |
| `SPEC-104` | Implemented | Frontend app shell and auth UI | `SPEC-101` | `frontend/`, `Makefile`, `docker-compose.yml`, `.env.example`, `README.md` |
| `SPEC-102` | Implemented | Organizations and RBAC | `SPEC-101` | Backend models, migration, APIs, services, tests |
| `SPEC-103` | Implemented | Projects and tasks | `SPEC-102` | Backend models, migration, APIs, services, tests |
| `SPEC-105` | Implemented | Frontend organizations UI | `SPEC-102`, `SPEC-104` | Organization routes, forms, member/admin UI, frontend tests |
| `SPEC-106` | Implemented | Frontend projects and tasks UI | `SPEC-103`, `SPEC-105` | Project/task routes, forms, filters, frontend tests |
| `SPEC-201` | Implemented | Background jobs and notifications | `SPEC-103` | Redis/Celery worker, notification payloads, tests |
| `SPEC-301` | Implemented | Production deployment and operations | Starts after `SPEC-010`; evolves with services | Production Compose, Caddy, deployment docs, backup/restore docs, CI |
| `SPEC-302` | Implemented | Predeployment UI stabilization and small corrections/additions | `SPEC-104`, `SPEC-105`, `SPEC-106` | App shell navigation, organization/project/task frontend routes, frontend regression tests |
| `SPEC-303` | Implemented | Member invitations by email and project-level access | `SPEC-102`, `SPEC-103`, `SPEC-105`, `SPEC-106` | Organization invitations, project invitations/memberships, project visibility, invite APIs, migration `0008`, frontend management UI |
| `SPEC-304` | Implemented | Internal organization member chat with WebSocket delivery and shared-project member ordering | `SPEC-102`, `SPEC-103`, `SPEC-303`, `SPEC-305`, `SPEC-306` | Chat persistence, WebSocket chat APIs, organization chat UI, unread conversation notifications; merged through PR #17 |
| `SPEC-305` | Implemented | Restricted client accounts, project tickets, ticket status, ticket comments, and accepted handoff requests | `SPEC-101`, `SPEC-102`, `SPEC-103`, `SPEC-106`, `SPEC-303`, `SPEC-306` | Client account access, ticket APIs, ticket comments, client shell, migrations `0010`/`0011`; merged through PR #16 |
| `SPEC-306` | Implemented | Persistent in-app notifications | `SPEC-201`, `SPEC-303` | Notification models, APIs, inbox UI, invitation/project/task notification fan-out |
| `SPEC-307` | Implemented | Release automation and safe production updates after initial deployment | `SPEC-301`, initial public deployment | GitHub Actions/manual release workflow, pre-deploy backup script, production migrations, post-deploy checks, rollback docs |
| `SPEC-308` | Implemented | Enriched profile, organization, project, and task metadata | `SPEC-101`, `SPEC-102`, `SPEC-103`, `SPEC-104`, `SPEC-105`, `SPEC-106` | User profile, organization metadata, project metadata, task metadata, migrations, frontend forms |
| `SPEC-309` | Implemented | Project-scoped task labels | `SPEC-103`, `SPEC-106`, `SPEC-308`, optionally `SPEC-303` | Label models/APIs, task label assignments, task filters, label UI, migrations |
| `SPEC-310` | Implemented | Production release changelog | `SPEC-307`, `SPEC-104` | `CHANGELOG.md`, release validation, public changelog route/link |
| `SPEC-311` | Implemented | Static public portfolio home for OpsDesk and future apps | `SPEC-104`, `SPEC-310` | Public `/` route, app cards, changelog link, frontend tests |
| `SPEC-312` | Implemented | Expanded Playwright E2E coverage for auth, profile, filters, mobile viewport, and optional CI | `SPEC-104`, `SPEC-105`, `SPEC-106`, `SPEC-309`, `SPEC-311` | `frontend/e2e/`, Playwright config, E2E Compose runner, CI/harness docs |
| `SPEC-313` | Implemented | Cross-browser and accessibility E2E hardening | `SPEC-312`, `SPEC-305`, `SPEC-306`, `SPEC-311` | Firefox/WebKit Playwright smoke coverage, automated accessibility checks, E2E CI artifacts |
| `SPEC-314` | Implemented | External notification delivery | `SPEC-201`, `SPEC-303`, `SPEC-305`, `SPEC-306`, `SPEC-307` | Resend email delivery provider adapter, Celery delivery jobs, delivery audit, production env/docs |
| `SPEC-315` | Implemented | Real-time notification inbox | `SPEC-306`, `SPEC-304`, `SPEC-307` | Notification WebSocket endpoint, unread-count live updates, polling fallback, frontend cache updates |
| `SPEC-316` | Implemented | Scheduled jobs and operational audit | `SPEC-201`, `SPEC-301`, `SPEC-306`, `SPEC-314` | Celery beat scheduler service, scheduled job audit table, admin audit UI, production Compose/docs |
| `SPEC-317` | Implemented | Public legal pages | `SPEC-104`, `SPEC-311` | Public terms, copyright, cookies routes, landing footer links, frontend tests |
| `SPEC-318` | Implemented | Portfolio landing visual refresh and factual ERP current-versus-planned presentation | `SPEC-311`, `SPEC-310`, `SPEC-317`, `SPEC-313`, `SPEC-307` | Public `/` layout, OpsDesk entry, ERP repository card, responsive and accessibility checks, release visual verification |
| `SPEC-319` | Implemented | EventFlow second portfolio card and conceptual thumbnail | `SPEC-318` | Replace ERP panel with factual EventFlow copy, source link, responsive illustration, and regression checks; local review pending |

Implementation order should usually follow spec dependencies:

```text
SPEC-010 -> SPEC-011 -> SPEC-101 -> SPEC-104 -> SPEC-002 -> SPEC-102 -> SPEC-103 -> SPEC-105 -> SPEC-106 -> SPEC-201 -> SPEC-302
SPEC-303, SPEC-305, and SPEC-306 are implemented before internal organization chat. Implement SPEC-304 after SPEC-305 so restricted client-account behavior and ticket-comment boundaries are established before internal organization chat adds WebSockets.
SPEC-301 starts after SPEC-010 and should evolve as backend, frontend, Redis, and worker services exist.
SPEC-307 is implemented for manual post-launch release automation after the initial `SPEC-301` public deployment is executed.
SPEC-308 should be implemented before `SPEC-309` because task labels depend on the expanded project/task surfaces.
SPEC-310 can be implemented after `SPEC-307`; `SPEC-311` should wait until the personal home-page copy questions are resolved.
SPEC-312 can be implemented after the initial Playwright critical path exists and should remain separate from product feature work.
SPEC-313 can be implemented after `SPEC-312` because it builds on the established E2E runner.
SPEC-315 can be implemented after `SPEC-306` and `SPEC-304` because it reuses persistent notifications and WebSocket session-auth patterns.
SPEC-314 should be implemented before `SPEC-316` because scheduled delivery retry sweeps depend on external delivery audit state.
SPEC-317 can be implemented after `SPEC-311` because it extends the public portfolio surface.
SPEC-318 follows `SPEC-311` and `SPEC-317` because it redesigns the existing public portfolio presentation while retaining legal links. It supersedes `SPEC-311`'s earlier ERP coming-soon/small-team-market assumption with a source-available ERP whose current authentication and HR foundation is distinguished from planned modules; its production release uses the established `SPEC-307` and `SPEC-310` gates.
SPEC-319 replaces only SPEC-318's second project panel with EventFlow while retaining the established layout and release gates.
```

## Agent Routing

- Start with `docs/project-state.md` to identify active work, current gaps, and the latest validation baseline.
- Read the active feature spec before touching implementation or tests.
- Read `SPEC-001` for any API endpoint, error, auth, pagination, or tenant-isolation work.
- Read `specs/harness/local-validation.md` before changing Make targets, Docker services, tests, migrations, or validation docs.
- Read related ADRs in `docs/decisions/` before changing package management, module layout, database topology, deployment topology, auth token strategy, or other durable cross-cutting decisions.
- Use `docs/implementation-log.md` for history and evidence, not as the first source for current state.

## Touch-To-Spec Routing

Use this table to decide which feature spec to open before editing.

| If touching... | Read spec |
|---|---|
| Product boundaries, MVP scope, recruiter/demo goals | `SPEC-000` |
| API paths, error shape, cookies, pagination, status codes, tenant-isolation conventions | `SPEC-001` |
| File-level comments, function/class comments, or repository-wide code readability comments | `SPEC-002` |
| Backend scaffold, settings, health endpoint, PostgreSQL, Alembic baseline, Make targets, local database env vars | `SPEC-010` |
| Adminer, local DB inspection, Adminer port, local database admin smoke checks | `SPEC-011` |
| Users, password hashing/policy, auth cookies/JWTs, `/api/v1/auth/*`, `/api/v1/users/me` | `SPEC-101` |
| React app shell, login/signup/profile UI, frontend session bootstrap, Vite proxy, frontend auth tests | `SPEC-104` |
| Organizations, memberships, roles, RBAC, tenant isolation helpers, `/api/v1/organizations*` | `SPEC-102` |
| Projects, tasks, assignment, status/priority rules, task filters, archive behavior | `SPEC-103` |
| Frontend organization/workspace routes, organization forms, member/admin UI, active organization context | `SPEC-105` |
| Frontend project/task routes, project forms, task forms, task filters, assignment UI | `SPEC-106` |
| Redis, Celery, workers, background jobs, task assignment notifications | `SPEC-201` |
| Production Compose, Caddy, public deployment, backup/restore, production smoke checks | `SPEC-301` |
| Predeployment UI corrections, app shell navigation regressions, small frontend additions before launch | `SPEC-302` |
| Adding organization members by email, invitations, project member access | `SPEC-303` |
| Organization chat, chat member list, shared-project ordering | `SPEC-304` |
| Project clients, client access, client-created tickets | `SPEC-305` |
| In-app notifications, unread inbox, invitation notifications, missed chat notifications | `SPEC-306` |
| GitHub Actions deployment workflows, release automation, post-launch production updates, pre-deploy backup, rollback docs | `SPEC-307` |
| User profile metadata, email change with password confirmation, organization metadata, project metadata, task metadata, non-editable organization slugs | `SPEC-308` |
| Project task labels, label colors/descriptions, task label assignment, label task filters | `SPEC-309` |
| `CHANGELOG.md`, release notes, public changelog page/link, changelog validation in release workflows | `SPEC-310` |
| Public `/` portfolio/app hub, OpsDesk app card, ERP coming-soon card, personal developer description | `SPEC-311` |
| Public `/` portfolio visual layout and selected mockup reference, ERP current-versus-planned copy and source link, responsive hierarchy, release visual check | `SPEC-318` |
| Public legal pages, terms, copyright, cookie policy, landing footer legal links | `SPEC-317` |
| Playwright E2E tests, browser projects, E2E CI job, E2E artifacts, auth/profile/filter browser coverage | `SPEC-312` |
| Firefox/WebKit E2E coverage, accessibility scans, axe/Playwright checks | `SPEC-313` |
| Email delivery, external notification providers, delivery audit, notification templates | `SPEC-314` |
| Real-time notification inbox, notification WebSocket, unread count push updates | `SPEC-315` |
| Scheduled jobs, Celery beat, operational audit, cleanup/retention jobs | `SPEC-316` |
