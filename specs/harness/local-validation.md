# Local Validation Harness

Status: Ready  
Owner: Review agent  
Last updated: 2026-06-10

This file defines validation commands for local development and review. Feature specs may require a subset or add feature-specific checks.

## Target Make Commands

The repository should converge toward:

```bash
make verify
make test
make test-backend
make test-frontend
make lint
make format-check
make typecheck
make migrations-check
make smoke
```

Expected meaning:

| Command | Expected coverage |
|---|---|
| `make verify` | Full local verification before PR |
| `make test` | Backend and frontend tests |
| `make test-backend` | Backend unit/integration/API tests |
| `make test-frontend` | Frontend unit/component tests |
| `make lint` | Backend and frontend lint |
| `make format-check` | Formatting checks without modifying files |
| `make typecheck` | Backend and frontend type checks where configured |
| `make migrations-check` | Alembic migration consistency |
| `make smoke` | Docker/local service startup and health checks |

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

## Initial Frontend Direct Commands

Use these until Make targets exist:

```bash
cd frontend
npm run lint
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
```

If Adminer uses a non-default `ADMINER_PORT`, replace `8080` with that local port.

After a frontend exists, add the frontend URL to smoke checks. If frontend is served through a reverse proxy instead of Vite in local mode, document that URL here.

## Minimum Review Evidence

Every implementation review should report:

- Active spec ID.
- Commands run.
- Pass/fail/not-run status.
- Any unavailable commands and why.
- Residual risk if scaffold or CI is not mature yet.

## CI Expectation

Pull requests should run `make verify`, or a documented subset while the project is still being scaffolded. The subset must expand as backend, frontend, database, and Docker become available.
