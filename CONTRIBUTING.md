# Contributing to Solacia

Thanks for your interest! Here's how to get started.

## Development Setup

```bash
git clone https://github.com/iweb3insight/solacia.git
cd solacia
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env  # Add your API key
```

## Running Tests

```bash
make test
```

## Code Style

- Formatter: `ruff format`
- Linter: `ruff check`
- Run before committing: `make lint`

## Pull Requests

1. Fork the repo
2. Create a feature branch (`git checkout -b feature/amazing`)
3. Commit with clear messages
4. Push and open a PR

## Reporting Issues

Open an issue with:

- Steps to reproduce
- Expected vs actual behavior
- Python version + OS
