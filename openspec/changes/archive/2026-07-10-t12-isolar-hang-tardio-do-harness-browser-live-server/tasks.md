## 1. Build single-test-at-a-time replay tool

- [x] 1.1 Add `task test-bdd-single <name>` in `pyproject.toml` under `[tool.taskipy.tasks]` that: (a) rebuilds test DB from scratch (alembic upgrade head + seed), (b) runs `pytest tests/bdd/test_scenarios.py -k "<name>" --no-header -v -p no:cacheprovider`, (c) reports pass/fail + elapsed seconds.
- [x] 1.2 Add optional `--trace` flag variant that captures Playwright trace on failure (via `browser.new_context(record_video_dir=...)` or `context.tracing.start()`).
- [x] 1.3 Validate basic tool: `task test-bdd-single login_creates_new_profile` passes on a fresh DB.
- [x] 1.4 Extend tool with `--after <file>` flag that runs a list of preceding tests before the target, to replay cumulative suite pressure. Validate with a 5-test prefix.

## 2. Collect ordered test list

- [x] 2.1 Run `pytest tests/bdd/test_scenarios.py --collect-only -q` and write the ordered test list to `tests/bdd/.collected_order.txt`.
- [x] 2.2 Record the exact ordered list at `tests/bdd/.collected_order.baseline.txt` so future deltas are visible.
- [x] 2.3 Run first 10 tests via replay tool to confirm baseline green for non-hanging prefix.

## 3. Reproduce hang and diagnose root cause

- [x] 3.1 Advance through ordered list in batches (10 tests at a time) running `task test-bdd-single --after <prefix-list> <target>` until one fails or hangs. Record exact ordinal position and test name.
- [x] 3.2 Capture the hang diagnostic: (a) tail uvicorn stdout from the hung test's server process, (b) check `data/test_bdd.db` for SQLite WAL/lock state, (c) verify no orphan chromium processes via `ps aux | grep chromium`.
- [x] 3.3 Classify the root cause as one of: server-teardown race, browser-process leak, DB-wipe deadlock, or event-loop accumulation. Update design.md decision record with confirmed cause.

## 4. Apply fixture/harness fix

- [x] 4.1 `tests/e2e/conftest.py live_url` teardown: replace `proc.terminate()` + `timeout=5` with `terminate()` → 3s wait → `poll()` → if alive `kill()` → 2s wait. Log kill path. Add port-free check after teardown.
- [x] 4.2 `tests/bdd/conftest.py live_url` teardown: mirror same fix from 4.1.
- [x] 4.3 `tests/e2e/conftest.py _browser` teardown: wrap `browser.close()` in try/except that logs failures instead of swallowing them. Add explicit `context.close()` fallback in `browser_context` teardown if `_browser` was not cleanly closed.
- [x] 4.4 `tests/bdd/conftest.py _wipe_profile`: add `PRAGMA busy_timeout = 3000` on the sqlite3 connection so lock contention waits 3s instead of raising immediately.
- [x] 4.5 `tests/e2e/conftest.py _wipe_classes_for`: add same `PRAGMA busy_timeout = 3000` for consistency.
- [x] 4.6 If event-loop accumulation confirmed: add `@pytest.fixture(scope="function")` documentation update or close guard on `sync_playwright` context manager.

## 5. Verify fix

- [x] 5.1 Re-run the ordered list from scratch via replay tool: full ordered pass completes without hang.
- [x] 5.2 `uv run task test-bdd` no longer times out or flakes late in suite. Record before/after wall time.
- [x] 5.3 `uv run task test-e2e` also green (regression check — e2e shares the same `_browser` and `live_url` patterns).
- [x] 5.4 `uv run task lint` clean.
- [x] 5.5 `openspec list --specs` clean (no spec drift from this change).

## 6. Document serial-replay procedure

- [x] 6.1 Add section "Debugging late-suite hangs" to `tests/bdd/README.md` covering: (a) when to use `task test-bdd-single`, (b) how to replay with `--after <prefix-list>`, (c) how to collect and update `.collected_order.txt`, (d) what diagnostic output to inspect (uvicorn stdout, chromium orphans, SQLite lock state).
- [x] 6.2 Update `tests/e2e/conftest.py` docstring to reflect any teardown behavior changes.
- [x] 6.3 Update `tests/bdd/conftest.py` docstring to reflect any fixture changes.
