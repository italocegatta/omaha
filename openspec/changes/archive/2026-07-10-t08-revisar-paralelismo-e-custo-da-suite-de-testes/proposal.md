## Why

T07 is blocked on late-suite BDD timeout/load flakes, and the current test harness no longer gives a clean signal about what is slow, what is serial by contract, and what each named test bucket actually runs. Marker drift, task/help drift, hook drift, and CI drift now obscure whether failures come from product regressions or from the suite architecture itself.

## What Changes

- Reconcile marker/allowlist rules with canonical task, hook, and CI buckets so every named entrypoint runs the family it claims to run.
- Investigate late-suite BDD timeout/load flakes as a harness problem, keeping product/browser regression fixes in T07/T09/T10/T11.
- Review e2e and visual fixture-scope reuse to cut repeated browser/server startup cost where isolation contracts still hold.
- Produce an explicit decision record for what stays serial, what can be parallelized or reused safely, and what is too risky to change now.
- Keep test pruning narrow: only remove or consolidate coverage when a duplicate canonical owner is obvious and already covers the contract.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `unit-test-effectiveness`: refine the marker and task-bucket contract so `unit`, `integration`, `bdd`, e2e, and visual families stay explicitly partitioned and drift is loud.
- `prek-hooks`: align local hook entrypoints with canonical task buckets instead of ad hoc pytest selection.
- `test-suite-quality`: add suite-architecture requirements for concurrency classes, cost-center ownership, and repeated-run evidence before changing browser-backed harness behavior.

## Impact

- `tests/conftest.py`
- `tests/bdd/conftest.py`
- `tests/bdd/step_defs/_workflows.py`
- `tests/bdd/README.md`
- `tests/e2e/conftest.py`
- `tests/visual/conftest.py`
- `pyproject.toml`
- `prek.toml`
- `.github/workflows/ci.yml`
- `openspec/specs/unit-test-effectiveness/spec.md`
- `openspec/specs/prek-hooks/spec.md`
- `openspec/specs/test-suite-quality/spec.md`
- No product-route, template, CSV-pipeline, rebalance-contract, or baseline-refresh work belongs to this slice.
