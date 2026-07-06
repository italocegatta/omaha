# quote-provider-factory Specification

## Purpose

Codifies the runtime seam between application wiring and the
concrete quote-provider implementation — the
`get_quote_provider()` selector driven by `Settings.QUOTE_PROVIDER`
and the `StubProvider` implementation that let the runtime swap the
active provider without touching the consumers (`QuoteCache`,
`QuoteService`, `OmahaMarketPriceLookup`,
`rebalance/quotes_adapter`).

This spec lives next to [`quote-provider`](./quote-provider/spec.md)
(the contract every provider must satisfy) because the selector + stub
are about **plumbing**, not about how a provider fetches a quote.
Splitting the two keeps the fetch contract (`QuoteProvider` Protocol
+ symbol-mapping rules) separate from the wiring concern (which
provider the process actually uses).

## Requirements

### Requirement: Selector is the single consumer entry point

The system SHALL expose a `get_quote_provider()` function that
returns the concrete `QuoteProvider` named by
`Settings.QUOTE_PROVIDER`. Application startup wiring
(`main.py:_start_quote_service`) SHALL call this function instead
of importing a concrete provider class directly.

#### Scenario: Startup wiring goes through the selector

- **WHEN** the FastAPI application starts up
- **THEN** `_start_quote_service` calls `get_quote_provider()` and
  passes the result to `QuoteService(provider=...)`
- **AND** `_start_quote_service` does NOT import `YFinanceProvider`
  or `StubProvider` directly

#### Scenario: Selector is callable from any module

- **WHEN** any consumer runs `from omaha.quotes.provider import
  get_quote_provider`
- **THEN** the import succeeds and the function is callable

### Requirement: StubProvider is the test/offline implementation

The system SHALL provide a `StubProvider` class in
`omaha.quotes.provider.stub` that implements the `QuoteProvider`
Protocol structurally. The class SHALL be the canonical offline
provider used by integration tests that want to exercise
`QuoteService.refresh_once` without hitting the network.

#### Scenario: StubProvider satisfies the Protocol structurally

- **WHEN** `isinstance(StubProvider(), QuoteProvider)` is checked at
  runtime
- **THEN** the check passes (structural Protocol satisfaction)

#### Scenario: StubProvider honors a response map

- **WHEN** a `StubProvider` is constructed with
  `responses={"PETR4.SA": <Quote>, "INVALID": None}`
- **THEN** `fetch("PETR4.SA")` returns the configured Quote
- **AND** `fetch("INVALID")` returns `None`
- **AND** `fetch("UNMAPPED")` returns `None` (fall-through default)

#### Scenario: StubProvider isolates per-symbol failures

- **WHEN** a `StubProvider` is constructed with
  `responses={"A": <Quote_a>}`
- **AND** `fetch_many(["A", "B", "C"])` is called
- **THEN** the result is `[Quote_a, None, None]` in input order

### Requirement: Settings drive the selector

The system SHALL define a `QUOTE_PROVIDER` setting on
`Settings` (pydantic-settings) that accepts the literal values
`"yfinance"` and `"stub"`. The default SHALL be `"yfinance"`. A
value outside the allowed set SHALL fail at pydantic-settings
validation time so the app does not start.

#### Scenario: Default setting resolves to yfinance

- **WHEN** `Settings()` is instantiated with no overrides
- **THEN** `Settings.QUOTE_PROVIDER == "yfinance"`
- **AND** `get_quote_provider()` returns a `YFinanceProvider`

#### Scenario: Environment variable override

- **WHEN** the environment sets `OMAHA_QUOTE_PROVIDER=stub`
- **THEN** `Settings.QUOTE_PROVIDER == "stub"`
- **AND** `get_quote_provider()` returns a `StubProvider`

#### Scenario: Invalid value fails at validation time

- **WHEN** the environment sets `OMAHA_QUOTE_PROVIDER=brapi`
- **THEN** `Settings()` instantiation raises a pydantic validation
  error
- **AND** the FastAPI startup hook never runs
