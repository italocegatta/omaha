## MODIFIED Requirements

### Requirement: Test coverage report
The system SHALL provide taskipy shortcuts for coverage reporting. Canonical
`uv run task test` SHALL execute unit, integration, audit integration, E2E, BDD,
and retained visual coverage concurrently through the existing Python
supervisor, without changing individual task definitions, lane selection, or
the public Taskipy entrypoint. Within that supervisor only, each canonical lane
MAY execute its exact pytest command directly instead of invoking
`uv run task <lane>`; this exception SHALL NOT apply to serve, database, lint,
coverage, focused-test, or other Taskipy shortcuts.

The six direct lane commands SHALL preserve the current task-defined pytest
paths, markers, coverage flags, `--no-cov` flags, visual `not t32_pruned`
selection, `-vv`, supervisor plugin, output visibility, and governance
deselections. The runner SHALL preserve six concurrent lanes, launch order,
fail-fast, interruption handling, dynamic DB isolation, ownership receipts,
bounded cleanup/reaping, reconciliation, exact skips, and the 300-second
deadline.

Runner SHALL isolate each child in its own process group and use only the
task-defined direct pytest commands for canonical lane children. It SHALL
preflight test-only lane DB targets and SHALL NOT invoke production DB tasks,
migrations, seeds, resets, or arbitrary raw commands. Before launch, runner
SHALL create a ledger entry for every canonical lane and record run-owned
PID/PGID, exact log/timing/resource mapping, owner evidence, and start
timestamp when available. On first child failure it SHALL terminate only
remaining current-run-owned child groups; on SIGINT/SIGTERM it SHALL forward
the signal only to remaining owned groups; after bounded grace it SHALL SIGKILL
only owned survivors; it SHALL always attempt to reap every launched child. A
child that vanishes between polling, signaling, waiting, or cleanup MUST be
recorded as an expected lifecycle race (including PID-not-found,
`NoSuchProcess`, or EPIPE observation) without replacing the original lane,
fail-fast, interruption, or deadline result. Unknown, pre-existing, or
foreign processes, ports, paths, or databases SHALL be preserved and SHALL NOT
become cleanup targets. Runner SHALL return non-zero for lane, cleanup,
receipt, reconciliation, or interruption failure.

Runner SHALL emit one complete run receipt with one lane entry for each of the
six canonical lanes even when launch or cleanup fails. Each lane entry MUST
include lane/task, PID and PGID or explicit null, owned resource mapping,
start/end timestamps, launch/return/signal status, sibling-stop reason when
applicable, cleanup result, residue/foreign-owner evidence, and failure or
timeout telemetry. Run receipt MUST include elapsed wall-clock through
cleanup, deadline/300-second classification, final cleanup verdict, and
six-lane reconciliation evidence. Missing evidence MUST be explicit and SHALL
NOT be treated as success.

The run identity and six placeholder lane records SHALL be durably persisted
before the first child launch. Runner SHALL attempt durable receipt persistence
after launch, child failure, stop/reap cleanup, lane log/timing/DB collection,
reconciliation, and finalization. Serialization or receipt-write errors SHALL
be recorded as `receipt_error` without replacing already captured return,
signal, sibling-stop, cleanup, or timing telemetry; a JSON-safe fallback MAY be
used for serialization failures, and receipt failure SHALL remain non-zero.

For T29, runner SHALL use the current `tests/AUDIT.md` as normative population
source. The canonical expected node set SHALL be the 1,032 blocking node IDs
declared by that audit, with its node checksum and six lane checksums. The 12
owner-approved, versioned T32 cases explicitly outside canonical lanes SHALL
remain excluded from canonical lane membership and SHALL NOT be added to the
canonical expected population. Comparison SHALL include exact node-ID set, lane
membership, checksum, and these exact two skip identities, in order:

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
- **AND** each lane executes the exact direct pytest command mapped from its existing task definition inside the Python supervisor
- **AND** `uv run task test` remains the canonical entrypoint
- **AND** all lane failures make full task fail
- **AND** resulting population matches the current `tests/AUDIT.md` 1,032-node
  blocking manifest/checksum
- **AND** the 12 explicitly outside-lane T32 cases are excluded from canonical
  lane membership
- **AND** receipt reports exactly the two expected skip identities above
- **AND** receipt contains six lane entries, coverage/skips, and cleanup evidence

#### Scenario: Direct mapping preserves current lane semantics
- **WHEN** runner constructs a canonical child command
- **THEN** command starts with `uv run pytest` and contains no `uv run task <lane>` wrapper
- **AND** unit/integration retain their marker, audit ignore, coverage source, and XML report flags
- **AND** audit, E2E, BDD, and visual retain their current paths and `--no-cov` behavior
- **AND** visual retains `-m "not t32_pruned"`
- **AND** runner appends `-s`, `-p test_profile_plugin`, and only existing governance deselections

#### Scenario: Taskipy remains canonical outside lane child boundary
- **WHEN** operator runs serve, DB, lint, coverage, or focused-test workflow
- **THEN** its existing `uv run task <name>` entrypoint remains unchanged
- **AND** no policy wording authorizes replacing those shortcuts with raw commands

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
- **THEN** `uv run task test` remains present, callable, canonical, and mapped
  to all six existing lanes
- **AND** each individual Taskipy lane command remains available and its
  existing test, marker, skip, coverage, DB-safety, receipt, and cleanup
  behavior remains required
- **AND** the individual commands remain `uv run task test-unit`,
  `uv run task test-integration`, `uv run task test-audit-integration`,
  `uv run task test-e2e`, `uv run task test-bdd`, and `uv run task test-visual`
 - **AND** the suspension makes only the parallel canonical full-suite result
  non-blocking for apply, review, and pre-push delivery enforcement
- **AND** no test, lane, marker, skip, xfail, retry, coverage, or command is
  deleted, disabled, weakened, or reclassified
- **AND** reactivation requires resolution of the concurrent dynamic SQLite
  readonly-DB diagnosis and BDD browser-timeout diagnosis, followed by one
  isolated green six-lane `uv run task test` through cleanup in `<=300s`
