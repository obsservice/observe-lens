.PHONY: install init-env bootstrap run dev test lint format typecheck mcp_test

UV_CACHE_DIR ?= .uv-cache
UV = uv --cache-dir $(UV_CACHE_DIR)

install:
	$(UV) sync --extra dev

init-env:
	@test -f .env || cp -f .env.example .env

bootstrap: install init-env

run: init-env
	$(UV) run python -m observability_mcp_gateway.main

dev: init-env
	$(UV) run python -m observability_mcp_gateway.main

test:
	$(UV) run pytest

lint:
	$(UV) run ruff check src tests

format:
	$(UV) run ruff format src tests

typecheck:
	$(UV) run mypy src

mcp-test:
	$(UV) run python scripts/test_tools.py http://localhost:3084/sse
