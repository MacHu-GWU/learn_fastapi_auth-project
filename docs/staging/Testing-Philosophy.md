# Testing Philosophy

## Core Principles

1. **Test file mirrors source file**: `learn_fastapi_auth/<pkg>/<module>.py` → `tests/<pkg>/test_<pkg>_<module>.py`
2. **Unit tests = direct function calls**: Parameter in, parameter out. No HTTP client, no mock of the function itself.
3. **Integration tests are separate**: API endpoint tests go in `tests/test_app.py`, not in module-specific test files.
4. **Coverage goal**: 95%+ for implementation files.

## Test Types

| Type | What to test | Fixtures | Location |
|------|-------------|----------|----------|
| Unit test | Individual functions | `test_session` (database) | `tests/<pkg>/test_<pkg>_<module>.py` |
| Integration test | HTTP endpoints | `client` (AsyncClient) | `tests/test_app.py` |

## Anti-Patterns to Avoid

- **Don't mock the function you're testing** - that's self-deception
- **Don't test module X through HTTP endpoints** - put those tests in `test_app.py`
- **Don't test third-party library behavior** - trust fastapi-users, sqlalchemy, etc.

## File Organization

```
tests/
├── conftest.py                    # Imports from learn_fastapi_auth/tests/conftest.py
├── test_app.py                    # Integration tests (HTTP endpoints)
├── test_utils.py                  # Unit tests for utils.py
├── auth/
│   └── test_auth_users.py         # Unit tests for auth/users.py functions
└── all.py
```

## Examples

- Unit test example: `tests/auth/test_auth_users.py::TestTokenManagement`
- Integration test example: `tests/test_app.py::TestUserRegistration`

## Fixtures

Defined in `learn_fastapi_auth/tests/conftest.py`:
- `test_engine` - In-memory SQLite database engine
- `test_session` - Database session for unit tests
- `client` - AsyncClient for integration tests
