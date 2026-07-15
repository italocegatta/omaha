# prek-hooks Specification

## Purpose

Defines the project's git-hook automation: which hooks run, on which pre-commit / pre-push / commit-msg stage, and whether they block or report-only on failure. Backed by the `prek.toml` file at the project root.
## Requirements
### Requirement: Stage-split hook layout
The prek configuration SHALL split hooks across three stages: `pre-commit` for fast, non-mutating checks plus the unit-test gate; `pre-push` for mutating hooks and integration tests (parallel via `test-integration-parallel`); `commit-msg` for commit-message format validation.

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
The pre-commit stage SHALL run `uv run task test-unit` as a blocking gate. The hook entry MUST delegate through taskipy with `pass_filenames = false` so marker selection, command text, and help text stay single-sourced in `pyproject.toml`.

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
The pre-push stage SHALL run integration tests only through `uv run task test-integration-parallel` (parallel via pytest-xdist with `--dist loadgroup`). Unit tests are gated at pre-commit only and MUST NOT be duplicated at pre-push. The selected coverage MUST match the documented integration bucket while excluding browser-backed families (`tests/bdd`, `tests/e2e`, `tests/visual`) and any separately documented heavy family such as `tests/audit_integration`. The hook entry MUST use `pass_filenames = false`.

#### Scenario: Pre-push delegates to canonical integration task
- **WHEN** developer runs `git push`
- **THEN** the pre-push pytest gate executes `uv run task test-integration-parallel`
- **AND** that command resolves to the integration bucket documented in `pyproject.toml`
- **AND** unit tests are NOT re-run (already gated at pre-commit)

#### Scenario: Browser suites stay out of the pre-push gate
- **WHEN** developer runs `git push`
- **THEN** the pre-push pytest gate does not collect `tests/bdd/`, `tests/e2e/`, or `tests/visual/`
- **AND** the push is not blocked on a browser-backed live-server workflow

### Requirement: Masked-pass guard on pre-push
The pre-push stage SHALL reject diffs that introduce new masked-pass test constructs (`skip`, `skipif`, `xfail`, `pytest.skip`, empty `pass` placeholders, or `NotImplementedError` used as stand-ins for missing assertions) unless the exact file/line is explicitly allowlisted by the canonical test-quality spec or roadmap.
The gate SHALL also run xfail unmasked (`--runxfail` or equivalent) so a test only remains green because of bypass logic cannot slip through.

#### Scenario: New xfail blocks push
- **WHEN** a push includes a new `@pytest.mark.xfail` without allowlist support
- **THEN** the pre-push gate fails
- **AND** the push is blocked

#### Scenario: Legacy allowlisted skip does not block
- **WHEN** a push touches a pre-existing, documented skip that already has allowlist coverage
- **THEN** the pre-push gate accepts it
- **AND** the allowlist reason remains intact

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
BDD scenarios under `tests/bdd/` MUST run via the dedicated `task test-bdd` bucket in local verification and in CI. They MUST NOT run in the pre-push pytest gate because the suite depends on a live server and currently remains serial by contract.

#### Scenario: BDD scenarios are excluded from pre-push pytest
- **WHEN** developer runs `git push`
- **THEN** the pre-push pytest hook does NOT collect or run any scenario from `tests/bdd/`
- **AND** the dev server is not required to start for the pre-push stage

#### Scenario: BDD scenarios run via task test-bdd in CI
- **WHEN** CI executes the test-bdd job (or developer runs `task test-bdd`)
- **THEN** the suite runs through the same named task entrypoint
- **AND** the job reflects the serial BDD bucket contract instead of a separate ad hoc pytest command

#### Scenario: Flaky BDD scenarios do not block pushes
- **WHEN** a BDD scenario fails intermittently (e.g., 1-in-5 flake from
  `test_per_class_sum_off_100_accepted_target_pct[Italo]`)
- **THEN** the push is NOT blocked (because BDD is excluded from pre-push)
- **AND** the developer must run `task test-bdd` locally or wait for CI to
  observe the flake

### Requirement: Pre-push pytest hook entry documents the dev-server carve-out
The `prek.toml` `pytest` hook entry for the `pre-push` stage MUST include
a comment explaining why `tests/bdd` is excluded. The comment MUST reference
`task test-bdd` as the canonical execution path. The entry MUST use
`task test-integration-parallel` for parallel execution with `loadgroup`
serialization of `xdist_group("serial")` tests.

#### Scenario: prek.toml has explanatory comment
- **WHEN** a developer reads `prek.toml` and locates the pre-push pytest hook entry
- **THEN** the entry includes a comment stating "integration tests only (unit gated at pre-commit)"
- **AND** the entry passes `--ignore=tests/bdd` to pytest via the taskipy command
