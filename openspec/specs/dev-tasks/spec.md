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
The system SHALL provide taskipy shortcuts for coverage reporting. Canonical
`uv run task test` SHALL execute unit, integration, audit integration, E2E, BDD,
and retained visual coverage concurrently through taskipy-owned runner, without
changing individual task entrypoints or selection.

Runner SHALL isolate each child in own process group and use only taskipy task
entrypoints. It SHALL preflight test-only lane DB targets and SHALL NOT invoke
production DB tasks, migrations, seeds, resets, or raw pytest commands. On first
child failure it SHALL terminate remaining child groups; on SIGINT/SIGTERM it
SHALL forward signal to remaining child groups; after bounded grace it SHALL
SIGKILL survivors; it SHALL always reap children. It SHALL return non-zero for
lane, cleanup, or interruption failure.

For T29, runner SHALL compare every canonical execution against committed
immutable post-removal 1,043-node manifest/checksum. Comparison SHALL include
exact node-ID set, lane membership, checksum, and two exact skip identities.
Eighteen focused T29 harness nodes remain deliberate coverage. Runner SHALL NOT
obtain match through deletion, skip, xfail, disable, or lane reduction, except
historical mobile removal and exact owner-authorized desktop removal documented
in `visual-regression-baseline`.

#### Scenario: Full task concurrently preserves complete coverage
- **WHEN** operator runs `uv run task test`
- **THEN** unit, integration, audit integration, E2E, BDD, and visual lanes run
- **AND** each lane uses existing canonical taskipy entrypoint
- **AND** all lane failures make full task fail
- **AND** resulting population matches 1,043-node manifest/checksum

#### Scenario: Interrupted full task reaps browser and server children
- **WHEN** operator interrupts `uv run task test` with SIGINT or SIGTERM
- **THEN** runner forwards signal to every running lane process group
- **AND** waits bounded grace then kills only surviving groups
- **AND** reaps every child before returning non-zero

#### Scenario: Full task refuses non-test database target
- **WHEN** full-task runner detects lane database target outside recognized test paths
- **THEN** it fails before starting children
- **AND** it does not access production database

#### Scenario: Run with coverage
- **WHEN** user runs `uv run task coverage`
- **THEN** pytest runs unit + integration tests with `--cov=src/omaha --cov-report=term-missing --cov-report=xml:reports/coverage.xml` and shows missing lines per module

#### Scenario: Unit tests produce coverage via task
- **WHEN** user runs `uv run task test-unit`
- **THEN** pytest runs with `--cov=src/omaha` flag explicitly in the taskipy command

#### Scenario: Integration tests produce coverage via task
- **WHEN** user runs `uv run task test-integration`
- **THEN** pytest runs with `--cov=src/omaha` flag explicitly in the taskipy command

#### Scenario: Browser tasks do not produce coverage
- **WHEN** user runs `uv run task test-e2e`, `uv run task test-bdd`, or `uv run task test-visual`
- **THEN** pytest runs with `--no-cov` flag and no `reports/coverage.xml` is written

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

### Requirement: Git-hook installation
The system SHALL provide a taskipy shortcut for installing the prek git hooks into `.git/hooks/`.

#### Scenario: Install prek hooks
- **WHEN** user runs `uv run task prek-install`
- **THEN** `prek install` populates `.git/hooks/` with the configured `pre-commit`, `pre-push`, and `commit-msg` hooks
- **AND** the hooks are active for subsequent `git commit` and `git push` invocations

#### Scenario: Install is idempotent
- **WHEN** user runs `uv run task prek-install` more than once
- **THEN** prek updates the existing hooks in place (does not error or duplicate)

### Requirement: Housekeeping purge of debug artefacts
Debug artefacts (`data/probe*.db`, `data/test_*.db`, `pytestdebug.log`, `data/seed/fixtures/auto_class.csv`) SHALL be candidate for deletion during housekeeping slices. The canonical live database `data/portfolio.db` SHALL remain untouched. The `.gitignore` rules SHALL continue to cover these patterns so they do not re-enter the working tree after `git clean`.

#### Scenario: Debug artefacts are gitignored
- **WHEN** developer inspects `.gitignore`
- **THEN** `data/*`, `*.log` rules keep debug artefacts out of the working tree

#### Scenario: Live portfolio DB is preserved
- **WHEN** housekeeping slice runs purge
- **THEN** `data/portfolio.db` is preserved (gitignored but excluded from the purge path)
