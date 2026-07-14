# T14 — Design

## Module layout after refactoring

```
tests/support/
├── __init__.py          # unchanged
├── browser.py           # + _HarnessPage, + resolve_chromium already here
├── constants.py         # NEW — REPO_ROOT, TEST_ADMIN_PASSWORD, TEST_SECRET_KEY, port constants
├── db.py                # + _set_asset_target_pcts_via_db
├── hooks.py             # NEW — pytest_runtest_makereport + _remember_call_report
├── import_flow.py       # + _seed_assets_with_positions_via_import, unified login
└── server.py            # NEW — run_test_server context manager
```

## New modules

### `tests/support/constants.py`

Single source of truth for shared test constants.

```python
REPO_ROOT: Path              # Path(__file__).resolve().parent.parent.parent
TEST_ADMIN_PASSWORD: str     # "test-password"
TEST_SECRET_KEY: str         # base secret; suites override suffix if needed
```

Per-suite constants (port, DB path, secret suffix) stay in their conftest files — only the truly shared values move here.

### `tests/support/server.py`

Context manager wrapping uvicorn subprocess lifecycle:

```python
@contextmanager
def run_test_server(
    db_path: Path,
    port: int,
    *,
    label: str,
    secret_key: str = TEST_SECRET_KEY,
    admin_password: str = TEST_ADMIN_PASSWORD,
    extra_env: dict[str, str] | None = None,
) -> Iterator[str]:
    """Start uvicorn, wait for port, yield base URL, shutdown."""
```

Internally uses `compose_server_env`, `uvicorn_log_file`, `wait_for_port`, `shutdown_uvicorn` from `browser.py`.

### `tests/support/hooks.py`

```python
def remember_call_report(item: pytest.Item, report: pytest.TestReport) -> None:
    """Store the call-phase report on the item for trace artifact decisions."""

def make_report_hook():
    """Return a pytest_runtest_makereport hookimpl wrapper."""
```

## Moves to existing modules

### → `tests/support/browser.py`

- `_HarnessPage` class (goto retry guard for same-URL navigation)

### → `tests/support/db.py`

- `set_asset_target_pcts_via_db(assignments, db_path)` — extracted from e2e conftest's `_set_asset_target_pcts_via_db`

### → `tests/support/import_flow.py`

- `seed_assets_with_positions_via_import(page, live_url, class_assignments, positions)` — extracted from e2e conftest's `_seed_assets_with_positions_via_import`
- `login_as_italo(page, base_url)` — consolidated from visual conftest; delegates to `login_and_select_italo` or replaces it (they differ only in selector source)

## Conftest changes

### `tests/conftest.py` (root)
- No structural changes. Already uses `tests.support.db`.

### `tests/e2e/conftest.py`
- Remove `_HarnessPage` → import from `tests.support.browser`
- Remove `_start_uvicorn` → use `tests.support.server.run_test_server`
- Remove `_seed_assets_with_positions_via_import` → import from `tests.support.import_flow`
- Remove `_set_asset_target_pcts_via_db` → import from `tests.support.db`
- Remove local `TEST_ADMIN_PASSWORD`, `TEST_SECRET_KEY` → import from `tests.support.constants`
- Remove `pytest_runtest_makereport` hook → import from `tests.support.hooks`
- `live_url` and `live_url_short_ttl` fixtures become thin wrappers around `run_test_server`

### `tests/bdd/conftest.py`
- Remove inline uvicorn start pattern → use `tests.support.server.run_test_server`
- Remove `pytest_runtest_makereport` hook → import from `tests.support.hooks`
- Remove local `TEST_ADMIN_PASSWORD`, `TEST_SECRET_KEY` → import from `tests.support.constants`
- Keep `clean_seeded_profiles` and step-def re-exports (BDD-specific)

### `tests/visual/conftest.py`
- Remove `login_as_italo` → import from `tests.support.import_flow`
- Remove inline uvicorn start pattern → use `tests.support.server.run_test_server`
- Remove local `TEST_ADMIN_PASSWORD`, `TEST_SECRET_KEY` → import from `tests.support.constants`
- Keep `VisualViewport`, `VIEWPORTS`, screenshot comparison logic (visual-specific)

## Interface contracts

### `run_test_server` contract
- Caller owns DB file deletion before calling.
- Caller provides port; no auto-assignment.
- Context manager guarantees uvicorn shutdown on exit (normal or exception).
- Returns base URL string (e.g., `http://127.0.0.1:8765`).

### `set_asset_target_pcts_via_db` contract
- Takes `dict[str, float]` mapping asset name → target percentage.
- Takes optional `db_path`; defaults to e2e test DB.
- Direct sqlite3 write — test-only, bypasses ORM.

### `seed_assets_with_positions_via_import` contract
- Takes page, live_url, class_assignments, optional positions dict.
- Drives import modal end-to-end.
- Cleans up temp CSV on success.

## Migration order

1. Create `constants.py` — zero consumers yet, safe.
2. Create `hooks.py` — zero consumers yet, safe.
3. Create `server.py` — zero consumers yet, safe.
4. Move `_HarnessPage` to `browser.py` — update e2e import.
5. Move `_set_asset_target_pcts_via_db` to `db.py` — update e2e import.
6. Move `_seed_assets_with_positions_via_import` to `import_flow.py` — update e2e import.
7. Consolidate `login_as_italo` — update visual conftest.
8. Rewire e2e conftest to use `server.py` + `constants.py` + `hooks.py`.
9. Rewire bdd conftest to use `server.py` + `constants.py` + `hooks.py`.
10. Rewire visual conftest to use `server.py` + `constants.py`.
11. Run full suite: `task test-unit && task test-integration && task test-bdd && task test-visual && task test-e2e`.

## Non-goals confirmed

- No `delta-spec.md` — pure refactoring, no behavior change.
- No changes to production code (`src/omaha/`).
- No changes to `scripts/seed_from_csv/`.
