# Test Run Ownership Contract

## Purpose

Define bounded ownership, cleanup, and preflight behavior for test runs.

## Requirements

### Requirement: Each test run records owned resources in a ledger

Apply and review workflows SHALL maintain a per-run ownership ledger for every
test resource they create or launch. Each entry MUST identify resource kind and
identity, including PID, PGID, port, log, temporary path, or test DB resource
as applicable, plus owner, owner evidence, start timestamp, end timestamp,
classification, evidence, status, and cleanup result. Ownership SHALL be
established before cleanup can target an entry; observing a matching name,
port, path, PID, DB path, or descendant alone is not ownership proof.

#### Scenario: Owned resource has complete ledger evidence

- **WHEN** current run creates a child process, process group, port, log,
  temporary path, or test DB resource
- **THEN** ledger records its PID/PGID/port/path identity as applicable,
  owner, owner evidence, start timestamp, and current status before cleanup
- **AND** end timestamp, evidence, and cleanup result are recorded when the
  resource exits or cleanup is attempted

#### Scenario: Identity without ownership proof is not cleanable

- **WHEN** preflight observes a PID, PGID, port, path, or DB resource that
  matches a possible test resource but no current-run ledger ownership exists
- **THEN** workflow classifies it as unknown, pre-existing, or foreign
- **AND** workflow does not target it for cleanup

### Requirement: Apply cleanup is bounded and idempotent

Apply SHALL clean only resources recorded as owned by its current run. Cleanup
MUST be idempotent: absent resources and resources already closed or removed are
recorded as no-op outcomes, not rediscovered targets. Apply SHALL include ledger,
cleanup, residue, and ownership evidence in its `READY_FOR_REVIEW` handoff.

#### Scenario: Current-run owned resource is cleaned

- **WHEN** apply finishes focused validation and ledger identifies a resource as
  owned by current run
- **THEN** apply performs bounded cleanup for that ledger entry only
- **AND** records end timestamp, cleanup result, and any remaining residue

#### Scenario: Repeated cleanup does not expand scope

- **WHEN** apply cleanup runs again after owned resource is already absent or
  closed
- **THEN** cleanup records an idempotent no-op
- **AND** it does not search for or terminate similarly named or host-wide
  resources

### Requirement: Review canonical suite requires an isolated runner

Review SHALL run the canonical suite only on an isolated runner. Before launch,
ownership preflight MUST find no relevant unowned process, listener, or
test-temporary resource. A relevant resource MAY be absent or have current-run
ledger ownership evidence; pre-existing, foreign, unknown, or otherwise
unowned state fails isolation. No foreign-resource baseline exception or
allowlist exception is permitted.

#### Scenario: Foreign residue requests isolated environment

- **WHEN** review preflight finds a relevant process, listener, or test-temporary
  resource without current-run ownership evidence
- **THEN** review records inventory, classification, owner evidence, and the
  failed isolation precondition
- **AND** review returns `BLOCKED` before launching `uv run task test` and
  requests an isolated environment
- **AND** review does not adopt, kill, free, delete, mask, or allowlist the
  resource

### Requirement: Review preflight and postflight govern canonical suite

Review SHALL run ownership preflight before the single canonical
`uv run task test` invocation and postflight after lane/process cleanup. Review
SHALL record receipts before its verdict, including ownership evidence, residue
classification, cleanup outcome, canonical command, six lane results, coverage
and skip evidence, fail-fast disposition, elapsed wall-clock through cleanup,
and the 300-second classification.

#### Scenario: Trusted isolated preflight permits one canonical suite

- **WHEN** review preflight confirms isolated runner state, with no relevant
  unowned process, listener, or test-temporary resource, and records current-run
  ownership state
- **THEN** review runs exactly one `uv run task test`
- **AND** postflight records all six lanes, cleanup, residue, and duration
  evidence before APPROVED or CHANGES_REQUESTED

#### Scenario: Untrusted preflight blocks before launch

- **WHEN** review preflight finds unknown, pre-existing, foreign, or
  contradictory resource state
- **THEN** review records diagnosis and BLOCKED decision
- **AND** review does not launch canonical full suite or attempt foreign cleanup

### Requirement: Unknown or foreign residue stops safely

Apply and review SHALL classify observed residue as owned-current-run,
pre-existing, foreign, unknown, absent, or owned-cleaned. Unknown,
pre-existing, foreign, or incomplete cleanup state SHALL block the affected
handoff/verdict and escalate with evidence. Workflow SHALL preserve any known
original lane/fail-fast/deadline failure when PID-not-found, PID reuse, EPIPE,
or vanished-child races occur; it SHALL not convert incomplete cleanup into
success.

#### Scenario: Foreign process or port is preserved

- **WHEN** preflight or postflight finds a process or port owned by another
  run/user, or ownership cannot be established
- **THEN** workflow records foreign or unknown residue with PID/PGID/port,
  timestamps, and evidence
- **AND** workflow stops without killing the process, freeing the port, or
  deleting its files

#### Scenario: Vanished child preserves causal failure

- **WHEN** a ledger child disappears before signal, wait, or cleanup and the
  operation reports PID-not-found or EPIPE
- **THEN** workflow records the race and remaining ownership evidence
- **AND** it preserves original lane/fail-fast/deadline result and blocks when
  receipt state is not trustworthy

### Requirement: Cleanup never uses broad host actions

Ownership protocol SHALL prohibit broad kill, process-name or pattern-based
kill, host-wide port cleanup, indiscriminate descendant termination, adoption
of foreign resources, and cleanup of resources not recorded as current-run
owned. These prohibitions SHALL not remove or weaken the canonical six lanes,
fail-fast behavior, coverage-producing lanes, retained tests/skips, taskipy
entrypoints, or the absolute 300-second suite ceiling.

#### Scenario: Name-based cleanup is rejected

- **WHEN** an operator or workflow proposes killing all processes matching a
  name, command fragment, or test label
- **THEN** protocol rejects action and requires ledger-scoped ownership evidence
- **AND** no process outside current-run owned entries is terminated

#### Scenario: Canonical suite contract remains unchanged

- **WHEN** ownership preflight/postflight is added around canonical review
- **THEN** unit, integration, audit integration, e2e, bdd, and visual lanes,
  fail-fast, coverage, all tests/skips, taskipy entrypoints, and 300-second
  ceiling remain required
- **AND** ownership checks do not authorize lane removal, masking, or duration
  relaxation
