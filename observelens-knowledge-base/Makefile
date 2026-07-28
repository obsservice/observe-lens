.PHONY: install init-env bootstrap run dev test lint format typecheck migrate

UV_CACHE_DIR ?= .uv-cache
UV = uv --cache-dir $(UV_CACHE_DIR)

install:
	$(UV) sync --extra dev

init-env:
	@test -f .env || cp .env.example .env

bootstrap: install init-env migrate

run: init-env
	$(UV) run uvicorn observelens_knowledge_base.main:app --host 0.0.0.0 --port 3085

dev: init-env
	$(UV) run uvicorn observelens_knowledge_base.main:app --host 0.0.0.0 --port 3085 --reload --reload-dir src

test:
	$(UV) run pytest

lint:
	$(UV) run ruff check src tests

typecheck:
	$(UV) run mypy src

format:
	$(UV) run ruff format src tests

migrate: init-env
	$(UV) run alembic upgrade head
