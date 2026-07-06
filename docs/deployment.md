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

Create a server-side env file from `.env.example` and replace the placeholders. Keep the
Compose project name stable so every operational command targets the same deployment:

```bash
cp .env.example .env.production
```

The commands below use `opdesk-prod` as that stable project name. Do not reuse it for local
development or smoke tests; `make prod-smoke` defaults to the isolated `opdesk-prod-smoke`
project.

Required production values:

| Variable | Purpose |
|---|---|
| `POSTGRES_USER` | PostgreSQL application user, defaults to `opdesk` if omitted. |
| `POSTGRES_PASSWORD` | Strong PostgreSQL password. Required by production Compose. |
| `POSTGRES_DB` | PostgreSQL database name, defaults to `opdesk` if omitted. |
| `PROD_DATABASE_URL` | Backend PostgreSQL URL using the Compose host `postgres`; credentials must match the PostgreSQL variables and the password must be URL-encoded. |
| `AUTH_SECRET_KEY` | Strong token signing secret; never reuse the local placeholder. |
| `CADDY_SITE_ADDRESS` | Public domain, for example `opsdesk.example.com`. Use `:80` only for local smoke tests. |
| `PROD_HTTP_PORT` | Host HTTP port, normally `80`. |
| `PROD_HTTPS_PORT` | Host HTTPS port, normally `443`. |

Production Compose forces `APP_ENV=production`, `DEBUG=false`, `AUTH_COOKIE_SECURE=true`, and keeps PostgreSQL off public host ports.

Do not build `PROD_DATABASE_URL` by pasting a raw strong password directly into the URL. URL-encode
reserved characters first, otherwise passwords containing characters such as `@`, `:`, `/`, `?`, or
`#` can be parsed as URL syntax instead of password text. For example, a password containing `@`
must use `%40` in the URL.

## DNS And Firewall

1. Point the domain in `CADDY_SITE_ADDRESS` at the VPS public IP.
2. Allow inbound TCP `80` and `443`.
3. Do not expose PostgreSQL publicly.

## Build And Start

Validate the production Compose file before starting:

```bash
docker compose --project-name opdesk-prod --env-file .env.production \
  -f docker-compose.prod.yml config
```

Apply database migrations:

```bash
docker compose --project-name opdesk-prod --env-file .env.production \
  -f docker-compose.prod.yml run --rm backend poetry run alembic upgrade head
```

Start or update the deployment:

```bash
docker compose --project-name opdesk-prod --env-file .env.production \
  -f docker-compose.prod.yml up -d --build
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

Create a PostgreSQL custom-format backup. This format supports a clean, transactional restore
and avoids replaying ownership or privilege statements from the source environment:

```bash
mkdir -p backups
docker compose --project-name opdesk-prod --env-file .env.production \
  -f docker-compose.prod.yml exec -T postgres sh -c \
  'pg_dump --format=custom --no-owner --no-privileges -U "$POSTGRES_USER" -d "$POSTGRES_DB"' \
  > "backups/opdesk-$(date +%Y%m%d-%H%M%S).dump"
```

Store backups outside the VPS as well as on disk. Take a fresh backup before deployment changes.

## Restore

Stop the app services that may write to the database:

```bash
docker compose --project-name opdesk-prod --env-file .env.production \
  -f docker-compose.prod.yml stop backend
```

Restore a backup. This replaces the current application schema and data, so verify the selected
file before running it:

```bash
docker compose --project-name opdesk-prod --env-file .env.production \
  -f docker-compose.prod.yml exec -T postgres sh -c \
  'pg_restore --clean --if-exists --no-owner --no-privileges --single-transaction --exit-on-error -U "$POSTGRES_USER" -d "$POSTGRES_DB"' \
  < backups/opdesk-YYYYMMDD-HHMMSS.dump
```

Restart the app:

```bash
docker compose --project-name opdesk-prod --env-file .env.production \
  -f docker-compose.prod.yml up -d
```

## Operational Notes

- Run `make verify` locally before deployment when Docker/PostgreSQL are available.
- Run `make prod-config` in CI or locally to validate production Compose structure with safe placeholder secrets.
- `make prod-data-smoke` applies migrations and proves a custom-format backup can restore a marker row inside the isolated smoke project.
- Rotate `AUTH_SECRET_KEY` carefully; existing browser sessions become invalid.
- Keep `.env.production` and backup files out of Git.
