# asset-class-quote-kind Specification

## Purpose
TBD - created by archiving change add-market-quote-service. Update Purpose after archive.
## Requirements
### Requirement: AssetClass has a quote_kind field

The system SHALL add a `quote_kind` column to the `asset_classes`
table as an enum with three values: `auto`, `manual`, `none`. The
default value for existing rows (migration) SHALL be `none` to
require an explicit opt-in for live quotes. The column is non-null.

#### Scenario: Migration adds the column with default none
- **WHEN** the migration runs against a database with existing asset classes
- **THEN** every existing row has `quote_kind = 'none'`

#### Scenario: New asset classes can set quote_kind explicitly
- **WHEN** the user creates a new asset class via the editor
- **THEN** they can choose between `auto`, `manual`, or `none` for `quote_kind`

### Requirement: QuoteService skips classes with quote_kind = none

The system SHALL NOT query yfinance for any position under an asset
class whose `quote_kind = none`. The position continues to use
`Position.current_price` (from the broker CSV import) as its price
source.

#### Scenario: NONE class positions are not fetched
- **WHEN** an asset class "Renda Fixa" has `quote_kind = none` and contains 3 positions (CDB, RDB, Tesouro Selic)
- **THEN** the QuoteService does NOT include any of these symbols in its refresh list

#### Scenario: NONE class positions use broker price at read time
- **WHEN** a consumer reads the price for a position under a NONE class
- **THEN** the price returned is `Position.current_price` (the value written by the S04 CSV import)

### Requirement: QuoteService skips classes with quote_kind = manual

The system SHALL NOT query yfinance for any position under an asset
class whose `quote_kind = manual`. The position uses
`Position.current_price` from the broker CSV by default; the
`manual` value is reserved for a future change that lets the user
type a price per position via the UI.

#### Scenario: MANUAL class positions are not fetched
- **WHEN** an asset class "Fundos fechados" has `quote_kind = manual` and contains 2 positions
- **THEN** the QuoteService does NOT include any of these symbols in its refresh list

### Requirement: QuoteService fetches only classes with quote_kind = auto

The system SHALL query yfinance only for positions under asset
classes whose `quote_kind = auto`. The symbols fed to the provider
are the `Position.broker_ticker` values of those positions.

#### Scenario: AUTO class positions are fetched
- **WHEN** an asset class "Ações BR" has `quote_kind = auto` and contains 5 positions with tickers `PRIO3`, `SLCE3`, `GMAT3`, `KEPL3`, `WIZC3`
- **THEN** the QuoteService refreshes quotes for those 5 tickers (mapped to `.SA` by the provider)

#### Scenario: Mixed classes are filtered correctly
- **WHEN** the database has 3 asset classes: "Ações BR" (auto, 5 positions), "Renda Fixa" (none, 3 positions), "Ações US" (auto, 2 positions)
- **THEN** the refresh fetches only the 7 positions under the 2 AUTO classes
- **AND** the 3 positions under Renda Fixa are NOT fetched

### Requirement: Quote kind is exposed by the classes API

The system SHALL include `quote_kind` in the JSON response of
`GET /api/classes` and the editor PATCH payload, so the existing
class editor (S02) can render a dropdown for it.

#### Scenario: GET /api/classes returns quote_kind
- **WHEN** a client calls `GET /api/classes`
- **THEN** each class in the response includes the `quote_kind` field

