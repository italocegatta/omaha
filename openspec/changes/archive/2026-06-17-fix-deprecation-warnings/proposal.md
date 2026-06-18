## Why

2 deprecation warnings in test suite: `StarletteDeprecationWarning` (httpx) and `HTTP_422_UNPROCESSABLE_ENTITY` → `HTTP_422_UNPROCESSABLE_CONTENT`. Silent tech debt — no behavior change, but pollutes output and masks real warnings. Fix now while scope is trivial.

## What Changes

- Replace `HTTP_422_UNPROCESSABLE_ENTITY` with `HTTP_422_UNPROCESSABLE_CONTENT` in all test files
- Add `httpx2` dependency to `pyproject.toml`
- Migrate `from starlette.testclient import TestClient` → `from httpx2.testclient import TestClient` in conftest and all test files
- Remove old Starlette testclient import

## Capabilities

### New Capabilities

*(none — pure maintenance, no new capability)*

### Modified Capabilities

- `dev-tasks`: remove StarletteDeprecationWarning from known-warnings list if present

## Impact

- `tests/`: all files importing starlette.testclient or referencing HTTP_422_UNPROCESSABLE_ENTITY
- `pyproject.toml`: add `httpx2` dependency
- `.venv/`: re-lock after dependency change
