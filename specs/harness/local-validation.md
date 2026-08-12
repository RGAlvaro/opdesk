# Local Validation Harness

Status: Ready  
Owner: Review agent  
Last updated: 2026-08-11

This file defines validation commands for local development and review. Feature specs may require a subset or add feature-specific checks.

## Target Make Commands

The repository should converge toward:

```bash
make verify
make verify-no-db
make test
make test-backend
make test-frontend
make lint
make format-check
make typecheck
make migrations-check
make migrations-check-compose
make smoke
make prod-config
make prod-data-smoke
make prod-smoke
make prod-down
make changelog-check
make release-workflow-check
make memory-check SPEC=SPEC-XXX
make review-ready SPEC=SPEC-XXX
make memory-entry SPEC=SPEC-XXX
```

Expected meaning:

| Command | Expected coverage |
|---|---|
| `make verify` | Full local verification before PR |
| `make verify-no-db` | Lint, format, type checks, and non-DB tests without Docker/PostgreSQL access |
| `make test` | Backend and frontend tests |
| `make test-backend` | Backend unit/integration/API tests |
| `make test-frontend` | Frontend unit/component tests |
| `make lint` | Backend and frontend lint |
| `make format-check` | Formatting checks without modifying files |
| `make typecheck` | Backend and frontend type checks where configured |
| `make migrations-check` | Alembic migration consistency from the host Python environment against host-published PostgreSQL |
| `make migrations-check-compose` | Alembic migration consistency from inside the Docker Compose backend container |
| `make smoke` | Docker/local service startup and health checks, including Redis and worker once background jobs exist |
| `make prod-config` | Render and validate the production Compose definition with safe placeholder secrets |
| `make prod-data-smoke` | Apply production migrations and prove backup/restore against the isolated production-smoke database |
| `make prod-smoke` | Run the data smoke, build/start the isolated production stack, and check frontend/backend through Caddy |
| `make prod-down` | Stop the isolated production-smoke stack without deleting its database volume |
| `make changelog-check` | Validate root `CHANGELOG.md` structure, newest-first release entries, allowed sections, bullets, and secret-like content guards |
| `make release-workflow-check` | Validate the manual production release workflow, release script syntax, changelog guardrails, and missing-env failure guard |
| `make memory-check SPEC=SPEC-XXX` | Checks that `docs/project-state.md` and `docs/implementation-log.md` mention the active spec and include required log sections before review handoff |
| `make review-ready SPEC=SPEC-XXX` | Alias for the current memory readiness check; feature specs still define the validation commands that must also pass |
| `make memory-entry SPEC=SPEC-XXX` | Prints a paste-ready implementation-log template without inventing validation evidence |

`make verify` remains the complete pre-review and pre-PR check. It intentionally depends on
PostgreSQL migration validation. Use `make verify-no-db` only when the local environment cannot
reach Docker or PostgreSQL; record that migration validation remains unverified until
`make migrations-check` or `make migrations-check-compose` passes.

Memory validation is required before a Review agent returns `APPROVED`. The canonical trigger is the
review decision, not commit or push. The helper targets intentionally validate and scaffold memory;
they do not write project history automatically because validation evidence and known gaps must stay
factual.

In managed sandbox environments, commands that access host-published PostgreSQL ports or the Docker
socket must be treated as outside-sandbox validation from the first attempt. Run
`make migrations-check` elevated when validating the host `LOCAL_DATABASE_URL`; run
`make migrations-check-compose` elevated when validating through Compose networking. A sandboxed
`psycopg.OperationalError` such as `connection is bad: no error details available`, a blocked
`/dev/tcp` probe, or Docker socket `permission denied` is an environment access constraint, not
migration evidence. Record the elevated result as the validation result.

## Initial Backend Direct Commands

Use these until Make targets exist. Adjust package manager only after documenting the decision in setup docs.

```bash
cd backend
poetry run ruff check .
poetry run ruff format --check .
poetry run pytest
poetry run alembic check
```

If Poetry is not chosen during scaffold, replace this section immediately with exact commands.

## Backend API Test Client Guidance

Backend API tests must exercise public HTTP endpoints when a feature spec requires API coverage. Direct calls to route functions or services may supplement API tests, but they do not replace endpoint-level validation.

Preferred in-process API clients:

- FastAPI `TestClient`.
- HTTPX `ASGITransport`.

When in-process ASGI tests use synchronous FastAPI endpoints or sync dependencies, configure the test event loop with `uvloop` if the default `asyncio` loop is unreliable in the local environment.

Examples:

```python
from fastapi.testclient import TestClient

client = TestClient(app, backend_options={"use_uvloop": True})
```

```python
import asyncio

import uvloop

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
```

If an in-process ASGI client cannot be made reliable, an automated Docker/local-backend HTTP test path is acceptable when it covers the same acceptance criteria, status codes, error shapes, and cookie behavior required by the active spec.

## Initial Frontend Direct Commands

Use these until Make targets exist:

```bash
cd frontend
npm install
npm run lint
npm run format:check
npm run typecheck
npm run test
npm run build
```

If pnpm/yarn is chosen during scaffold, replace this section immediately with exact commands.

## Docker Smoke Checks

Use after Compose exists:

```bash
docker compose up -d --build
curl -f http://localhost:8000/health
curl -f http://127.0.0.1:8080
curl -f http://127.0.0.1:5173
```

If Adminer uses a non-default `ADMINER_PORT`, replace `8080` with that local port.
If the frontend is served through a reverse proxy instead of Vite in local mode, document that URL here.

Production smoke targets use the Compose project `opdesk-prod-smoke` by default so they do not
reuse local-development containers, networks, or volumes. Any override of
`PROD_COMPOSE_PROJECT` must name another non-production project ending in `-smoke`; destructive
smoke and shutdown targets reject other names.

## Compose Migration Checks

When PostgreSQL is reachable only from the Docker Compose network, use:

```bash
make migrations-check-compose
```

This runs Alembic inside the backend container, where the configured `DATABASE_URL` resolves
`postgres:5432` through Compose networking. It is equivalent in coverage to `make migrations-check`
for migration upgrade/drift validation, but it requires Docker Compose access.

## Managed Sandbox Migration Checks

For agent runs inside a managed sandbox, do not use a first sandboxed `make migrations-check`
failure as feature evidence. The target needs host TCP access to the PostgreSQL port published by
Compose, and the sandbox may block that access even when PostgreSQL is healthy. Request elevated
execution for:

```bash
make migrations-check
```

If host PostgreSQL is genuinely unavailable but Docker Compose is running, request elevated
execution for:

```bash
make migrations-check-compose
```

Either passing target satisfies Alembic upgrade/drift coverage; prefer recording both when both are
available.

## Minimum Review Evidence

Every implementation review should report:

- Active spec ID.
- Commands run.
- Pass/fail/not-run status.
- Any unavailable commands and why.
- Residual risk if scaffold or CI is not mature yet.
- Memory evidence from `docs/project-state.md` and `docs/implementation-log.md`, normally checked with `make memory-check SPEC=SPEC-XXX`.

## CI Expectation

Pull requests should run `make verify`, or a documented subset while the project is still being scaffolded. The subset must expand as backend, frontend, database, and Docker become available.
