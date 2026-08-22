## MODIFIED Requirements

### Requirement: Apply validates focused relevant tests during canonical-gate suspension
The `apply` agent SHALL identify affected behavior from change tasks and diff,
run every applicable focused command through `uv run task …`, and report exact
commands and results. Product behavior tests SHALL remain mandatory. While the
owner-authorized I10 state is `maintenance-suspended`, apply SHALL NOT run
`uv run task test` as routine validation and SHALL NOT treat its absence as a
test deletion, skip, xfail, retry, or coverage reduction.

#### Scenario: Focused apply test is required
- **WHEN** an implementation change has applicable product behavior tests
- **THEN** apply runs those focused command(s) and records green/red evidence
- **AND** a red related test blocks handoff until diagnosed and resolved or
  escalated

#### Scenario: Canonical suite is suspended during apply
- **WHEN** I10 `maintenance-suspended` state is active
- **THEN** apply records canonical full suite as not run/non-blocking
- **AND** it does not launch `uv run task test` as routine apply validation

### Requirement: Review audits focused evidence while canonical gate is suspended
The `review` agent SHALL audit complete slice scope, product behavior test
coverage, focused command/result evidence, no-test-deletion invariants, and
suspension visibility. While `maintenance-suspended` is active, review SHALL
record `NOT RUN — maintenance-suspended` for the canonical full suite and SHALL
not launch it. Review SHALL run exactly one isolated `uv run task test` only
after reactivation conditions are satisfied.

#### Scenario: Suspended review has complete focused evidence
- **WHEN** focused applicable commands are green and canonical gate is
  `maintenance-suspended`
- **THEN** review audits scope and focused evidence and may approve an eligible
  change without a canonical-suite result
- **AND** review records the suspended state and canonical command as not run

#### Scenario: Suspended review finds product-test failure or scope breach
- **WHEN** a focused product test is red, missing, weakened, or scope audit
  finds an unrelated change
- **THEN** review does not approve
- **AND** suspension does not override the failure

#### Scenario: Reactivation restores one canonical review gate
- **WHEN** isolated diagnosis resolves both the concurrent dynamic SQLite
  readonly-DB failure and BDD browser-timeout failure
- **AND** owner reactivates the canonical gate
- **THEN** review runs exactly one isolated `uv run task test`
- **AND** approval requires six green lanes, complete receipts and focused
  evidence, no test deletion/masking, and elapsed wall-clock through cleanup
  `<=300s`
