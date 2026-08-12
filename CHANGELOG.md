# Changelog

## 2026-08-12 - Production Release

### Added

- Project-scoped task labels with color, description, archive state, task assignment, and label filtering.
- User, organization, project, and task metadata fields for richer portfolio demo workflows.

### Changed

- Production release automation now validates migration drift after applying migrations.
- Project label management is available from the project detail page for regular project-visible team members.

### Fixed

- Production releases now build the backend image before running migrations so newly added migration files are available during deploy.
