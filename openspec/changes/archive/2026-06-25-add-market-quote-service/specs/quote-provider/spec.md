## ADDED Requirements

### Requirement: QuoteProvider interface

The system SHALL define a `QuoteProvider` protocol with a method
`async def fetch(symbol: str) -> Quote | None` that returns a
`Quote` (price, currency) or `None` if the provider could not
resolve the symbol. All concrete providers (yfinance, future brapi)
MUST implement this interface so that consumer code is decoupled
from the source.

#### Scenario: Provider returns a Quote for a known symbol
- **WHEN** a provider fetches a symbol it recognizes
- **THEN** it returns a `Quote` with non-None `price` and `currency`

#### Scenario: Provider returns None for an unknown symbol
- **WHEN** a provider fetches a symbol it does not recognize
- **THEN** it returns `None` and does not raise

### Requirement: YFinanceProvider maps Brazilian tickers to .SA suffix

The system SHALL, for symbols whose name matches the Brazilian
ticker pattern (uppercase letters followed by a digit and a digit,
or a 6-letter code ending in `11` for FIIs/ETFs/BDRs), append `.SA`
when delegating to yfinance.

#### Scenario: BR stock ticker is suffixed
- **WHEN** the provider fetches `PRIO3`
- **THEN** it queries yfinance for `PRIO3.SA`

#### Scenario: FII ticker is suffixed
- **WHEN** the provider fetches `HGLG11`
- **THEN** it queries yfinance for `HGLG11.SA`

#### Scenario: BDR ticker is suffixed
- **WHEN** the provider fetches `IVVB11`
- **THEN** it queries yfinance for `IVVB11.SA`

### Requirement: YFinanceProvider passes US tickers through

The system SHALL, for symbols whose name is an uppercase US ticker
(no `.SA` suffix, no recognized crypto / FX pattern), query yfinance
with the symbol verbatim.

#### Scenario: US stock ticker is not modified
- **WHEN** the provider fetches `AAPL`
- **THEN** it queries yfinance for `AAPL`

#### Scenario: US ETF ticker is not modified
- **WHEN** the provider fetches `SMH`
- **THEN** it queries yfinance for `SMH`

### Requirement: YFinanceProvider maps BTC to BTC-USD

The system SHALL, when the symbol is `BTC` (or another recognized
crypto code), query yfinance for `<CODE>-USD` to obtain a USD price.

#### Scenario: Bitcoin is fetched as BTC-USD
- **WHEN** the provider fetches `BTC`
- **THEN** it queries yfinance for `BTC-USD`
- **AND** the returned `Quote.currency` is `USD`

### Requirement: YFinanceProvider returns BRL=X for FX

The system SHALL, when the symbol matches the FX pattern
(`BRL=X`, `USDBRL=X`, `BRLUSD=X`), query yfinance with the same
symbol and return the price in the appropriate currency.

#### Scenario: BRL=X is fetched as a USD/BRL rate
- **WHEN** the provider fetches `BRL=X`
- **THEN** it queries yfinance for `BRL=X`
- **AND** the returned `Quote.currency` is `BRL`
- **AND** the price represents 1 USD in BRL (e.g. 5.18)

### Requirement: YFinanceProvider tolerates per-symbol failures

The system SHALL, when fetching a batch of symbols, isolate each
symbol's failure: a 404, timeout, or empty response for one symbol
MUST NOT abort the batch. Failed symbols are returned as `None` in
the batch result; successful symbols return their `Quote`.

#### Scenario: One bad symbol does not poison the batch
- **WHEN** the provider fetches `['PETR4.SA', 'INVALID_XYZ', 'AAPL']` and `INVALID_XYZ` 404s
- **THEN** the result is `[Quote(PETR4.SA), None, Quote(AAPL)]`

#### Scenario: Timeout on one symbol does not block others
- **WHEN** the provider fetches `['AAPL', 'SLOW', 'MSFT']` and `SLOW` times out after 10s
- **THEN** the result is `[Quote(AAPL), None, Quote(MSFT)]` within ~10s + overhead

### Requirement: YFinanceProvider uses asyncio.to_thread for yfinance calls

The system SHALL wrap each `yfinance.Ticker(...).fast_info` call in
`asyncio.to_thread(...)` so the synchronous yfinance library does
not block the FastAPI event loop.

#### Scenario: Event loop stays responsive during a refresh
- **WHEN** the provider fetches 50 symbols in a batch
- **THEN** the FastAPI event loop can serve other requests during the batch (verified by a concurrent request returning within 1s)
