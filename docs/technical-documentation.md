# OpsDesk Technical Documentation

Last updated: 2026-09-15

This document is the complete internal technical reference for OpsDesk as implemented on `main` after `SPEC-316`. It is intentionally detailed and designed to be a source document for a later public, shortened PDF.

## 1. Purpose And Product Boundary

OpsDesk is a spec-driven B2B SaaS portfolio application for operational work management. It demonstrates a production-minded full-stack system with authentication, organizations, RBAC, projects, tasks, project labels, client accounts, tickets, comments, invitations, chat, persistent notifications, external email delivery, real-time notification updates, background jobs, scheduled maintenance jobs, audit rows, CI, local Docker development, and production deployment automation.

The product is built for recruiter and technical review. The intended proof is not only that the UI works, but that the repository contains specs, tests, migrations, operational scripts, CI workflows, deployment docs, and durable project memory.

## 2. Repository Shape

```text
.
|-- AGENTS.md
|-- README.md
|-- Makefile
|-- docker-compose.yml
|-- docker-compose.prod.yml
|-- Caddyfile
|-- CHANGELOG.md
|-- backend/
|-- frontend/
|-- specs/
|-- docs/
`-- scripts/
```

The repository follows spec-driven development. `specs/` defines intended behavior and acceptance criteria. Code implements specs. Durable project memory lives in `docs/project-state.md`, `docs/implementation-log.md`, ADRs in `docs/decisions/`, migrations, tests, and Git history.

## 3. Technology Stack

### Backend

| Area | Technology | Purpose |
|---|---|---|
| Runtime | Python 3.12 | Backend language |
| API framework | FastAPI | HTTP and WebSocket API |
| Validation/config | Pydantic v2, pydantic-settings | Request/response schemas and environment config |
| ORM | SQLAlchemy 2.x | Database models and queries |
| Migrations | Alembic | Schema versioning and drift checks |
| Database driver | psycopg 3 | PostgreSQL connectivity |
| Database | PostgreSQL 16 | Persistent relational storage |
| Auth crypto | Argon2 via `argon2-cffi` | Password hashing |
| JWT | PyJWT | Access and refresh token signing |
| Jobs | Celery 5 | Background and scheduled task execution |
| Broker/result backend | Redis 7 | Celery broker/result backend |
| Tests | Pytest, HTTPX, FastAPI TestClient | Backend unit/API coverage |
| Lint/format | Ruff | Backend lint and format checks |
| Type checking | mypy strict | Backend static typing |

### Frontend

| Area | Technology | Purpose |
|---|---|---|
| Runtime/build | Node, Vite | Development server and production build |
| Language | TypeScript | Frontend type safety |
| UI library | React 18 | Component model |
| Routing | React Router | Public/authenticated route tree |
| Server state | TanStack Query | API caching, invalidation, polling fallback |
| Forms | React Hook Form | Form state |
| Validation | Zod | Client-side form validation |
| Styling | Tailwind CSS | Utility-first styling |
| Icons | lucide-react | UI icon set |
| Component tests | Vitest, React Testing Library | Frontend unit/component coverage |
| Browser tests | Playwright | E2E, cross-browser smoke, accessibility scans |
| Accessibility | `@axe-core/playwright` | Automated serious/critical WCAG checks |
| Lint/format | ESLint, Prettier | Frontend quality checks |

### Infrastructure And Operations

| Area | Technology | Purpose |
|---|---|---|
| Local orchestration | Docker Compose | Local backend, frontend, PostgreSQL, Redis, worker, scheduler, Adminer |
| Production orchestration | Docker Compose | Private app services behind Caddy |
| TLS/reverse proxy | Caddy | Public HTTP/HTTPS entry point |
| Local DB inspection | Adminer | Local-only PostgreSQL inspection |
| CI | GitHub Actions | Verify and E2E jobs |
| Release automation | GitHub Actions + shell scripts | Backup, migrations, drift check, deploy, smoke, rollback notes |
| Email provider | Resend or console adapter | External email notification delivery |

## 4. Runtime Architecture

### Local Development Topology

`docker-compose.yml` starts:

| Service | Role | Public exposure |
|---|---|---|
| `postgres` | PostgreSQL database | Host port `5432` |
| `redis` | Celery broker/result backend | Host loopback Redis port |
| `backend` | FastAPI API | Host port `8000` |
| `worker` | Celery worker | No public port |
| `scheduler` | Celery beat scheduler | No public port |
| `frontend` | Vite dev server | Host loopback frontend port, default `5173` |
| `adminer` | Local DB admin UI | Host loopback Adminer port, default `8080` |
| `e2e` | Playwright runner profile | Runs on demand |

Local API requests usually flow:

```text
Browser -> Vite dev server -> FastAPI backend -> PostgreSQL
                                      `------> Redis/Celery for async work
```

### Production Topology

`docker-compose.prod.yml` starts:

| Service | Role | Public exposure |
|---|---|---|
| `caddy` | TLS/reverse proxy | Public HTTP/HTTPS ports |
| `frontend` | Built frontend static server/container | Private |
| `backend` | FastAPI API | Private, healthchecked |
| `postgres` | PostgreSQL database | Private volume |
| `redis` | Celery broker/result backend | Private volume |
| `worker` | Celery worker | Private |
| `scheduler` | Celery beat scheduler | Private, exactly one instance in V1 |

Production traffic flows:

```text
Browser -> Caddy -> frontend
Browser -> Caddy -> backend API/WebSocket
backend -> PostgreSQL
backend -> Redis -> worker
scheduler -> Redis -> worker -> PostgreSQL
worker -> Resend or console provider
```

The current production deployment described in project memory is behind:

```text
https://rgalvaro.es/
https://www.rgalvaro.es/
```

At the time of this document, production is documented as deployed at Alembic `0012`, while `main` now includes migrations through `0014`. A production release is needed before production reflects `SPEC-314`, `SPEC-315`, and `SPEC-316`.

## 5. Backend Architecture

The backend is organized into explicit layers:

| Layer | Path | Responsibility |
|---|---|---|
| API routers | `backend/app/api/` | FastAPI endpoints, dependency wiring, response schemas |
| Services | `backend/app/services/` | Business rules, authorization policy, state transitions |
| Repositories | `backend/app/repositories/` | Query/persistence boundaries |
| Models | `backend/app/models/` | SQLAlchemy persistence models |
| Schemas | `backend/app/schemas/` | Pydantic request/response contracts |
| DB | `backend/app/db/` | Engine/session/base metadata |
| Jobs | `backend/app/jobs/` | Celery app, tasks, enqueue helpers |
| Notifications | `backend/app/notifications/` | Background notification payloads and external delivery adapters |
| Core | `backend/app/core/` | Environment-backed settings |

Routers stay thin. Business decisions belong in services. Data access is isolated in repositories where practical. SQLAlchemy models represent storage, while Pydantic schemas define API shape.

### Backend Application Entry Point

`backend/app/main.py` creates the FastAPI app, registers a shared `APIError` handler, and includes these routers:

- auth
- users
- organizations
- projects
- tasks
- labels
- invitations
- notifications
- client tickets
- chat
- operational audit
- health

### Settings

Settings are defined in `backend/app/core/config.py` using `pydantic-settings`. Important variables:

| Variable | Purpose |
|---|---|
| `APP_ENV` | Runtime environment label |
| `DEBUG` | Debug flag |
| `DATABASE_URL` / `PROD_DATABASE_URL` | SQLAlchemy database URL |
| `AUTH_SECRET_KEY` | JWT signing secret |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token lifetime |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token lifetime |
| `ACCESS_TOKEN_COOKIE_NAME` | Access cookie name |
| `REFRESH_TOKEN_COOKIE_NAME` | Refresh cookie name |
| `AUTH_COOKIE_SECURE` | Secure cookie flag |
| `AUTH_COOKIE_SAMESITE` | Cookie SameSite policy |
| `CELERY_BROKER_URL` | Redis broker URL |
| `CELERY_RESULT_BACKEND` | Redis result backend URL |
| `EMAIL_NOTIFICATIONS_ENABLED` | External email delivery enablement |
| `EMAIL_DELIVERY_PROVIDER` | `console` or `resend` |
| `PUBLIC_APP_URL` / `PROD_PUBLIC_APP_URL` | Absolute URL for user-facing links |
| `RESEND_API_KEY` / `PROD_RESEND_API_KEY` | Resend credential |
| `RESEND_FROM_EMAIL` / `PROD_RESEND_FROM_EMAIL` | Email sender |
| `EMAIL_PROVIDER_TIMEOUT_SECONDS` | Provider request timeout |

## 6. Database Model

OpsDesk stores data in PostgreSQL. Alembic migrations version the schema.

### Migration Timeline

| Revision | Purpose |
|---|---|
| `0001` | Initial baseline |
| `0002` | Users |
| `0003` | Organizations |
| `0004` | Single owner enforcement |
| `0005` | Projects and tasks |
| `0006` | Enriched record metadata |
| `0007` | Project task labels |
| `0008` | Member invitations and project access |
| `0009` | In-app notifications |
| `0010` | Project clients and tickets |
| `0011` | Ticket assignment requests |
| `0012` | Organization member chat |
| `0013` | External notification deliveries |
| `0014` | Operational audit runs |

### Core Tables And Models

| Model | Table | Purpose |
|---|---|---|
| `User` | `users` | Authenticated users, profile fields, account type |
| `Organization` | `organizations` | Tenant/workspace boundary |
| `OrganizationMembership` | organization membership table | Owner/admin/member RBAC |
| `Invitation` | invitations | Organization and project invitations |
| `Project` | `projects` | Work container within an organization |
| `ProjectMembership` | project membership table | Project-level membership |
| `Task` | `tasks` | Internal task and client ticket base record |
| `TaskWatcher` | task watchers | Notification/watch relationships |
| `TaskLabel` | task labels | Project-scoped task labels |
| `TaskLabelAssignment` | task-label assignments | Many-to-many task labels |
| `ProjectClientAccess` | project client access | Client user access to projects |
| `TicketComment` | ticket comments | Client/internal ticket discussion |
| `TicketAssignmentRequest` | ticket assignment requests | Worker handoff acceptance workflow |
| `Notification` | notifications | Persistent in-app notifications |
| `NotificationDelivery` | notification deliveries | External delivery audit/retry state |
| `ChatConversation` | chat conversations | Organization/direct chat conversations |
| `ChatConversationParticipant` | chat participants | Conversation membership/read state |
| `ChatMessage` | chat messages | Persisted chat messages |
| `OperationalAuditRun` | operational audit runs | Scheduled job run evidence |

### Important Enums

| Enum | Values / Role |
|---|---|
| `UserAccountType` | Internal user vs restricted client user |
| `MembershipRole` | Owner, admin, member |
| `InvitationScope` | Organization or project |
| `InvitationStatus` | Pending, accepted, declined, expired, revoked |
| `ProjectStatus` | Project lifecycle |
| `ProjectVisibility` | Organization/project visibility rules |
| `TaskStatus` | Task/ticket workflow status |
| `TaskPriority` | Task priority |
| `TaskType` | Internal task vs client ticket |
| `TicketAssignmentRequestStatus` | Pending/accepted/declined |
| `NotificationType` | Invitation, project, task, ticket, chat, assignment notification categories |
| `NotificationDeliveryStatus` | Pending, sent, failed, suppressed |
| `OperationalAuditStatus` | Started, succeeded, failed, skipped |

## 7. API Surface

All versioned public API paths use `/api/v1` unless explicitly health-related. API errors use the shared envelope:

```json
{
  "error": {
    "code": "stable_code",
    "message": "Human-readable safe message",
    "details": {}
  }
}
```

List endpoints use:

```json
{
  "items": [],
  "total": 0,
  "limit": 20,
  "offset": 0
}
```

### Authentication And Users

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/api/v1/auth/register` | Register internal user |
| `POST` | `/api/v1/auth/login` | Login and set cookies |
| `POST` | `/api/v1/auth/refresh` | Refresh session |
| `POST` | `/api/v1/auth/logout` | Clear session cookies |
| `GET` | `/api/v1/users/me` | Current user profile |
| `PATCH` | `/api/v1/users/me` | Update current user profile |

Authentication uses JWTs stored in httpOnly cookies. Access tokens are short-lived. Refresh tokens are longer-lived. Production cookies are `Secure`.

### Organizations And RBAC

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/api/v1/organizations` | Create organization |
| `GET` | `/api/v1/organizations` | List current user's organizations |
| `GET` | `/api/v1/organizations/{organization_id}` | Organization detail |
| `PATCH` | `/api/v1/organizations/{organization_id}` | Update organization metadata |
| `DELETE` | `/api/v1/organizations/{organization_id}` | Delete organization |
| `GET` | `/api/v1/organizations/{organization_id}/members` | List members |
| `PATCH` | `/api/v1/organizations/{organization_id}/members/{user_id}` | Change member role |
| `DELETE` | `/api/v1/organizations/{organization_id}/members/{user_id}` | Remove member |
| `POST` | `/api/v1/organizations/{organization_id}/transfer-ownership` | Transfer ownership |

Tenant isolation is enforced server-side. Backend authorization is authoritative; frontend checks are UX only.

### Invitations

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/api/v1/organizations/{organization_id}/invitations` | Invite user to organization |
| `GET` | `/api/v1/organizations/{organization_id}/invitations` | List organization invitations |
| `DELETE` | `/api/v1/organizations/{organization_id}/invitations/{invitation_id}` | Revoke invitation |
| `GET` | `/api/v1/invitations` | List current user's invitations |
| `POST` | `/api/v1/invitations/{invitation_id}/accept` | Accept invitation |
| `POST` | `/api/v1/invitations/{invitation_id}/decline` | Decline invitation |
| `POST` | `/api/v1/projects/{project_id}/invitations` | Invite user to project |

Invitation notifications are created for relevant recipients. Expired pending invitations are later marked by scheduled maintenance.

### Projects

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/api/v1/organizations/{organization_id}/projects` | Create project |
| `GET` | `/api/v1/organizations/{organization_id}/projects` | List projects |
| `GET` | `/api/v1/projects/{project_id}` | Project detail |
| `PATCH` | `/api/v1/projects/{project_id}` | Update project |
| `GET` | `/api/v1/projects/{project_id}/members` | List project members |
| `DELETE` | `/api/v1/projects/{project_id}/members/{user_id}` | Remove project member |

Projects belong to organizations. Access depends on organization membership, project visibility, project membership, or client access depending on workflow.

### Tasks And Labels

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/api/v1/projects/{project_id}/tasks` | Create task |
| `GET` | `/api/v1/projects/{project_id}/tasks` | List tasks with filters |
| `GET` | `/api/v1/tasks/{task_id}` | Task detail |
| `PATCH` | `/api/v1/tasks/{task_id}` | Update task |
| `GET` | `/api/v1/projects/{project_id}/labels` | List labels |
| `POST` | `/api/v1/projects/{project_id}/labels` | Create label |
| `PATCH` | `/api/v1/projects/{project_id}/labels/{label_id}` | Update label |
| `POST` | `/api/v1/tasks/{task_id}/labels` | Assign label to task |
| `DELETE` | `/api/v1/tasks/{task_id}/labels/{label_id}` | Remove label from task |

Task assignment changes can enqueue background notifications. Task labels are project-scoped.

### Client Tickets

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/v1/projects/{project_id}/clients` | List project clients |
| `POST` | `/api/v1/projects/{project_id}/clients` | Grant client access |
| `DELETE` | `/api/v1/projects/{project_id}/clients/{client_access_id}` | Revoke client access |
| `GET` | `/api/v1/projects/{project_id}/tickets` | Internal ticket list |
| `GET` | `/api/v1/tickets/{ticket_id}` | Internal ticket detail |
| `PATCH` | `/api/v1/tickets/{ticket_id}` | Internal ticket update |
| `GET` | `/api/v1/tickets/{ticket_id}/comments` | Ticket comments |
| `POST` | `/api/v1/tickets/{ticket_id}/comments` | Add ticket comment |
| `GET` | `/api/v1/client/projects` | Client's accessible projects |
| `POST` | `/api/v1/client/projects/{project_id}/tickets` | Client creates ticket |
| `GET` | `/api/v1/client/tickets` | Client ticket list |
| `GET` | `/api/v1/client/tickets/{ticket_id}` | Client ticket detail |
| `GET` | `/api/v1/client/tickets/{ticket_id}/comments` | Client ticket comments |
| `POST` | `/api/v1/client/tickets/{ticket_id}/comments` | Client adds comment |

Client accounts are restricted. They can see their project/ticket surfaces, not internal organization/admin areas.

### Ticket Assignment Requests

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/v1/ticket-assignment-requests` | List pending assignment requests |
| `POST` | `/api/v1/ticket-assignment-requests/{request_id}/accept` | Accept handoff |
| `POST` | `/api/v1/ticket-assignment-requests/{request_id}/decline` | Decline handoff |

Acceptance revalidates current project access and assignment eligibility before mutating the task assignee.

### Notifications

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/v1/notifications` | List notifications |
| `GET` | `/api/v1/notifications/unread-count` | Current unread count |
| `PATCH` | `/api/v1/notifications/{notification_id}` | Mark notification read/unread |
| `POST` | `/api/v1/notifications/mark-all-read` | Mark all notifications read |
| `WS` | `/api/v1/notifications/ws` | Authenticated notification events |

Persistent notifications are stored in PostgreSQL. WebSocket delivery is in-process fan-out with REST polling fallback. Redis pub/sub fan-out remains future scope before horizontal backend scaling.

### Chat

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/v1/organizations/{organization_id}/chat/members` | Chat-capable organization members |
| `GET` | organization chat endpoints | Conversation listing and retrieval |
| `POST` | chat conversation endpoints | Create direct/project conversations |
| `GET` | project chat channel endpoint | Project channel retrieval |
| `POST` | chat message endpoints | Send messages |
| `POST` | `/api/v1/chat/conversations/{conversation_id}/read` | Mark conversation read |
| `POST` | `/api/v1/chat/conversations/{conversation_id}/clear` | Clear conversation unread state |
| `WS` | `/api/v1/chat/ws` | Authenticated chat WebSocket |

Chat uses persisted conversations/messages plus WebSocket delivery. Missed or unread chat activity can create aggregate unread notifications.

### Operational Audit

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/v1/admin/operational-audit` | Owner/admin list of scheduled job audit rows |

The audit endpoint supports `limit`, `offset`, optional `job_name`, and optional `status`. It returns safe operational data only: job name, timestamps, status, counts, and sanitized error summary.

### Health

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/health` | Backend health check |

## 8. Authentication And Authorization

### Session Flow

1. User submits credentials to `/api/v1/auth/login`.
2. Backend verifies password hash.
3. Backend issues access and refresh JWTs.
4. Tokens are stored in httpOnly cookies.
5. Browser API calls include cookies automatically.
6. Protected endpoints resolve the current user through dependencies.
7. Logout clears cookies.

### RBAC Model

Authorization is based on:

- account type: internal vs client
- organization membership role: owner/admin/member
- project membership
- project visibility
- project client access
- resource ownership/recipient checks

Rules:

- Backend authorization is authoritative.
- Tenant-scoped resource access must validate membership/access before returning data.
- Non-members generally receive 404 for hidden tenant resources.
- Members without sufficient role receive 403.
- Client accounts are denied internal app/admin surfaces.

## 9. Frontend Architecture

The frontend is organized by application shell and feature folders:

| Path | Purpose |
|---|---|
| `frontend/src/app/` | Router, shell, providers, public pages, changelog |
| `frontend/src/shared/` | API client and shared helpers |
| `frontend/src/features/auth/` | Login, signup, session, guards |
| `frontend/src/features/profile/` | Current user profile |
| `frontend/src/features/organizations/` | Organization CRUD, members, invitations |
| `frontend/src/features/projects/` | Project list/detail/settings and project task routes |
| `frontend/src/features/tasks/` | Task list/detail/forms/filters |
| `frontend/src/features/client-tickets/` | Client and internal ticket UI |
| `frontend/src/features/notifications/` | Notification inbox and realtime/polling behavior |
| `frontend/src/features/chat/` | Organization chat UI |
| `frontend/src/features/operational-audit/` | Owner/admin scheduled-job audit UI |

### Route Tree

Public routes:

- `/`
- `/terms`
- `/copyright`
- `/cookies`
- `/login`
- `/signup`
- `/changelog`

Authenticated app routes under `/app`:

- `/app`
- `/app/profile`
- `/app/invitations`
- `/app/notifications`
- `/app/admin/operational-audit`
- `/app/ticket-assignment-requests`
- `/app/organizations`
- `/app/organizations/new`
- `/app/organizations/:organizationId`
- `/app/organizations/:organizationId/settings`
- `/app/organizations/:organizationId/members`
- `/app/organizations/:organizationId/chat`
- `/app/organizations/:organizationId/projects`
- `/app/organizations/:organizationId/projects/new`
- `/app/projects/:projectId`
- `/app/projects/:projectId/settings`
- `/app/projects/:projectId/tasks`
- `/app/projects/:projectId/tasks/new`
- `/app/projects/:projectId/tickets`
- `/app/tasks/:taskId`
- `/app/tickets/:ticketId`
- `/app/client`
- `/app/client/tickets/:ticketId`

### Client Data Flow

1. React component renders route.
2. Feature hook calls `apiRequest` from `frontend/src/shared/api.ts`.
3. Browser sends cookie-authenticated request.
4. TanStack Query caches server state.
5. Mutations invalidate relevant query keys.
6. WebSocket events update notification/chat state when connected.
7. Polling fallback keeps notifications usable if WebSocket is unavailable.

## 10. Background Jobs And Notifications

### Celery Runtime

`backend/app/jobs/celery_app.py` configures Celery with:

- JSON serialization
- Redis broker
- Redis result backend
- UTC timezone
- deterministic beat schedule
- included task module `app.jobs.tasks`

### Worker Tasks

| Task | Purpose |
|---|---|
| `notifications.task_assignment` | Process task assignment notification payloads |
| `notifications.external_delivery` | Process one external delivery audit row |
| `notifications.external_delivery_due` | Sweep due external deliveries |
| `operational.scheduler_heartbeat` | Record scheduler heartbeat audit |
| `operational.external_delivery_retry_sweep` | Retry due external email deliveries with audit |
| `operational.expired_invitation_maintenance` | Mark expired invitations |
| `operational.stale_ticket_assignment_request_reminders` | Re-emit safe idempotent assignment request reminders |

### Scheduled Jobs

Celery beat schedules:

| Schedule entry | Task | Interval |
|---|---|---|
| `scheduler-heartbeat` | `operational.scheduler_heartbeat` | 5 minutes |
| `external-delivery-retry-sweep` | `operational.external_delivery_retry_sweep` | 5 minutes |
| `expired-invitation-maintenance` | `operational.expired_invitation_maintenance` | 1 hour |
| `stale-ticket-assignment-request-reminders` | `operational.stale_ticket_assignment_request_reminders` | 6 hours |

Production V1 expects exactly one scheduler. Multiple schedulers need a future locking/scaling spec.

### External Email Delivery

Email delivery uses the notification delivery audit table:

1. A business event creates an in-app notification.
2. The notification service may enqueue an email delivery row.
3. A Celery task processes the delivery.
4. The provider is either `console` or `resend`.
5. Success/failure/suppression is recorded on the delivery audit row.
6. Scheduled retry sweeps process pending due deliveries.

Email logs and audit rows avoid raw provider payloads, secrets, tokens, cookies, and message bodies.

## 11. WebSockets And Realtime Behavior

OpsDesk has two realtime channels:

| Channel | Endpoint | Purpose |
|---|---|---|
| Notifications | `/api/v1/notifications/ws` | Notification created/read/read-all events |
| Chat | `/api/v1/chat/ws` | Chat delivery and conversation activity |

The current implementation uses authenticated WebSockets and in-process fan-out. This is sufficient for one backend instance. Horizontal backend scaling needs Redis pub/sub or equivalent shared fan-out.

Fallback behavior:

- Notifications keep REST list/unread APIs.
- Frontend uses TanStack Query cache updates and polling fallback where needed.
- Backend remains the source of truth.

## 12. Security Model

### Secrets

Secrets are not committed. Real environment files are ignored. `.env.example` documents expected variables.

Important secrets:

- database passwords
- `AUTH_SECRET_KEY`
- Resend API key
- production SSH/GitHub Actions secrets

### Cookies And Tokens

- Browser auth uses httpOnly cookies.
- Production cookies are secure.
- Access token default lifetime: 15 minutes.
- Refresh token default lifetime: 7 days.
- Logout clears access and refresh cookies.

### Data Isolation

Tenant isolation is enforced in backend services/policies. Frontend route visibility is not treated as security. Every tenant-scoped backend operation must validate access.

### Logging And Audit Safety

Logs and operational audit rows should include:

- safe ids
- job names
- status values
- counts
- exception classes

They must not include:

- passwords
- JWTs
- cookies
- API tokens
- provider payloads
- private message bodies
- raw email contents

## 13. Deployment And Release Process

Production deployment is documented in `docs/deployment.md` and automated by `scripts/prod_release.sh` plus GitHub Actions.

Release flow:

1. Validate target commit.
2. Run CI verification.
3. Connect to VPS.
4. Create pre-deploy backup.
5. Build backend image before migrations.
6. Run `alembic upgrade head`.
7. Run `alembic check` for migration drift.
8. Recreate/update Compose services.
9. Check backend health.
10. Check frontend.
11. Check Redis.
12. Check worker.
13. Check scheduler.
14. Record release manifest.

Rollback docs cover stopping app services and restoring backups. Database rollback must be treated carefully because migrations may be destructive or not trivially reversible in production data.

## 14. Validation Harness

Primary Make targets:

| Command | Purpose |
|---|---|
| `make verify` | Full local verification including migrations |
| `make verify-no-db` | Lint, format, type checks, non-DB tests |
| `make test` | Backend and frontend tests |
| `make test-backend` | Backend tests excluding DB-marked tests |
| `make test-frontend` | Vitest frontend suite |
| `make test-e2e` | Playwright suite against Docker/local stack |
| `make lint` | Backend Ruff and frontend ESLint |
| `make format-check` | Backend Ruff format check and frontend Prettier |
| `make typecheck` | Backend mypy and frontend TypeScript |
| `make migrations-check` | Host Alembic upgrade/check |
| `make migrations-check-compose` | Compose-network Alembic upgrade/check |
| `make smoke` | Local stack health checks |
| `make prod-config` | Production Compose render/syntax validation |
| `make prod-data-smoke` | Production-like data backup/restore/migration smoke |
| `make prod-smoke` | Isolated production stack smoke |
| `make prod-down` | Stop isolated production smoke stack |
| `make changelog-check` | Changelog validation |
| `make release-workflow-check` | Production release workflow validation |
| `make memory-check SPEC=SPEC-XXX` | Pre-review memory validation |
| `make merge-memory-check SPEC=SPEC-XXX` | Post-merge memory validation |

CI currently runs verify and E2E checks. Playwright includes Chromium full coverage, mobile Chromium critical path, Firefox/WebKit smoke, and automated accessibility checks.

## 15. Main Product Workflows

### Internal User Signup To Work Management

1. User registers.
2. User logs in.
3. User creates an organization and becomes owner.
4. Owner creates projects.
5. Owner/admin/member creates tasks.
6. Tasks can be updated, filtered, assigned, watched, and labeled.
7. Notifications are created for relevant assignment/project/task activity.

### Organization Invitation

1. Owner/admin invites a target email.
2. Invitation row is created.
3. If target user exists, an in-app notification can be created.
4. Target user accepts or declines from invitation UI.
5. Accepting creates organization/project membership depending on scope.
6. Expired pending invitations are later marked by scheduled maintenance.

### Client Ticket Workflow

1. Internal user grants a client access to a project.
2. Client account logs into restricted client shell.
3. Client creates a ticket in an accessible project.
4. Internal users see ticket in project/internal ticket surfaces.
5. Client and internal users can add comments subject to access policy.
6. Assignment handoff requests can require explicit worker acceptance.
7. Notifications and reminders are generated for pending assignment requests.

### Notification Workflow

1. Business event occurs.
2. Notification service creates a persistent notification if no equivalent unread one exists where idempotency is required.
3. In-app inbox can list and mark notifications.
4. WebSocket pushes created/read-count events to active sessions.
5. Optional email delivery row is created.
6. Worker sends external delivery.
7. Retry sweep handles pending due deliveries.

### Chat Workflow

1. Authenticated internal user opens organization chat.
2. Backend validates organization/project access.
3. User lists or creates conversations.
4. Messages persist in PostgreSQL.
5. WebSocket delivers live activity.
6. Read/clear endpoints update unread state.
7. Missed chat activity can produce aggregate notifications.

### Scheduled Operational Audit Workflow

1. Scheduler enqueues configured Celery beat task.
2. Worker starts the task.
3. `OperationalAuditService.run_job` writes a `started` audit row.
4. Job performs idempotent maintenance.
5. On success, audit row records status and safe counts.
6. On failure, audit row records failure status, exception class, and generic safe summary.
7. Owner/admin can inspect rows in `/app/admin/operational-audit`.

## 16. Observability And Operations

The app currently uses:

- health endpoint
- Compose healthchecks
- CI checks
- logs
- persistent delivery audit rows
- persistent operational audit rows
- release manifests
- project memory docs

Not currently implemented:

- centralized metrics backend
- external alerting vendor
- distributed tracing
- multi-backend WebSocket fan-out
- distributed scheduler locking

These are future scale/operations concerns, not required for the current portfolio-grade deployment.

## 17. Known Technical Gaps

The current known gaps are intentionally documented rather than hidden:

- Production currently needs a release to move from deployed Alembic `0012` to current `main` through `0014`.
- A full privacy policy remains needed before production use that relies on real user account/profile data beyond portfolio evaluation.
- Redis pub/sub or another shared fan-out layer is needed before horizontal backend scaling of WebSockets.
- Scheduler production V1 expects exactly one scheduler instance; multiple schedulers require future locking/scaling design.
- Manual deletion/retention management for notifications, delivery audits, and operational audit rows is future scope.
- Visual snapshot testing is future scope; accessibility and cross-browser smoke coverage already exist.
- Full observability stack and external alerting are future scope.

## 18. PDF Strategy

This document is written to be PDF-friendly:

- one Markdown file
- stable heading hierarchy
- no embedded HTML
- simple tables
- fenced code blocks
- no external image dependency
- no generated table of contents syntax tied to a specific tool

The preferred conversion path later is Pandoc:

```bash
pandoc docs/technical-documentation.md \
  -o docs/technical-documentation.pdf \
  --toc \
  --pdf-engine=xelatex
```

If LaTeX is not available, an alternate path is Markdown to HTML and then Chromium/Playwright print-to-PDF. That can be scripted without changing this source document.

Current environment note: no PDF converter was found in PATH during documentation preparation (`pandoc`, `wkhtmltopdf`, `weasyprint`, and `md-to-pdf` were not installed). The Markdown source is therefore the canonical artifact for now.

## 19. Public Summary Strategy

The later public production version should not publish this full internal detail. It should be a short technical overview with:

- product purpose
- high-level architecture diagram text
- stack summary
- security highlights
- deployment/CI highlights
- selected feature list
- testing/quality strategy
- known scale boundaries

It should omit:

- operational secrets and exact secret names where not needed
- excessive endpoint tables
- internal process history
- VPS-specific backup paths
- low-level implementation details that do not help a reviewer understand quality

## 20. Source Of Truth References

Primary source documents:

- `specs/README.md`
- `specs/000-product-vision.md`
- `specs/001-api-conventions.md`
- `specs/features/*.md`
- `docs/project-state.md`
- `docs/implementation-log.md`
- `docs/deployment.md`
- `docs/decisions/*.md`
- Alembic migrations under `backend/alembic/versions/`
- Backend and frontend tests

If this document conflicts with specs, migrations, tests, or ADRs, the lower-level source of truth wins and this document should be updated.

## 21. Maintenance Harness

Run this check after changes that affect architecture, runtime services, migrations, APIs, frontend routes, deployment, jobs, WebSockets, security, or PDF/public documentation strategy:

```bash
make technical-docs-check
```

The check verifies that this document keeps required architecture sections, mentions the current Alembic head, mentions Compose services from local and production Compose files, includes required stack technologies, and remains ASCII-only for predictable PDF conversion.

`make verify-no-db` also runs `make technical-docs-check`, so normal verification catches stale technical documentation before PR review.
