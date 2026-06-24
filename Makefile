ifneq (,$(wildcard .env))
include .env
export
endif

ADMINER_PORT ?= 8080
FRONTEND_PORT ?= 5173

.PHONY: verify verify-no-db test test-backend test-backend-db lint format-check typecheck
.PHONY: migrations-check migrations-check-compose smoke compose-up compose-down
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
	curl --fail --retry 10 --retry-delay 1 --retry-all-errors http://127.0.0.1:$(ADMINER_PORT)
	curl --fail --retry 10 --retry-delay 1 --retry-all-errors http://127.0.0.1:$(FRONTEND_PORT)

compose-up:
	docker compose up -d --build

compose-down:
	docker compose down
