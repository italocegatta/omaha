# T15 — Design

## Changes by file

### 1. `openspec/specs/bdd-workflow-reuse/spec.md`

Fix stale references throughout the spec:

- All references to `login_and_pick_profile` → `login_and_land`
- Carve-out examples: remove `profile_isolation.feature` from `files=frozenset({...})` — the actual code decorator only has `{"login.feature"}` since the `2026-06-26-direct-landing-with-header-profile-switcher` change (task 8.2)
- Scenario "profile_isolation.feature has no login wrapper" → update to `profile_sharing.feature` or remove (file was renamed)
- Update workflow count date: "As of 2026-06-23" → current date

This is a spec-only fix. The BDD README and actual code already reflect the current state.

### 2. `tests/conftest.py`

Remove `tests/test_csv_import.py` from `_INTEGRATION_PREFIXES` (line 183).

**Rationale:** The file's docstring says "Unit tests for :mod:`omaha.csv_import`. No DB, no FastAPI, no session". It only imports from `omaha.csv_import`. It's already listed in `_UNIT_FILES`. The integration prefix overrides the unit tag, routing pure-function tests through the integration lane.

After removal: the file is tagged `unit` via `_UNIT_FILES`. Tests run in `task test-unit` (fast lane, 16s) instead of `task test-integration` (219s lane).

**Verification:** `task test-file tests/test_csv_import.py` must pass after the marker change.

### 3. `tests/PERFORMANCE.md`

Fix row count reconciliation in the "Resumo por grupo" table:

- `unit`: 869 collected → verify breakdown (349 passed + 518 deselected + 2 skipped = 869)
- `integration`: 856 collected → verify breakdown (386 passed + 468 deselected + 2 skipped = 856)

The `Collected` column likely means "collected by pytest" (includes deselected), not "ran". Clarify the table or add a note explaining that `Collected = Passed + Failed + Skipped + Deselected`.

### 4. `tests/bdd/README.md`

BDD README already documents the `profile_isolation.feature` → `profile_sharing.feature` rename correctly (lines 98-101). The carve-out section references `login_and_land` and explains the rename history. No changes needed — verified current.

The workflow table (lines 109-114) names `login_and_land`, `create_one_class`, `create_two_default_classes`, `add_one_asset` — matches actual `_workflows.py` exports.

### 5. `openspec/specs/test-suite-quality/spec.md` (delta)

Add requirement: **Marker allow-lists MUST NOT overlap.** A file listed in `_INTEGRATION_PREFIXES` MUST NOT also appear in `_UNIT_FILES`. The `_INTEGRATION_PREFIXES` check wins in `pytest_collection_modifyitems`, so a dual-listed file is silently tagged `integration` even if its tests are pure functions.

## Non-goals confirmed

- No `delta-spec.md` for `dev-tasks` — no task behavior changes.
- No changes to production code (`src/omaha/`).
- No changes to `scripts/seed_from_csv/`.
