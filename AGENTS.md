This file provides guidance to LLM tools such as [aider](https://aider.chat/) 
and [Claude Code](claude.ai/code) when working with code in this repository.

## Project Overview

Testfixtures is a Python testing utilities library that provides helpers and mock objects for automated testing. It includes tools for comparing objects, mocking, logging capture, stream output testing, file/directory testing, exception/warning testing, Django support, and Twisted support.

## Development Commands

### Environment

Always work in a virtualenv managed by uv:

```bash
# First time setup or after pulling changes
uv sync --all-extras
```

If you need to recreate the environment:

```bash
rm -rf .venv
uv sync --all-extras
```

### Running Tests
```bash
uv run pytest                                  # Run all tests
uv run pytest tests/test_comparison.py         # Run specific test file
uv run pytest --cov                            # Run with coverage
```

### Type Checking
```bash
uv run mypy src/testfixtures                   # Run type checking
```
**CRITICAL**: Always run mypy after code changes. All type checks must pass.

### Coverage
```bash
uv run pytest --cov=testfixtures --cov-report=term-missing
```
**CRITICAL**: Always run coverage after code changes. Coverage must not drop below baseline.

### Documentation
```bash
cd docs && uv run sphinx-build -b html . _build
```

### Package Building
```bash
uv build                                       # Build sdist and wheel
```

## Architecture

### Core Components

- **comparison.py**: Core comparison functionality including `compare()`, `diff()`, and various comparison classes (`Comparison`, `StringComparison`, `RoundComparison`, etc.)
- **replace.py**: Mocking and replacement functionality via `Replacer` class and `replace()` decorators
- **logcapture.py**: Logging capture via `LogCapture` class for testing logged output
- **datetime.py**: Date/time mocking utilities (`mock_datetime`, `mock_date`, `mock_time`)
- **tempdirectory.py**: Temporary directory management for file system testing
- **shouldraise.py**: Exception testing utilities (`ShouldRaise`, `should_raise`)
- **shouldwarn.py**: Warning testing utilities (`ShouldWarn`, `ShouldNotWarn`)

### Key Features

1. **Object Comparison**: Enhanced comparison with detailed diff output for complex nested structures
2. **Mocking System**: Comprehensive replacement/mocking system for objects, methods, and modules
3. **Logging Testing**: Capture and assert on logging output
4. **File System Testing**: Temporary directories and file operations
5. **Time Mocking**: Mock datetime, date, and time objects
6. **Exception/Warning Testing**: Assert on raised exceptions and warnings

### Module Organization

- Main API exports are in `__init__.py`
- Each major feature has its own module (comparison, replace, logcapture, etc.)
- Django-specific functionality in `django.py`
- Twisted-specific functionality in `twisted.py`

## Configuration

- **pyproject.toml**: Package configuration with optional dependencies for Django, Sybil, and Twisted
