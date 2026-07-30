# SPEC-310 — Release Changelog

Status: Ready
Owner: Arquitecto de specs
Last updated: 2026-07-28

## Scope And Required Context

This spec governs:

- Versioned `CHANGELOG.md` entries for production releases/deploys.
- Public frontend access to release changes through a web route or static page.
- Release workflow checks that require changelog evidence before production deployment.
- Documentation and tests for changelog formatting.

Required context:

- `AGENTS.md`
- `docs/project-state.md`
- `specs/README.md`
- `specs/000-product-vision.md`
- `specs/harness/local-validation.md`
- `specs/features/104-frontend-app-shell-and-auth-ui.md`
- `specs/features/301-deployment-and-ops.md`
- `specs/features/307-release-automation-and-safe-updates.md`

Memory updates:

- `docs/project-state.md` when release documentation state, validation baseline, next work, or known gaps change
- `docs/implementation-log.md` for meaningful spec-prep, implementation, review, validation, or merge events
- `specs/README.md` when status, dependencies, order, or primary surfaces change
- ADRs if versioning strategy or release provenance changes materially

## Problem

OpsDesk has deployment evidence and release automation, but there is no user-facing or repository-level changelog that summarizes what changed in each production release. Future reviewers and users should be able to understand releases without reading git history or GitHub Actions logs.

## Goals

- Add a repository-root `CHANGELOG.md`.
- Record only production releases/deploys, not every commit or merged PR.
- Use an `Added`, `Changed`, `Fixed` format for release entries.
- Link to the changelog from the public website.
- Ensure production release workflow or release validation fails when a production deploy lacks an entry for the target release.
- Keep technical deployment evidence in `docs/implementation-log.md` and user-facing release notes in `CHANGELOG.md`.

## Non-Goals

- Generating full changelog entries automatically from commit messages.
- Requiring semantic versioning for every internal PR.
- Replacing GitHub Actions logs, implementation log, or project state.
- Database-backed release notes.
- In-app authenticated notification of release notes.

## Actors And Permissions

| Actor | Permission | Notes |
|---|---|---|
| Anonymous visitor | Read public changelog page | No auth required |
| Authenticated user | Read public changelog page | Same as anonymous |
| Repository maintainer | Add release changelog entries | Required before production deploy |
| GitHub Actions runner | Validate changelog entry exists and is formatted | No app role involved |

## Business Rules

- BR-1: `CHANGELOG.md` lives at the repository root.
- BR-2: Changelog entries are required only for production releases/deploys.
- BR-3: Entries use headings with release version or date and deployment date.
- BR-4: Each release entry may include `Added`, `Changed`, and `Fixed` sections. Empty sections should be omitted.
- BR-5: The newest release entry appears first.
- BR-6: Each production deploy target must identify the changelog entry it is deploying.
- BR-7: The changelog must not include secrets, private operational commands, personal data, raw stack traces, or internal credentials.
- BR-8: The public changelog page must render repository changelog content or a generated static equivalent without requiring authentication.
- BR-9: The public site must link to the changelog from the home or app footer/header after `SPEC-311` is implemented.

## Data Model Impact

No application database changes are required.

New or changed files expected:

- `CHANGELOG.md`
- optional changelog validation script under `scripts/`
- optional generated/static changelog asset under frontend public assets
- frontend route or static page for `/changelog`

## API Contract

No backend API endpoint is required.

If the implementation serves changelog content through the frontend build, it should be static content bundled at build time rather than an authenticated API call.

## Frontend Impact

- Add a public `/changelog` route or static page.
- Add a visible link to the changelog from public navigation once `SPEC-311` home exists.
- The page displays release entries in newest-first order with `Added`, `Changed`, and `Fixed` sections.
- The page must be readable on mobile and desktop.
- The page must not expose internal deployment commands or secrets.

## Changelog Format

`CHANGELOG.md` uses this structure:

```markdown
# Changelog

## 2026-07-28 - Production Release

### Added

- New user-visible feature.

### Changed

- User-visible behavior change.

### Fixed

- User-visible bug fix.
```

Version labels may be date-based until a later spec adopts semantic versioning.

## Acceptance Criteria

- AC-1: Given a production release is prepared, when the maintainer updates release notes, then `CHANGELOG.md` contains a newest-first entry for that release.
- AC-2: Given a production deploy workflow targets a revision, when release validation runs, then it verifies a changelog entry exists for the release.
- AC-3: Given the changelog is linked from the public site, when an anonymous visitor opens it, then they can read release entries without logging in.
- AC-4: Given a changelog entry contains `Added`, `Changed`, or `Fixed`, when rendered on the web, then the section headings and bullets remain legible and ordered.
- AC-5: Given a release has no changes for one section, then the empty section is omitted rather than rendered blank.
- AC-6: Given committed files are inspected, then changelog content contains no secrets, private credentials, or personal data.

## Harness Requirements

Required tests/checks:

- Static validation for `CHANGELOG.md` heading order and allowed sections.
- Release workflow validation that requires a changelog entry when `deploy_to_production=true`.
- Frontend test for public changelog route/link if implemented as a route.
- Existing release workflow checks from `SPEC-307`.

Required commands:

```bash
make release-workflow-check
make test-frontend
make lint
make format-check
make typecheck
make memory-check SPEC=SPEC-310
```

## Observability And Failure Cases

- Release workflow output should report whether changelog validation passed.
- Do not print changelog content as a substitute for validation.
- Missing changelog entry must fail production deploy validation before any production SSH action.

## Open Questions

- [x] Changelog records production releases/deploys only.
- [x] Format uses `Added`, `Changed`, and `Fixed`.
- [x] The public website links to the changelog.

## Implementation Notes

- Prefer a small deterministic parser for `CHANGELOG.md` validation.
- Keep release evidence in `docs/implementation-log.md`; keep user-facing changes in `CHANGELOG.md`.
