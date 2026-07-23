.DEFAULT_GOAL := help

.PHONY: help install dev build lint typecheck test format format-check check env

help: ## Show available commands
	@awk 'BEGIN {FS = ":.*##"}; /^[a-zA-Z_-]+:.*##/ {printf "%-16s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install project dependencies
	pnpm install

env: ## Create a local environment file if it does not exist
	@test -f .env.local || cp .env.example .env.local

dev: ## Start the development server
	pnpm dev

build: ## Build the production application
	pnpm build

lint: ## Run ESLint
	pnpm lint

typecheck: ## Run the TypeScript type checker
	pnpm typecheck

test: ## Run unit tests
	pnpm test

format: ## Format source files
	pnpm format

format-check: ## Check source formatting
	pnpm format:check

check: lint typecheck format-check test ## Run all quality checks
