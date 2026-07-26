## MODIFIED Requirements

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
