## Why

`tests/e2e/test_import_user_journey.py::TestS04ImportJourney::test_expired_preview_shows_expirado`
fails intermittently when the full pytest suite runs (`task test`) but passes
in isolation (`uv run pytest <file>::<test>`). The test exercises
`GET /api/import/preview/{id}` after a 1-second `PREVIEW_TTL_SECONDS` window.
In the full suite, the server returns `200` (preview still fresh) instead of
the expected `404` (expired). The flake is reproducible on this host with
the standard `task test` invocation. The test was last touched in
`51901c9 test(decision-5)` (2026-06-24 09:37) — this is a pre-existing
flakiness, not a regression from `fix-asset-table-ui-bugs`.

A short-term workaround (direct-SQL backdate of `created_at` by 2 s) is in
place in `tests/e2e/test_import_user_journey.py` as of the most recent
`fix-asset-table-ui-bugs` commit. The workaround was committed because the
flake blocks the merge gate. **It may be reverted as part of this change**
once the root cause is found and the proper fix is in. See
**Workaround status** below for what to remove if the investigation lands
on a non-DB fix.

## What Changes

- **Investigate** the root cause of the flake end-to-end:
  1. Confirm or refute the "two inodes for one path" hypothesis
     (conftest `_start_uvicorn` does `db_path.unlink()` then spawns a
     uvicorn subprocess that keeps the unlinked inode open via its file
     descriptor; a later test that opens the same path gets a NEW inode,
     so test writes and server reads land on different files).
  2. If confirmed, decide between the three resolutions below and pick
     one.
  3. If refuted, capture whatever the actual cause turns out to be
     (SQLite WAL visibility, pydantic-settings caching, dev-server
     port collision, asyncio loop leak, etc.) and propose the fix.
- **Fix the conftest** (or the test, or both) so `live_url_short_ttl`
  cannot end up with a stale DB view.
- **Lock the behaviour** with a regression test that fails deterministically
  if the bug returns (e.g. a unit test that asserts the conftest and the
  test process see the same inode for `test_e2e_short_ttl.db`).
- **Remove the backdate workaround** in
  `tests/e2e/test_import_user_journey.py` and `import time` /
  `TEST_DB_PATH_SHORT_TTL` only if the fix makes the original
  `wait_for_timeout(1500)` reliable. Otherwise keep the workaround and
  document why in the test header.

### Candidate resolutions (to be validated during investigation)

- **(a) Drop `db_path.unlink()` from `_start_uvicorn`.** Let uvicorn
  itself create the file at startup (it calls Alembic migrations which
  create tables). Removes the unlink-open-new-inode race entirely.
  Trade-off: if the test DB file is left over from a previous run with
  a non-matching schema, the migration step may fail. Mitigation: run
  `alembic downgrade base && alembic upgrade head` at fixture setup, or
  use a temp directory that pytest cleans.
- **(b) Switch `live_url_short_ttl` to `scope="function"`.** Each test
  gets a fresh uvicorn + fresh DB. Slowest fix (~3 s per test × N
  tests) but most isolated.
- **(c) Open the test-side SQLite connection BEFORE the unlink.**
  Reference the unlinked-but-still-open inode via the same fd the
  uvicorn holds. Brittle and not portable to other DB drivers — not
  recommended unless (a) and (b) both fail.

### Workaround status — can be reverted

The following code is in
`tests/e2e/test_import_user_journey.py` as a stop-gap while this change
is in flight. It is **explicitly allowed to be reverted** by the fix
that lands in this change, whichever path the investigation takes:

- `import time` near the top of the file (dead code after the
  backdate replacement) — remove.
- `TEST_DB_PATH_SHORT_TTL = REPO_ROOT / "data" / "test_e2e_short_ttl.db"`
  constant — remove if the fix doesn't need direct-SQL access.
- The block inside `test_expired_preview_shows_expirado` that opens a
  sqlite3 connection, computes `past = now - 2 s`, and runs
  `UPDATE import_previews SET created_at = ? WHERE id = ?` before the
  GET. Replace with `page.wait_for_timeout(<chosen margin>)`.

The current `task test` gate is GREEN with the workaround in place. If
the investigation finds that the conftest bug is the root cause and the
fix removes the inode race, restoring the original `wait_for_timeout`
is a one-line revert.

## Capabilities

### New Capabilities

- `e2e-fixture-isolation`: a small, focused capability describing the
  contract between test-side fixtures and the uvicorn subprocess they
  spawn — same file, same inode, same data, no stale views across
  fixture teardown/setup boundaries.

### Modified Capabilities

- *(none)* — the production `ImportPreview` route behaviour is correct;
  this change only touches the test fixture plumbing.

## Impact

- **Affected code:**
  - `tests/e2e/conftest.py` — `_start_uvicorn`, `live_url_short_ttl`,
    possibly `live_url` (same pattern) and `_wipe_classes_for_in_db`
  - `tests/e2e/test_import_user_journey.py` — remove workaround (if
    the fix makes it unnecessary)
  - **NEW:** regression test that pins the inode/visibility contract
- **Affected users:** none. Production code is untouched. Test suite
  goes from "intermittently red on full run" to "always green".
- **Risk:** if the wrong root cause is picked, the fix could mask the
  real bug and the flake resurfaces later. Mitigation: the
  regression test must fail deterministically if the inode race
  (or whichever cause lands) ever returns.
- **Migration:** none.
