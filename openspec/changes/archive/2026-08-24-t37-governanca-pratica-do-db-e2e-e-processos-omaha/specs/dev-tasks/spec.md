## ADDED Requirements

### Requirement: Canonical runner emits actionable governance receipts

The canonical `uv run task test` runner SHALL retain one complete run receipt
with one entry for each of the six lanes when preflight, launch, cleanup,
reconciliation, or receipt persistence fails. Each applicable lane entry SHALL
include run/lane identity, parent PID, child PID, PGID, exact command and cwd,
port and DB mapping, ownership classification, preflight/recreate disposition,
restart phases/signals, timestamps, cleanup result, residue evidence, and final
return status. Missing or contradictory evidence SHALL remain non-zero and
shall not be reported as green.

#### Scenario: Preflight block still explains all lanes

- **WHEN** canonical preflight finds a foreign listener or untrusted resource
  before any child launch
- **THEN** runner emits six explicit lane placeholders plus preflight identity,
  classification, and blocked reason
- **AND** no lane is marked launched, no resource is adopted, and exit code is
  non-zero

#### Scenario: Recreate and cleanup evidence survives finalization failure

- **WHEN** an E2E DB is recreated or a lane cleanup/finalization step fails
- **THEN** run receipt preserves recreate disposition, `adopted` flag, lane
  identity, original lane/fail-fast/deadline result, and receipt error
- **AND** a missing receipt field cannot convert the run to success

### Requirement: Canonical runner preserves lane and duration contracts during recovery

Governance preflight, graceful restart, stale-process blocking, and exact E2E DB
recreation SHALL not change the six canonical lanes, taskipy entrypoints,
fail-fast behavior, coverage-producing lanes, retained tests/skips, or absolute
300-second wall-clock ceiling. Recovery SHALL not rerun a full lane merely to
repair ownership or telemetry.

#### Scenario: Owned survivor is bounded without lane relaxation

- **WHEN** an owned lane child survives graceful grace during fail-fast,
  interruption, or deadline cleanup
- **THEN** runner escalates only its recorded PGID, reaps the child, records
  cleanup evidence, and returns the causal non-zero result when cleanup is
  untrusted
- **AND** no lane, test, skip, coverage path, or duration rule is removed

#### Scenario: Foreign residue preserves canonical gate

- **WHEN** postflight observes foreign or unknown process/port/DB residue
- **THEN** runner preserves it, records untrusted cleanup, and returns
  non-zero
- **AND** it does not free the resource or claim six-lane green evidence
