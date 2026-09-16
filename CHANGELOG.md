# Changelog

## 2026-09-16 - Operations Readiness Release

### Added

- Cross-browser Playwright smoke coverage and automated accessibility checks for critical public, authenticated, and client-facing routes.
- External notification delivery with Resend-backed email support, delivery audit rows, retry handling, and safe provider logging.
- Real-time notification inbox updates through authenticated WebSockets with REST polling fallback.
- Scheduled maintenance jobs with Celery beat, operational audit records, and an owner/admin operational audit screen.
- Public terms, copyright, and cookie-policy pages linked from the public portfolio home.
- Internal technical documentation covering architecture, stack, runtime services, data model, API surfaces, validation, and production constraints.

### Changed

- Production Compose now includes a private Celery beat scheduler service alongside the backend, frontend, PostgreSQL, Redis, and worker services.
- Production release checks now expect the scheduler service to be running after deployment.
- The frontend public surface now includes legal-information routes in addition to the portfolio home and changelog.

## 2026-08-18 - Collaboration Release

### Added

- Project client accounts can now create tickets, follow ticket status, and participate in ticket comments.
- Internal team members can use organization chat with direct conversations, organization channels, project channels, unread state, and real-time message delivery.
- Project teams can manage client access and accepted ticket handoff requests from the authenticated app.

### Changed

- Notifications now include unread chat summaries and ticket collaboration events alongside the existing inbox workflow.

## 2026-08-14 - Notification Inbox Release

### Added

- Persistent in-app notification inbox with unread count, mark-read, mark-all-read, and action links.
- Notification fan-out for organization/project invitations, project access changes, project updates, task assignments, and task status changes.

### Changed

- The authenticated app shell now shows notification unread state while keeping invitations as the dedicated accept/decline surface.

## 2026-08-12 - Production Release

### Added

- Project-scoped task labels with color, description, archive state, task assignment, and label filtering.
- User, organization, project, and task metadata fields for richer portfolio demo workflows.

### Changed

- Production release automation now validates migration drift after applying migrations.
- Project label management is available from the project detail page for regular project-visible team members.

### Fixed

- Production releases now build the backend image before running migrations so newly added migration files are available during deploy.
