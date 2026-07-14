## Context

Integration tests currently spend ~15-20s on repeated bootstrap/alembic/seed setup across three hotspot files:

1. **`test_audit_inventory.py`** (~11s): Parses production `app.css` and builds Jinja2 `Environment` per module. The `stylesheet` and `jinja_env` fixtures are module-scoped but the underlying files never change during a test session — they could be session-scoped or cached.

2. **`test_db_reset_both_profiles.py`** (~4.5s): Defines its own `_run_alembic()` helper and spawns subprocesses for `omaha.seed` and `scripts.reset_both_profiles`. The alembic helper duplicates `tests/support/db.py:run_alembic_upgrade()`.

3. **`test_seed_from_csv.py`** (~3s+): The `omaha_db` fixture spawns `alembic upgrade head` via subprocess, then does module save/restore gymnastics to reimport `omaha.*`. This duplicates the alembic helper and the seed call pattern.

The session-scoped conftest (`tests/conftest.py`) already runs alembic + seed once per session/worker. The hotspot tests each create their own isolated DB (correct for isolation) but repeat the same subprocess + import dance without reusing existing helpers.

## Goals / Non-Goals

**Goals:**

- Add `run_alembic_and_seed()` to `tests/support/db.py` — one-call helper combining migration + seed
- Add `make_test_env()` to `tests/support/db.py` — env dict composition for subprocess tests
- Refactor `test_audit_inventory` to use session-scoped fixtures for CSS parsing and Jinja env (or `functools.lru_cache`)
- Refactor `test_seed_from_csv.omaha_db` fixture to use shared helpers
- Refactor `test_db_reset_both_profiles` to use shared helpers
- Maintain per-test DB isolation (each test gets its own `tmp_path` SQLite)

**Non-Goals:**

- Changing test assertions or test logic
- Modifying production code
- Changing the conftest session-scoped DB setup
- Reducing the number of tests (all 20 `test_seed_from_csv` cases stay)
- Touching e2e, BDD, or visual test infrastructure

## Decisions

### D1: Add `run_alembic_and_seed()` to `tests/support/db.py`

**Choice**: New function that calls `run_alembic_upgrade()` + `omaha.seed.seed()` in one shot.

**Rationale**: Both `test_seed_from_csv.omaha_db` and `test_db_reset_both_profiles` need alembic + seed. Currently each inlines the logic. A shared helper eliminates duplication and ensures consistent env var setup.

**Alternative considered**: Keep inline helpers — rejected because it perpetuates the duplication pattern.

### D2: Add `make_test_env()` for subprocess env composition

**Choice**: A function that takes `db_url` and returns a complete env dict with `DATABASE_URL`, `ADMIN_PASSWORD`, `SECRET_KEY`, `OMAHA_SKIP_STARTUP`, `OMAHA_ENV`.

**Rationale**: `test_db_reset_both_profiles._set_test_env()` and `test_seed_from_csv._run_seed()` both build nearly identical env dicts. Extracting this removes ~15 lines of duplication per file.

### D3: Session-scope `jinja_env` and `stylesheet` in `test_audit_inventory`

**Choice**: Promote `jinja_env` and `stylesheet` from `scope="module"` to `scope="session"`. Keep `factory` module-scoped (cheap to construct, no reason to change).

**Rationale**: `_TEMPLATES_DIR` and `_CSS_PATH` point to production files that don't change during a test run. Parsing `app.css` (~2500 lines) once per session instead of once per module saves ~2-3s. The `jinja_env` fixture only needs the `brl` filter registered once.

**Risk**: If a future test mutates the Jinja env or stylesheet, session-scoping would leak state. Mitigation: these fixtures are read-only by design; add a docstring note.

### D4: Refactor `omaha_db` fixture to use shared helpers

**Choice**: Replace the inline `subprocess.run(alembic)` + module juggling with `run_alembic_and_seed()` from `tests/support/db.py`.

**Rationale**: The fixture currently does: (1) save modules, (2) set env vars, (3) spawn alembic subprocess, (4) delete + reimport omaha modules, (5) call `omaha.seed.seed()`. Steps 3-5 are exactly what `run_alembic_and_seed()` will do. The module save/restore dance stays because `test_seed_from_csv` tests need to control `sys.modules` for CSV mutation isolation.

## Risks / Trade-offs

- **[Risk] Session-scoped fixtures leak state if mutated** → Mitigation: fixtures are read-only; add docstring warning. If leakage occurs, revert to module-scoped.
- **[Risk] `run_alembic_and_seed()` hides the subprocess boundary** → Mitigation: function name makes the subprocess explicit; callers still control `db_url` and env.
- **[Trade-off] Module save/restore in `test_seed_from_csv` stays** → The `omaha_db` fixture must still manipulate `sys.modules` because CSV-mutating tests need fresh module state. The shared helper handles only the alembic + seed part, not the module juggling.
