#!/usr/bin/env bash
# Validate migrations plus a real backup/restore cycle in the isolated production-smoke stack.

set -euo pipefail

readonly compose_project="${PROD_COMPOSE_PROJECT:-opdesk-prod-smoke}"
readonly probe_table="opsdesk_restore_probe"
readonly probe_value="backup-restore-ok"

if [[ "${compose_project}" != *-smoke ]]; then
  echo "PROD_COMPOSE_PROJECT must end in -smoke for this destructive data test." >&2
  exit 2
fi

backup_file="$(mktemp /tmp/opdesk-prod-backup-XXXXXX.dump)"
readonly backup_file
trap 'rm -f "${backup_file}"' EXIT

compose=(docker compose --project-name "${compose_project}" -f docker-compose.prod.yml)

"${compose[@]}" up -d postgres
"${compose[@]}" stop backend
"${compose[@]}" run --rm backend poetry run alembic upgrade head

"${compose[@]}" exec -T postgres sh -c \
  'psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB"' <<SQL
DROP TABLE IF EXISTS ${probe_table};
CREATE TABLE ${probe_table} (value text PRIMARY KEY);
INSERT INTO ${probe_table} (value) VALUES ('${probe_value}');
SQL

"${compose[@]}" exec -T postgres sh -c \
  'pg_dump --format=custom --no-owner --no-privileges -U "$POSTGRES_USER" -d "$POSTGRES_DB"' \
  >"${backup_file}"

"${compose[@]}" exec -T postgres sh -c \
  'psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB"' <<SQL
DROP TABLE ${probe_table};
SQL

"${compose[@]}" exec -T postgres sh -c \
  'pg_restore --clean --if-exists --no-owner --no-privileges --single-transaction --exit-on-error -U "$POSTGRES_USER" -d "$POSTGRES_DB"' \
  <"${backup_file}"

restored_value="$(
  "${compose[@]}" exec -T postgres sh -c \
    'psql -At -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT value FROM opsdesk_restore_probe"'
)"

if [[ "${restored_value}" != "${probe_value}" ]]; then
  echo "Production backup/restore smoke failed: restored probe value did not match." >&2
  exit 1
fi

"${compose[@]}" exec -T postgres sh -c \
  'psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB"' <<SQL
DROP TABLE ${probe_table};
SQL
"${compose[@]}" run --rm backend poetry run alembic check

echo "Production migrations and backup/restore smoke passed for ${compose_project}."
