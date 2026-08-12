ifneq (,$(wildcard .env))
include .env
export
endif

ADMINER_PORT ?= 8080
FRONTEND_PORT ?= 5173
PROD_HTTP_PORT ?= 8081
PROD_HTTPS_PORT ?= 8443
PROD_COMPOSE_PROJECT ?= opdesk-prod-smoke
PROD_POSTGRES_PASSWORD ?= prod_config_placeholder_password
PROD_DATABASE_URL ?= postgresql+psycopg://opdesk:prod_config_placeholder_password@postgres:5432/opdesk
PROD_AUTH_SECRET_KEY ?= prod_config_placeholder_min_32_chars
CELERY_BROKER_URL ?= redis://redis:6379/0
CELERY_RESULT_BACKEND ?= redis://redis:6379/1

.PHONY: verify verify-no-db test test-backend test-backend-db lint format-check typecheck
.PHONY: migrations-check migrations-check-compose smoke prod-config prod-smoke-project-check
.PHONY: prod-data-smoke prod-smoke prod-down changelog-check release-workflow-check compose-up compose-down
.PHONY: test-frontend memory-check review-ready memory-entry

verify: verify-no-db migrations-check

verify-no-db: lint format-check typecheck test

test: test-backend test-frontend

test-backend:
	cd backend && poetry run pytest -m "not db"

test-frontend:
	cd frontend && npm run test

memory-check:
	test -n "$(SPEC)" || (echo "Usage: make memory-check SPEC=SPEC-106" && exit 2)
	python3 scripts/memory_check.py --spec "$(SPEC)"

review-ready: memory-check

memory-entry:
	test -n "$(SPEC)" || (echo "Usage: make memory-entry SPEC=SPEC-106 ROLE='Review agent' STATUS=Reviewed" && exit 2)
	python3 scripts/memory_entry.py --spec "$(SPEC)" --role "$${ROLE:-Ingeniero de software}" --status "$${STATUS:-Implemented}" --branch "$${BRANCH:-branch-name}" --commit "$${COMMIT:-Pending}" --title "$${TITLE:-Short title}"

changelog-check:
	python3 scripts/validate_changelog.py

test-backend-db:
	cd backend && DATABASE_URL=$${LOCAL_DATABASE_URL:-postgresql+psycopg://opdesk:opdesk_dev_password@localhost:5432/opdesk} poetry run pytest -m db

lint:
	cd backend && poetry run ruff check .
	cd frontend && npm run lint

format-check:
	cd backend && poetry run ruff format --check .
	cd frontend && npm run format:check

typecheck:
	cd backend && poetry run mypy app
	cd frontend && npm run typecheck

migrations-check:
	cd backend && DATABASE_URL=$${LOCAL_DATABASE_URL:-postgresql+psycopg://opdesk:opdesk_dev_password@localhost:5432/opdesk} poetry run alembic upgrade head
	cd backend && DATABASE_URL=$${LOCAL_DATABASE_URL:-postgresql+psycopg://opdesk:opdesk_dev_password@localhost:5432/opdesk} poetry run alembic check

migrations-check-compose:
	docker compose exec -T backend poetry run alembic upgrade head
	docker compose exec -T backend poetry run alembic check

smoke:
	docker compose up -d --build
	curl --fail --retry 10 --retry-delay 1 --retry-all-errors http://localhost:8000/health
	docker compose exec -T redis redis-cli ping
	docker compose ps --status running --services worker | grep -x worker
	curl --fail --retry 10 --retry-delay 1 --retry-all-errors http://127.0.0.1:$(ADMINER_PORT)
	curl --fail --retry 10 --retry-delay 1 --retry-all-errors http://127.0.0.1:$(FRONTEND_PORT)

prod-config:
	bash -n scripts/prod_data_smoke.sh
	bash -n scripts/prod_release.sh
	POSTGRES_PASSWORD="$(PROD_POSTGRES_PASSWORD)" PROD_DATABASE_URL="$(PROD_DATABASE_URL)" AUTH_SECRET_KEY="$(PROD_AUTH_SECRET_KEY)" CELERY_BROKER_URL="$(CELERY_BROKER_URL)" CELERY_RESULT_BACKEND="$(CELERY_RESULT_BACKEND)" CADDY_SITE_ADDRESS=":80" PROD_HTTP_PORT="$(PROD_HTTP_PORT)" PROD_HTTPS_PORT="$(PROD_HTTPS_PORT)" docker compose --project-name "$(PROD_COMPOSE_PROJECT)" -f docker-compose.prod.yml config

release-workflow-check: changelog-check
	bash -n scripts/prod_release.sh
	python3 scripts/validate_release_workflow.py
	RELEASE_REF=test bash scripts/prod_release.sh >/tmp/opdesk-release-missing-env.out 2>&1; test "$$?" = "1"; grep -q "PROD_PUBLIC_URL" /tmp/opdesk-release-missing-env.out

prod-smoke-project-check:
	@case "$(PROD_COMPOSE_PROJECT)" in *-smoke) ;; *) echo "PROD_COMPOSE_PROJECT must end in -smoke for destructive smoke targets." >&2; exit 2 ;; esac

prod-data-smoke: prod-smoke-project-check
	POSTGRES_PASSWORD="$(PROD_POSTGRES_PASSWORD)" PROD_DATABASE_URL="$(PROD_DATABASE_URL)" AUTH_SECRET_KEY="$(PROD_AUTH_SECRET_KEY)" CELERY_BROKER_URL="$(CELERY_BROKER_URL)" CELERY_RESULT_BACKEND="$(CELERY_RESULT_BACKEND)" CADDY_SITE_ADDRESS=":80" PROD_HTTP_PORT="$(PROD_HTTP_PORT)" PROD_HTTPS_PORT="$(PROD_HTTPS_PORT)" PROD_COMPOSE_PROJECT="$(PROD_COMPOSE_PROJECT)" ./scripts/prod_data_smoke.sh

prod-smoke: prod-data-smoke
	POSTGRES_PASSWORD="$(PROD_POSTGRES_PASSWORD)" PROD_DATABASE_URL="$(PROD_DATABASE_URL)" AUTH_SECRET_KEY="$(PROD_AUTH_SECRET_KEY)" CELERY_BROKER_URL="$(CELERY_BROKER_URL)" CELERY_RESULT_BACKEND="$(CELERY_RESULT_BACKEND)" CADDY_SITE_ADDRESS=":80" PROD_HTTP_PORT="$(PROD_HTTP_PORT)" PROD_HTTPS_PORT="$(PROD_HTTPS_PORT)" docker compose --project-name "$(PROD_COMPOSE_PROJECT)" -f docker-compose.prod.yml up -d --build
	curl --fail --retry 20 --retry-delay 1 --retry-all-errors http://127.0.0.1:$(PROD_HTTP_PORT)/health
	POSTGRES_PASSWORD="$(PROD_POSTGRES_PASSWORD)" PROD_DATABASE_URL="$(PROD_DATABASE_URL)" AUTH_SECRET_KEY="$(PROD_AUTH_SECRET_KEY)" CELERY_BROKER_URL="$(CELERY_BROKER_URL)" CELERY_RESULT_BACKEND="$(CELERY_RESULT_BACKEND)" CADDY_SITE_ADDRESS=":80" PROD_HTTP_PORT="$(PROD_HTTP_PORT)" PROD_HTTPS_PORT="$(PROD_HTTPS_PORT)" docker compose --project-name "$(PROD_COMPOSE_PROJECT)" -f docker-compose.prod.yml exec -T redis redis-cli ping
	POSTGRES_PASSWORD="$(PROD_POSTGRES_PASSWORD)" PROD_DATABASE_URL="$(PROD_DATABASE_URL)" AUTH_SECRET_KEY="$(PROD_AUTH_SECRET_KEY)" CELERY_BROKER_URL="$(CELERY_BROKER_URL)" CELERY_RESULT_BACKEND="$(CELERY_RESULT_BACKEND)" CADDY_SITE_ADDRESS=":80" PROD_HTTP_PORT="$(PROD_HTTP_PORT)" PROD_HTTPS_PORT="$(PROD_HTTPS_PORT)" docker compose --project-name "$(PROD_COMPOSE_PROJECT)" -f docker-compose.prod.yml ps --status running --services worker | grep -x worker
	curl --fail --retry 20 --retry-delay 1 --retry-all-errors http://127.0.0.1:$(PROD_HTTP_PORT)/

prod-down: prod-smoke-project-check
	POSTGRES_PASSWORD="$(PROD_POSTGRES_PASSWORD)" PROD_DATABASE_URL="$(PROD_DATABASE_URL)" AUTH_SECRET_KEY="$(PROD_AUTH_SECRET_KEY)" CELERY_BROKER_URL="$(CELERY_BROKER_URL)" CELERY_RESULT_BACKEND="$(CELERY_RESULT_BACKEND)" CADDY_SITE_ADDRESS=":80" PROD_HTTP_PORT="$(PROD_HTTP_PORT)" PROD_HTTPS_PORT="$(PROD_HTTPS_PORT)" docker compose --project-name "$(PROD_COMPOSE_PROJECT)" -f docker-compose.prod.yml down

compose-up:
	docker compose up -d --build

compose-down:
	docker compose down
