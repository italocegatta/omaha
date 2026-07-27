## ADDED Requirements

### Requirement: Apply validates only focused relevant tests
The `apply` agent and `openspec-apply-change` skill SHALL identify affected behavior from change tasks and diff, run smallest relevant test set through `uv run task …`, and report exact command and result. They SHALL NOT run full `uv run task test` as routine validation after an apply pass or after all tasks complete. Related red tests SHALL block apply handoff.

#### Scenario: Apply completes a documented change
- **WHEN** `apply` completes an implementation pass
- **THEN** it runs and reports focused relevant tests
- **AND** it does not run full `uv run task test` as routine apply validation

#### Scenario: Focused apply test is red
- **WHEN** a focused relevant test fails
- **THEN** `apply` SHALL not hand off as `Applied` until failure is diagnosed and resolved or escalated

### Requirement: Review owns one timed full-suite correctness gate
The `review` agent and `code-review` skill SHALL run exactly one full `uv run task test` invocation per review before standards and spec review. Review SHALL measure elapsed wall-clock from process start to finish and record command, green/red result, elapsed wall-clock, threshold classification, and explicit verdict. Any red test SHALL return `CHANGES_REQUESTED`; elapsed time SHALL NOT relax this requirement.

#### Scenario: Full suite is green
- **WHEN** review's one full `uv run task test` invocation is green
- **THEN** review proceeds to standards and spec review subject to performance classification

#### Scenario: Full suite is red
- **WHEN** review's one full `uv run task test` invocation has any failure
- **THEN** review returns `CHANGES_REQUESTED` and classifies each failure
- **AND** review does not APPROVE regardless of elapsed wall-clock

### Requirement: Review reports time threshold telemetry and blocks ceiling breaches
Review SHALL classify its measured full-suite wall-clock as under 3 minutes, 3–5 minutes inclusive, or over 5 minutes. A 3–5-minute result SHALL be warning telemetry only and SHALL NOT fail delivery. A result over 5 minutes SHALL return `CHANGES_REQUESTED` and SHALL NOT be APPROVED, even when tests are green.

#### Scenario: Full suite completes in 3–5 minutes
- **WHEN** review measures a green full suite from 3 through 5 minutes
- **THEN** review records warning telemetry with elapsed wall-clock
- **AND** may APPROVE if no correctness or review findings remain

#### Scenario: Full suite exceeds five minutes
- **WHEN** review measures a full suite over 5 minutes
- **THEN** review returns `CHANGES_REQUESTED` with elapsed wall-clock and measured-bottleneck evidence
- **AND** review does not APPROVE

### Requirement: Ceiling remediation preserves test protection
For a result over five minutes, review SHALL investigate bottleneck using output from its one full suite and existing measured evidence without routine duplicate full-suite execution. Report SHALL require scoped remediation based on measured bottleneck and SHALL prohibit disabling, skipping, masking, or removing tests and reducing coverage. This change SHALL NOT schedule or claim immediate suite-speed optimization; under three minutes is aspirational, not an acceptance gate.

#### Scenario: Ceiling breach lacks exact per-test duration data
- **WHEN** review's full-suite output cannot identify individual slow tests
- **THEN** review records available measured lane evidence and requires focused profiling in remediation work
- **AND** does not rerun full suite solely to collect additional timing data

#### Scenario: Remediation is proposed after ceiling breach
- **WHEN** review returns `CHANGES_REQUESTED` because full suite exceeds five minutes
- **THEN** remediation preserves all tests and coverage
- **AND** it may assess evidence-supported patterns from T16–T18 or T23 without treating those patterns as preapproved changes
