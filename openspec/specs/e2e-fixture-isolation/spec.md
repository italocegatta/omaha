# e2e-fixture-isolation Specification

## Purpose
TBD - created by archiving change investigate-expired-preview-flake. Update Purpose after archive.
## Requirements
### Requirement: E2E fixture and uvicorn subprocess share one DB file
The e2e conftest (`tests/e2e/conftest.py`) MUST guarantee that the test
process and every uvicorn subprocess it spawns operate on the **same
file** (same path, same inode) for any given test database. The two
processes MUST observe each other's writes within the same fixture
scope.

The implementation MUST NOT rely on the test process and the uvicorn
subprocess independently re-creating a database at the same path. Any
`db_path.unlink()` (or `os.remove`) call that happens **before** the
uvicorn subprocess is spawned creates a race window: on POSIX, the
unlink removes the directory entry but the inode survives while the
uvicorn holds it open via its file descriptor; a later `open()` on the
same path from the test process returns a new inode, breaking the
shared-file contract.

The conftest MUST either:
- (a) Avoid unlinking the DB file before spawning the uvicorn (let the
  uvicorn create it via Alembic migrations, and clean per-test data
  via the existing autouse `clean_italo*` fixtures), or
- (b) Scope the uvicorn fixture to `function` so the test process and
  subprocess never share state across test boundaries.

#### Scenario: Test and uvicorn see the same DB inode
- **WHEN** an e2e test uses a session-scoped uvicorn fixture (e.g.
  `live_url_short_ttl`)
- **THEN** the test process's `os.stat(db_path).st_ino` and the
  uvicorn's view of the same path (via a debug endpoint or sentinel
  round-trip) MUST be equal
- **AND** a write performed by the test process to the shared DB
  (via `sqlite3.connect(db_path)`) MUST be visible to the uvicorn on
  the next request, and vice versa

#### Scenario: Unlink before spawn does not orphan the DB inode
- **WHEN** the conftest's `_start_uvicorn` removes the DB file
  (`db_path.unlink()`) before spawning the uvicorn
- **THEN** the test process MUST NOT be able to open a different
  inode for the same path
- **AND** every subsequent test that uses the fixture MUST see the
  same inode the uvicorn has open

### Requirement: Session-scoped uvicorn fixtures MUST bind unique ports
MUST each bind a distinct port. The main e2e `live_url`, the e2e
`live_url_short_ttl`, and the bdd `live_url` are the three
session-scoped uvicorn fixtures in the test suite. Two uvicorns on
the same port is a silent failure mode: depending on the kernel's
`SO_REUSEADDR` behaviour, the second bind either raises (and the
test that needed it crashes with "uvicorn did not start") or
succeeds but the OS routes new connections to whichever uvicorn
was bound first (typically the bdd suite, since pytest collects
`tests/bdd/` before `tests/e2e/` alphabetically).

The symptom of a port collision is a test that passes in isolation
but fails in the full suite, with status codes that don't match the
expected fixture's behaviour (e.g. a 1 s TTL test that gets 200
because it talked to a uvicorn with the default 3600 s TTL).

#### Scenario: All three session-scoped ports are distinct
- **WHEN** the conftest modules `tests/e2e/conftest.py` and
  `tests/bdd/conftest.py` are imported
- **THEN** `tests.e2e.conftest.TEST_PORT`,
  `tests.e2e.conftest.TEST_PORT_SHORT_TTL`, and
  `tests.bdd.conftest.BDD_PORT` MUST be three distinct values
- **AND** each MUST sit in the IANA dynamic range
  (1024-65535)
- **AND** `tests.e2e.conftest.TEST_BASE_URL_SHORT_TTL` MUST
  encode the same port as `TEST_PORT_SHORT_TTL`

### Requirement: Regression test pins the port-uniqueness contract
A regression test MUST exist that fails deterministically if any
session-scoped uvicorn fixture collides with another on the same
port. The test MUST be a static check (no DB, no HTTP, no
Playwright) so it runs as part of `uv run task test-unit` and
`uv run task test`. The test MUST be in the unit-test allow-list
(`_UNIT_FILES` in `tests/conftest.py`).

#### Scenario: Port collision check fails when the bug is reintroduced
- **WHEN** any of `tests.e2e.conftest.TEST_PORT`,
  `tests.e2e.conftest.TEST_PORT_SHORT_TTL`, or
  `tests.bdd.conftest.BDD_PORT` is changed to collide with another
- **THEN** the regression test fails with a clear message naming
  the colliding constants
- **AND** restoring the unique port values makes the test pass
  again

#### Scenario: Port collision check passes with the canonical assignment
- **WHEN** the e2e `live_url` binds 8765, the e2e
  `live_url_short_ttl` binds 8767, and the bdd `live_url` binds
  8766
- **THEN** the regression test passes
- **AND** `uv run pytest tests/bdd tests/e2e` runs to completion
  with all tests green (the bdd and e2e suites can coexist in the
  same pytest session)

