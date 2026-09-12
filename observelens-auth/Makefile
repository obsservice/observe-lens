.PHONY: install init-env bootstrap migrate migrate-sql downgrade reset-admin-password run dev test lint format check openapi db-up db-down docker-up docker-down

UV_CACHE_DIR ?= .uv-cache
UV = uv --cache-dir $(UV_CACHE_DIR)

install:
	$(UV) sync --extra dev

init-env:
	@test -f .env || cp .env.example .env

bootstrap: install init-env migrate

migrate: init-env
	$(UV) run alembic upgrade head

migrate-sql: init-env
	$(UV) run alembic upgrade head --sql

downgrade: init-env
	$(UV) run alembic downgrade -1

reset-admin-password: init-env
	$(UV) run python scripts/reset_bootstrap_admin_password.py

run: init-env
	$(UV) run uvicorn observelens_auth.main:app --host 0.0.0.0 --port 9081

dev: init-env
	$(UV) run uvicorn observelens_auth.main:app --host 0.0.0.0 --port 9081 --reload --reload-dir src

test:
	$(UV) run pytest

lint:
	$(UV) run ruff check .

format:
	$(UV) run ruff format .

check: lint test

openapi:
	$(UV) run python scripts/export_openapi.py

db-up:
	docker compose up -d postgres

db-down:
	docker compose stop postgres

docker-up:
	docker compose up --build

docker-down:
	docker compose down
