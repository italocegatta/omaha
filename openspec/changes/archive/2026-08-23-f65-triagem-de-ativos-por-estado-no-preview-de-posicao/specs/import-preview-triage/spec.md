## ADDED Requirements

### Requirement: Preview rows are classified against pre-preview state

The preview response SHALL classify every incoming row exactly once in additive
`triage.new`, `triage.changed`, or `triage.unchanged` groups. Classification
SHALL use the active profile's Asset and Position state captured when the
ImportPreview was created, not name matching alone and not a later database
state when a baseline is available.

An incoming row with no Asset match under existing normalized-name matching is
`new`. A matched Asset with no Position for the same Asset and exact
`broker_ticker`, or with any unequal compared field, is `changed`. A matched
Asset and Position with all compared fields equal is `unchanged`.

#### Scenario: Unmatched asset is new

- **WHEN** preview row has no normalized-name Asset match in the pre-preview
  active profile
- **THEN** row appears in `triage.new` and appears in neither other group

#### Scenario: Matched row with changed quantity is changed

- **WHEN** normalized Asset identity matches and incoming `qty` differs from
  the pre-preview Position `qty`
- **THEN** row appears in `triage.changed` and not in `triage.unchanged`

#### Scenario: Matched row with no prior Position is changed

- **WHEN** Asset identity matches but no Position exists for its Asset and
  incoming `broker_ticker`
- **THEN** row appears in `triage.changed` with a missing prior Position
  indication and not in `triage.new`

#### Scenario: Equal matched row is unchanged

- **WHEN** matched Asset and Position have equal compared values
- **THEN** row appears only in `triage.unchanged` and has no changed-field
  disclosure

### Requirement: Position and Asset metadata equality is typed and explicit

Position equality SHALL compare `qty`, `avg_price`, `current_price`,
`total_invested`, and `total_current` as exact Decimal values. `None` SHALL
equal only `None`; missing broker totals SHALL NOT equal numeric zero.

Asset metadata equality SHALL compare incoming preview-represented `name`,
`buy_enabled`, `sell_enabled`, and `currency_code` against the baseline Asset.
Names SHALL be trimmed and compared case-sensitively after identity matching;
booleans SHALL compare as booleans; currency codes SHALL compare upper-cased.
Absent incoming metadata SHALL not be fabricated or treated as changed.
`broker_ticker` SHALL remain row identity, not a changed field.

#### Scenario: Decimal scale alone is equal

- **WHEN** incoming Decimal value is `10.0` and prior value is `10.00`
- **THEN** field is equal and does not place row in `triage.changed`

#### Scenario: Missing total differs from zero

- **WHEN** incoming broker total is absent and prior Position total is numeric
  zero
- **THEN** total is reported as changed with previous zero disclosed

#### Scenario: Asset spelling metadata is visible

- **WHEN** normalized identity matches but trimmed incoming Asset name differs
  in case or accent from prior Asset name
- **THEN** `asset.name` is included in `changed_fields` with both values

### Requirement: Triage payload preserves compatibility arrays

The preview response SHALL retain existing top-level `preview_id`,
`auto_matched`, `unmatched`, and `asset_classes` keys and their established
meaning and fields. Additive `triage` data SHALL not remove, rename, reorder,
or reinterpret those compatibility arrays until a separately approved
replacement contract exists. Every triage row SHALL retain its
`broker_ticker` assignment key for downstream class/trade/currency binding;
the review surface SHALL keep that key hidden rather than exposing ticker as a
visible identity column.

#### Scenario: Manual response keeps legacy keys

- **WHEN** manual `POST /api/import/preview` returns a valid preview
- **THEN** existing consumers can read `auto_matched`, `unmatched`, and
  `asset_classes` exactly as before and `triage` is additionally present

#### Scenario: MyProfit response uses same additive shape

- **WHEN** F59 polling returns a successful preview
- **THEN** its preview contains the same compatibility keys and triage shape
  without changing job, TTL, or commit semantics

#### Scenario: Triage row keeps hidden assignment identity

- **WHEN** a triage row is hydrated in Step 2
- **THEN** `broker_ticker` remains addressable for assignments and commit, while
  no visible ticker value or `Ativo / ticker` replacement is required

### Requirement: Groups and changed fields are deterministic

Each triage group SHALL be sorted by Asset name using case- and
accent-insensitive comparison with missing names last. Equal normalized names
SHALL use normalized broker ticker as tie-breaker and raw values as final
deterministic tie-breakers. Each changed row SHALL expose `changed_fields`
entries containing stable field id, PT-BR label, unit, sign, incoming value,
and previous value/display data.

#### Scenario: Group ordering ignores case and accent

- **WHEN** group contains names `Árvore`, `arara`, and `AZUL`
- **THEN** rows render in `arara`, `Árvore`, `AZUL` order independent of
  broker input order

#### Scenario: Ticker breaks equal names

- **WHEN** two rows share equivalent normalized names but have tickers `B3SA3`
  and `ABEV3`
- **THEN** `ABEV3` sorts before `B3SA3`

#### Scenario: Numeric diff carries sign and unit

- **WHEN** incoming `qty` is greater than prior `qty`
- **THEN** changed field identifies `qty`, includes its quantity unit and
  `positive` sign, and retains both incoming and previous values

### Requirement: Preview triage does not mutate portfolio safety state

Building or reading triage SHALL not mutate Asset, Position, AssetClass,
ImportPreview ownership/TTL semantics, snapshots, audit rows, or commit state.
Explicit existing confirmation SHALL remain sole import mutation boundary, and
Família SHALL remain read-only.

#### Scenario: Preview comparison is read-only

- **WHEN** preview response is built with new, changed, and unchanged rows
- **THEN** Asset/Position counts and mutation-audit/snapshot state are
  unchanged until existing explicit commit

#### Scenario: Família cannot receive mutable triage flow

- **WHEN** active profile is Família and preview/sync review is requested
- **THEN** existing household-read-only response/disabled behavior remains and
  no triage path bypasses the guard
