## Context

2 deprecation warnings in pytest output. No behavior change. Trivial mechanical fix.

## Goals / Non-Goals

**Goals:**
- Zero deprecation warnings in `pytest -q` output
- Pin `httpx2` as replacement for Starlette testclient

**Non-Goals:**
- No API behavior changes
- No test logic changes

## Decisions

- **Replace Starlette TestClient with httpx2 TestClient** — the deprecation path is clear: install `httpx2`, change import. No API surface difference.
- **Use `HTTP_422_UNPROCESSABLE_CONTENT`** — Starlette 0.42+ renamed `HTTP_422_UNPROCESSABLE_ENTITY` to `HTTP_422_UNPROCESSABLE_CONTENT`. Compat alias exists, but new name is forward-looking.

## Risks / Trade-offs

- [Low] `httpx2` may have subtle API differences from `httpx` — verify one test run before committing.
