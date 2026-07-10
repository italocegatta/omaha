## ADDED Requirements

### Requirement: Canonical test bucket matrix stays documented and aligned
The test suite SHALL keep an explicit decision matrix for each named bucket: `unit`, `integration`, `audit_integration`, `bdd`, `e2e`, `visual`, and full-suite. For each bucket, the matrix MUST name the canonical task entrypoint, hook or CI owner, concurrency class (`serial`, `parallelizable`, or `too risky for now`), and the reason for any carve-out from another gate.

Changes to markers, task help text, hooks, CI jobs, or suite docs MUST update that matrix in the same slice so bucket drift is visible at review time.

#### Scenario: BDD bucket is documented as serial
- **WHEN** an operator reads the canonical bucket matrix after T08
- **THEN** the `bdd` bucket is labeled `serial`
- **AND** the reason names the live-server and fixture-isolation constraints that block parallel execution today

#### Scenario: Audit cost center has an explicit owner
- **WHEN** an operator reads the canonical bucket matrix after T08
- **THEN** the `audit_integration` or equivalent heavy audit family has an explicit task or CI owner
- **AND** it is not silently omitted from hooks or CI without a written reason

### Requirement: Browser-backed throughput changes require repeated-run evidence
Any harness change that widens fixture scope, reuses browser/server resources, or changes the concurrency class of `bdd`, `e2e`, or `visual` suites SHALL be justified by repeated focused verification on the affected family. If a suite stays serial or keeps per-test browser launch because reuse is too risky, the decision record MUST say so explicitly.

Harness-only optimization MAY come from fixture reuse, bucket realignment, or duplicate-coverage pruning with a clear canonical owner. It MUST NOT rely on undocumented ignores, baseline refreshes, or moving product regressions into unrelated slices.

#### Scenario: Risky parallelism is rejected with a written reason
- **WHEN** repeated focused verification shows that a browser-backed suite still flakes or leaks state under broader reuse or concurrency
- **THEN** the suite remains in its safer current class
- **AND** the decision record marks it `too risky for now` with the observed reason

#### Scenario: Duplicate coverage can be pruned only with a canonical replacement
- **WHEN** T08 removes or consolidates a slow test for throughput reasons
- **THEN** review can point to the remaining canonical test that still owns the same contract
- **AND** the change does not replace the removed coverage with `skip`, `xfail`, or an undocumented carve-out
