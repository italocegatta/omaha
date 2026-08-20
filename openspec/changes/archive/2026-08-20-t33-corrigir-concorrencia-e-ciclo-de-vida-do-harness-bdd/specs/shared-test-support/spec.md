## ADDED Requirements

### Requirement: Shared test-server lifecycle preserves lane ownership

The shared test-server lifecycle helper SHALL provide a deterministic startup and
teardown boundary for BDD/e2e/visual callers: it SHALL compose the requested
lane DB environment, detect child startup failure rather than accepting an
unrelated listener, expose abnormal lifecycle evidence, and reap the spawned
child on exit. Existing hosts, ports, browser selection, and caller DB paths
remain unchanged.

#### Scenario: Lifecycle helper fails on dead child

- **WHEN** a spawned uvicorn child exits before its requested port is ready
- **THEN** the helper raises with the child return code and captured log tail
- **AND** it does not yield a live URL

#### Scenario: Lifecycle helper tears down deterministically

- **WHEN** a caller exits the helper context normally or by exception
- **THEN** the child is terminated/reaped using the existing bounded cleanup
  contract
- **AND** a still-bound port or abnormal return code is logged as diagnostic
  evidence

#### Scenario: Existing lane contracts remain unchanged

- **WHEN** BDD, e2e, or visual callers use the shared helper
- **THEN** each caller keeps its current host, assigned port, DB path, test env,
  and browser scope
- **AND** no caller gains an undocumented retry, skip, xfail, or coverage change
