# SPEC-307 — Release Automation And Safe Updates

Status: Ready
Owner: Arquitecto de specs
Last updated: 2026-07-22

## Scope And Required Context

This spec governs:

- GitHub Actions release/deployment workflows for updating an already deployed production VPS.
- Server-side update scripts or commands that pull/build/start the production Compose stack.
- Pre-deploy backups, Alembic migration execution, post-deploy health checks, rollback guidance, deployment secrets, and release evidence.

Required context:

- `AGENTS.md`
- `docs/project-state.md`
- `specs/README.md`
- `specs/harness/local-validation.md`
- `specs/features/301-deployment-and-ops.md`
- `docs/deployment.md`
- `docs/decisions/ADR-008-production-compose-and-caddy.md`
- `docs/decisions/ADR-009-managed-sandbox-github-cli.md`

Memory updates:

- `docs/project-state.md` when release readiness, deployment baseline, known gaps, or next work changes
- `docs/implementation-log.md` for spec-prep, implementation, validation, review, deployment, or rollback evidence
- `specs/README.md` when status, dependencies, order, or primary surfaces change
- ADRs if the implementation changes deployment topology, image distribution, secret handling, rollback strategy, or CI/CD trust boundaries

## Problem

`SPEC-301` provides a production deployment path, but updates after the initial public launch still rely on an operator manually running the right commands in the right order. A missed backup, skipped migration, stale Compose build, or absent health check can turn a routine update into an avoidable outage.

OpsDesk needs a repeatable and reviewable update mechanism for post-launch changes while staying simple enough for a solo portfolio VPS deployment.

## Goals

- Provide a controlled release workflow for updating the existing production VPS after the first public deployment.
- Make production updates explicit, auditable, and hard to run without validation.
- Take a PostgreSQL backup before applying production migrations or replacing running app containers.
- Run migrations and production Compose updates through one documented path.
- Verify backend, frontend, Redis, and worker health after each update.
- Document rollback steps and preserve enough release evidence for future agents and reviewers.

## Non-Goals

- Replacing `SPEC-301` initial VPS/domain deployment.
- Requiring auto-deploy on every merge to `main`.
- Kubernetes, blue/green infrastructure, canary releases, or multi-region deployment.
- Managed container registry adoption unless the implementation chooses it and records the decision.
- Fully automated destructive database restore without explicit operator confirmation.

## Actors And Permissions

| Actor | Permission | Notes |
|---|---|---|
| Repository maintainer | Trigger production update workflow | Uses GitHub Actions with protected secrets or a documented equivalent. |
| VPS operator | Prepare `.env.production`, SSH access, backups directory, and production Compose project | May be the same person as the repository maintainer. |
| GitHub Actions runner | Execute validation and remote update commands | Must receive only narrowly scoped secrets needed for deployment. |
| Anonymous user | None | No release endpoints are exposed through the app. |
| Authenticated app user | None | Application roles do not grant deployment permission. |

## Business Rules

- BR-1: The first implementation must use an explicit manual trigger, such as `workflow_dispatch`, unless a later spec or ADR approves automatic deployment from `main`.
- BR-2: A release must run the repository verification baseline before touching production.
- BR-3: Production updates must target a stable Compose project name, normally `opdesk-prod`.
- BR-4: A fresh PostgreSQL custom-format backup must be created before production migrations or container replacement.
- BR-5: If backup creation fails, the deployment must stop before migrations or application updates.
- BR-6: Alembic migrations must run as a blocking step against the production database before the updated app is considered deployed.
- BR-7: The update must rebuild or pull the backend/frontend images and restart the production Compose stack with the existing server-side environment.
- BR-8: Post-deploy checks must include `/health` through Caddy, frontend availability through Caddy, Redis `PING`, and worker running state.
- BR-9: PostgreSQL and Redis must remain private and must not gain public host ports as part of release automation.
- BR-10: Secrets must live in GitHub Actions secrets, server-side secret files, or server environment only; workflows and scripts must not print secret values.
- BR-11: Rollback instructions must distinguish app rollback from database restore. Database restore remains an explicit operator action because it can destroy production data written after the backup.
- BR-12: Release evidence must include the commit or tag deployed, validation status, backup artifact path or identifier, migration result, post-deploy check result, and known gaps.

## Data Model Impact

No application schema changes are required by this spec.

The implementation may add release metadata outside the application database, such as:

- GitHub Actions workflow logs.
- A server-side `releases/` or `backups/` directory.
- A text manifest recording deployed commit, backup file, and timestamp.

If application-level deployment audit tables are introduced later, they require a separate feature spec or an update to this one before implementation.

## API Contract

No public application API endpoints are added or changed.

The existing production health endpoint from `SPEC-301` remains the externally checked backend signal:

```text
GET /health
```

Release automation must not add unauthenticated administrative app endpoints.

## Frontend Impact

No user-facing frontend behavior is required.

The frontend production build must continue to be served through Caddy after an update, and the release workflow must verify the deployed frontend route responds successfully.

## Acceptance Criteria

- AC-1: Given a maintainer opens GitHub Actions, when they trigger the production update workflow manually with a commit or branch input, then the workflow records the target revision before running validation.
- AC-2: Given validation fails, when the workflow runs, then no production backup, migration, or Compose update is attempted.
- AC-3: Given validation passes and production secrets are configured, when the workflow starts the remote update, then it creates a PostgreSQL custom-format backup before migrations.
- AC-4: Given backup creation fails, when the update runs, then migrations and container updates are skipped and the failure is visible in workflow logs.
- AC-5: Given backup succeeds, when migrations run, then `alembic upgrade head` is executed against the production Compose backend environment and a migration failure stops the deployment.
- AC-6: Given migrations pass, when the update continues, then the production Compose stack is rebuilt or refreshed and started with `docker-compose.prod.yml` and the stable production project name.
- AC-7: Given the stack starts, when post-deploy checks run, then `/health`, the frontend route, Redis `PING`, and worker running state are verified.
- AC-8: Given any post-deploy check fails, when the workflow exits, then it marks the release failed and reports the rollback instructions needed for the operator.
- AC-9: Given a release succeeds, when future agents inspect project memory or workflow logs, then they can identify the deployed revision, validation result, backup reference, migration result, and post-deploy status.
- AC-10: Given the production Compose config is inspected after implementation, when services are listed, then PostgreSQL and Redis are still private by default.
- AC-11: Given workflow logs are reviewed, when secrets are used, then secret values are not printed.
- AC-12: Given rollback is documented, when an operator needs to undo an app-only release, then the documented path can redeploy the previous commit or image without automatically restoring the database.

## Harness Requirements

Required tests/checks:

- Workflow validation:
  - Static validation that the release workflow is syntactically valid.
  - A dry-run or non-production path proving the workflow can execute validation without production secrets.
- Script tests:
  - Unit or shell checks for release scripts if scripts are introduced.
  - Failure-path coverage for missing required environment variables where practical.
- Integration/smoke tests:
  - Existing `make prod-config`.
  - Existing `make prod-data-smoke`.
  - Existing `make prod-smoke` and `make prod-down` for isolated production-smoke coverage.
- Migration checks:
  - Existing `make migrations-check` or `make migrations-check-compose`.
- Security checks:
  - Verify no committed production secrets.
  - Verify workflow logs and scripts do not echo secret values.

Required commands:

```bash
make verify
make prod-config
make prod-data-smoke
make prod-smoke
make prod-down
make memory-check SPEC=SPEC-307
```

If the implementation adds a release script or workflow validation target, add it to `Makefile` and this list during implementation.

## Observability And Failure Cases

- Logs:
  - GitHub Actions job summary must show target revision, validation result, backup result, migration result, Compose update result, and post-deploy checks.
  - Server-side scripts may write a non-secret deployment manifest for the latest release.
- Metrics-ready events:
  - Not required for first implementation.
- Expected failure paths:
  - Missing GitHub Actions secrets.
  - SSH connection failure.
  - Backup command failure.
  - Migration failure.
  - Compose build/start failure.
  - Failed backend, frontend, Redis, or worker post-deploy check.
- Retry behavior:
  - Network checks may use bounded retries.
  - Migrations and restores must not retry blindly after failure.

## Open Questions

- [ ] Final VPS hostname, deploy user, and SSH hardening choices.
- [ ] Whether the implementation should build on the VPS from Git source or publish versioned images to a registry.
- [ ] Whether successful manual releases should later evolve into automatic deploys from protected `main`.

## Implementation Notes

- Prefer a manual GitHub Actions `workflow_dispatch` first. It gives CI/CD evidence without making every merge a production change.
- Keep `.env.production` on the VPS; do not copy it into the repository or workflow logs.
- Reuse the `SPEC-301` backup format and production Compose commands unless a new ADR changes the release strategy.
- If deployment uses `gh`, follow `ADR-009` and the managed sandbox GitHub CLI rules.
