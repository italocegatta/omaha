## ADDED Requirements

### Requirement: BDD harness remains deterministic during expanded-lane concurrency

The canonical BDD task SHALL complete its 51 collected scenarios deterministically
both in isolation and while the named `test-t32-expanded` task runs concurrently.
The BDD lane SHALL remain serial, and this requirement SHALL NOT be satisfied by
skipping, xfail-ing, deselecting, removing, or pruning BDD scenarios.

#### Scenario: Isolated BDD lane is green

- **WHEN** an operator runs `uv run task test-bdd` from a fresh test-server/DB
  state
- **THEN** all 51 BDD scenarios pass
- **AND** zero scenario fails with `net::ERR_CONNECTION_REFUSED` on port 8766

#### Scenario: Expanded lane does not invalidate BDD

- **WHEN** `uv run task test-bdd` and `uv run task test-t32-expanded` run
  concurrently from fresh lane-owned state
- **THEN** BDD reports 51 passed and zero failed
- **AND** the expanded lane retains its governed selected cases
- **AND** no BDD scenario is removed from collection or execution

#### Scenario: BDD refusal blocks delivery rather than being masked

- **WHEN** BDD loses its live server or port 8766 during execution
- **THEN** the lane reports a failure with server/process/port evidence
- **AND** no browser retry, skip, xfail, or lane reduction claims success
