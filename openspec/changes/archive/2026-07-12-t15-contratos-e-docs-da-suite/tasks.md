## 1. README contract refresh

- [x] 1.1 Update `README.md` Tests section so `uv run task test` is described as full suite (unit + integration + audit + e2e + visual + BDD).
- [x] 1.2 Replace any stale raw `pytest` lane wording with taskipy entrypoints (`uv run task ...`) and keep coverage wording tied to `reports/coverage.xml`.
- [x] 1.3 Check task-table rows against `uv run task --list`; keep only real task names and current descriptions.

## 2. BDD README alignment

- [x] 2.1 Update `tests/bdd/README.md` workflow table to current canonical workflow names.
- [x] 2.2 Keep `task test-bdd` documented as serial and `task test-bdd-single` documented as replay/debug command that rebuilds `data/test_bdd.db`.
- [x] 2.3 Keep workflow-threshold / carve-out guidance aligned with current contract language and current file names.

## 3. Performance baseline refresh

- [x] 3.1 Refresh `tests/PERFORMANCE.md` header metadata (date, environment, branch) to current baseline snapshot.
- [x] 3.2 Replace stale command examples with taskipy commands and keep fast-lane vs browser-lane separation explicit.
- [x] 3.3 Update summary tables / notes so BDD serial behavior and current suite grouping are obvious.

## 4. Contract-comment cleanup

- [x] 4.1 Review `tests/conftest.py` comments around marker allow-list / `UnknownTestPath`; adjust text only if it improves clarity.
- [x] 4.2 Do not change marker behavior, task definitions, or test runtime.

## 5. Validation

- [x] 5.1 Run `uv run task --list` and compare docs/task names.
- [x] 5.2 Run `openspec validate t15-contratos-e-docs-da-suite --json`.
- [x] 5.3 Run `openspec validate readme-freshness --json`, `openspec validate bdd-workflow-reuse --json`, and `openspec validate test-suite-quality --json`.
