## MODIFIED Requirements

### Requirement: Pytest full gate on pre-push
The pre-push stage SHALL run the pytest suite as a blocking gate, with the
following exclusions: `tests/e2e` (run by `task test-e2e`), `tests/audit_integration`
(run by the audit CI job), and `tests/bdd` (run by `task test-bdd`). The hook
entry MUST use `pass_filenames = false` so the full filtered subset runs.

#### Scenario: Pre-push pytest runs unit + integration, skips e2e/audit/bdd
- **WHEN** developer runs `git push`
- **THEN** the pre-push pytest hook executes `uv run pytest --ignore=tests/e2e --ignore=tests/audit_integration --ignore=tests/bdd`
- **AND** the hook reports success when all selected tests pass
- **AND** the hook reports failure when any selected test fails (push is blocked)

### Requirement: BDD scenarios run via task test-bdd, not pre-push
BDD scenarios under `tests/bdd/` MUST run via the dedicated `task test-bdd`
task, which orchestrates the dev server before pytest. BDD scenarios MUST
NOT run in the pre-push pytest gate because they require a live dev server
on `http://127.0.0.1:8766` that the pre-push hook does not start.

#### Scenario: BDD scenarios are excluded from pre-push pytest
- **WHEN** developer runs `git push`
- **THEN** the pre-push pytest hook does NOT collect or run any scenario from `tests/bdd/`
- **AND** the dev server is not required to start for the pre-push stage

#### Scenario: BDD scenarios run via task test-bdd in CI
- **WHEN** CI executes the test-bdd job (or developer runs `task test-bdd`)
- **THEN** the task orchestrates the dev server (`http://127.0.0.1:8766`) before invoking pytest
- **AND** pytest runs `tests/bdd/` against the live server
- **AND** the task reports per-scenario pass/fail summary

#### Scenario: Flaky BDD scenarios do not block pushes
- **WHEN** a BDD scenario fails intermittently (e.g., 1-in-5 flake from
  `test_per_class_sum_off_100_accepted_target_pct[Italo]`)
- **THEN** the push is NOT blocked (because BDD is excluded from pre-push)
- **AND** the developer must run `task test-bdd` locally or wait for CI to
  observe the flake

## ADDED Requirements

### Requirement: Pre-push pytest hook entry documents the dev-server carve-out
The `prek.toml` `pytest` hook entry for the `pre-push` stage MUST include
a comment explaining why `tests/bdd` is excluded. The comment MUST reference
`task test-bdd` as the canonical execution path.

#### Scenario: prek.toml has explanatory comment
- **WHEN** a developer reads `prek.toml` and locates the pre-push pytest hook entry
- **THEN** the entry includes a comment stating "BDD moved to `task test-bdd`
  (needs dev server) — runs in CI job, not pre-push"
- **AND** the entry passes `--ignore=tests/bdd` to pytest