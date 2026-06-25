# prek-hooks Specification

## Purpose

Defines the project's git-hook automation: which hooks run, on which pre-commit / pre-push / commit-msg stage, and whether they block or report-only on failure. Backed by the `prek.toml` file at the project root.
## Requirements
### Requirement: Stage-split hook layout
The prek configuration SHALL split hooks across three stages: `pre-commit` for fast, non-mutating checks plus the unit-test gate; `pre-push` for mutating hooks and slow checks; `commit-msg` for commit-message format validation.

#### Scenario: Pre-commit stage runs only non-mutating checks
- **WHEN** developer runs `git commit`
- **THEN** the pre-commit stage hooks run in priority order
- **AND** no hook in this stage modifies any tracked file

#### Scenario: Pre-push stage runs mutating and slow hooks
- **WHEN** developer runs `git push`
- **THEN** the pre-push stage hooks run in priority order
- **AND** mutating hooks (`ruff-format`, `ruff --fix`, `trailing-whitespace`, `end-of-file-fixer`, `uv-lock`) may modify tracked files

#### Scenario: Commit-msg stage validates message format
- **WHEN** developer runs `git commit -m "..."` or `git commit` (with editor)
- **THEN** the `commitizen` hook validates the message against Conventional Commits format

### Requirement: File sanity checks
The pre-commit stage SHALL run file sanity hooks: `check-merge-conflict`, `check-yaml`, `check-toml`, `check-json`, `check-added-large-files`, `detect-private-key`, `gitleaks`, `validate-pyproject`.

#### Scenario: All file sanity hooks block the commit on failure
- **WHEN** any file sanity hook fails
- **THEN** the `git commit` is blocked
- **AND** the failure message identifies which file or rule failed

#### Scenario: gitleaks runs in addition to detect-private-key
- **WHEN** the pre-commit hooks run
- **THEN** both `detect-private-key` (builtin, ~10ms) and `gitleaks` (~100ms) execute
- **AND** the two hooks are independent (a fail in one does not skip the other)

### Requirement: Pytest unit gate on pre-commit
The pre-commit stage SHALL run `pytest -m unit` as a blocking gate. The hook entry MUST be `./.venv/bin/python -m pytest -m unit` with `pass_filenames = false` so the full unit subset runs.

#### Scenario: Unit tests pass and commit lands
- **WHEN** all unit tests pass
- **THEN** the pre-commit hook reports success
- **AND** the `git commit` proceeds

#### Scenario: Unit tests fail and commit is blocked
- **WHEN** one or more unit tests fail
- **THEN** the pre-commit hook reports failure with the failing test names
- **AND** the `git commit` is blocked

### Requirement: Mutating Python tooling on pre-push
The pre-push stage SHALL run `ruff-format`, `ruff --fix`, `trailing-whitespace`, `end-of-file-fixer`, and `uv-lock`. `ruff-format` MUST run at priority 1, `ruff --fix` at priority 2, and the remaining mutating hooks at priority 3 (or lower).

#### Scenario: Ruff format and fix run before tests
- **WHEN** developer runs `git push`
- **THEN** `ruff-format` runs first (priority 1)
- **AND** `ruff --fix` runs second (priority 2)
- **AND** the full pytest suite runs after (priority 4+)

#### Scenario: uv-lock regenerates the lockfile when stale
- **WHEN** `pyproject.toml` dependencies have changed since the last lock
- **THEN** the `uv-lock` hook updates `uv.lock`
- **AND** the updated lockfile is included in the push

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

### Requirement: Pyright type-check gate on pre-push
The pre-push stage SHALL run `pyright` in `basic` mode, scoped to `src/omaha`, with the project's `.venv` for type resolution. Pyright MUST be marked `continue-on-error: true` while the codebase has pre-existing type errors (a follow-up change removes the flag).

#### Scenario: Pyright basic mode reports only on src/omaha
- **WHEN** the pyright hook runs
- **THEN** it scans `src/omaha/` and the project's `.venv`
- **AND** it does NOT scan `tests/`, `alembic/`, or `scripts/`

#### Scenario: Pyright failure does not block push
- **WHEN** pyright reports one or more type errors
- **THEN** the pre-push hook shows the failure
- **AND** the `git push` is NOT blocked (because of `continue-on-error: true`)

### Requirement: Commit-message and branch validation
The prek configuration SHALL validate commit messages via `commitizen` (commit-msg stage) and branch names via `commitizen-branch` (pre-push stage).

#### Scenario: Commit message follows Conventional Commits
- **WHEN** developer runs `git commit -m "fix(import): class binding"`
- **THEN** the `commitizen` hook accepts the message
- **AND** the commit proceeds

#### Scenario: Commit message violates Conventional Commits
- **WHEN** developer runs `git commit -m "did stuff"`
- **THEN** the `commitizen` hook rejects the message
- **AND** the commit is blocked

#### Scenario: Branch name is not bumpable
- **WHEN** developer pushes a branch named `fix/import-modal-binding` (not a release-bump branch)
- **THEN** `commitizen-branch` reports a warning (does NOT block by default)

### Requirement: Hooks with pre-existing failures use continue-on-error
The prek configuration SHALL mark the ruff hooks (`ruff-format`, `ruff --fix`) and the pyright hook with `continue-on-error: true` until the underlying issues (171 ruff errors + 26 pyright errors) are fixed in a follow-up change.

#### Scenario: Ruff hooks run and report but do not block
- **WHEN** `ruff-format` would reformat 4 files or `ruff --fix` would change 171 lines
- **THEN** the hooks run, report the would-be changes
- **AND** the commit/push is NOT blocked

#### Scenario: Follow-up change can remove the flag
- **WHEN** the 197 pre-existing issues are fixed
- **THEN** the `continue-on-error: true` flags are removed in a follow-up change
- **AND** the hooks become fully blocking

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

### Requirement: Pre-push pytest hook entry documents the dev-server carve-out
The `prek.toml` `pytest` hook entry for the `pre-push` stage MUST include
a comment explaining why `tests/bdd` is excluded. The comment MUST reference
`task test-bdd` as the canonical execution path.

#### Scenario: prek.toml has explanatory comment
- **WHEN** a developer reads `prek.toml` and locates the pre-push pytest hook entry
- **THEN** the entry includes a comment stating "BDD moved to `task test-bdd`
  (needs dev server) — runs in CI job, not pre-push"
- **AND** the entry passes `--ignore=tests/bdd` to pytest

