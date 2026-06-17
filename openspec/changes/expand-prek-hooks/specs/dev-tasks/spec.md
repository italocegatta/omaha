# dev-tasks Specification (delta)

## Purpose

Taskipy shortcut tasks for development workflow automation — covering Docker, database operations, code quality, project onboarding, and git-hook installation.

## ADDED Requirements

### Requirement: Git-hook installation
The system SHALL provide a taskipy shortcut for installing the prek git hooks into `.git/hooks/`.

#### Scenario: Install prek hooks
- **WHEN** user runs `uv run task prek-install`
- **THEN** `prek install` populates `.git/hooks/` with the configured `pre-commit`, `pre-push`, and `commit-msg` hooks
- **AND** the hooks are active for subsequent `git commit` and `git push` invocations

#### Scenario: Install is idempotent
- **WHEN** user runs `uv run task prek-install` more than once
- **THEN** prek updates the existing hooks in place (does not error or duplicate)
