# Agent Instructions

## Principles

- **Done means green** — a change is only complete when `./happy.sh` exits 0; do not commit until it does. If `./happy.sh` was already failing before your changes, you must fix those pre-existing failures too — or stop and ask the user how to proceed.
- **Docs for everything public** — new functionality or public API changes must have accompanying docs in `docs/*.rst`
- **Type-annotate public APIs** — all public functions and classes need type annotations; mypy is the gate

## Project Overview

Testfixtures is a Python testing utilities library. Features: object comparison with diff output, mocking/replacement, logging capture, temporary directories, datetime mocking, exception/warning testing, Django and Twisted support.

## Environment

```bash
uv sync --all-extras --all-groups              # setup or after pulling
rm -rf .venv && uv sync --all-extras --all-groups  # full reset
```

## Commands

```bash
./happy.sh                                         # all checks — required before commit
uv run pytest                                      # all tests + doctests
uv run pytest tests/test_comparison.py             # single file
uv run pytest --cov=testfixtures --cov-report=term-missing  # with coverage
uv run mypy src/testfixtures                       # type checking
make -C docs html                                  # build docs (use this, not sphinx-build directly)
uv build                                           # build sdist + wheel
```

## Architecture

`src/testfixtures/` — all source. Key modules:

- `comparison.py` — `compare()`, `diff()`, `Comparison`, `StringComparison`, `RoundComparison`, etc.
- `replace.py` — `Replacer`, `replace()` decorators
- `logcapture.py` — `LogCapture`
- `datetime.py` — `mock_datetime`, `mock_date`, `mock_time`
- `tempdirectory.py` — temporary directory management
- `shouldraise.py` — `ShouldRaise`, `should_raise`
- `shouldwarn.py` — `ShouldWarn`, `ShouldNotWarn`
- `django.py`, `twisted.py` — framework-specific support
- `__init__.py` — main API exports

Config: `pyproject.toml` (optional deps for Django, Sybil, Twisted).
