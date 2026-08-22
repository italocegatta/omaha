## MODIFIED Requirements

### Requirement: Delivery gate preserves focused protection during maintenance suspension
Runtime changes SHALL retain applicable product behavior tests and focused
regression evidence. The owner-authorized I10 state
`maintenance-suspended` MAY suspend only the parallel canonical
`uv run task test` result as a mandatory apply/review/pre-push delivery gate;
it SHALL NOT delete, disable, skip, xfail, retry, mask, serialize, remove, or
weaken any test, lane, marker, coverage contract, task command, DB-safety rule,
receipt, cleanup rule, or fail-fast rule. `uv run task test` SHALL remain
callable and canonical.

#### Scenario: Product change proceeds on focused evidence
- **WHEN** a change has applicable focused product behavior tests and the
  canonical gate is `maintenance-suspended`
- **THEN** those focused tests run and pass before apply/review approval
- **AND** review audits scope, test coverage, command/result evidence, and
  suspension visibility
- **AND** the canonical full suite is recorded as non-blocking/not run rather
  than falsely reported green

#### Scenario: Individual test commands remain mandatory
- **WHEN** an operator runs any existing unit, integration, audit, E2E, BDD, or
  visual Taskipy command
- **THEN** its existing selection, tests, skips, coverage/no-coverage,
  isolation, and result semantics remain unchanged
- **AND** suspension does not authorize deleting or disabling that command

#### Scenario: Reactivation requires exact diagnosis and one green suite
- **WHEN** isolated diagnosis resolves both concurrent dynamic SQLite
  readonly-DB failure and BDD browser-timeout failure
- **THEN** the owner may reactivate the canonical gate
- **AND** one isolated `uv run task test` run SHALL be green across all six
  lanes with complete coverage/skips/manifest/DB/temp/cleanup evidence
- **AND** elapsed wall-clock through cleanup SHALL be `<=300s`
- **AND** any red lane, missing evidence, mismatch, untrusted cleanup, or
  duration breach keeps the gate suspended and blocks reactivation

#### Scenario: Suspension does not become permanent exemption
- **WHEN** focused evidence is green but reactivation trigger is incomplete
- **THEN** the change may proceed only under focused policy if no other blocker
  exists
- **AND** T34 remains responsible for bounded diagnosis/correction
- **AND** F58 remains `Blocked` behind T34's reactivated canonical acceptance
