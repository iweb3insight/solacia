# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- SECURITY.md with vulnerability reporting policy
- .dockerignore for optimized Docker builds
- PyPI publish workflow (tag-triggered)
- Docker build + GHCR publish workflow
- CI: ruff format check, pytest-cov, pip-audit, bandit
- pyproject.toml: classifiers, project URLs, CLI entry point, ruff/pytest config
- Makefile: `make all`, `make help`, `make format`, `make coverage`, `make security`, `make docker`

### Changed
- Dockerfile: multi-stage build, non-root user, HEALTHCHECK
- Default API_HOST: 0.0.0.0 → 127.0.0.1 (safe for local dev)
- Session cache: TTL (30min) + LRU capacity (1000) to prevent OOM
- ChatMessage.content: max_length=4000 input validation
- Emotion LLM fallback: silent catch → logger.warning with traceback

## [0.1.0] - 2026-05-29

### Added
- Emotional conversation engine with 6 emotion types
- Implicit emotion detection (keywords + LLM fallback)
- Mood diary with SQLite persistence
- OpenAI-compatible Chat Completions API (streaming + non-streaming)
- Chatbox / NextChat integration support
- Docker deployment support
- CI pipeline with GitHub Actions
