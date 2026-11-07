#!/usr/bin/env sh
# The single command CI and contributors run: format check, lint, types, tests.
set -eu
uv run ruff format --check .
uv run ruff check .
uv run mypy
uv run pytest -q
