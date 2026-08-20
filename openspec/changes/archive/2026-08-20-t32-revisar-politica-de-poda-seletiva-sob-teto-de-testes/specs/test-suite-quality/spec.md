## ADDED Requirements

### Requirement: Selective pruning is versioned and contract-preserving

Any proposed removal or consolidation of test coverage under the duration
ceiling SHALL be recorded at stable pytest node/case granularity, including
parametrized instances. The record MUST classify each candidate as
`parametrized-case`, `example`, `snapshot`, or `redundant-low-value-assert`,
group overlapping candidates, name the protected requirement/scenario or
behavioral contract, identify replacement node IDs and lanes, and include
measured savings, owner, date, and record version. No whole suite or whole
bucket SHALL be treated as one removable candidate.

#### Scenario: Candidate has complete retention record

- **WHEN** a contributor proposes removing or consolidating a test node
- **THEN** the change record names exact node/case ID, category, redundancy
  group, protected contract, replacement coverage, lane, measured savings,
  owner, date, and version
- **AND** review can reconcile record against the audit manifest and lane
  population

#### Scenario: Parametrized case is classified individually

- **WHEN** only one instance of a parametrized test is proposed for removal
- **THEN** the record identifies that parametrized node instance rather than
  the containing function or suite
- **AND** remaining instances and replacement coverage stay explicit

#### Scenario: Redundant coverage lacks canonical replacement

- **WHEN** a candidate has no surviving node that owns the same protected
  contract
- **THEN** the pruning proposal is rejected
- **AND** it is not replaced with a skip, xfail, placeholder, or undocumented
  carve-out

### Requirement: Selective pruning cannot weaken the blocking delivery gate

Selective pruning SHALL NOT remove an entire suite, mask a failure, or be
decided during a timeout or a green run above the `<=300s` ceiling. Approved
cases MAY remain versioned with an explicit `t32_pruned` rationale and be
excluded only from the standard blocking lane after the owner records scope,
date, owner, schedule, and evidence. A later Apply MUST preserve protected
behavior, update versioned population/audit evidence, and prove canonical
`uv run task test` success within the PRD §4.13 ceiling.

#### Scenario: Apply uses recorded gate disposition

- **WHEN** a pruning record has owner-approved
  `gate_disposition: outside-blocking-standard-lane`
- **THEN** Apply keeps its source node/case versioned and excludes only the
  named marker from the standard blocking task
- **AND** manifest, lane, and replacement evidence remain explicit

#### Scenario: Owner records blocking-gate retention

- **WHEN** owner records dated approval that removed cases remain in the
  blocking canonical gate
- **THEN** any later Apply keeps those cases in that gate's required evidence
- **AND** the change still proves full-suite green and `<=300s`

#### Scenario: Owner records outside-gate execution

- **WHEN** owner records dated approval that removed cases may run outside the
  blocking gate
- **THEN** the record names schedule, responsible owner, execution command,
  and retained evidence
- **AND** no silent skip, xfail, lane deletion, or coverage claim replaces
  that evidence

#### Scenario: Timeout is not pruning authorization

- **WHEN** a canonical run exceeds 300 seconds, fails, or leaves unclean
  children
- **THEN** the run blocks delivery and triggers bottleneck investigation
- **AND** no case is removed or gate disposition chosen from that run alone

#### Scenario: Whole-suite removal is proposed

- **WHEN** a proposal removes or disables an entire suite or bucket to meet
  the ceiling
- **THEN** review rejects the proposal
- **AND** PRD §4.13 full-suite, lane, and coverage obligations remain active

### Requirement: Authorized T32 harness remediation preserves coverage

The owner-authorized 2026-08-19 T32 expansion SHALL permit only measured
harness scheduling, resource-isolation, or teardown remediation and stale audit
wording normalization. It SHALL preserve every versioned test, lane, marker,
skip, xfail, and coverage contract except the already approved 12
`t32_pruned` visual cases outside the standard blocking lane.

#### Scenario: Harness remediation meets delivery gate

- **WHEN** Apply changes directly linked test harness scheduling, isolation, or
  teardown
- **THEN** one canonical `uv run task test` run exits 0 with clean children and
  wall-clock duration at or below 300 seconds
- **AND** population, lane checksums, skip identities, and protected coverage
  remain reconciled

#### Scenario: Safe remediation cannot meet ceiling

- **WHEN** the bounded harness remediation cannot produce a green canonical run
  within 300 seconds
- **THEN** Apply stops and reports profiling evidence and exact blocker
- **AND** no test, lane, marker, skip, xfail, coverage contract, or timeout
  decision is weakened

### Requirement: Expanded T32 governance classifies and selects cases

Every collected node/case SHALL receive exactly one explicit importance level:
`critical`, `high`, `normal`, or `low`. Missing classification SHALL fail
collection or governance validation. Active node count SHALL remain a transparent
current-state report, not an immutable delivery contract.

If measured or prior-known preflight cost predicts a breach of the 300-second
ceiling, selection SHALL happen before blocking children launch and SHALL choose
only lowest-importance cases in deterministic importance/cost/node order. A
within-ceiling forecast SHALL select no new case. Selected cases remain
versioned, separately runnable, and recorded with rationale, owner/date,
protected contract, replacement coverage, and measured or prior-known cost.

#### Scenario: Classification coverage is complete
- **WHEN** governance validates collected nodes, including parametrized cases
- **THEN** every node has one importance marker
- **AND** an unclassified node fails the gate

#### Scenario: Preflight selection preserves expanded execution
- **WHEN** forecast exceeds the ceiling
- **THEN** only lowest-importance cases are selected before execution
- **AND** the named expanded lane can run selected cases without masking failure

#### Scenario: Already-disabled cases are not selected again

- **WHEN** pre-run governance evaluates current blocking nodes
- **THEN** cases already outside the standard lane are excluded from candidate
  selection
- **AND** selection uses only currently blocking, explicitly classified cases
- **AND** every selected case remains runnable in the named expanded lane
