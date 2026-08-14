# Changelog

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
