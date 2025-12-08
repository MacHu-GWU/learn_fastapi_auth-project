# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Quick Reference

For project overview, technology stack, and learning goals, see [README.md](README.md).

This document focuses on development workflow, commands, and codebase architecture.

## Development Environment Setup

### Prerequisites
- Python 3.12
- `uv` package manager (installed via `mise`)
- Virtual environment

### Key Commands

All commands use `mise` task runner (defined in `mise.toml`). The `.venv` contains a Python interpreter, so scripts can be run as `.venv/bin/python`.

**Environment Setup:**
- `mise run venv-create` - Create virtual environment
- `mise run inst` - Install all dependencies (runtime + dev + test + doc)
- `mise run export` - Export locked dependencies to requirements.txt

**Development & Testing:**
- `mise run fmt` - Format code with ruff
- `mise run test` - Run unit tests
- `mise run cov` - Run tests with coverage report (output: `htmlcov/index.html`)
- `mise run view-cov` - Open coverage report in browser

**Documentation:**
- `mise run build-doc` - Build Sphinx documentation (output: `docs/build/html`)
- `mise run view-doc` - Open documentation in browser

**Building & Publishing:**
- `mise run build` - Build wheel and source distribution packages
- `mise run publish` - Publish to AWS CodeArtifact (requires `build` dependency)

## Project Structure

```
learn_fastapi_auth-project/
├── learn_fastapi_auth/          # Main package
│   ├── __init__.py
│   ├── paths.py                 # Centralized path management (PathEnum)
│   ├── utils.py                 # Utility functions
│   ├── tests/                   # Test helpers
│   │   ├── helper.py            # Test runners with coverage
│   │   └── pytest_cov_helper.py # Vendor code for coverage automation
│   └── vendor/                  # Third-party utilities
├── tests/                       # Tests directory
│   ├── test_app.py              # Integration tests (HTTP endpoints)
│   ├── test_utils.py            # Unit tests for utils.py
│   ├── auth/
│   │   └── test_auth_users.py   # Unit tests for auth/users.py
│   └── all.py
├── docs/                        # Sphinx documentation
│   └── source/
├── .claude/                     # Claude Code configuration
│   ├── settings.json            # Permissions and settings
│   └── settings.local.json      # Local overrides
├── pyproject.toml               # Project metadata and dependencies
├── mise.toml                    # Task automation configuration
└── README.md                    # Project overview (Chinese)
```

## Architecture & Design Patterns

### Path Management
The `learn_fastapi_auth/paths.py` module provides centralized absolute path management via `PathEnum` class. This eliminates current directory dependencies and enables IDE autocomplete. Use `path_enum` for all file/directory references (see module docstring for available paths).

### Test Structure

**See [Testing Philosophy](docs/source/Testing-Philosophy.md) for full guidelines.**

Key points:
- Unit tests: Direct function calls (`test_session` fixture) → `tests/<pkg>/test_<pkg>_<module>.py`
- Integration tests: HTTP endpoints (`client` fixture) → `tests/test_app.py`
- Coverage goal: 95%+
- Don't mock the function being tested
- Coverage reports in `htmlcov/` directory

### Dependency Management
- `pyproject.toml` defines all dependencies with version constraints
- `uv` handles dependency resolution and lockfile (`uv.lock`)
- Optional dependencies via `[project.optional-dependencies]`: dev, test, doc, auto
- Virtual environment in `.venv/` managed via `mise`

## Python Version & Environment

- **Python Version**: 3.12 (specified in `pyproject.toml` and `mise.toml`)
- **Virtual Environment**: `.venv/` directory (created by `mise run venv-create`)
- **Python Executable**: `.venv/bin/python`
- **Package Manager**: `uv` (latest version via `mise`)

## Permissions & IDE Integration

Claude Code permissions are configured in `.claude/settings.json`:
- Writing: `.claude/**/*.md`, `**/*.rst`, `learn_fastapi_auth/**/*.py`, `tests/**/*.py`
- Bash execution: `.venv/bin/python` scripts and `mise` tasks

Use these paths when writing code and running commands to respect permission boundaries.

## Common Development Tasks

**Run a single test:**
```bash
.venv/bin/pytest -s tests/test_utils.py::test_add_two
```

**Check test coverage for a specific module:**
```bash
.venv/bin/pytest --cov=learn_fastapi_auth.utils --cov-report=term-missing tests/
```

**Format and check code:**
```bash
mise run fmt
```

**Create a new test:**
- Unit tests for `learn_fastapi_auth/<pkg>/<module>.py` → `tests/<pkg>/test_<pkg>_<module>.py`
- Integration tests (HTTP endpoints) → `tests/test_app.py`
- Use `run_cov_test()` helper from `learn_fastapi_auth.tests` for standalone coverage

## Next Steps for Implementation

When implementing new features:
1. Add application code to `learn_fastapi_auth/` package
2. Add corresponding tests to `tests/` directory
3. Update paths in `learn_fastapi_auth/paths.py` if new directories needed
4. Run `mise run cov` to verify test coverage
5. Documentation (if needed): Add `.rst` files to `docs/source/`