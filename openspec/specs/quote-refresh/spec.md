# quote-refresh Specification

## Purpose
TBD - created by archiving change add-market-quote-service. Update Purpose after archive.
## Requirements
### Requirement: QuoteService runs a background refresh loop

The system SHALL start an `asyncio` task in the FastAPI
`on_event("startup")` hook that periodically refreshes quotes for
all asset classes whose `quote_kind = auto`. The task SHALL be
cancelled in `on_event("shutdown")`. The refresh interval SHALL be
configurable via env var `QUOTE_REFRESH_INTERVAL_SECONDS`, defaulting
to 900 seconds (15 minutes).

#### Scenario: Loop starts at application boot
- **WHEN** the FastAPI application starts (and `OMAHA_SKIP_STARTUP != 1`)
- **THEN** a background task is created and starts the refresh loop

#### Scenario: Loop refreshes AUTO classes
- **WHEN** the loop runs and the database contains 2 asset classes with `quote_kind = auto` (Ações BR, Ações US) and 1 with `quote_kind = none` (Renda Fixa)
- **THEN** the loop queries yfinance for the symbols under the 2 AUTO classes
- **AND** the loop does NOT query yfinance for symbols under the Renda Fixa class

#### Scenario: Loop runs at the configured interval
- **WHEN** `QUOTE_REFRESH_INTERVAL_SECONDS = 60` and the loop completes a refresh
- **THEN** the next refresh starts ~60 seconds after the previous one finished

#### Scenario: Loop is cancelled on shutdown
- **WHEN** the FastAPI application shuts down
- **THEN** the background task is cancelled and does not log a stack trace

### Requirement: QuoteService refresh tolerates yfinance intermittent failures

The system SHALL handle intermittent yfinance failures (timeouts,
404s, 429 rate limits, empty responses, network errors) without
crashing the loop, blocking the event loop, or flooding the log.

#### Scenario: Single symbol failure does not abort the batch
- **WHEN** a refresh batch of 10 symbols is in progress and the 3rd symbol times out
- **THEN** the 3rd symbol is marked failed and the remaining 7 symbols are still fetched
- **AND** the loop continues to the next iteration

#### Scenario: Circuit breaker opens after consecutive full-batch failures
- **WHEN** 3 consecutive refresh attempts fail entirely (e.g. yfinance unreachable)
- **THEN** the circuit breaker opens and the loop pauses for a cool-down period (`QUOTE_REFRESH_CIRCUIT_COOLDOWN_SECONDS`, default 300s = 5min)
- **AND** during the cool-down, no HTTP requests are made to yfinance
- **AND** the log emits one `error` line per failed batch (not per symbol)

#### Scenario: Circuit breaker closes after cool-down
- **WHEN** the cool-down period elapses
- **THEN** the next refresh attempt runs normally
- **AND** if it succeeds, the circuit breaker is closed
- **AND** if it fails, the cool-down restarts

#### Scenario: Partial refresh is a success
- **WHEN** a refresh of 10 symbols succeeds for 7 and fails for 3
- **THEN** the 7 successful quotes are written to the cache
- **AND** the loop logs a `warn` line summarizing the partial result (`refreshed 7/10`)
- **AND** the circuit breaker is NOT tripped (partial failure does not count toward the consecutive-failure threshold)

#### Scenario: Refresh is non-blocking with request handlers
- **WHEN** a refresh is in progress and a request hits `GET /api/quotes/PETR4.SA`
- **THEN** the request returns from the cache within 50ms regardless of the refresh state

### Requirement: QuoteService exposes a manual refresh trigger

The system SHALL expose a `POST /api/quotes/refresh` endpoint that
forces an immediate refresh, intended to be called by the future
portfolio optimization feature before it reads quotes. The trigger
SHALL NOT block the caller: it returns `202 Accepted` as soon as the
refresh task is scheduled. The background loop and the manual
trigger MUST serialize their writes to the cache (no overlapping
refreshes of the same symbol).

#### Scenario: Trigger schedules a refresh
- **WHEN** a client calls `POST /api/quotes/refresh`
- **THEN** the server returns `202 Accepted` within 100ms
- **AND** a refresh task is scheduled in the event loop

#### Scenario: Trigger and background loop do not overlap
- **WHEN** the background loop is mid-refresh and `POST /api/quotes/refresh` is called
- **THEN** the manual refresh waits for the background refresh to complete before starting

#### Scenario: Trigger is the integration point for the future optimizer
- **WHEN** the (future) portfolio optimization feature needs fresh quotes
- **THEN** it SHALL call `POST /api/quotes/refresh` to force an update before reading from the cache
- **AND** the response code 202 signals "refresh scheduled" — the optimizer should not poll; it reads the cache directly after a short delay

### Requirement: QuoteService reads symbols from the database

The system SHALL build the list of symbols to refresh by querying
the database for asset classes with `quote_kind = auto` and their
underlying positions' `broker_ticker` values. Symbols with no
position SHALL NOT be refreshed (the cache is fed by real holdings).

#### Scenario: Symbol list reflects current positions
- **WHEN** the database contains 5 positions under AUTO classes and 3 positions under NONE classes
- **THEN** the refresh fetches only the 5 AUTO-class symbols
