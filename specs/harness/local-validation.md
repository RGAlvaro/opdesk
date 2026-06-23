# Local Validation Harness

Status: Ready  
Owner: Review agent  
Last updated: 2026-06-23

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
| `make migrations-check` | Alembic migration consistency |
| `make migrations-check-compose` | Alembic migration consistency from inside the Docker Compose backend container |
| `make smoke` | Docker/local service startup and health checks |

`make verify` remains the complete pre-review and pre-PR check. It intentionally depends on
PostgreSQL migration validation. Use `make verify-no-db` only when the local environment cannot
reach Docker or PostgreSQL; record that migration validation remains unverified until
`make migrations-check` or `make migrations-check-compose` passes.

In managed sandbox environments, commands that access host-published PostgreSQL ports or the Docker
socket may need elevated execution permissions. This is an environment access constraint, not a
project validation shortcut. When that happens, rerun the same target with the required permissions
and record both the sandbox failure and the elevated result.

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

## Compose Migration Checks

When PostgreSQL is reachable only from the Docker Compose network, use:

```bash
make migrations-check-compose
```

This runs Alembic inside the backend container, where the configured `DATABASE_URL` resolves
`postgres:5432` through Compose networking. It is equivalent in coverage to `make migrations-check`
for migration upgrade/drift validation, but it requires Docker Compose access.

## Minimum Review Evidence

Every implementation review should report:

- Active spec ID.
- Commands run.
- Pass/fail/not-run status.
- Any unavailable commands and why.
- Residual risk if scaffold or CI is not mature yet.

## CI Expectation

Pull requests should run `make verify`, or a documented subset while the project is still being scaffolded. The subset must expand as backend, frontend, database, and Docker become available.
