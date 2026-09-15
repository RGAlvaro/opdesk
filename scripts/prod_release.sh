#!/usr/bin/env bash
# Run a safe production update on the VPS from an already uploaded release directory.

set -euo pipefail

readonly release_dir="$(pwd)"
readonly deploy_root="${PROD_DEPLOY_ROOT:-/srv/opdesk}"
readonly compose_project="${PROD_COMPOSE_PROJECT:-opdesk-prod}"
readonly env_file="${PROD_ENV_FILE:-${deploy_root}/.env.production}"
readonly public_url="${PROD_PUBLIC_URL:?Set PROD_PUBLIC_URL to the public production origin.}"
readonly release_ref="${RELEASE_REF:?Set RELEASE_REF to the deployed commit or tag.}"
readonly safe_release_ref="${release_ref//[^A-Za-z0-9._-]/_}"
readonly backup_dir="${PROD_BACKUP_DIR:-${deploy_root}/backups}"
readonly manifest_dir="${PROD_MANIFEST_DIR:-${deploy_root}/releases}"
readonly timestamp="$(date -u +%Y%m%d-%H%M%S)"
readonly backup_file="${backup_dir}/opdesk-${timestamp}-${safe_release_ref:0:32}.dump"
readonly manifest_file="${manifest_dir}/latest-release.txt"
alembic_current=""

compose=(
  docker compose
  --project-name "${compose_project}"
  --env-file "${env_file}"
  -f "${release_dir}/docker-compose.prod.yml"
)

release_summary=()

# Record non-secret status lines that GitHub Actions and future operators can inspect.
add_summary() {
  release_summary+=("$1")
  echo "$1"
}

# Exit with rollback guidance after a failed production step.
fail_with_rollback() {
  local message="$1"
  {
    echo "::error::${message}"
    echo "Rollback: redeploy the previous release directory with RELEASE_REF set to that commit."
    echo "Database restore is manual only: stop backend, worker, and scheduler, then restore the chosen dump explicitly."
  } >&2
  exit 1
}

# Retry public HTTP checks because Caddy and app health can lag container start briefly.
check_url() {
  local url="$1"
  curl --fail --silent --show-error --retry 20 --retry-delay 2 --retry-all-errors "${url}" >/dev/null
}

# Start an existing production service without allowing Compose to create or recreate it.
start_existing_service() {
  local service="$1"
  local container_id

  container_id="$("${compose[@]}" ps -q "${service}")"
  if [[ -z "${container_id}" ]]; then
    fail_with_rollback "Production ${service} container does not exist; run the initial deployment before release automation."
  fi

  "${compose[@]}" start "${service}" \
    || fail_with_rollback "Failed to start existing production ${service} container before backup."
}

if [[ "${compose_project}" != "opdesk-prod" ]]; then
  fail_with_rollback "Refusing to deploy with PROD_COMPOSE_PROJECT=${compose_project}; expected opdesk-prod."
fi

if [[ ! -f "${env_file}" ]]; then
  fail_with_rollback "Production env file not found at ${env_file}."
fi

mkdir -p "${backup_dir}" "${manifest_dir}"

add_summary "release_ref=${release_ref}"
add_summary "release_dir=${release_dir}"
add_summary "compose_project=${compose_project}"

"${compose[@]}" config >/dev/null || fail_with_rollback "Production Compose config validation failed."
add_summary "compose_config=PASS"

start_existing_service postgres
start_existing_service redis
add_summary "data_services_started=PASS"

"${compose[@]}" exec -T postgres sh -c \
  'pg_dump --format=custom --no-owner --no-privileges -U "$POSTGRES_USER" -d "$POSTGRES_DB"' \
  >"${backup_file}" || fail_with_rollback "Production PostgreSQL backup failed before migrations."
add_summary "backup=PASS ${backup_file}"

"${compose[@]}" build backend \
  || fail_with_rollback "Production backend image build failed before migrations."
add_summary "backend_image_build=PASS"

"${compose[@]}" run --rm backend poetry run alembic upgrade head \
  || fail_with_rollback "Production Alembic migrations failed; app containers were not updated."
add_summary "migrations=PASS"

"${compose[@]}" run --rm backend poetry run alembic check \
  || fail_with_rollback "Production Alembic drift check failed; app containers were not updated."
add_summary "migration_drift_check=PASS"

alembic_current="$("${compose[@]}" run --rm backend poetry run alembic current 2>/dev/null | tail -n 1)"
if [[ -z "${alembic_current}" ]]; then
  fail_with_rollback "Production Alembic current revision check returned no output."
fi
add_summary "alembic_current=${alembic_current}"

"${compose[@]}" up -d --build || fail_with_rollback "Production Compose update failed after migrations."
add_summary "compose_update=PASS"

check_url "${public_url%/}/health" || fail_with_rollback "Backend health check through Caddy failed."
add_summary "backend_health=PASS"

check_url "${public_url%/}/" || fail_with_rollback "Frontend check through Caddy failed."
add_summary "frontend=PASS"

"${compose[@]}" exec -T redis redis-cli ping | grep -x PONG >/dev/null \
  || fail_with_rollback "Redis PING check failed."
add_summary "redis=PASS"

"${compose[@]}" ps --status running --services worker | grep -x worker >/dev/null \
  || fail_with_rollback "Worker running-state check failed."
add_summary "worker=PASS"

"${compose[@]}" ps --status running --services scheduler | grep -x scheduler >/dev/null \
  || fail_with_rollback "Scheduler running-state check failed."
add_summary "scheduler=PASS"

{
  printf 'timestamp_utc=%s\n' "${timestamp}"
  printf 'release_ref=%s\n' "${release_ref}"
  printf 'release_dir=%s\n' "${release_dir}"
  printf 'backup_file=%s\n' "${backup_file}"
  printf 'compose_project=%s\n' "${compose_project}"
  printf 'public_url=%s\n' "${public_url}"
  printf '%s\n' "${release_summary[@]}"
} >"${manifest_file}"

ln -sfn "${release_dir}" "${deploy_root}/current"
add_summary "manifest=${manifest_file}"
add_summary "release=PASS"
