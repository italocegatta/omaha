## MODIFIED Requirements

### Requirement: Shared test-server lifecycle preserves lane ownership

The shared test-server lifecycle helper SHALL provide deterministic startup and
teardown for BDD/e2e/visual callers: it SHALL compose the requested lane DB
environment, record run/lane-linked parent PID, child PID, actual PGID, launch,
readiness, port, log, exit, and teardown evidence, detect child startup failure
rather than accepting an unrelated listener, expose abnormal lifecycle
evidence, and reap the spawned child on exit. Existing hosts, ports, browser
selection, caller DB paths, and browser scopes remain unchanged.

Readiness SHALL be accepted only while the spawned child is alive and the exact
requested host/port is accepting connections. Startup timeout or child exit
SHALL include child return code and flushed captured log tail. The helper SHALL
not retry browser navigation or convert a missing/foreign listener into a live
URL.

#### Scenario: Lifecycle helper fails on dead child

- **WHEN** a spawned uvicorn child exits before its requested port is ready
- **THEN** helper raises with run/lane identity, child return code, and captured
  log tail
- **AND** it does not yield a live URL

#### Scenario: Stale listener cannot satisfy readiness

- **WHEN** an unrelated listener accepts the requested port while spawned child
  is dead or has a different ownership identity
- **THEN** helper rejects readiness
- **AND** it preserves unrelated listener and reports child lifecycle evidence

#### Scenario: Lifecycle helper tears down deterministically

- **WHEN** caller exits helper context normally or by exception
- **THEN** child is terminated/reaped using existing bounded cleanup
- **AND** a still-bound port, abnormal return code, signal, or log failure is
  logged as diagnostic evidence

#### Scenario: Existing lane contracts remain unchanged

- **WHEN** BDD, e2e, or visual callers use shared helper
- **THEN** each caller keeps current host, assigned port, DB path, test env, and
  browser scope
- **AND** no caller gains undocumented retry, skip, xfail, or coverage change

## ADDED Requirements

### Requirement: Current-run pytest temporary ownership is receipt-bound

Shared DB/conftest support SHALL publish the exact pytest base temporary path
for each canonical run/lane using the runner's run identity. Receipt publication
MUST preserve safe dynamic DB bootstrap, import ordering, explicit marker
allow-lists, and production-DB refusal.

Runner-facing reconciliation SHALL inspect only canonical runner-declared exact
run/lane paths. A path with an exact current-run receipt/ownership match SHALL
be removed only within bounded cleanup and recorded as `owned-cleaned`; an exact
absent path is `absent`. Missing,
mismatched, pre-existing, foreign, contradictory, or incomplete evidence inside
the declared boundary SHALL remain untouched and be classified as
untrusted/nonzero and SHALL block the affected operation. A temporary path
outside every declared boundary SHALL be
recorded as preserved/non-target and SHALL NOT block by itself. Helpers SHALL
NOT expand declaration membership from pathname or parent, discover
`pytest-of-*`, traverse or delete broad `/tmp` roots, or infer parent cleanup
from an observed child path.

#### Scenario: Lane publishes exact temp ownership

- **WHEN** a canonical lane session starts with run/lane identity
- **THEN** conftest/support emits one exact pytest temp-root receipt tied to that
  run and lane
- **AND** existing DB target receipt and safe DB binding remain unchanged

#### Scenario: Current-run temp root reconciles without broad cleanup

- **WHEN** lane exits and its exact temp-root receipt is present
- **THEN** runner records post-exit state as `absent` or `owned-cleaned` only with
  current-run ownership evidence
- **AND** foreign or pre-existing temp paths are preserved and make cleanup
  untrusted when they are inside the declared boundary

#### Scenario: Out-of-bound pytest path is preserved and non-target

- **WHEN** an observed pytest temporary path is outside every canonical
  runner-declared run/lane boundary, including pre-existing
  `/tmp/pytest-of-juca`
- **THEN** support records it as preserved/non-target without cleanup
- **AND** review does not block on that observation alone
- **AND** support does not allowlist, adopt, delete, discover by `pytest-of-*`,
  or traverse a broad `/tmp` parent

#### Scenario: Declared-boundary mismatch or foreign path blocks untouched

- **WHEN** a temporary receipt path mismatches or identifies unknown/foreign
  state inside the canonical declared boundary
- **THEN** support preserves the exact path and reports untrusted/nonzero
- **AND** support does not clean, adopt, or broaden the target set
