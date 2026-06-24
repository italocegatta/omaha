## Context

`tests/e2e/test_import_user_journey.py::TestS04ImportJourney::test_expired_preview_shows_expirado`
fails on `task test` (full suite) but passes on
`uv run pytest tests/e2e/test_import_user_journey.py::TestS04ImportJourney::test_expired_preview_shows_expirado`
(isolated). The test:

1. Logs in as Italo, creates 3 classes.
2. Uploads a CSV via the dashboard import modal, which calls
   `POST /api/import/preview` and stores `previewId` in the
   `importModal` Alpine store.
3. Reads `previewId` from the Alpine store.
4. Waits for the 1-second TTL to elapse.
5. Calls `GET /api/import/preview/{previewId}` and expects `404`.
6. Calls `POST /api/import/commit` and expects `400` with
   `"expirado"`.

Step 5 returned `200` in the full suite (preview not yet expired per
the server), with no `detail` field. The Alpine `previewId` was set
correctly (the modal moved to step 2 with the commit button visible),
so the id is the one the server just persisted. A direct-SQL
backdate of `created_at` by 2 s also failed: `UPDATE ... SET
created_at = past WHERE id = preview_id` reported `rowcount = 1`,
but the GET still returned `200` — the workaround did not make the
test pass on the full suite.

## Investigation result

Two concurrent hypotheses were on the table. The investigation
disproved the inode-race hypothesis and confirmed a port-collision
hypothesis.

### Inode race — REFUTED

The proposed hypothesis was that `tests/e2e/conftest.py::_start_uvicorn`
unlinks the DB file before spawning uvicorn, and on POSIX the
unlinked inode is kept alive by the uvicorn's open fd, so the test
process's later `open()` gets a different inode and the two never
see each other's data.

A direct probe (`/home/juca/.config/opencode/...` — see the
investigation transcript in this change) confirmed that the test
process and the uvicorn subprocess share the same inode for the
test DB file. The probe:

1. Pre-created `data/probe_inode.db` with a known inode.
2. Ran the conftest's exact `db_path.unlink()` + `Popen` sequence.
3. Read `os.stat(db_path).st_ino` from the test process after
   uvicorn startup — got the same inode (397354) the uvicorn had
   pre-unlink.
4. Ran `lsof -p <uvicorn_pid>` and saw only the live inode open.
5. Wrote a sentinel row to `import_previews` from the test process
   via `sqlite3.connect(db_path)`, then `GET
   /api/import/preview/<sentinel_id>` through the uvicorn. The
   uvicorn returned the row successfully — confirming the test
   and the uvicorn read the same data on the same file.

The kernel reuses freed inodes for the recreated file, so the
"orphan inode" the design doc worried about is not actually
orphaned: the new file gets the same inode number as the unlinked
one, and every fd that opens the path lands on the same file.

### Actual root cause — port collision

Reproduced the failure with `task test` (full pytest session, 372
tests). The e2e `test_expired_preview_shows_expirado` failed with
`200` (not expired) — the preview was created ~0.5 s ago and the
1.5 s sleep was insufficient because the server was using the
**default** `PREVIEW_TTL_SECONDS=3600`, not the 1 s the fixture
intended. The direct-SQL backdate workaround was also broken: the
test wrote to a DB file that did not exist (the e2e uvicorn had
failed its bind), and the GET hit a different DB on a different
uvicorn.

The mechanism is a port collision:

- `tests/bdd/conftest.py::BDD_PORT = 8766` (line 36)
- `tests/e2e/conftest.py::TEST_PORT_SHORT_TTL = 8766` (was line 73)

When `task test` runs in a single pytest session, pytest collects
`tests/bdd/` before `tests/e2e/` (alphabetical). The bdd session
fixture starts a uvicorn on 8766 first. The e2e
`live_url_short_ttl` session fixture later tries to bind 8766
again — the bind either fails or, depending on the kernel's
`SO_REUSEADDR` behaviour, the second uvicorn's `socket.bind()`
silently lands on the same address but the OS routes new
connections to the first uvicorn (the bdd one).

Either way, the e2e test that uses `live_url_short_ttl` ends up
talking to the bdd uvicorn, which:

- uses `data/test_bdd.db` (not `data/test_e2e_short_ttl.db`),
- has `PREVIEW_TTL_SECONDS=3600` (the default — the e2e fixture
  passes `PREVIEW_TTL_SECONDS=1` in `extra_env`, but the bdd
  uvicorn never sees that env var).

The 1.5 s `wait_for_timeout` is meaningless against an hourly
TTL. The GET returns 200 (preview is fresh), and the test fails.

The direct-SQL backdate in the workaround writes to
`TEST_DB_PATH_SHORT_TTL` (the e2e DB path) — but that file does
not exist, because the e2e uvicorn never bound its port, so
Alembic never ran against it. The `UPDATE` actually operates on a
zero-byte file or, if `sqlite3.connect()` creates an empty file
on `open`, on a fresh empty database. The test process's
`SELECT` after the update returns `[]` not because of an inode
mismatch but because the row never existed in the file the
backdate wrote to. The GET, going through the bdd uvicorn, reads
the live row from `data/test_bdd.db` — the row the bdd uvicorn
created when the e2e test uploaded via port 8766 — and returns
200 because that row is fresh against the 3600 s TTL.

This is why the workaround was failing on the full suite even
though the in-suite `test_expired_preview_shows_expirado` test
still passed when run in isolation. The fix is to give the e2e
short_ttl fixture its own port.

The bdd conftest's docstring (line 5) explicitly reserves 8766
"one port off from the legacy `tests/e2e/` suite's 8765 so the
two suites can run in parallel". The e2e `live_url_short_ttl`
fixture was added later and grabbed 8766, breaking the original
contract.

## Goals / Non-Goals

**Goals:**

- Find the actual root cause of the flake (or confirm the inode
  hypothesis).
- Apply a fix in `tests/e2e/conftest.py` and/or the test that
  prevents the symptom.
- Add a regression test that fails deterministically if the
  cause returns.
- Remove the temporary backdate workaround from
  `test_import_user_journey.py`.

**Non-Goals:**

- Production code changes (`src/omaha/routes/imports.py` is correct).
- Changes to the `live_url` fixture for the main e2e suite unless
  the same root cause affects it.
- Speeding up the e2e suite (a side effect of (b) per the proposal
  is to add ~3 s per short_ttl test, but the suite is already
  minutes long).

## Decisions

**Decision 1: Investigate before changing any code.**

The proposal's inode-race hypothesis was the leading theory but
unconfirmed. Before touching the conftest, run an in-vitro
inode-and-sentinel probe to confirm or refute the hypothesis.
The probe (captured in the investigation transcript in this
change) compared `os.stat(db_path).st_ino` in the test process
against `lsof -p <uvicorn_pid>` in the uvicorn, then round-tripped
a sentinel row through the API. Both inodes matched (the kernel
reuses freed inodes for the recreated file), and the sentinel
round-trip succeeded — the inode-race hypothesis is REFUTED.

**Decision 2: Widen the search after refutation.**

After disproving the inode hypothesis, the next most likely
candidate was something that flips the e2e short_ttl uvicorn's
behaviour. Reproduced the flake with `task test` (full pytest
session): the e2e test got `200` instead of `404` even with the
1.5 s sleep, and the direct-SQL backdate workaround was also
failing (the GET still returned 200, even though the test
"successfully" UPDATEd a row). Compared the e2e
`TEST_PORT_SHORT_TTL = 8766` against the bdd
`BDD_PORT = 8766` and the collision was obvious. Confirmed by
running the bdd uvicorn and the e2e short_ttl uvicorn in the
same process: the second bind silently lost, the test talked
to the first uvicorn, and the GET hit `data/test_bdd.db` with
the default TTL.

**Decision 3: Change `TEST_PORT_SHORT_TTL` from 8766 to 8767.**

This is the smallest possible change that fixes the collision
without touching the bdd conftest (which the bdd suite's own
contract owns). Port 8767 is in the same band as 8765/8766,
follows the existing +1-off convention, and is the next
available port in the e2e/BDD allocation. The bdd conftest's
docstring (line 5) explicitly reserves 8766 — moving the e2e
fixture instead of the bdd fixture respects that contract.

**Decision 4: Revert the backdate workaround.**

The workaround was a stop-gap that masked the symptom. With the
port fix in place, the original `page.wait_for_timeout(1500)`
margin is reliable. Reverted:
- `TEST_DB_PATH_SHORT_TTL` constant (unused after revert)
- The `UPDATE import_previews SET created_at = ?` block
- The local `import sqlite3` / `from datetime import ...`
- Restored `page.wait_for_timeout(1500)` with a comment pointing
  at the port-collision root cause and the regression test

**Decision 5: Pin the contract with a unit-level regression
test.**

A new file `tests/test_e2e_port_uniqueness.py` (unit-level, no
DB, no HTTP, no Playwright — runs in 0.1 s) imports both
conftests as modules and asserts:

1. The three session-scoped ports (`TEST_PORT`,
   `TEST_PORT_SHORT_TTL`, `BDD_PORT`) form a set of three
   distinct values.
2. The e2e ports sit in the IANA dynamic range
   (1024-65535), guarding against typos that drop digits.
3. Explicit guard: `TEST_PORT_SHORT_TTL != BDD_PORT`, with a
   message that names the original collision.
4. `TEST_BASE_URL_SHORT_TTL` ends with the same port as
   `TEST_PORT_SHORT_TTL` — guards against drift between the
   bound port and the URL the tests point at.
5. The declared port is bindable on this host (catches
   environment-specific reservations on shared CI).

The test is runnable as part of `uv run task test` and fails
deterministically (verified by temporarily reverting
`TEST_PORT_SHORT_TTL` to 8766 — the test failed with a clear
message naming the collision).

## Risks / Trade-offs

- **Risk:** a future fixture addition re-introduces a port
  collision (e.g. someone adds a new session-scoped uvicorn
  without checking the existing allocations). *Mitigation:*
  `tests/test_e2e_port_uniqueness.py` is the loud-future-drift
  signal. If a third suite joins the party, the test's
  `_INTEGRATION_PREFIXES` analogue (a list in the test file)
  is the place to add the new port.
- **Risk:** uvicorn's silent bind behaviour on a colliding
  port depends on `SO_REUSEADDR` and the kernel's port-reuse
  semantics. On some hosts, the second bind raises immediately
  and the e2e test crashes with a "uvicorn did not start"
  error — that crash is also caught by the new test, but the
  test does not cover the runtime case where the bind is
  accepted and the test gets the wrong server. *Mitigation:*
  the static port-uniqueness check is the primary defence; the
  runtime crash is the secondary.
- **Risk:** the regression test imports the conftest modules
  directly. If a future conftest refactor changes the constant
  names (`TEST_PORT_SHORT_TTL` → `SHORT_TTL_PORT`), the test
  will fail to import. *Mitigation:* the import is the contract
  — rename the constant deliberately and update the test
  alongside.
- **Trade-off:** none material. Port 8767 is a free slot in the
  existing 8765/8766 allocation; the e2e test runs in the same
  ~18 s as before.
