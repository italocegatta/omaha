# quote-cache Specification

## Purpose
TBD - created by archiving change add-market-quote-service. Update Purpose after archive.
## Requirements
### Requirement: QuoteCache persists quotes with TTL

The system SHALL persist fetched quotes in a `quotes` table with the
columns `symbol` (PRIMARY KEY, TEXT), `price` (NUMERIC), `currency`
(TEXT), and `fetched_at` (TIMESTAMP). A quote row SHALL be considered
fresh when `now() - fetched_at <= QUOTE_TTL_SECONDS`. The TTL is
configurable via env var, defaulting to 900 seconds (15 minutes).

#### Scenario: Storing a quote writes a single row
- **WHEN** the service stores a quote for symbol `PETR4.SA` with price `38.50`, currency `BRL`
- **THEN** the `quotes` table contains exactly one row with `symbol = 'PETR4.SA'`, `price = 38.50`, `currency = 'BRL'`, and `fetched_at` within the last second

#### Scenario: Upserting updates the existing row
- **WHEN** the service stores a quote for `PETR4.SA` with a new price, and a row for that symbol already exists
- **THEN** the existing row's `price` and `fetched_at` are updated in place; no duplicate row is created

#### Scenario: Reading a fresh quote returns the cached price
- **WHEN** a quote for `PETR4.SA` was stored 30 seconds ago and `QUOTE_TTL_SECONDS = 900`
- **THEN** `QuoteCache.get('PETR4.SA')` returns the stored price and a flag indicating the quote is fresh

#### Scenario: Reading a stale quote returns None
- **WHEN** a quote for `PETR4.SA` was stored 1000 seconds ago and `QUOTE_TTL_SECONDS = 900`
- **THEN** `QuoteCache.get('PETR4.SA')` returns `None` and a flag indicating the quote is stale

#### Scenario: Reading an unknown symbol returns None
- **WHEN** no quote exists for `UNKNOWN.SA`
- **THEN** `QuoteCache.get('UNKNOWN.SA')` returns `None` and a flag indicating no data

### Requirement: QuoteCache returns multiple quotes in one call

The system SHALL provide a `QuoteCache.get_many(symbols)` method that
returns a dict mapping symbol to (price, currency, fresh) for every
symbol that has a row, omitting symbols that are missing.

#### Scenario: Batch read returns only stored symbols
- **WHEN** the cache holds fresh quotes for `PETR4.SA` and `AAPL`, but nothing for `TSLA`
- **THEN** `get_many(['PETR4.SA', 'AAPL', 'TSLA'])` returns `{'PETR4.SA': ..., 'AAPL': ...}` and omits `TSLA`

### Requirement: QuoteCache survives application restart

The system SHALL persist quotes in the same SQLite/Postgres database as
the rest of the application (not in-process memory), so a uvicorn reload
or container restart does not clear the cache. Quotes older than the
TTL SHALL be treated as stale on the next read, regardless of restart
history.

#### Scenario: Cache survives a reload
- **WHEN** the application stores a quote and then restarts
- **THEN** the next read for that symbol returns the stored price with the original `fetched_at` timestamp

