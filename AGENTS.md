This file provides guidance to LLM tools such as [aider](https://aider.chat/) 
and [Claude Code](claude.ai/code) when working with code in this repository.

## Project Overview

Testfixtures is a Python testing utilities library that provides helpers and mock objects for automated testing. It includes tools for comparing objects, mocking, logging capture, stream output testing, file/directory testing, exception/warning testing, Django support, and Twisted support.

## Development Commands

### Environment

Always work in a virtualenv contained in `.venv` in the checkout:

```bash
source .venv/bin/activate
```

If the environment doesn't exist, create it as follows:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip setuptools
pip install -U -e .[test,build,docs]
```

### Running Tests
```bash
pytest                    # Run all tests
pytest testfixtures/tests/test_comparison.py  # Run specific test file
```

### Type Checking
```bash
mypy testfixtures/        # Run type checking with mypy
```
**CRITICAL**: Always run mypy after code changes. All type checks must pass.

### Coverage
```bash
pytest --cov=testfixtures --cov-report=term-missing  # Run with coverage
```
**CRITICAL**: Always run coverage after code changes. Coverage must not drop below baseline.

### Documentation
```bash
cd docs && make html      # Build HTML documentation
cd docs && make clean     # Clean documentation build
```

### Package Installation
```bash
pip install -e .[test,build]  # Install in development mode with test dependencies
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
- Tests are in `testfixtures/tests/` with comprehensive coverage
- Django-specific functionality in `django.py`
- Twisted-specific functionality in `twisted.py`

## Configuration

- **pytest.ini**: Test configuration with Django settings module
- **mypy.ini**: Type checking configuration with Django and Zope plugins
- **setup.py**: Package configuration with optional dependencies for Django, Sybil, and Twisted

## Testing Notes

- Tests use pytest framework
- Django tests require `DJANGO_SETTINGS_MODULE=testfixtures.tests.test_django.settings`
- Type checking excludes some modules (`testfixtures.datetime`, test modules)
- Supports Python 3.11+
