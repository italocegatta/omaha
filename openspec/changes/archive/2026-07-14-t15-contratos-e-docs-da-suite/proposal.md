# T15 — Contratos e docs da suíte

## Problem

Docs and contracts drift from real suite behavior:

| Drift | Source | Impact |
|---|---|---|
| `bdd-workflow-reuse` spec names workflow `login_and_pick_profile` | `openspec/specs/bdd-workflow-reuse/spec.md` | Stale — actual code uses `login_and_land` since T05 rename |
| `test_csv_import.py` in `_INTEGRATION_PREFIXES` | `tests/conftest.py` line 183 | Pure-function test tagged `integration`; runs in wrong lane |
| Performance baseline row counts don't reconcile | `tests/PERFORMANCE.md` lines 27-32 | 869 collected ≠ 349 passed + 0 failed + 2 skipped |
| BDD README workflow table may have stale carve-out info | `tests/bdd/README.md` | `profile_isolation.feature` was renamed to `profile_sharing.feature` |

## Non-goals

- **No runtime code changes.** Only docs, specs, and test config.
- **No marker system refactoring.** `pytest_collection_modifyitems` logic stays.
- **No new test files.** Only `conftest.py` allow-list edit.
- **No changes to `scripts/seed_from_csv/`.**

## Approach

1. **Fix `bdd-workflow-reuse` spec** — rename `login_and_pick_profile` → `login_and_land` to match actual code.
2. **Fix marker allow-list** — remove `tests/test_csv_import.py` from `_INTEGRATION_PREFIXES` (it's pure-function, already in `_UNIT_FILES`).
3. **Fix performance baseline** — reconcile row counts in `tests/PERFORMANCE.md`.
4. **Update BDD README** — fix stale carve-out reference if `profile_isolation.feature` no longer exists.
5. **Add marker overlap rule to `test-suite-quality` spec** — files in `_UNIT_FILES` MUST NOT also appear in `_INTEGRATION_PREFIXES`.

## Risk

Low. Doc-only changes plus one allow-list line removal in `conftest.py`. No runtime behavior change.
