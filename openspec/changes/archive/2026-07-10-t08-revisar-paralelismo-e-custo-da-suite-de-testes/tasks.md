## 1. Audit bucket ownership

- [x] 1.1 Map current marker allowlists, task help text, prek hooks, and CI jobs to the test families they actually execute.
- [x] 1.2 Define the canonical bucket/concurrency matrix for `unit`, `integration`, `audit_integration`, `bdd`, `e2e`, `visual`, and full-suite gates.

## 2. Investigate late-suite BDD cost and flake behavior

- [x] 2.1 Reproduce late-suite BDD timeout/load flakes with repeated task-driven runs and isolate whether cost sits in server startup, DB/profile wipe, browser launch, or workflow waits.
- [x] 2.2 Apply or document harness-only mitigation that keeps BDD serial and leaves product/browser regressions to T07/T09/T10/T11.

## 3. Align harness buckets and fixture reuse

- [x] 3.1 Align `tests/conftest.py`, `pyproject.toml`, `prek.toml`, and `.github/workflows/ci.yml` to the canonical bucket map and task/help contract.
- [x] 3.2 Review `tests/e2e/conftest.py` and `tests/visual/conftest.py` for safe browser/server reuse, implementing only changes that preserve isolation contracts.
- [x] 3.3 Update operator-facing docs/comments with the serial vs parallelizable vs too-risky decision record, including the audit cost-center owner.

## 4. Verify and close proposal gate

- [x] 4.1 Run focused verification through canonical task commands for all affected buckets.
- [x] 4.2 Re-run affected late-suite BDD scenarios multiple times, confirm entrypoint alignment, and finish with `openspec list --specs`.
