## Purpose

Contrato aditivo de classificação e comparação do preview de posições.

## Requirements

### Requirement: Preview rows are classified against pre-preview state

The preview response SHALL classify every incoming row exactly once in additive
`triage.new`, `triage.changed`, or `triage.unchanged` groups, using active-profile
Asset and Position state captured when preview was created.

#### Scenario: Unmatched asset is new
- **WHEN** preview row has no normalized-name Asset match
- **THEN** row appears only in `triage.new`

#### Scenario: Matched row with changed quantity is changed
- **WHEN** matched row quantity differs from pre-preview Position
- **THEN** row appears only in `triage.changed`

#### Scenario: Equal matched row is unchanged
- **WHEN** matched Asset and Position have equal compared values
- **THEN** row appears only in `triage.unchanged` without changed disclosure

### Requirement: Position and Asset metadata equality is typed and explicit

Position fields SHALL compare exact Decimal values, preserving None-versus-zero
distinction. Asset metadata SHALL compare represented name, trade flags, and
upper-cased currency; `broker_ticker` remains identity, not changed metadata.

#### Scenario: Decimal and metadata comparison is exact
- **WHEN** incoming and prior values differ in typed value or represented metadata
- **THEN** changed field is reported without treating missing totals as zero

### Requirement: Triage payload preserves compatibility arrays

The response SHALL retain `preview_id`, `auto_matched`, `unmatched`, and
`asset_classes` with established meaning, while adding triage data and hidden
`broker_ticker` assignment identity.

#### Scenario: Legacy keys remain available
- **WHEN** preview response is returned
- **THEN** existing compatibility arrays remain readable alongside triage

### Requirement: Groups and changed fields are deterministic

Each group SHALL sort by case/accent-insensitive asset name, then normalized
broker ticker and raw values. Changed fields SHALL include stable id, PT-BR
label, unit, sign, incoming value, and previous value/display.

#### Scenario: Group order is stable
- **WHEN** equivalent rows arrive in different input orders
- **THEN** each triage group has identical deterministic order

### Requirement: Preview triage does not mutate portfolio safety state

Triage SHALL not mutate assets, positions, ownership/TTL, snapshots, audit rows,
or commit state. Explicit confirmation remains sole mutation boundary and Família
remains read-only.

#### Scenario: Preview comparison is read-only
- **WHEN** triage response is built
- **THEN** portfolio and audit state remain unchanged until explicit commit
