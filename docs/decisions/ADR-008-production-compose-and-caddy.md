# ADR-008 — Production Compose And Caddy Deployment

Status: Accepted
Date: 2026-06-30
Related specs:
- SPEC-301

## Context

OpsDesk needs a portfolio-friendly production deployment that can run on a single VPS without introducing Kubernetes or managed infrastructure. The app already has a FastAPI backend, PostgreSQL, and a React frontend.

## Decision

Use `docker-compose.prod.yml` as the production runtime definition. Caddy is the only public entry point and terminates HTTP/TLS traffic. It proxies `/api/*` and `/health` to the backend service and all other paths to a frontend service that serves the Vite production build as static files.

PostgreSQL remains private on the Compose network and stores data in a named Docker volume. Production secrets are provided through server-side environment variables; committed files only contain placeholders.

## Consequences

The production path stays close to the local Docker workflow and is simple enough for a solo portfolio deployment. The deployment does not depend on a cloud database or external process manager.

Backups and restores operate against the named PostgreSQL volume through `docker compose exec`. Redis and worker services will be added later when `SPEC-201` is implemented.

## Alternatives Considered

- Serve the frontend directly from the reverse-proxy Caddy container: this removes one service, but makes the Compose build less direct because the Caddy image would need the frontend build output.
- Run the Vite dev server in production: this is simpler but not production-suitable and would weaken the deployment boundary.
- Use Kubernetes or a managed platform: this is outside the first public version scope.
