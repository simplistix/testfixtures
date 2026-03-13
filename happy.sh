#!/bin/bash
set -ex

echo "=== Syncing dependencies ==="
uv sync --all-extras --all-groups

echo "=== Tests + Coverage ==="
uv run pytest --cov=testfixtures --cov-report=term-missing

echo "=== Type Checking ==="
uv run mypy .

echo "=== Docs Build ==="
make -C docs clean html SPHINXOPTS=--fail-on-warning

echo "=== All checks passed! ==="
