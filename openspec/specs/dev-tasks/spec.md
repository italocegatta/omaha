# dev-tasks Specification

## Purpose
Taskipy shortcut tasks for development workflow automation — covering Docker, database operations, code quality, and project onboarding.

## Requirements

### Requirement: DB migration inspection commands
The system SHALL provide taskipy shortcuts for inspecting Alembic migration state — current revision, full history, and rollback.

#### Scenario: Show current revision
- **WHEN** user runs `uv run task db-current`
- **THEN** output shows the current Alembic revision head

#### Scenario: Show migration history
- **WHEN** user runs `uv run task db-history`
- **THEN** output shows the full Alembic migration timeline

#### Scenario: Rollback one migration
- **WHEN** user runs `uv run task db-downgrade`
- **THEN** Alembic reverts the last migration

### Requirement: Docker dev stack shortcuts
The system SHALL provide taskipy shortcuts for the dev Docker Compose stack (docker-compose.yml) — build, up, down.

#### Scenario: Build dev image
- **WHEN** user runs `uv run task docker-build`
- **THEN** Docker Compose builds the dev image from docker-compose.yml

#### Scenario: Start dev stack
- **WHEN** user runs `uv run task docker-up`
- **THEN** Docker Compose starts the dev stack in detached mode

#### Scenario: Stop dev stack
- **WHEN** user runs `uv run task docker-down`
- **THEN** Docker Compose stops and removes the dev containers

### Requirement: Docker prod stack shortcuts
The system SHALL provide taskipy shortcuts for the production Docker Compose stack (prod.yml) — up, down, logs, rebuild.

#### Scenario: Start prod stack
- **WHEN** user runs `uv run task prod-up`
- **THEN** Docker Compose starts the prod stack from prod.yml in detached mode

#### Scenario: Stop prod stack
- **WHEN** user runs `uv run task prod-down`
- **THEN** Docker Compose stops and removes the prod containers

#### Scenario: Follow prod logs
- **WHEN** user runs `uv run task prod-logs`
- **THEN** Docker Compose streams logs from all prod services

#### Scenario: Rebuild and deploy prod
- **WHEN** user runs `uv run task prod-rebuild`
- **THEN** Docker builds the prod image and restarts the stack

### Requirement: Test coverage report
The system SHALL provide a taskipy shortcut for running tests with coverage reporting, with `pytest-cov` added to dev dependencies.

#### Scenario: Run with coverage
- **WHEN** user runs `uv run task coverage`
- **THEN** pytest runs with coverage on `src/omaha` and shows missing lines per module

### Requirement: Lockfile update
The system SHALL provide a taskipy shortcut for upgrading all dependencies within existing version constraints.

#### Scenario: Upgrade dependencies
- **WHEN** user runs `uv run task update`
- **THEN** uv syncs with --upgrade flag, updating uv.lock

### Requirement: SECRET_KEY generation
The system SHALL provide a taskipy shortcut for generating a cryptographically random SECRET_KEY for .env configuration.

#### Scenario: Generate secret key
- **WHEN** user runs `uv run task secret-key`
- **THEN** a 50-char URL-safe base64 token is printed to stdout
