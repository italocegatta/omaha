## Why

The global `addopts` in `pyproject.toml` appends `--cov=src/omaha --cov-report=xml:reports/coverage.xml` to **every** pytest invocation. This means `task test-e2e`, `task test-bdd`, and `task test-visual` all pay the coverage instrumentation overhead and generate XML reports even though:

1. Browser-heavy lanes (e2e, bdd, visual) validate UI flow, not code coverage — the XML they produce is noise.
2. CI already separates lanes correctly: the `coverage` job runs unit + integration only; browser jobs run without coverage upload.
3. `task test-visual` already has a `--no-cov` override, but `test-e2e` and `test-bdd` do not — they inherit the global addopts silently.
4. Coverage instrumentation adds measurable overhead to Playwright-based tests that are already the slowest part of the suite (195s e2e, 198s BDD, 82s visual vs 17s unit).

The goal is to make the local dev experience match CI semantics: coverage belongs to the fast lane (unit + integration) only, and browser lanes run clean without instrumentation.

## What Changes

- Remove `--cov` and `--cov-report=xml:reports/coverage.xml` from the global `[tool.pytest.ini_options] addopts` in `pyproject.toml`.
- Add explicit `--cov` + `--cov-report` flags to the `task test-unit`, `task test-integration`, and `task coverage` taskipy commands that need them.
- Ensure `task test-e2e`, `task test-bdd`, and `task test-visual` run without any coverage flags (no behavior change for visual, which already has `--no-cov`).
- Verify CI workflow `.github/workflows/ci.yml` is already correct (it is — no changes needed there).
- Update `README.md` Tests section to clarify that coverage is opt-in via `task coverage`, not default on all runs.

No test behavior changes. No production code changes. No new dependencies.

## Capabilities

### New Capabilities

- `test-lane-coverage-separation`: Configuration change that separates coverage reporting into the fast lane only (unit + integration), removing instrumentation from browser-heavy lanes (e2e, bdd, visual).

### Modified Capabilities

- `dev-tasks`: Taskipy commands for unit and integration gain explicit `--cov` flags; global addopts no longer carries them.
- `test-suite-quality`: The addopts baseline changes — coverage is no longer implicit on every pytest invocation.

## Impact

- **Files modified**: `pyproject.toml` (addopts + taskipy task definitions), `README.md` (Tests section).
- **CI**: No changes needed — `.github/workflows/ci.yml` already runs browser jobs without coverage upload and has a dedicated `coverage` job for the fast lane.
- **Local dev**: `task test-e2e` and `task test-bdd` stop generating `reports/coverage.xml` and stop paying instrumentation cost. `task test-unit` and `task test-integration` gain explicit coverage flags. `task coverage` behavior unchanged.
- **Risk**: Low. If any downstream tool reads `reports/coverage.xml` after an e2e run, it will find the file missing. The only canonical producer of that file should be `task coverage` — verified by checking CI and README.
