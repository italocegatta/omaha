## MODIFIED Requirements

### Requirement: Stage-split hook layout
The prek configuration SHALL split hooks across three stages: `pre-commit` for fast, non-mutating checks plus the unit-test gate; `pre-push` for mutating hooks and integration tests (parallel via `test-integration-parallel`); `commit-msg` for commit-message format validation.

### Requirement: Pytest full gate on pre-push
The pre-push stage SHALL run integration tests only through `uv run task test-integration-parallel` (parallel via pytest-xdist with `--dist loadgroup`). Unit tests are gated at pre-commit only and MUST NOT be duplicated at pre-push. The selected coverage MUST match the documented integration bucket while excluding browser-backed families (`tests/bdd`, `tests/e2e`, `tests/visual`) and any separately documented heavy family such as `tests/audit_integration`. The hook entry MUST use `pass_filenames = false`.

#### Scenario: Pre-push delegates to canonical integration task
- **WHEN** developer runs `git push`
- **THEN** the pre-push pytest gate executes `uv run task test-integration-parallel`
- **AND** that command resolves to the integration bucket documented in `pyproject.toml`
- **AND** unit tests are NOT re-run (already gated at pre-commit)

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
