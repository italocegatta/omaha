## Why

`uv run task test-bdd` and `uv run task test-e2e` both exhibit a deterministic late-suite hang/timeout that surfaces only after several tests complete. The hang is order-dependent and doesn't reproduce with isolated single-test runs. T07 and T08 confirmed the root cause is not a product regression — it lives in the harness layer: server teardown, browser/context lifecycle, or DB/profile wipe fixture. Until this is isolated and fixed, every full suite run wastes time on an unproductive "rerun and see if it passes" loop.

## What Changes

- Build a repeatable single-test-at-a-time replay harness so each failing case can be debugged in isolation without running the full suite.
- Collect and document the exact order+conditions that trigger the late-suite hang.
- Fix the smallest correct side of the harness (fixture teardown, server shutdown, browser close, DB wipe, or wait timeout) to eliminate the hang.
- Add serial-replay docs to `tests/bdd/README.md` so future harness debugging follows the same proven procedure.
- Keep every change inside `tests/e2e/conftest.py`, `tests/bdd/conftest.py`, `tests/bdd/README.md`. Touch `tests/conftest.py` only if a shared marker or fixture-boundary split is necessary.
- No product code changes. No import-matcher or CSV-semantics changes. No route/template/product changes.

## Capabilities

### New Capabilities

- None. This slice is debug-only; no new product capability.

### Modified Capabilities

- None. No spec-level contract changes. Harness behavior that changes (e.g. teardown ordering, wait timeout, fixture scope) is an internal implementation detail of the conftest files, not a contracted capability.

## Impact

- `tests/e2e/conftest.py` — fix server/browser teardown, wait plumbing, or fixture cleanup that causes the hang.
- `tests/bdd/conftest.py` — mirror any e2e conftest fix that applies to BDD suite too.
- `tests/bdd/README.md` — document the serial-replay procedure for future harness debugging.
- `tests/conftest.py` — only if shared fixture boundary or marker split is needed.
