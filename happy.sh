#!/bin/bash
set -ex

echo "=== Syncing dependencies ==="
uv sync --all-extras --all-groups

echo "=== Tests + Coverage ==="
uv run pytest --cov --cov-report=term-missing:skip-covered

echo "=== Type Checking ==="
uv run mypy .

echo "=== Docs Build ==="
make -C docs clean html SPHINXOPTS=--fail-on-warning

echo "=== All checks passed! ==="
