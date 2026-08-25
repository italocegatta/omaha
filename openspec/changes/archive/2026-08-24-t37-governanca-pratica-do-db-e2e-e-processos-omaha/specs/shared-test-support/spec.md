## MODIFIED Requirements

### Requirement: Shared test-server lifecycle preserves lane ownership

The shared test-server lifecycle helper SHALL provide deterministic startup and
teardown for BDD/e2e/visual callers: it SHALL compose requested lane DB
environment, record run/lane-linked parent PID, child PID, actual PGID, exact
command, repository cwd, launch, readiness, port, DB, log, exit, and teardown
evidence, detect child startup failure rather than an unrelated listener, expose
abnormal lifecycle evidence, and reap the spawned child. Existing hosts, ports,
browser selection, caller DB paths, and browser scopes remain unchanged.

Readiness and teardown SHALL be accepted only for the spawned child with
matching lane/process identity. Graceful teardown/restart SHALL send TERM,
wait within the existing bounded grace, escalate to KILL only for the same
recorded owned group, and record port-free status. The helper SHALL not retry
browser navigation, adopt a stale listener, or convert a missing/foreign
listener into a live URL.

#### Scenario: Lifecycle helper fails on dead child

- **WHEN** a spawned uvicorn child exits before its requested port is ready
- **THEN** helper raises with run/lane identity, child return code, exact
  command/cwd evidence, and captured log tail
- **AND** it does not yield a live URL

#### Scenario: Stale listener cannot satisfy readiness

- **WHEN** an unrelated or identity-mismatched listener accepts the requested
  port while spawned child is dead
- **THEN** helper rejects readiness and records stale/foreign evidence
- **AND** it preserves unrelated listener without retry or cleanup

#### Scenario: Lifecycle helper performs graceful owned teardown

- **WHEN** caller exits helper context normally or by exception and the child
  identity is current-run-owned
- **THEN** helper records teardown-start, TERM, bounded wait, optional owned-only
  KILL, exit, and port-free events
- **AND** abnormal return code, signal, still-bound port, or lifecycle race
  remains observable and does not become an unqualified success

#### Scenario: Existing lane contracts remain unchanged

- **WHEN** BDD, e2e, or visual callers use shared helper
- **THEN** each caller keeps current host, assigned port, DB path, test env, and
  browser scope
- **AND** no caller gains undocumented retry, skip, xfail, or coverage change

## ADDED Requirements

### Requirement: Shared DB support guards ephemeral E2E recreation

Shared DB support SHALL expose one helper for recreating exact fixed E2E test
DBs. It SHALL accept only explicitly registered E2E paths, reject
`data/portfolio.db`, symlinks, directories, and paths outside repository
`data/`, and emit a run/lane-linked disposition with `adopted: false` before
returning. Existing dynamic safe DB bootstrap, import ordering, production-DB
guard, and DB receipts SHALL remain unchanged.

#### Scenario: E2E fixture receives fresh exact DB

- **WHEN** caller requests recreation of `data/test_e2e.db` or the already
  declared E2E short-TTL DB before server launch
- **THEN** helper removes only an exact regular file if present, records
  `ephemeral-recreated` or an idempotent absent result, and returns the same
  path for uvicorn and test processes
- **AND** helper does not inspect or adopt old rows

#### Scenario: Production DB cannot be recreated

- **WHEN** caller requests `data/portfolio.db` or an unresolved/contradictory
  path
- **THEN** helper fails before removal with explicit target evidence
- **AND** production DB and unrelated files remain untouched
