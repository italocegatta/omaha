## ADDED Requirements

### Requirement: Provider selector resolves from settings

The system SHALL expose a `get_quote_provider()` factory in
`omaha.quotes.provider` that returns the concrete provider named by
`Settings.QUOTE_PROVIDER`. The default value SHALL be `"yfinance"`,
which resolves to a `YFinanceProvider` instance. When
`Settings.QUOTE_PROVIDER == "stub"`, the factory SHALL return a
`StubProvider`. For any other value, the factory SHALL raise
`ValueError` with the offending value quoted so a misconfigured
deploy fails loudly at startup.

The selector SHALL be the only sanctioned consumer entry point for
wiring a `QuoteProvider` into `QuoteService`. Direct imports of
`YFinanceProvider` from application code (outside the
`omaha.quotes.provider` package itself) SHALL NOT occur in production
runtime paths.

#### Scenario: Default settings resolve to YFinanceProvider

- **WHEN** `Settings.QUOTE_PROVIDER == "yfinance"` (the default)
- **THEN** `get_quote_provider()` returns a `YFinanceProvider` instance

#### Scenario: Stub setting resolves to StubProvider

- **WHEN** `Settings.QUOTE_PROVIDER == "stub"`
- **THEN** `get_quote_provider()` returns a `StubProvider` instance

#### Scenario: Unknown provider name raises ValueError

- **WHEN** `Settings.QUOTE_PROVIDER == "brapi"` (or any other value
  not in the allowed set)
- **THEN** `get_quote_provider()` raises `ValueError` with the value
  quoted in the message

### Requirement: StubProvider exists in the package for tests + offline

The system SHALL provide a `StubProvider` in
`omaha.quotes.provider.stub` that implements `QuoteProvider` via
structural typing (no inheritance). The `StubProvider` SHALL be
configurable via two constructor arguments:

* `responses: dict[str, Quote | None]` — per-symbol response map.
  Symbols present in the map return the mapped value (a `Quote` or
  `None`). Symbols absent from the map fall through to `default`.
* `default: Quote | None` — value returned for unmapped symbols
  (`None` when not provided).

`fetch` SHALL return the mapped value (or `default` for unmapped
symbols) without raising. `fetch_many` SHALL call `fetch` once per
input symbol and return the per-symbol results in input order, with
the same per-symbol isolation contract as `YFinanceProvider` (one
symbol that returns `None` SHALL NOT abort the batch).

#### Scenario: Mapped symbol returns configured Quote

- **WHEN** `StubProvider(responses={"PETR4.SA": Quote(...)})` receives
  `fetch("PETR4.SA")`
- **THEN** it returns the configured `Quote`

#### Scenario: Unmapped symbol returns default None

- **WHEN** `StubProvider()` receives `fetch("UNKNOWN")`
- **THEN** it returns `None`

#### Scenario: Unmapped symbol returns configured default

- **WHEN** `StubProvider(default=Quote(...))` receives
  `fetch("UNKNOWN")`
- **THEN** it returns the configured default `Quote`

#### Scenario: fetch_many preserves input order

- **WHEN** `StubProvider(responses={"A": Quote_a, "B": Quote_b})`
  receives `fetch_many(["B", "A", "MISSING"])`
- **THEN** the result is `[Quote_b, Quote_a, None]` in that order

#### Scenario: Per-symbol None does not abort fetch_many

- **WHEN** `StubProvider(responses={"A": Quote_a})` receives
  `fetch_many(["A", "MISSING", "A"])`
- **THEN** the result is `[Quote_a, None, Quote_a]` (one bad symbol
  does not poison the batch)

### Requirement: Provider lives in a package, public names preserved

The system SHALL organize the quote-provider surface as a Python
package at `src/omaha/quotes/provider/` (a directory with an
`__init__.py`), not a single module file. The package `__init__.py`
SHALL re-export the following public names so existing consumer
imports continue to work without changes:

* `Quote` (the wire-format dataclass)
* `QuoteProvider` (the typing.Protocol)
* `YFinanceProvider` (the yfinance-backed implementation)
* `map_symbol` (the pure symbol-mapping helper)
* `StubProvider` (the test/offline implementation, new in this slice)
* `get_quote_provider` (the settings-driven selector, new in this slice)

The internal submodule layout SHALL keep `Quote` and `QuoteProvider`
in `protocol.py`, `map_symbol` and the B3/crypto regex constants in
`mapper.py`, `YFinanceProvider` in `yfinance.py`, and `StubProvider`
in `stub.py`. The internal submodules are an implementation detail;
consumers SHALL import from `omaha.quotes.provider` (the package) only.

#### Scenario: Existing import path resolves to the package

- **WHEN** any consumer runs `from omaha.quotes.provider import Quote,
  QuoteProvider, YFinanceProvider, map_symbol`
- **THEN** all four names resolve via the package re-exports

#### Scenario: Consumer imports StubProvider via the package

- **WHEN** a test runs `from omaha.quotes.provider import StubProvider`
- **THEN** `StubProvider` resolves to the implementation in
  `omaha.quotes.provider.stub`

#### Scenario: Selector importable from the package root

- **WHEN** `main.py` runs `from omaha.quotes.provider import
  get_quote_provider`
- **THEN** the selector function is imported (no direct
  `YFinanceProvider` import in `main.py`)