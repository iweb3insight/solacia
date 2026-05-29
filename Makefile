.PHONY: install run test lint format coverage clean docker help

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

all: lint test ## Run lint + test (default)

install: ## Install dev dependencies
	pip install -e ".[dev]"

run: ## Start the server
	python -m solacia

test: ## Run tests
	python -m pytest tests/test_api.py -v

test-e2e: ## Run E2E tests (starts real server)
	python -m pytest tests/test_e2e.py -v

lint: ## Check code quality
	ruff check src/ tests/
	ruff format --check src/ tests/

format: ## Auto-fix code formatting
	ruff format src/ tests/
	ruff check --fix src/ tests/

coverage: ## Run tests with coverage report
	python -m pytest tests/test_api.py -v --cov=solacia --cov-report=term --cov-report=html

security: ## Run security checks
	pip-audit
	bandit -r src/ -c pyproject.toml

clean: ## Remove build artifacts
	find . -type d -name __pycache__ -exec rm -rf {} +
	rm -rf .pytest_cache .ruff_cache *.egg-info dist build htmlcov .coverage

docker: ## Build Docker image
	docker build -t solacia .
