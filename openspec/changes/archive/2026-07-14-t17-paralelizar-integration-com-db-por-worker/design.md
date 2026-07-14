## Context

Integration tests (`task test-integration`) run >3 min wall-clock and are the main pre-merge bottleneck. The suite is serial because all tests share one session-scoped SQLite database created at conftest module-load time. The `prepare_safe_test_database()` function in `tests/support/db.py` creates a temp directory, sets `DATABASE_URL`, imports `omaha.db` to bind `SessionLocal`, runs `alembic upgrade head` in a subprocess, and seeds data — all once per pytest session.

Current architecture:
- `tests/conftest.py` calls `prepare_safe_test_database()` at module load (line 64)
- `_SAFE_DB_FILE` is a single path shared across all tests
- `SessionLocal` binds to this single SQLite file at import time
- The `_omaha_test_env` fixture (session-scoped) re-exports the same DB
- Per-test `client` fixture creates a `TestClient` pointing at the same DB
- `verify_session_local_is_safe()` is the prod-DB guard (defense-in-depth)

`pytest-xdist` is not currently a dependency. Adding it alone would cause workers to share the same SQLite file, leading to lock contention and state corruption.

## Goals / Non-Goals

**Goals:**
- Each xdist worker gets its own isolated SQLite database
- Integration tests can run in parallel without shared-state corruption
- New `test-integration-parallel` taskipy task enables `-n auto`
- Existing serial `test-integration` task remains unchanged as fallback
- Worker DB provisioning reuses existing alembic + seed pipeline

**Non-Goals:**
- Parallelizing browser-backed lanes (e2e, bdd, visual) — still serial per T08
- Changing CI workflows — GH Actions deferred per owner
- Modifying production code
- Optimizing individual test setup time (that's T18's scope)
- Postgres parallelism — this is SQLite-only for dev

## Decisions

### D1: Worker detection via `PYTEST_XDIST_WORKER` env var

pytest-xdist sets `PYTEST_XDIST_WORKER` (e.g., `gw0`, `gw1`) on each worker process. The conftest module-load block checks this var: if present, provision a per-worker DB; if absent, use existing session-scoped behavior.

**Alternatives considered:**
- `request.config.workerinput` fixture — not available at module load time (conftest runs before fixtures)
- `xdist.get_xdist_worker_id()` — requires xdist import at module load, creates hard dependency even for serial runs

**Decision:** env var check — zero import overhead when xdist is absent, no new import dependency in serial mode.

### D2: Per-worker DB in tempdir hierarchy

Each worker creates its own tempdir (`omaha-worker-{id}-`) containing `portfolio.db` and `snapshots/`. The directory structure mirrors the existing session-scoped layout. Workers clean up on teardown.

**Alternatives considered:**
- In-memory SQLite (`:memory:`) — incompatible with subprocess alembic migrations (alembic runs in a separate process that can't access the parent's in-memory DB)
- Shared tempdir with per-worker subdirectories — adds complexity for no gain

**Decision:** independent tempdir per worker — simple, isolated, matches existing pattern.

### D3: Module-load detection with fallback

The conftest module-load block (`tests/conftest.py` lines 49-66) gains a branch: if `PYTEST_XDIST_WORKER` is set, call a new `prepare_worker_database()` function instead of `prepare_safe_test_database()`. The new function returns the same `SafeTestDatabase` dataclass but scoped to the worker.

**Alternatives considered:**
- pytest plugin with `pytest_configure` hook — more complex, harder to debug, changes import order
- Session-scoped fixture override — can't override module-load-time binding

**Decision:** module-load branch — minimal change, preserves the critical import-ordering contract (PRD §4.12 prod-DB isolation).

### D4: Serial fallback preserved

The existing `test-integration` task stays unchanged. A new `test-integration-parallel` task adds `-n auto`. This lets the team opt-in to parallelism without breaking the known-good serial path.

**Alternatives considered:**
- Replace serial with parallel — risky; if xdist has flakiness, no fallback
- Auto-detect in the same task — `-n auto` changes pytest behavior even when serial would be preferred

**Decision:** separate task — explicit opt-in, easy rollback.

## Risks / Trade-offs

**[Risk] SQLite write contention under parallel workers**
→ Each worker has its own DB file. No shared writes. Mitigation complete.

**[Risk] Alembic subprocess overhead per worker**
→ Each worker runs `alembic upgrade head` + seed. With 4 workers, that's 4× the migration cost upfront. Mitigated by: migrations are fast (<1s for SQLite), seed is idempotent. Net wall-clock gain from parallelism outweighs startup cost.

**[Risk] Test count imbalance across workers**
→ xdist default scheduling (loadscope) groups by module. Integration test modules vary in size. Acceptable for first iteration; fine-grained grouping is a follow-up.

**[Risk] Module-load ordering fragility**
→ The conftest module-load block is the prod-DB isolation contract (PRD §4.12). Adding a branch here must not break the env-setup-before-import guarantee. Mitigated by: the new `prepare_worker_database()` function uses the same env-var-setting + import pattern as `prepare_safe_test_database()`.

**[Trade-off] Extra disk usage per parallel run**
→ N workers × (DB + snapshots) tempdirs. SQLite DBs are ~5MB each. With 4 workers: ~20MB extra. Tempdirs are cleaned by OS. Acceptable.
