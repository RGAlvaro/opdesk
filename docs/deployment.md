# Production Deployment

This guide covers the first OpsDesk production path for `SPEC-301`: one VPS, Docker Compose, Caddy, PostgreSQL, backend API, and the built React frontend.

## Services

Public services:

- `caddy`: exposes HTTP/HTTPS, terminates TLS, and routes traffic.

Private Compose-network services:

- `backend`: FastAPI API server.
- `frontend`: static React build served by nginx.
- `postgres`: PostgreSQL with a named persistent volume.

Redis, workers, and scheduled jobs are not part of this deployment until `SPEC-201` is implemented.

## Required Server Variables

Create a server-side env file from `.env.example` and replace the placeholders:

```bash
cp .env.example .env.production
```

Required production values:

| Variable | Purpose |
|---|---|
| `POSTGRES_USER` | PostgreSQL application user, defaults to `opdesk` if omitted. |
| `POSTGRES_PASSWORD` | Strong PostgreSQL password. Required by production Compose. |
| `POSTGRES_DB` | PostgreSQL database name, defaults to `opdesk` if omitted. |
| `AUTH_SECRET_KEY` | Strong token signing secret; never reuse the local placeholder. |
| `CADDY_SITE_ADDRESS` | Public domain, for example `opsdesk.example.com`. Use `:80` only for local smoke tests. |
| `PROD_HTTP_PORT` | Host HTTP port, normally `80`. |
| `PROD_HTTPS_PORT` | Host HTTPS port, normally `443`. |

Production Compose forces `APP_ENV=production`, `DEBUG=false`, `AUTH_COOKIE_SECURE=true`, and keeps PostgreSQL off public host ports.

## DNS And Firewall

1. Point the domain in `CADDY_SITE_ADDRESS` at the VPS public IP.
2. Allow inbound TCP `80` and `443`.
3. Do not expose PostgreSQL publicly.

## Build And Start

Validate the production Compose file before starting:

```bash
set -a
. ./.env.production
set +a
docker compose -f docker-compose.prod.yml config
```

Apply database migrations:

```bash
set -a
. ./.env.production
set +a
docker compose -f docker-compose.prod.yml run --rm backend poetry run alembic upgrade head
```

Start or update the deployment:

```bash
set -a
. ./.env.production
set +a
docker compose -f docker-compose.prod.yml up -d --build
```

Check health through Caddy:

```bash
curl --fail https://opsdesk.example.com/health
```

For a local production smoke test without TLS, use:

```bash
make prod-smoke
make prod-down
```

## Backup

Create a compressed PostgreSQL backup:

```bash
set -a
. ./.env.production
set +a
mkdir -p backups
docker compose -f docker-compose.prod.yml exec -T postgres \
  pg_dump -U "${POSTGRES_USER:-opdesk}" -d "${POSTGRES_DB:-opdesk}" \
  | gzip > "backups/opdesk-$(date +%Y%m%d-%H%M%S).sql.gz"
```

Store backups outside the VPS as well as on disk. Take a fresh backup before deployment changes.

## Restore

Stop the app services that may write to the database:

```bash
set -a
. ./.env.production
set +a
docker compose -f docker-compose.prod.yml stop backend
```

Restore a backup:

```bash
gunzip -c backups/opdesk-YYYYMMDD-HHMMSS.sql.gz | \
  docker compose -f docker-compose.prod.yml exec -T postgres \
  psql -U "${POSTGRES_USER:-opdesk}" -d "${POSTGRES_DB:-opdesk}"
```

Restart the app:

```bash
docker compose -f docker-compose.prod.yml up -d
```

## Operational Notes

- Run `make verify` locally before deployment when Docker/PostgreSQL are available.
- Run `make prod-config` in CI or locally to validate production Compose structure with safe placeholder secrets.
- Rotate `AUTH_SECRET_KEY` carefully; existing browser sessions become invalid.
- Keep `.env.production` and backup files out of Git.
