## Context

T07 identified that `uv run task test-bdd` ends red with 7 failures after 44 passes. T08 reproduced the pattern repeatedly and confirmed the failures are late-suite arrival-time issues (`create_one_class` and `login_and_land` timeout/load flakes), not isolated assertion regressions. The hang only manifests after ~30+ sequential tests exercising:

1. Session-scoped uvicorn subprocess per suite (`tests/bdd/conftest.py:live_url`)
2. Per-test browser launch and close (`tests/e2e/conftest.py:_browser`)
3. Per-test fresh context+page (`tests/e2e/conftest.py:browser_context`, `page`)
4. Per-test DB wipe of both profiles via `clean_seeded_profiles`

The current harness offers no single-test-at-a-time replay path that preserves the same fixture ordering and cumulative state pressure. Current debug cycle is "run full suite, watch it hang, guess." T12 builds the replay tool and fixes the hang.

### Harness architecture (relevant pieces)

- **`tests/bdd/conftest.py`**: `live_url` session scoped → uvicorn on port 8766 → `_wait_for_bdd_port()` (30s timeout). `clean_seeded_profiles` autouse per-test → wipes both profiles via raw sqlite3. Imports `_browser`, `browser_context`, `page` from e2e conftest.
- **`tests/e2e/conftest.py`**: `live_url` session scoped → uvicorn on port 8765 → `_wait_for_port()` (20s timeout). `_browser` function scoped → chromium launch via `sync_playwright`. `browser_context` + `page` function scoped.
- **`tests/bdd/step_defs/_workflows.py`**: `login_and_land`, `create_one_class`, etc. called per-scenario.
- **Hang symptom**: near end of BDD suite, a test gets stuck on `page.wait_for_selector(... timeout=5000)` or similar Playwright wait, the 5s timeout fires, and subsequent tests fail because the server or browser state is corrupted from the hung test's partial teardown.

### Hypothesized root causes (in order of likelihood)

1. **Server subprocess teardown race**: `live_url` fixture yield runs `proc.terminate()` then `proc.wait(timeout=5)`. If the server is mid-request when terminated, the subprocess might not die cleanly, leaving `data/test_bdd.db` locked or port 8766 in TIME_WAIT. Next test's server startup (session-scoped, so only relevant for full-suite debugging) or DB wipe hits stale state.

2. **Browser process leak**: `_browser` closes via `browser.close()` in its `finally` block, but if a test hangs and pytest kills the thread, the `finally` may not run — leaving a chromium orphan holding resources. Over 30+ tests, orphan browsers accumulate and the OS or kernel throttles new process/thread creation, causing the timeout.

3. **DB wipe fixture deadlock**: `clean_seeded_profiles` opens a `sqlite3.connect`, writes, commits, closes. If the previous test's server process still holds a SQLite WAL lock on `data/test_bdd.db`, the wipe blocks or fails silently, causing inconsistent per-test data that manifests as a timeout in the workflow step.

4. **Playwright event-loop accumulation**: `_browser` launches via `sync_playwright()`. If a prior test's Playwright context was not properly closed (e.g. `browser_context.close()` skipped due to exception), the sync Playwright connection accumulates stale state until it wedges on the next `wait_for_selector`.

## Goals / Non-Goals

**Goals:**
- Build and document a single-test-at-a-time replay command (`task test-bdd-single <test-name>`) that runs one test in isolation against a fresh server+browser but preserves the cumulative setup pattern (full alembic+seed, then clean per-test via the autouse wipe).
- Collect the exact ordered test list that triggers the hang by replaying tests sequentially with a known execution seed.
- Determine which of the four hypothesized causes (server teardown, browser leak, DB wipe deadlock, event-loop accumulation) is the dominant root cause.
- Fix the smallest correct side: adjust teardown ordering, add timeout/retry to fixture teardown, or scope lifecycle for safer cleanup.
- Verify: after fix, `uv run task test-bdd-single <each-problematic-test>` passes in order, and `uv run task test-bdd -- -k <problematic-group>` no longer hangs.
- Document the serial-replay procedure in `tests/bdd/README.md`.

**Non-Goals:**
- Fix product/browser assertion regressions (owned by T07).
- Fix import matcher, CSV semantics, or step definition expectations (owned by T10, T07).
- Change the BDD concurrency model (BDD stays serial; concurrency decisions belong to T08).
- Change the e2e fixture-isolation spec or any product spec.
- Add new feature tests or product behavior.
- Refactor step definitions or workflows beyond what's needed for fixture teardown.
- Rebalance, visual, or CSV pipeline work.

## Decisions

### D1. Single-test-at-a-time replay via `task test-bdd-single <name>`

A shell wrapper that:
1. Rebuilds the test DB from scratch (`alembic upgrade head` + `seed()`)
2. Runs `pytest tests/bdd/test_scenarios.py -k <name> --no-header -v`
3. Reports pass/fail and elapsed time
4. Optionally collects Playwright trace on failure

This mirrors the full-suite setup but runs only one scenario. The `-k` filter must select exactly one scenario to isolate order dependence. If a scenario passes in isolation but fails after test N, the replay script will support `--after <preceding-list>` to run N-1 prereqs then the target.

**Alternatives considered:**
- Use `pytest --co` (collect-only) + `pytest -k` ordering: rejected; doesn't control DB lifecycle per-run.
- Use `pytest --order-group`: rejected; introduces new dependency, doesn't help with fixture sequencing.
- Manual `uv run task test-bdd` with `--junit-xml` parsing: viable for observation but doesn't help with fix iteration.

### D2. Fix teardown first, not setup

The hang appears after many tests, not early. This points at accumulation of something that doesn't clean up. Strategy: add defensive cleanup to every teardown path before trying to change setup timing or scope.

Specific teardown patches:
- `live_url` teardown: replace `proc.terminate()` + `proc.wait(timeout=5)` with a stronger sequence: `proc.terminate()` → wait 3s → if alive, `proc.kill()` → wait 2s → verify port is free (`_wait_for_port` inverted). Log any kill path.
- `_browser` teardown: wrap `browser.close()` in a try/except that logs but doesn't swallow. Add `context.close()` fallback in `browser_context` if `_browser` teardown was skipped.
- `clean_seeded_profiles`: add a retry loop (3 attempts, 0.5s backoff) for the sqlite3 connect, in case server still holds a WAL lock.
- `_wipe_profile`: add explicit `conn.execute("PRAGMA busy_timeout = 3000")` so SQLite waits instead of raising immediately on contention.

**Alternatives considered:**
- Change server scope from session to function per-test: expensive (alembic + seed per test, ~6s overhead), and T08 already documented that cost.
- Change browser scope from function to session: risky, as the `_browser` docstring explicitly warns about asyncio loop pollution when sharing across tests.

### D3. Collection strategy: seeded ordered run

Record the `pytest` test order with `--collect-only` and pipe it into an ordered file. Then run tests in that order via the single-task wrapper, stopping on the first hang. This gives a deterministic "fails after test N" verdict.

After a hang, extract the failed test's Playwright trace (if any) and the uvicorn stdout tail (currently piped to `subprocess.PIPE` but never inspected). The fix may need to add `--log-level info` for diagnostics.

### D4. DB wipe uses `busy_timeout` pragma

SQLite's default behavior on lock contention is to raise `sqlite3.OperationalError: database is locked` immediately. The `_wipe_profile` and `_wipe_classes_for` functions run on the test DB while the uvicorn subprocess may still hold an active connection. Adding `PRAGMA busy_timeout = 3000` (3 second wait) turns a hard crash into a controlled retry. This alone may eliminate the "next test sees stale/wiped state" issue.

### D5. Port reuse check in teardown

After `live_url` teardown, verify the port is actually free by attempting a socket bind. If the port stays in TIME_WAIT, log it as a diagnostic but don't block. This helps future debugging if the hang resurfaces.

### D6. Confirmed cause: browser-side same-URL navigation overlap in debug replay

Confirmed during T12 apply/review loop:

- The review repro `uv run task test-bdd-single --trace --after <prefix-09> test_inline_add_with_patch_target[Ana]` no longer failed only after server/db teardown changes; the first stable failure after replay-helper alignment was ordinal **7** (`tests/bdd/test_scenarios.py::test_inline_create_2_classes_soma_110[Italo]`).
- Failure shape was browser-side, not server-side: `Page.goto("/") is interrupted by another navigation to "/"` from BDD workflows that click an action which already triggers `window.location.reload()` and then immediately call `page.goto()` to the same dashboard URL.
- Diagnostics ruled out other buckets: no `data/test_bdd.db-wal` / `-shm` residue after replay failure, no orphan chromium processes after the run, and the uvicorn harness no longer needed special teardown to recover once the browser-side guard was in place.

Classification: **event-loop accumulation / browser navigation timing**, not server-teardown race, browser-process leak, or DB-wipe deadlock.

Harness-side fix:

1. Make `tests/bdd_replay.py` invoke `uv run ...` for collect / alembic / seed / pytest so ordered replay uses the same runtime boundary as canonical repo tasks.
2. Wrap the shared Playwright `page` fixture with a narrow same-URL `goto()` guard: if Playwright reports that `goto(target)` was interrupted by another navigation to the **same** target, wait for the in-flight reload to finish instead of failing the test.

Result: trace-enabled ordered replay of the first 10 tests passes again, full ordered replay of all 48 BDD scenarios passes, and `uv run task test-bdd` / `uv run task test-e2e` both complete green.

## Risks / Trade-offs

- **[Hang has multiple causes]** → the `task test-bdd-single` wrapper and ordered collection will reveal which hypothesis fires first. Accept that more than one cause may need fixing; split secondary fixes into a follow-up slice.
- **[Adding retry/timeout masks real bug]** → log every retry path explicitly so the operator sees "WARN: DB wipe retry #1". A silent retry that always succeeds after 3 attempts is still a problem — the log makes it visible.
- **[Fix changes teardown timing but doesn't eliminate hang]** → the ordered-collection and single-test replay make iteration fast: change → rerun ordered list → compare hang position.
- **[Playwright trace collection adds overhead]** → make trace opt-in via `--trace` flag; default is no trace.
- **[Port verification in teardown may flake]** → the check is best-effort diagnostic only, not a gate; a `bind()` failure on teardown is logged but not raised.

## Migration Plan

1. **Build replay tool**: `task test-bdd-single <name>` wrapper script. Validate by running a known-green scenario in isolation.
2. **Collect ordered list**: `pytest tests/bdd/test_scenarios.py --collect-only -q | head -50` → `tests/bdd/.collected_order.txt`.
3. **Reproduce hang**: run `task test-bdd-single` iteratively, advancing to the test that triggers the hang.
4. **Diagnose hang**: inspect uvicorn stdout, Playwright trace (if captured), and test DB state at hang moment.
5. **Fix root cause**: apply the defensive teardown changes from Decisions D2/D4/D5, targeting whichever hypothesis was confirmed.
6. **Verify**: re-run the ordered list from scratch — full pass completes without hang.
7. **Full-suite verification**: `uv run task test-bdd` completes without hang.
8. **Document**: add `tests/bdd/README.md` section with serial-replay procedure, ordered-list maintenance, and the `task test-bdd-single` usage.

## Verification Plan

- `uv run task test-bdd-single <test-that-used-to-hang>` passes in isolation (baseline).
- Ordered non-hanging prefix passes: `for t in $(head -25 .collected_order.txt); do task test-bdd-single $t; done` all green.
- Full ordered list passes: entire BDD collected order completes without hang.
- `uv run task test-bdd` no longer times out or flakes late in suite.
- `uv run task lint` clean.
- `openspec list --specs` clean (no spec changes needed).

## Open Questions

- Does the BDD hang also reproduce in the e2e suite, or is it BDD-specific?
- Is `uvicorn --log-level warning` hiding startup/teardown errors? Should we bump to `info` temporarily during diagnosis?
- Should `task test-bdd-single` live in `pyproject.toml` under `[tool.taskipy.tasks]` or as a standalone shell script?
- Is the hang deterministic (same test number every time) or non-deterministic (varies by run)?
