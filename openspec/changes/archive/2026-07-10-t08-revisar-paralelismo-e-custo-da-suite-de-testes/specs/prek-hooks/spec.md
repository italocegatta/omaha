## MODIFIED Requirements

### Requirement: Pytest unit gate on pre-commit
The pre-commit stage SHALL run `uv run task test-unit` as a blocking gate. The hook entry MUST delegate through taskipy with `pass_filenames = false` so marker selection, command text, and help text stay single-sourced in `pyproject.toml`.

#### Scenario: Unit task passes and commit lands
- **WHEN** all tests in `uv run task test-unit` pass
- **THEN** the pre-commit hook reports success
- **AND** the `git commit` proceeds

#### Scenario: Unit task fails and commit is blocked
- **WHEN** one or more tests in `uv run task test-unit` fail
- **THEN** the pre-commit hook reports failure with the failing test names
- **AND** the `git commit` is blocked

### Requirement: Pytest full gate on pre-push
The pre-push stage SHALL run the canonical non-browser gate through named task commands, not through an ad hoc raw `uv run pytest ...` expression. The selected coverage MUST match the documented local buckets for unit and integration while excluding browser-backed families (`tests/bdd`, `tests/e2e`, `tests/visual`) and any separately documented heavy family such as `tests/audit_integration`. The hook entry MUST use `pass_filenames = false`.

#### Scenario: Pre-push delegates to canonical tasks
- **WHEN** developer runs `git push`
- **THEN** the pre-push pytest gate executes one or more `uv run task ...` commands
- **AND** those commands resolve to the same unit and integration buckets documented in `pyproject.toml`

#### Scenario: Browser suites stay out of the pre-push gate
- **WHEN** developer runs `git push`
- **THEN** the pre-push pytest gate does not collect `tests/bdd/`, `tests/e2e/`, or `tests/visual/`
- **AND** the push is not blocked on a browser-backed live-server workflow

### Requirement: BDD scenarios run via task test-bdd, not pre-push
BDD scenarios under `tests/bdd/` MUST run via the dedicated `task test-bdd` bucket in local verification and in CI. They MUST NOT run in the pre-push pytest gate because the suite depends on a live server and currently remains serial by contract.

#### Scenario: BDD scenarios are excluded from pre-push pytest
- **WHEN** developer runs `git push`
- **THEN** the pre-push pytest gate does not collect any scenario from `tests/bdd/`
- **AND** the hook comments point the operator at `task test-bdd` as the canonical path

#### Scenario: BDD scenarios run through the same named bucket in CI
- **WHEN** CI executes the BDD job or the developer runs `uv run task test-bdd`
- **THEN** the suite runs through the same named task entrypoint
- **AND** the job reflects the serial BDD bucket contract instead of a separate ad hoc pytest command
