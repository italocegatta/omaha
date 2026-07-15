## MODIFIED Requirements

### Requirement: Stage-split hook layout
The prek configuration SHALL split hooks across three stages: `pre-commit` for code-correction hooks (format, lint fix, whitespace, EOF) plus file-sanity checks and the unit-test gate; `pre-push` for validation-only hooks (ruff check without fix, integration tests, commitizen, uv-lock); `commit-msg` for commit-message format validation.

#### Scenario: Pre-commit stage corrects code and gates commit
- **WHEN** developer runs `git commit`
- **THEN** the pre-commit stage hooks run in priority order
- **AND** mutating hooks (`ruff-format`, `ruff --fix`, `trailing-whitespace`, `end-of-file-fixer`) may modify tracked files to correct formatting and lint issues
- **AND** the corrected code is included in the commit

#### Scenario: Pre-push stage validates only, never modifies
- **WHEN** developer runs `git push`
- **THEN** the pre-push stage hooks run in priority order
- **AND** no hook in this stage modifies any tracked file (except `uv-lock` for lockfile sync)
- **AND** `ruff` runs WITHOUT `--fix` — it only validates, failing if issues remain

#### Scenario: Commit-msg stage validates message format
- **WHEN** developer runs `git commit -m "..."` or `git commit` (with editor)
- **THEN** the `commitizen` hook validates the message against Conventional Commits format

### Requirement: Mutating Python tooling on pre-commit
The pre-commit stage SHALL run `ruff-format` (priority 1), `ruff --fix` (priority 2), `trailing-whitespace` (priority 3), and `end-of-file-fixer` (priority 3). These hooks correct code before the commit is finalized, so the committed code is already clean.

#### Scenario: Ruff format runs before ruff fix
- **WHEN** developer runs `git commit`
- **THEN** `ruff-format` runs first (priority 1)
- **AND** `ruff --fix` runs second (priority 2)
- **AND** `trailing-whitespace` and `end-of-file-fixer` run third (priority 3)
- **AND** `pytest-unit` runs after all code-correction hooks (priority 4)

#### Scenario: Mutating hooks amend the staged commit
- **WHEN** a mutating hook modifies a tracked file
- **THEN** the modified file is included in the commit automatically (pre-commit amends)
- **AND** the developer does not need to re-commit

### Requirement: Validation-only ruff on pre-push
The pre-push stage SHALL run `ruff` WITHOUT the `--fix` flag as a validation gate. If any ruff rule is violated, the push is blocked. This catches issues that slipped through pre-commit (e.g., `--no-verify` bypass).

#### Scenario: Ruff validation passes
- **WHEN** all Python files pass `ruff check` (no violations)
- **THEN** the pre-push ruff hook reports success
- **AND** the push proceeds

#### Scenario: Ruff validation fails
- **WHEN** one or more Python files have ruff violations
- **THEN** the pre-push ruff hook reports the violations
- **AND** the push is blocked

## REMOVED Requirements

### Requirement: Mutating Python tooling on pre-push
**Reason**: Mutating hooks (`ruff-format`, `ruff --fix`, `trailing-whitespace`, `end-of-file-fixer`) moved to pre-commit stage. Pre-push is now validate-only.
**Migration**: Use the new "Mutating Python tooling on pre-commit" requirement. The "Validation-only ruff on pre-push" requirement covers the non-mutating ruff check.
