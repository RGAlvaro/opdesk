# SPEC-000 — Product Vision

Status: Ready  
Owner: Arquitecto de specs  
Last updated: 2026-06-07

## Product Summary

OpsDesk is a B2B SaaS web application for small teams that manage operational work: projects, tasks, tickets, assignments, comments, and activity history.

The project is also a professional portfolio artifact. It must demonstrate production-minded FastAPI engineering, not only CRUD endpoints.

## Target Users

- Small business owner or team lead.
- Team member managing assigned work.
- Admin managing users, roles, and workspace settings.
- Recruiter or technical interviewer evaluating the repository and live demo.

## Core Capabilities

1. User registration, login, logout, and profile management.
2. Organizations/workspaces with tenant isolation.
3. Role-based access control.
4. Projects and tasks/tickets.
5. Comments and activity history.
6. Notifications and background jobs.
7. Admin/recruiter-friendly deployment and documentation.

## MVP Boundary

The first public version should include:

- Authenticated app shell.
- User signup/login/logout/session bootstrap.
- Organization creation and membership.
- Project creation/list/detail.
- Task creation/list/update with assignment, status, priority, due date, and pagination/filtering.
- Health endpoint.
- Dockerized local development.
- CI-ready verification harness.

## Non-Goals For First Public Version

- Billing/subscriptions.
- Native mobile app.
- Real-time collaborative editing.
- Enterprise SSO.
- Advanced analytics.
- Full Jira clone scope.

## Portfolio Success Criteria

A recruiter should be able to inspect:

- Public demo URL.
- Clear README with setup and architecture.
- Dockerized local development.
- FastAPI backend with PostgreSQL, Redis, migrations, tests, and CI.
- React TypeScript frontend.
- Realistic auth and authorization.
- Background job example after MVP.
- Clean specs.
- Evidence of review and validation discipline.

## Deployment Principle

The app should be deployable on a rented VPS using Docker Compose, Caddy, TLS, persistent volumes, documented environment variables, and backup/restore procedures.
