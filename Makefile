.PHONY: verify test test-backend test-backend-db lint format-check typecheck migrations-check smoke compose-up compose-down

verify: lint format-check test-backend migrations-check

test: test-backend

test-backend:
	cd backend && poetry run pytest -m "not db"

test-backend-db:
	cd backend && DATABASE_URL=$${LOCAL_DATABASE_URL:-postgresql+psycopg://opdesk:opdesk_dev_password@localhost:5432/opdesk} poetry run pytest -m db

lint:
	cd backend && poetry run ruff check .

format-check:
	cd backend && poetry run ruff format --check .

typecheck:
	cd backend && poetry run mypy app

migrations-check:
	cd backend && DATABASE_URL=$${LOCAL_DATABASE_URL:-postgresql+psycopg://opdesk:opdesk_dev_password@localhost:5432/opdesk} poetry run alembic check

smoke:
	docker compose up -d --build
	curl --fail --retry 10 --retry-delay 1 --retry-all-errors http://localhost:8000/health

compose-up:
	docker compose up -d --build

compose-down:
	docker compose down
