## ADDED Requirements

### Requirement: Suite health report SHALL document all test lane results

The system SHALL provide a suite health report (`tests/SUITE_HEALTH.md` or equivalent) that documents the result of each test lane (unit, integration, e2e, bdd, visual) including pass count, fail count, and classification of each failure by type.

#### Scenario: Report includes all lanes

- **WHEN** suite health report is generated
- **THEN** it contains results for unit, integration, e2e, bdd, and visual lanes
- **AND** each lane shows pass count and fail count
- **AND** each failure is classified as: regression, drift, flaky, baseline-stale, or production-bug

#### Scenario: Report is machine-readable and human-readable

- **WHEN** maintainer reviews the suite health report
- **THEN** the report uses markdown tables or structured format
- **AND** each failure entry includes test name, file location, classification, and action taken

### Requirement: Failure classification SHALL be deterministic

Each failing test SHALL be classified into exactly one of: regression (recent commit introduced breakage), drift (assertion outdated after intentional change), flaky (passes in isolation, fails under parallel), baseline-stale (visual PNG outdated after UI change), or production-bug (code defect found by test).

#### Scenario: Regression classification

- **WHEN** a test fails due to a recent commit that broke existing behavior
- **THEN** the failure is classified as "regression"
- **AND** the report identifies the introducing commit if known

#### Scenario: Drift classification

- **WHEN** a test fails because assertion values are outdated after intentional UI/logic change
- **THEN** the failure is classified as "drift"
- **AND** the report identifies the change that caused the drift

#### Scenario: Flaky classification

- **WHEN** a test passes in isolation but fails under xdist or parallel execution
- **THEN** the failure is classified as "flaky"
- **AND** the report notes the isolation vs parallel discrepancy

#### Scenario: Baseline-stale classification

- **WHEN** a visual test fails because the PNG baseline no longer matches the current UI
- **THEN** the failure is classified as "baseline-stale"
- **AND** the report identifies which UI change made the baseline outdated

#### Scenario: Production-bug classification

- **WHEN** a test fails due to an actual code defect in production code
- **THEN** the failure is classified as "production-bug"
- **AND** the report describes the defect

### Requirement: Report SHALL document T28 supersession

The suite health report SHALL document that T28 (`fix-18-failing-e2e-bdd-tests`) is partially obsoleted by T27 commit `064113c`, and list which issues from T28 are already covered.

#### Scenario: T28 supersession documented

- **WHEN** suite health report is reviewed
- **THEN** it contains a section explaining T28's partial obsolescence
- **AND** it lists which T28 issues are already fixed by T27

### Requirement: Report SHALL be committed with the change

The suite health report SHALL be committed as part of the T29 change artifacts, not as a separate commit.

#### Scenario: Report included in change commit

- **WHEN** T29 change is committed
- **THEN** the suite health report file is included in the same commit
- **AND** any baseline updates are also included in the same commit
