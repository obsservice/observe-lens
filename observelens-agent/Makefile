.PHONY: install init-env bootstrap run dev test lint format typecheck

UV_CACHE_DIR ?= .uv-cache
UV = uv --cache-dir $(UV_CACHE_DIR)

install:
	$(UV) sync --extra dev

init-env:
	@test -f .env || cp .env.example .env

bootstrap: install init-env

run: init-env
	$(UV) run uvicorn observelens_agent.main:app --reload --reload-dir src --port 3082

dev: init-env
	$(UV) run uvicorn observelens_agent.main:app --reload --reload-dir src --port 3082

test:
	$(UV) run pytest

lint:
	$(UV) run ruff check src tests

format:
	$(UV) run ruff format src tests

typecheck:
	$(UV) run mypy src
