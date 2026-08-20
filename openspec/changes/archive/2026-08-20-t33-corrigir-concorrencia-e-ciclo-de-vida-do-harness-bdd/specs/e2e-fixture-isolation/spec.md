## ADDED Requirements

### Requirement: Session-scoped BDD server readiness and ownership are explicit

The BDD session-scoped uvicorn fixture SHALL not treat an arbitrary TCP listener
on port 8766 as proof that its spawned child is ready and owns the lane. Startup
and teardown SHALL make child liveness, abnormal exit, port availability, and
lane ownership observable, while preserving the existing BDD port assignment and
DB isolation.

#### Scenario: BDD readiness belongs to spawned child

- **WHEN** `tests/bdd/conftest.py::live_url` starts its session server
- **THEN** readiness succeeds only when the spawned uvicorn child is alive and
  the BDD-owned endpoint is accepting connections on 8766
- **AND** a stale or unrelated listener cannot silently satisfy readiness

#### Scenario: Startup failure is loud

- **WHEN** the spawned BDD uvicorn exits or cannot own port 8766 before readiness
- **THEN** the fixture fails with actionable process/port/log evidence
- **AND** it does not yield a URL backed by another lane or stale server

#### Scenario: BDD teardown releases lifecycle resources

- **WHEN** the session-scoped BDD fixture exits normally or after a scenario error
- **THEN** its child is reaped, abnormal return codes remain observable, and port
  8766 is checked for release
- **AND** e2e ports 8765/8767 and all lane-owned DB files remain unaffected
