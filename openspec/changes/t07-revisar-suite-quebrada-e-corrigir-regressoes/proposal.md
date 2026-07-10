## Why

The current regression suite is red across core families, so delivery signal is broken and real contract drift is hidden behind failing tests. This slice exists now to restore trust in `uv run task test` by fixing the smallest correct side in each failure path.

## What Changes

- Triage failing BDD, e2e, visual, CSV flow, seed, and rebalance tests by root cause.
- Fix tests when they encode stale expectations.
- Fix runtime code when it violates existing contracts.
- Update specs only when the source contract itself is wrong.
- Keep scope limited to regression stabilization; no new product behavior.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `test-suite-quality`: tighten delivery contract so canonical regression families stay green or are corrected in the owning spec/test before release.

## Impact

- `tests/bdd/`
- `tests/e2e/`
- `tests/visual/`
- `tests/test_real_csv_flow.py`
- `tests/test_seed_from_csv.py`
- `tests/test_rebalance_glue.py`
- `tests/test_rebalance_schemas.py`
- `openspec/specs/test-suite-quality/spec.md`
