## MODIFIED Requirements

### Requirement: Canonical test bucket matrix stays documented and aligned
The test suite SHALL keep an explicit decision matrix for each named bucket: `unit`, `integration`, `audit_integration`, `bdd`, `e2e`, `visual`, and full-suite. For each bucket, the matrix MUST name the canonical task entrypoint, hook or CI owner, concurrency class (`serial`, `parallelizable`, or `too risky for now`), and the reason for any carve-out from another gate.

Changes to markers, task help text, hooks, CI jobs, or suite docs MUST update that matrix in the same slice so bucket drift is visible at review time.

The matrix MUST document which buckets produce coverage reports and which do not. Browser-backed buckets (`bdd`, `e2e`, `visual`) SHALL be documented as running without coverage instrumentation. Fast-lane buckets (`unit`, `integration`) SHALL be documented as the only producers of coverage data.

#### Scenario: BDD bucket is documented as serial
- **WHEN** an operator reads the canonical bucket matrix after T08
- **THEN** the `bdd` bucket is labeled `serial`
- **AND** the reason names the live-server and fixture-isolation constraints that block parallel execution today

#### Scenario: Audit cost center has an explicit owner
- **WHEN** an operator reads the canonical bucket matrix after T08
- **THEN** the `audit_integration` or equivalent heavy audit family has an explicit task or CI owner
- **AND** it is not silently omitted from hooks or CI without a written reason

#### Scenario: Coverage lane assignment is documented
- **WHEN** an operator reads the canonical bucket matrix after T13
- **THEN** the matrix shows `unit` and `integration` as coverage-producing buckets
- **AND** the matrix shows `bdd`, `e2e`, and `visual` as non-coverage buckets
- **AND** the canonical coverage command is `task coverage` (unit + integration only)
