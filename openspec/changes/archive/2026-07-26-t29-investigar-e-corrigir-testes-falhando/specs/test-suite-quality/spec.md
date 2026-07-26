## MODIFIED Requirements

### Requirement: Delivery gate requires full suite green

Runtime changes SHALL not be considered delivered while `uv run task test` is
red. Canonical routine SHALL include unit, integration, audit integration, E2E,
BDD, and retained visual coverage. T29 performance acceptance requires three
fresh canonical runs, each green and <=300 seconds through cleanup, matching
immutable 1,043-node manifest by node IDs, lane membership, checksum, and two
exact skip identities.

#### Scenario: Three consecutive full routines prove ceiling
- **WHEN** T29 claims canonical full-routine performance acceptance
- **THEN** three fresh `uv run task test` runs are green and <=300 seconds
- **AND** each run matches 1,043-node immutable manifest and two exact skips

#### Scenario: Ceiling proof misses
- **WHEN** any fresh required proof run is red, exceeds 300 seconds, differs from
  manifest, or reports unclean children
- **THEN** T29 stops remaining proof runs and records measured alternatives
- **AND** it does not claim a <=300-second fix or remove further coverage

### Requirement: T29 accepted population is explicit and immutable

After exact owner-authorized desktop removal, repository SHALL commit canonical
manifest with 1,043 stable node IDs, lane membership, two exact skip identities,
and deterministic checksum. Audit SHALL record 18 focused harness nodes and
retained eight-node desktop matrix. No test removal, skip, xfail, disable, lane
reduction, or coverage move is permitted beyond prior mobile history and exact
assets/classes desktop removal.

#### Scenario: Canonical run matches accepted population
- **WHEN** runner completes canonical `uv run task test` collection
- **THEN** it compares population against committed 1,043-node manifest/checksum
- **AND** it fails reconciliation for any node, lane, checksum, or skip mismatch

### Requirement: Marker allow-lists must not overlap

Test file SHALL NOT appear in both `_INTEGRATION_PREFIXES` and `_UNIT_FILES` in
`tests/conftest.py`. Every root `tests/test_*.py` SHALL have explicit allowed
classification or `UnknownTestPath` warning. T29 SHALL retain zero classifier
warnings without changing immutable population.

#### Scenario: Classifier hygiene is clean
- **WHEN** maintainer collects suite after T29 updates
- **THEN** no `UnknownTestPath` warning is emitted
- **AND** allow-list intersection is empty
- **AND** collection matches 1,043-node manifest and two exact skips
