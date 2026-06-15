# SPEC-011 — Local Database Admin

Status: Implemented  
Owner: Arquitecto de specs  
Last updated: 2026-06-10

## Problem

Developers and review agents need a quick way to inspect and manually verify local PostgreSQL state while implementing specs. Direct database inspection is useful for debugging migrations, seed/demo data, and CRUD flows, but it must not become a production feature or bypass application authorization in deployed environments.

## Goals

- Provide a local-only browser database administration panel for the Docker Compose PostgreSQL service.
- Allow direct inspection of schemas, tables, rows, indexes, constraints, and migration state during development.
- Make connection details discoverable from committed local setup docs without committing secrets.
- Keep the tool isolated from production Compose and public deployment paths.
- Make local smoke validation able to confirm the admin panel starts without requiring destructive database actions.

## Dependencies

- Requires `SPEC-010` local PostgreSQL service, Docker Compose baseline, `.env.example`, and local validation harness.
- Supports later data-model specs: `SPEC-101`, `SPEC-102`, `SPEC-103`, and future migration-heavy features.
- Related decision: `docs/decisions/ADR-004-local-database-admin-tool.md`.

## Non-Goals

- Product-facing admin UI.
- Superuser management workflow.
- CRUD APIs for arbitrary database tables.
- Production database administration.
- Exposing PostgreSQL or the admin panel on a public network.
- Replacing migrations, repositories, service-layer validation, or application authorization tests.
- Managing remote or cloud databases.

## Actors And Permissions

| Actor | Permission | Notes |
|---|---|---|
| Developer | Open local DB admin panel and inspect local database | Uses local Docker Compose only |
| Review agent | Verify local database state while reviewing specs | Uses documented local credentials |
| Authenticated app user | None | App auth does not grant DB admin access |
| Production visitor | None | Service must not exist in production Compose |

## Business Rules

- BR-1: The database admin panel is local development tooling only.
- BR-2: The service must be defined only in local Compose configuration, not `docker-compose.prod.yml`.
- BR-3: The panel may bind to `127.0.0.1` on the host; it must not intentionally bind to all public interfaces.
- BR-4: The panel connects to the Compose `postgres` service using local development credentials from `.env` or `.env.example`.
- BR-5: Real production credentials, database dumps, personal data, or remote connection profiles must not be committed.
- BR-6: The tool may allow direct row edits locally, but such edits are not a substitute for migrations, tests, fixtures, or application APIs.
- BR-7: Documentation must state that local direct DB changes can invalidate test assumptions and should be reset through documented Docker/database reset commands when needed.
- BR-8: Local DB admin availability must not be required for production deployment or CI.

## Tooling Contract

Use Adminer as the default local database administration tool.

Expected local service behavior:

- Service name: `adminer`.
- Image: stable Adminer image pinned to a major/minor or explicit version where practical.
- Depends on local `postgres` service.
- Host binding: `127.0.0.1:8080:8080` unless the port is already owned by another documented local service.
- Connection target from the browser:
  - System: `PostgreSQL`
  - Server: `postgres`
  - Database: value of `POSTGRES_DB`
  - Username: value of `POSTGRES_USER`
  - Password: value of `POSTGRES_PASSWORD`

If implementation chooses a different local port, README and validation docs must name it explicitly.

## Required Repository Impact

Update only files needed for local tooling:

```text
.
├── docker-compose.yml
├── .env.example
├── README.md
├── specs/harness/local-validation.md
└── docs/
    └── decisions/
```

Do not add frontend product routes, backend API routes, database models, or migrations for this spec.

## Configuration Contract

`.env.example` must continue to document local database variables from `SPEC-010`.

Additional variables are optional. If added, they must use safe local defaults:

| Variable | Purpose | Example |
|---|---|---|
| `ADMINER_PORT` | Optional local host port for Adminer | `8080` |

If `ADMINER_PORT` is not added, the local port must be documented directly in README and validation docs.

## Docker Compose Contract

`docker-compose.yml` must include the local `adminer` service.

Rules:

- Adminer must use the same Docker network as `postgres`.
- Adminer must not require backend code to run.
- Adminer must not be included in `docker-compose.prod.yml`.
- Adminer must not mount repository source code or database data.
- PostgreSQL exposure rules from `SPEC-010` remain unchanged.

## Data Model Impact

None.

This spec must not create, alter, or drop application tables.

## API Contract

None.

This spec exposes no OpsDesk HTTP API endpoints.

## Frontend Impact

None.

This spec must not add a product UI route. The Adminer web interface is external local developer tooling.

## Documentation Impact

README or local setup docs must explain:

- How to start the local database admin panel.
- The local URL, expected to be `http://127.0.0.1:8080`.
- How to connect to PostgreSQL from Adminer using the Compose service name and local credentials.
- That the tool is for local inspection only and is not deployed publicly.
- How to stop the local stack.

`specs/harness/local-validation.md` must include a local smoke check for the Adminer URL once implemented.

## Acceptance Criteria

- AC-1: Given local Docker Compose is started, when a developer opens the documented Adminer URL, then the Adminer login page is reachable from localhost.
- AC-2: Given local PostgreSQL is healthy, when a developer logs in through Adminer using documented local credentials, then the `opdesk` database can be inspected.
- AC-3: Given `docker-compose.prod.yml` is inspected, when production services are reviewed, then Adminer is not present.
- AC-4: Given committed files are inspected, when secrets are reviewed, then no real DB credentials, dumps, remote connection profiles, or personal data are committed.
- AC-5: Given local validation runs, when smoke checks execute, then the Adminer HTTP endpoint is checked without requiring database mutation.
- AC-6: Given README/local docs are read, when a developer wants direct DB inspection, then the URL and login values are discoverable without guessing.

## Harness Requirements

Required checks:

- Docker Compose config validation if available.
- Local smoke check for Adminer HTTP availability.
- Secret review through existing repository review expectations.
- Production Compose review confirming Adminer is absent.

Required commands once implemented:

```bash
docker compose up -d postgres adminer
curl -f http://127.0.0.1:8080
docker compose config
```

If `curl` returns a redirect or HTML login page, that is acceptable as long as the command exits successfully.

## Observability And Failure Cases

- Adminer startup failures should be visible through Docker Compose logs.
- Invalid DB credentials should fail at Adminer login and should not trigger application errors.
- Port conflicts on `8080` must be resolved by documenting the chosen alternative port.
- This service should not emit application logs and should not be part of backend observability.

## Open Questions

- None.

## Implementation Notes

- Prefer Adminer over pgAdmin for this project because it is lightweight, needs no persistent configuration volume, and is sufficient for local schema/table inspection.
- Do not gate Adminer behind OpsDesk authentication; it is a separate local developer tool.
- Do not add Adminer to production deployment docs except to state that it is intentionally absent from production.
