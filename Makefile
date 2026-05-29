.PHONY: install run test lint clean

install:
	pip install -e ".[dev]"

run:
	python -m solacia

test:
	python -m pytest tests/ -v

lint:
	ruff check src/ tests/
	ruff format --check src/ tests/

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	rm -rf .pytest_cache .ruff_cache *.egg-info dist build
