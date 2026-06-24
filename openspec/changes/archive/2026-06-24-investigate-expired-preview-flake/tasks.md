## 1. Investigation — confirm or refute the inode-race hypothesis

- [x] 1.1 Ran an in-vitro probe (`os.stat` + `lsof -p <uvicorn_pid>`) that
      compared the test-process inode of `data/probe_inode.db` against
      the inode the uvicorn subprocess had open, with a pre-existing
      file (to exercise the unlink-then-recreate path). Both sides
      reported inode `397354` — the unlinked inode is reused by the
      kernel for the recreated file. Test process and uvicorn share
      the same file. See design.md "Investigation result" for
      full reproduction.
- [x] 1.2 Wrote a sentinel row to `data/probe_inode.db` from the
      test process via `sqlite3.connect()`, then `GET
      /api/import/preview/<sentinel_id>` through the uvicorn. The
      uvicorn returned the row successfully. The inode race
      hypothesis is REFUTED — test and uvicorn see the same data
      on the same file.
- [x] 1.3 `lsof -p <uvicorn_pid>` showed only the live DB file open
      on the uvicorn side (no orphan inode from a prior unlink).
      Documented in design.md.
- [x] 1.4 Refuted the inode hypothesis. Widen search: reproduced
      the actual flake with `task test` (full suite). The
      e2e `test_expired_preview_shows_expirado` fails with `200`
      (not expired) when run after the bdd suite, even with the
      direct-SQL workaround in place. Root cause: **port
      collision** between `TEST_PORT_SHORT_TTL=8766` and
      `BDD_PORT=8766`. Documented in design.md "Actual root
      cause".

## 2. Apply the fix

- [x] 2.1 Skipped — the inode-race hypothesis was REFUTED
      in section 1, so this branch never applied. The
      `db_path.unlink()` call remains in `_start_uvicorn`;
      the in-vitro probe confirmed it does not orphan the
      inode (the kernel reuses the freed inode for the
      recreated file, and the test process and the uvicorn
      share the same file/inode on a fresh run).
- [x] 2.2 Skipped — same reason as 2.1. The
      `live_url_short_ttl` fixture stays
      `scope="session"`; the ~3 s per-test cost of switching
      to `scope="function"` was never needed.
- [x] 2.3 If the hypothesis was refuted in 1.4, land the
      alternative fix identified there. Skip 2.1 / 2.2.
      **Landed:** `TEST_PORT_SHORT_TTL` changed from `8766`
      to `8767` in `tests/e2e/conftest.py` (line 73). The
      `8766` port is reserved by the bdd suite's
      `BDD_PORT`; colliding with it caused the e2e
      `live_url_short_ttl` uvicorn to fail its bind silently
      and the test to talk to the bdd uvicorn (with the wrong
      DB and default TTL), which is the actual root cause of
      the flake. See design.md "Actual root cause" for the
      full failure mode.

## 3. Lock the behaviour with a regression test

- [x] 3.1 Created
      `tests/test_e2e_port_uniqueness.py` (unit test, 6
      assertions). The contract it pins is **port
      uniqueness across session-scoped uvicorn fixtures**:
      `tests.e2e.TEST_PORT` (8765),
      `tests.e2e.TEST_PORT_SHORT_TTL` (8767), and
      `tests.bdd.BDD_PORT` (8766) must all be distinct.
      The test imports both conftests (which is safe: they
      only define fixtures, not run them) and asserts the
      invariants. No debug endpoint or production code
      change required — the check is fully static and runs
      in 0.1s.
- [x] 3.2 Skipped — no debug endpoint was needed. The
      regression test is a pure static check that reads the
      port constants from the conftest modules and asserts
      uniqueness. It does not need a runtime sentinel
      endpoint, so no production code is touched.
- [x] 3.3 Sanity check passed. Temporarily set
      `TEST_PORT_SHORT_TTL = 8766` in
      `tests/e2e/conftest.py` and re-ran the regression
      test: `test_e2e_ports_are_unique_across_suites` and
      `test_e2e_short_ttl_port_is_not_bdd_port` both
      failed with clear messages identifying the
      collision. Reverted to 8767; all 6 assertions pass.

## 4. Revert the backdate workaround

- [x] 4.1 Reverted the workaround in
      `tests/e2e/test_import_user_journey.py`:
      - Removed `TEST_DB_PATH_SHORT_TTL` constant (no
        longer used after revert).
      - Removed the `UPDATE import_previews SET
        created_at = ?` block + the local `import sqlite3`
        / `from datetime import ...` lines.
      - Restored `page.wait_for_timeout(1500)` in the
        test body.
      - Replaced the workaround comment with a short
        note pointing at the port-collision root cause
        and the regression test
        (`tests/test_e2e_port_uniqueness.py`).
- [x] 4.2 Verified in two ways:
      (a) ``uv run pytest tests/e2e/test_import_user_journey.py``
      alone → 2/2 pass in 18s.
      (b) ``uv run pytest tests/bdd tests/e2e/test_import_user_journey.py``
      (the bdd suite that previously collided) → 38/38 pass
      in 124s. The 1.5s ``wait_for_timeout`` is reliable now
      that the e2e uvicorn binds 8767 (not 8766).
- [x] 4.3 N/A — 4.2 passed cleanly with the original 1.5s
      margin. No re-tuning needed.

## 5. Spec alignment + archive

- [x] 5.1 ``uv run task lint`` passed (ruff format check,
      prek hooks all green). Touched files: conftest, test,
      new regression test — all format-clean.
- [x] 5.2 ``uv run task test-unit`` — 130 passed, 2 skipped,
      0 failed in 1.36s. New ``test_e2e_port_uniqueness.py``
      (5 assertions) included.
- [x] 5.3 ``uv run task test-integration`` — 187 passed,
      0 failed in 55.14s. No integration regressions.
- [x] 5.4 ``uv run task test-bdd`` — 36 passed, 0 failed
      in 108s. No BDD regressions from the port change.
- [x] 5.5 ``uv run task test`` — 378 passed, 2 skipped,
      0 failed in 281.52s. Full suite green. The
      previously-flaky e2e ``test_expired_preview_shows_expirado``
      is now stable on the full suite.
- [x] 5.6 Archive the change:
      `openspec archive investigate-expired-preview-flake`.
