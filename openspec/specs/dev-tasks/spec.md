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
and retained visual coverage concurrently through the existing Python
supervisor, without changing individual task definitions, lane selection, or
the public Taskipy entrypoint. Within that supervisor only, each canonical lane
MAY execute its exact pytest command directly instead of invoking
`uv run task <lane>`; this exception SHALL NOT apply to serve, database, lint,
coverage, focused-test, or other Taskipy shortcuts.

Runner SHALL isolate each child in its own process group and use only the
task-defined direct pytest commands for canonical lane children. It SHALL
preflight test-only lane DB targets and SHALL NOT invoke production DB tasks,
migrations, seeds, resets, or arbitrary raw commands.
Before launch, runner SHALL create a ledger entry for every canonical lane and
record run-owned PID/PGID, exact log/timing/resource mapping, owner evidence,
and start timestamp when available. On first child failure it SHALL terminate
only remaining current-run-owned child groups; on SIGINT/SIGTERM it SHALL
forward the signal only to remaining owned groups; after bounded grace it SHALL
SIGKILL only owned survivors; it SHALL always attempt to reap every launched
child. A child that vanishes between polling, signaling, waiting, or cleanup
MUST be recorded as an expected lifecycle race (including PID-not-found,
`NoSuchProcess`, or EPIPE observation) without replacing the original lane,
fail-fast, interruption, or deadline result. Unknown, pre-existing, or foreign
processes, ports, paths, or databases SHALL be preserved and SHALL NOT become
cleanup targets. Runner SHALL return non-zero for lane, cleanup, receipt,
reconciliation, or interruption failure.

Runner SHALL emit one complete run receipt with one lane entry for each of the
six canonical lanes even when launch or cleanup fails. Each lane entry MUST
include lane/task, PID and PGID or explicit null, owned resource mapping,
start/end timestamps, launch/return/signal status, sibling-stop reason when
applicable, cleanup result, residue/foreign-owner evidence, and failure or
timeout telemetry. Run receipt MUST include elapsed wall-clock through cleanup,
deadline/300-second classification, final cleanup verdict, and six-lane
reconciliation evidence. Missing evidence MUST be explicit and SHALL NOT be
treated as success.

The run identity and six placeholder lane records SHALL be durably persisted
before the first child launch. Runner SHALL attempt durable receipt persistence
after launch, child failure, stop/reap cleanup, lane log/timing/DB collection,
reconciliation, and finalization. Serialization or receipt-write errors SHALL
be recorded as `receipt_error` without replacing already captured return,
signal, sibling-stop, cleanup, or timing telemetry; a JSON-safe fallback MAY be
used for serialization failures, and receipt failure SHALL remain non-zero.

For T29, runner SHALL use the current `tests/AUDIT.md` as normative population
source. The canonical expected node set SHALL be the 1,032 blocking node IDs
declared by that audit, with node checksum
`31d93ee09ba067c1370cd36392d5af4abeaeba18f2c41402b28b83d3d3022ea1` and these
lane checksums: unit
`146f063ff2bf86b234703cbc65fa0942351350e65d079ee733d88698fd955640`,
integration
`bc8ecf8c2c4c867b591465081559790bb10c76c5161db8e7016c5ed8c1bbc894`, audit
`0d0832484bd349cb35aa77573321597780721c1a9f6df2ca95be22fc22d2eab6`, e2e
`41e5b405720b4765dc64e8ed7f414f9a7c397f36f315568011212316b86cc54c`, bdd
`a8543643bbf371fcd508c4822a79aa609b0abdd6b1e2a74a184f629e807e57db`, and
visual
`d7481c04e1d95966d4965284d324c67dbcda21923c080932a1801f011a03c031`.
The 12 owner-approved, versioned T32 cases explicitly outside canonical lanes
SHALL remain excluded from canonical lane membership and SHALL NOT be added to
the canonical expected population. Comparison SHALL include the exact node-ID
set, lane membership, checksums, and these exact skip identities, in order:

1. `tests/test_dockerfile.py::test_docker_build_pro_image_succeeds`
2. `tests/test_dockerfile.py::test_docker_run_pro_image_runs_as_omaha_user`

The two identities are expected skip outcomes, not population exclusions. Any
other skip identity, missing skip evidence, or count/checksum conflict with
current `tests/AUDIT.md` SHALL fail acceptance and SHALL be recorded exactly;
implementation SHALL NOT invent a count. Eighteen focused T29 harness nodes
remain deliberate coverage. Runner SHALL NOT obtain match through deletion,
new skip, xfail, disable, or lane reduction, except historical mobile removal
and exact owner-authorized desktop removal documented in
`visual-regression-baseline`.

#### Scenario: Full task concurrently preserves complete coverage
- **WHEN** operator runs `uv run task test`
- **THEN** unit, integration, audit integration, E2E, BDD, and visual lanes run
- **AND** each lane executes exact direct pytest command mapped from its existing
  task definition inside Python supervisor
- **AND** `uv run task test` remains canonical public entrypoint
- **AND** all lane failures make full task fail
- **AND** resulting population matches the current `tests/AUDIT.md` 1,032-node
  blocking manifest/checksum and lane checksums
- **AND** the 12 explicitly outside-lane T32 cases are excluded from canonical
  lane membership
- **AND** receipt reports exactly these two expected skip identities:
  `tests/test_dockerfile.py::test_docker_build_pro_image_succeeds` and
  `tests/test_dockerfile.py::test_docker_run_pro_image_runs_as_omaha_user`
- **AND** receipt contains six lane entries, coverage/skips, and cleanup evidence

#### Scenario: Vanished child preserves causal failure
- **WHEN** owned lane child disappears before signal, wait, or cleanup and
  lifecycle observation reports PID-not-found, `NoSuchProcess`, or EPIPE
- **THEN** runner records race, PID/PGID evidence, and cleanup result for lane
- **AND** original lane/fail-fast/interruption/deadline result remains primary
- **AND** incomplete or untrusted cleanup returns non-zero rather than green

#### Scenario: Owned descendant survivor is bounded
- **WHEN** current-run lane process group has a descendant still alive after grace
- **THEN** runner escalates only that owned process group to SIGKILL
- **AND** reaps launched child and records survivor/escalation evidence
- **AND** no process outside owned group is signaled

Each lane SHALL receive the run/lane identity and an exact pytest temporary-root
boundary and publish that path in a lane-scoped receipt. Runner SHALL reconcile
only canonical runner-declared exact paths: an exact current-run receipt match
with proven ownership and bounded cleanup is `owned-cleaned`; an exact absent
path is `absent`. Missing, mismatched, pre-existing, foreign, contradictory, or
incomplete evidence inside the declared boundary SHALL remain untouched and be
untrusted/non-zero. Paths outside declared boundaries SHALL be preserved as
non-target and SHALL NOT block alone. Runner SHALL NOT discover `pytest-of-*`,
scan/delete broad `/tmp`, or infer parent cleanup targets.

#### Scenario: Foreign process or port is preserved
- **WHEN** cleanup or reconciliation observes a process, port, path, or DB resource without current-run ownership evidence
- **THEN** runner classifies it foreign, pre-existing, or unknown
- **AND** runner does not kill, free, delete, adopt, or broadly search for it
- **AND** receipt records residue and cleanup as untrusted/nonzero

#### Scenario: Fail-fast sibling stop is attributable
- **WHEN** one launched lane exits nonzero before sibling lanes complete
- **THEN** runner records first failure before stopping remaining owned groups
- **AND** every six-lane receipt identifies sibling-stop signal and reason
- **AND** final exit preserves first failure unless parent interruption has priority

#### Scenario: Partial launch still emits complete receipt
- **WHEN** a canonical lane launch fails after earlier lanes launched
- **THEN** runner records launch error and null identity for failed lane
- **AND** receipt still contains all six lanes and cleanup evidence for launched lanes
- **AND** runner returns nonzero without inventing a successful lane result

#### Scenario: Deadline includes bounded cleanup
- **WHEN** canonical execution reaches its stop deadline or cleanup causes total elapsed time to exceed 300 seconds
- **THEN** runner records deadline trigger, timeout code, cleanup state, and elapsed wall-clock through cleanup
- **AND** runner returns `TIMEOUT_EXIT_CODE`
- **AND** it does not relax ceiling, omit lanes, or rerun full suite

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

#### Scenario: Canonical full-suite gate is maintenance-suspended
- **WHEN** owner-authorized I10 policy state is `maintenance-suspended`
- **THEN** `uv run task test` remains present, callable, canonical, and mapped to all six existing lanes
- **AND** each individual Taskipy lane command remains available with existing selection, skips, coverage, DB-safety, receipt, and cleanup behavior
- **AND** suspension makes only parallel canonical full-suite result non-blocking for apply, review, and pre-push enforcement
- **AND** no test, lane, marker, skip, xfail, retry, coverage, or command is deleted, disabled, weakened, or reclassified
- **AND** reactivation requires resolution of concurrent dynamic SQLite readonly-DB and BDD browser-timeout diagnosis followed by one isolated green six-lane run through cleanup in `<=300s`

#### Scenario: Current-run pytest temp root reconciles exactly

- **WHEN** lane publishes an exact pytest temp root under its run/lane boundary
- **THEN** runner records ownership and post-exit state as `absent` or `owned-cleaned`
- **AND** mismatched, pre-existing, foreign, or contradictory roots remain untouched

#### Scenario: Out-of-bound temporary observation is non-target

- **WHEN** preflight observes a temporary path outside every declared boundary
- **THEN** runner records it as preserved/non-target without cleanup
- **AND** runner does not adopt, delete, allowlist, or infer broad cleanup

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
