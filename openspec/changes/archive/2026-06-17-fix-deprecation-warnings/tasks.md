## 1. Add httpx2 dependency

- [x] 1.1 Add `httpx2` to pyproject.toml dev dependencies

## 2. Migrate Starlette testclient → httpx2 testclient

- [x] 2.1 Verify `from fastapi.testclient import TestClient` works without deprecation after httpx2 install (Starlette 1.2.1 auto-uses httpx2, no warning)
- [x] 2.2 No import changes needed — Starlette uses httpx2 internally when installed; `fastapi.testclient.TestClient` re-exports Starlette's TestClient

## 3. Fix HTTP_422_UNPROCESSABLE_ENTITY deprecation

- [x] 3.1 Replace all `HTTP_422_UNPROCESSABLE_ENTITY` references with `HTTP_422_UNPROCESSABLE_CONTENT` across test files

## 4. Verify

- [x] 4.1 Run `pytest -m unit -q` — zero deprecation warnings
