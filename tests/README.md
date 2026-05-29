# Solacia - Test Suite

## Overview

Tests are written with **pytest** and cover three areas:

1. **Emotion detection** — keyword matching for 6 emotion types
2. **API endpoints** — health, models, chat, diary CRUD, emotion stats
3. **Chat completions** — OpenAI-compatible request/response format

## Running Tests

```bash
# All tests
make test

# Verbose output
python -m pytest tests/ -v

# Specific test file
python -m pytest tests/test_api.py -v

# With coverage
python -m pytest tests/ --cov=solacia
```

## Test Structure

```
tests/
├── __init__.py
├── conftest.py          # Shared fixtures
├── pytest.ini           # Pytest configuration
├── test_api.py          # API and emotion detection tests
└── README.md            # This file
```

## Writing Tests

- Use descriptive function names: `test_<what>_<scenario>`
- Group related tests with comment headers
- Use fixtures from `conftest.py` for shared setup
- Mark slow or integration tests with `@pytest.mark.slow`
