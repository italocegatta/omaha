## Purpose

Define auditable retention evidence for Omaha test coverage. The manifest
records why surviving tests remain, making coverage decisions reviewable rather
than implicit.

## Requirements

### Requirement: Audit manifest exists and lists every surviving test file
`tests/AUDIT.md` SHALL contain one row per collected current test node, including
parameterized instances and skips. Each row MUST include node identifier, median
duration across three repetitions, protected behavior/contract, overlap
assessment, flake evidence, retention category, and recommendation. Per-node
grouping replaces stale per-file 864-total manifest and supplies decision
evidence for immutable accepted 1,043-node coverage.

#### Scenario: Manifest is present after T29
- **WHEN** T29 inventory generation completes
- **THEN** `tests/AUDIT.md` exists with Node, Median duration, Protected contract,
  Overlap, Flake evidence, Category, and Recommendation for every row

#### Scenario: Every collected node has manifest row
- **WHEN** canonical collection reports 1,043 nodes matching committed manifest
- **THEN** `tests/AUDIT.md` has exactly 1,043 node rows
- **AND** summary reports two exact accepted skips

### Requirement: T29 audit records exact authorized visual reduction

Audit SHALL reconcile committed 1,043-node manifest by exact node identity, lane
membership, checksum, and two exact skip identities. It SHALL identify 18 focused
T29 harness nodes as deliberate coverage, preserve mobile-removal history, and
record only assets/classes desktop removal with its lost focused pixel-diff
trade-off.

#### Scenario: Inventory covers manifest exactly
- **WHEN** T29 audit inventory is generated
- **THEN** its 1,043 rows cover every committed manifest node exactly once
- **AND** retained eight-node desktop matrix is recorded
- **AND** removed assets/classes desktop nodes have no audit rows

### Requirement: Retention categories are exhaustive
Every surviving test SHALL be classified into exactly one of four retention categories: `error-path`, `integration`, `spec-contract`, or `regression-guard`. A test that matches zero categories SHALL be removed, not kept with an empty justification.

#### Scenario: Test exerciting error path is classified error-path
- **WHEN** a test asserts a 4xx status, an exception, or an error message
- **THEN** its retention category is `error-path`

#### Scenario: Test exercising module integration is classified integration
- **WHEN** a test imports from two or more distinct `omaha.*` submodules and asserts their interaction
- **THEN** its retention category is `integration`

#### Scenario: Test validating spec contract is classified spec-contract
- **WHEN** a test asserts behavior described in an `openspec/specs/*/spec.md` requirement
- **THEN** its retention category is `spec-contract`

#### Scenario: Test protecting known regression is classified regression-guard
- **WHEN** a test exists because a specific bug was once present
- **THEN** its retention category is `regression-guard`
- **AND** the justification names the bug or commit

#### Scenario: Test matching zero categories is removed
- **WHEN** a test's only assertion is `isinstance`, `import`, function existence, or sentinel-only parametrize
- **AND** it matches none of the four retention categories
- **THEN** the test is deleted

### Requirement: No un-justified test files survive the audit
Every test file in `tests/` SHALL have a corresponding row in `tests/AUDIT.md` after T25. A test file without a manifest row is a gap in the audit.

#### Scenario: New test file added after T25 requires manifest update
- **WHEN** a developer adds a new test file in `tests/`
- **THEN** the same slice or PR MUST add a row to `tests/AUDIT.md` for that file

#### Scenario: Test file removed after T25 requires manifest update
- **WHEN** a developer removes a test file from `tests/`
- **THEN** the same slice or PR MUST remove the corresponding row from `tests/AUDIT.md`

### Requirement: Near-duplicate tests collapse into parametrize
Two or more tests that differ only by input and expected output, and share the same retention category, SHALL be collapsed into a single `@pytest.mark.parametrize` test. The collapsed test MUST keep every input/expected pair from the originals.

#### Scenario: Two identical-structure tests with different inputs collapse
- **WHEN** `test_foo_with_a` and `test_foo_with_b` differ only by their input values
- **AND** both are classified as the same retention category
- **THEN** they become one parametrized `test_foo` with both input pairs

#### Scenario: Collapsed test preserves coverage
- **WHEN** a parametrize collapse happens
- **THEN** the number of parametrized instances equals the sum of the original tests
- **AND** no input/expected pair is dropped

### Requirement: Sentinel-only parametrize blocks are forbidden
A parametrize block whose every expected value is `None` (or equivalent sentinel for "no match") SHALL be rewritten to include at least one positive case or removed entirely.

#### Scenario: All-None parametrize is rewritten
- **WHEN** a parametrize block has `(a, None), (b, None), (c, None)`
- **THEN** at least one case has a concrete non-None expected value
- **OR** the test is removed

#### Scenario: Positive case exists in every parametrize block
- **WHEN** a parametrize block is present in a surviving test
- **THEN** at least one case asserts a concrete result (not a sentinel)
