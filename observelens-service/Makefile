.PHONY: install init-env bootstrap run dev test lint format typecheck migrate

UV_CACHE_DIR ?= .uv-cache
UV = uv --cache-dir $(UV_CACHE_DIR)

install:
	$(UV) sync --extra dev

init-env:
	@test -f .env || cp .env.example .env

bootstrap: install init-env migrate

run: init-env
	$(UV) run uvicorn observelens_service.main:app --port 3081

dev: init-env
	$(UV) run uvicorn observelens_service.main:app --reload --port 3081

test:
	$(UV) run pytest

lint:
	$(UV) run ruff check src tests

format:
	$(UV) run ruff format src tests

typecheck:
	$(UV) run mypy src

migrate: init-env
	$(UV) run alembic upgrade head
