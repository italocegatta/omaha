## MODIFIED Requirements

### Requirement: Test coverage report
The system SHALL provide taskipy shortcuts for coverage reporting. Canonical
`uv run task test` SHALL execute unit, integration, audit integration, E2E, BDD,
and retained visual coverage concurrently through taskipy-owned runner, without
changing individual task entrypoints or selection.

Runner SHALL isolate each child in its own process group and use only taskipy
task entrypoints. It SHALL preflight test-only lane DB targets and SHALL NOT
invoke production DB tasks, migrations, seeds, resets, or raw pytest commands.
Before launch, runner SHALL create a run identity and ledger entry for every
canonical lane. Each launched entry SHALL record runner parent PID, child PID,
actual PGID, exact log/timing/resource mapping, owner evidence, and start
timestamp. Runner SHALL record bounded launch, poll, signal, wait, exit, and
return-code observations tied to the same run/lane ID. On first child failure
it SHALL terminate only remaining current-run-owned child groups; on
SIGINT/SIGTERM it SHALL forward the signal only to remaining owned groups; after
bounded grace it SHALL SIGKILL only owned survivors; it SHALL always attempt to
reap every launched child. A child that vanishes between polling, signaling,
waiting, or cleanup MUST be recorded as an expected lifecycle race (including
PID-not-found, `NoSuchProcess`, or EPIPE observation) without replacing the
original lane, fail-fast, interruption, or deadline result. Unknown,
pre-existing, or foreign processes, ports, paths, databases, or temporary roots
SHALL be preserved and SHALL NOT become cleanup targets. Runner SHALL return
non-zero for lane, cleanup, receipt, reconciliation, ownership, or interruption
failure.

Each lane SHALL receive the run/lane identity and an exact pytest temporary-root
boundary. The lane SHALL publish its actual pytest base temporary path in a
lane-scoped receipt. Runner SHALL define cleanup relevance only from canonical
runner-declared exact run/lane paths and reconcile only those declared paths:
an exact current-run receipt match with proven ownership and bounded cleanup
SHALL be `owned-cleaned`, while an exact absent path SHALL be `absent`.
Declaration membership is the sole relevance test; pathname, parent directory,
and host-wide observations SHALL NOT expand the cleanup set.
Missing, mismatched, pre-existing, foreign, contradictory, or incomplete
temporary evidence inside the declared boundary SHALL be classified as
`unknown`, `foreign`, or `pre-existing`, preserved, and treated as
untrusted/non-zero. A temporary path observed outside every declared boundary
SHALL be recorded as preserved/non-target and SHALL NOT block acceptance alone.
Runner SHALL NOT discover `pytest-of-*`, scan or delete broad `/tmp` paths, or
infer a parent cleanup target.

Runner SHALL emit one complete run receipt with one lane entry for each of the
six canonical lanes even when launch or cleanup fails. Each lane entry MUST
include lane/task, parent PID, child PID and PGID or explicit null, lifecycle
observations, owned resource mapping, start/end timestamps, launch/return/signal
status, sibling-stop reason when applicable, cleanup result, residue/foreign-
owner evidence, exact pytest temp receipt, and failure or timeout telemetry.
Run receipt MUST include elapsed wall-clock through cleanup,
deadline/300-second classification, final cleanup verdict, current-run temp
reconciliation, and six-lane reconciliation evidence. Missing evidence MUST be
explicit and SHALL NOT be treated as success.

The run identity and six placeholder lane records SHALL be durably persisted
before the first child launch. Runner SHALL attempt durable receipt persistence
after launch, child failure, stop/reap cleanup, lane log/timing/DB/temp
collection, reconciliation, and finalization. Serialization or receipt-write
errors SHALL be recorded as `receipt_error` without replacing already captured
return, signal, sibling-stop, cleanup, or timing telemetry; a JSON-safe fallback
MAY be used for serialization failures, and receipt failure SHALL remain
non-zero.

For T29, runner SHALL compare every canonical execution against the committed
current manifest/checksum. Comparison SHALL include exact node-ID set, lane
membership, checksum, and two exact skip identities. Focused T29 harness nodes
remain deliberate coverage. Runner SHALL NOT obtain match through deletion,
skip, xfail, disable, or lane reduction, except existing owner-authorized cases
documented by their owning spec.

#### Scenario: Full task concurrently preserves complete coverage

- **WHEN** operator runs `uv run task test`
- **THEN** unit, integration, audit integration, E2E, BDD, and visual lanes run
- **AND** each lane uses existing canonical taskipy entrypoint
- **AND** all lane failures make full task fail
- **AND** resulting population matches the committed current manifest/checksum
- **AND** receipt contains six lane entries, coverage/skips, lifecycle, temp,
  and cleanup evidence

#### Scenario: PID lineage and vanished child preserve causal failure

- **WHEN** an owned lane child disappears before signal, wait, or cleanup and
  lifecycle observation reports PID-not-found, `NoSuchProcess`, or EPIPE
- **THEN** runner records run/lane ID, parent PID, child PID, PGID, phase, race,
  and cleanup result
- **AND** original lane/fail-fast/interruption/deadline result remains primary
- **AND** incomplete or untrusted cleanup returns non-zero rather than green

#### Scenario: Owned descendant survivor is bounded

- **WHEN** current-run lane process group has a descendant still alive after
  grace
- **THEN** runner escalates only that recorded owned process group to SIGKILL
- **AND** reaps launched child and records survivor/escalation evidence
- **AND** no process outside owned group is signaled

#### Scenario: Foreign process, port, or temporary root is preserved

- **WHEN** cleanup or reconciliation observes a process, port, path, DB, or
  temporary root without current-run ownership evidence
- **THEN** runner classifies it foreign, pre-existing, or unknown
- **AND** runner does not kill, free, delete, adopt, scan broadly, or allowlist it
- **AND** receipt records residue and cleanup as untrusted/nonzero

#### Scenario: Current-run pytest temp root reconciles exactly

- **WHEN** lane publishes an exact pytest temp root under its run/lane boundary
- **THEN** runner records its owner evidence and post-exit state
- **AND** an absent root is `absent` or an owned exact root is `owned-cleaned`
- **AND** a missing, mismatched, pre-existing, foreign, or contradictory root
  inside the declared boundary remains untouched and makes receipt
  reconciliation untrusted

#### Scenario: Out-of-bound temporary observation is non-target

- **WHEN** preflight observes a temporary path outside every canonical
  runner-declared run/lane boundary, such as pre-existing `/tmp/pytest-of-juca`
- **THEN** runner records it as preserved and non-target
- **AND** it does not block acceptance by itself
- **AND** runner does not adopt, delete, allowlist, discover by `pytest-of-*`, or
  infer a parent/broad `/tmp` cleanup target

#### Scenario: Declared-boundary mismatch or foreign root blocks untouched

- **WHEN** a declared run/lane boundary has a mismatched, unknown, foreign, or
  contradictory temporary path or receipt
- **THEN** runner preserves that exact resource and records untrusted/non-zero
  reconciliation
- **AND** runner does not clean or adopt it

#### Scenario: Fail-fast sibling stop is attributable

- **WHEN** one launched lane exits nonzero before sibling lanes complete
- **THEN** runner records first failure before stopping remaining owned groups
- **AND** every six-lane receipt identifies sibling-stop signal and reason
- **AND** final exit preserves first failure unless parent interruption has priority

#### Scenario: Partial launch still emits complete receipt

- **WHEN** a canonical lane launch fails after earlier lanes launched
- **THEN** runner records launch error and null identity for failed lane
- **AND** receipt still contains all six lanes and cleanup evidence for launched
  lanes
- **AND** runner returns nonzero without inventing a successful lane result

#### Scenario: Deadline includes bounded cleanup

- **WHEN** canonical execution reaches its stop deadline or cleanup causes total
  elapsed time to exceed 300 seconds
- **THEN** runner records deadline trigger, timeout code, cleanup state, and
  elapsed wall-clock through cleanup
- **AND** runner returns `TIMEOUT_EXIT_CODE`
- **AND** it does not relax ceiling, omit lanes, or rerun full suite

#### Scenario: Interrupted full task reaps browser and server children

- **WHEN** operator interrupts `uv run task test` with SIGINT or SIGTERM
- **THEN** runner forwards signal to every running lane-owned process group
- **AND** waits bounded grace then kills only surviving owned groups
- **AND** reaps every child before returning non-zero

#### Scenario: Full task refuses non-test database target

- **WHEN** full-task runner detects lane database target outside recognized test paths
- **THEN** it fails before starting children
- **AND** it does not access production database

#### Scenario: Run with coverage

- **WHEN** user runs `uv run task coverage`
- **THEN** pytest runs unit + integration tests with `--cov=src/omaha
  --cov-report=term-missing --cov-report=xml:reports/coverage.xml` and shows
  missing lines per module

#### Scenario: Unit tests produce coverage via task

- **WHEN** user runs `uv run task test-unit`
- **THEN** pytest runs with `--cov=src/omaha` flag explicitly in taskipy command

#### Scenario: Integration tests produce coverage via task

- **WHEN** user runs `uv run task test-integration`
- **THEN** pytest runs with `--cov=src/omaha` flag explicitly in taskipy command

#### Scenario: Browser tasks do not produce coverage

- **WHEN** user runs `uv run task test-e2e`, `uv run task test-bdd`, or
  `uv run task test-visual`
- **THEN** pytest runs with `--no-cov` flag and no `reports/coverage.xml` is
  written
