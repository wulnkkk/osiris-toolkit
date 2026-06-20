# osiris-toolkit development automation
# Requires uv (https://docs.astral.sh/uv/)

.PHONY: help install setup lint format typecheck test test-cov test-file \
        docs-serve docs-build precommit bump clean clean-all

.DEFAULT_GOAL := help

help: ## Show help
	@echo "Usage: make <target>"
	@echo ""
	@echo "=== Environment ==="
	@$(MAKE) -pRrq -f $(lastword $(MAKEFILE_LIST)) : 2>/dev/null | \
		awk -v RS= -F: '/^# File/,/^# Finished Make data base/ {if ($$1 !~ "^[#.]") {print $$1}}' | \
		sort | \
		egrep -v -e '^[^[:alnum:]]' -e '^$@$$' | \
		xargs -I _ sh -c 'printf "  %-16s", _; grep -h "^_:" Makefile | grep -v "^_:" | head -1' 2>/dev/null
	@echo ""
	@echo "=== Install ==="
	@echo "  uv venv                         Create virtual environment"
	@echo "  uv sync --dev                   Install all dependencies"

# ---------------------------------------------------------------------------
# Install & Setup
# ---------------------------------------------------------------------------

install: ## Install all dependencies (including dev)
	uv sync --dev

setup: install ## Full dev environment setup
	uv run pre-commit install --hook-type pre-commit --hook-type commit-msg
	@echo "✅ pre-commit hooks installed"

# ---------------------------------------------------------------------------
# Code Quality
# ---------------------------------------------------------------------------

lint: ## Run ruff lint check
	uv run ruff check src/

lint-fix: ## Auto-fix ruff issues
	uv run ruff check --fix src/

format: ## Run ruff formatter
	uv run ruff format src/

format-check: ## Check ruff formatting (read-only)
	uv run ruff format --check src/

typecheck: ## Run mypy type check
	uv run mypy src/

# ---------------------------------------------------------------------------
# Testing
# ---------------------------------------------------------------------------

test: ## Run all tests
	uv run pytest tests/ -v

test-quick: ## Run fast tests (exclude slow + data markers)
	uv run pytest tests/ -v -m "not slow and not data"

test-cov: ## Run tests with coverage report
	uv run pytest tests/ --cov=osiris_toolkit --cov-report=term --cov-report=html

test-file: ## Run a single test file: make test-file f=tests/test_units.py
	uv run pytest $(f) -v

# ---------------------------------------------------------------------------
# Documentation
# ---------------------------------------------------------------------------

docs-serve: ## Serve docs locally
	uv run mkdocs serve

docs-build: ## Build docs in strict mode
	uv run mkdocs build --strict

# ---------------------------------------------------------------------------
# Git & Version Management
# ---------------------------------------------------------------------------

precommit: ## Run all pre-commit hooks manually
	uv run pre-commit run --all-files

cz: ## Interactive Commitizen commit
	uv run cz commit

bump: ## Interactive version bump (auto-updates version + git tag)
	uv run cz bump --changelog

# ---------------------------------------------------------------------------
# Cleanup
# ---------------------------------------------------------------------------

clean: ## Clean build artifacts and caches
	rm -rf .ruff_cache/ .mypy_cache/ .pytest_cache/
	rm -rf __pycache__/ */__pycache__/ */*/__pycache__/ */*/*/__pycache__/
	rm -rf *.egg-info/ .eggs/
	rm -rf dist/ build/
	rm -rf site/ docs/_build/
	rm -rf .coverage htmlcov/

clean-all: clean ## Additionally remove virtual environment
	rm -rf .venv/ uv.lock
