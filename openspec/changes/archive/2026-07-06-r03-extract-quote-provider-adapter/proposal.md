## Why

The `src/omaha/quotes/provider.py` module mixes the `QuoteProvider`
Protocol, the wire-format `Quote` dataclass, the pure `map_symbol`
helper, and the concrete `YFinanceProvider` in one 239-line file.
Consumers (`QuoteCache`, `OmahaMarketPriceLookup`,
`rebalance.quotes_adapter`) already couple to the `QuoteProvider`
Protocol — but `main.py:_start_quote_service` is the single line
that still imports `YFinanceProvider` directly. Today, swapping the
provider (e.g. for a brapi/Finnhub adapter, or for tests that want
a deterministic stub without monkeypatching) requires editing
`main.py`. The slice makes the seam real by promoting the file to a
package and routing the runtime wiring through a single selector.

## What Changes

- Replace `src/omaha/quotes/provider.py` with a `src/omaha/quotes/provider/` package:
  - `protocol.py` — `Quote` dataclass + `QuoteProvider` Protocol + `map_symbol` (pure helper that lives next to its contract).
  - `yfinance.py` — `YFinanceProvider` (moved verbatim, no behavior change).
  - `stub.py` — new `StubProvider` for tests + offline scenarios (configurable responses per symbol, no network).
  - `__init__.py` — re-exports `Quote`, `QuoteProvider`, `YFinanceProvider`, `StubProvider`, `map_symbol`, plus a `get_quote_provider()` selector.
- Add `Settings.QUOTE_PROVIDER` (`"yfinance"` default, `"stub"` alternative) driving the selector. Selector is the single import in `main.py:_start_quote_service`.
- Update `main.py` to call `get_quote_provider()` instead of importing `YFinanceProvider` directly. Same wire behavior — yfinance remains the default.
- No change to `QuoteCache`, `QuoteService`, `OmahaMarketPriceLookup`, `rebalance/quotes_adapter.py`. They already talk to `QuoteProvider` only through the Protocol; their imports move from `omaha.quotes.provider` to `omaha.quotes.provider` (the package), which re-exports the same names.
- Spec `quote-provider` gains three `ADDED` requirements codifying the new seam (see Capabilities).
- New tests:
  - `tests/test_quote_provider_selector.py` — selector resolves `QUOTE_PROVIDER=yfinance` → `YFinanceProvider`, `QUOTE_PROVIDER=stub` → `StubProvider`; unknown value raises a clear error.
  - `tests/test_quote_provider_stub.py` — `StubProvider.fetch` / `fetch_many` honor the configured responses and return `None` for unmapped symbols; per-symbol isolation holds.
- `tests/test_yfinance_provider.py` updates the import path from `omaha.quotes.provider` to the package (re-export keeps the old path working during the transition; removed at end of slice).
- `tests/conftest.py` `_UNIT_FILES` list extended for the two new test files.

No behavior change for the runtime path. No new dependency. No
migration. The yfinance branch stays default; the `StubProvider` is
opt-in via `OMAHA_QUOTE_PROVIDER=stub` (env var → pydantic setting).

## Capabilities

### New Capabilities

- `quote-provider-factory`: codifies the public selector
  (`get_quote_provider()`) and the `StubProvider` for tests. Lives
  next to the existing `quote-provider` spec because the contract
  shares the same `Quote` wire format.

### Modified Capabilities

- `quote-provider`: delta file
  `openspec/changes/r03-extract-quote-provider-adapter/specs/quote-provider/spec.md`
  adds three requirements:
  1. **Provider selector resolves from settings.** `get_quote_provider()`
     SHALL return the concrete provider named by `Settings.QUOTE_PROVIDER`
     (default `"yfinance"`); an unknown value SHALL raise a clear
     `ValueError`. The selector is the only sanctioned consumer entry
     point — `main.py` and any future wiring MUST go through it.
  2. **StubProvider exists in the package for tests + offline.**
     `StubProvider` SHALL live in `omaha.quotes.provider.stub` and
     implement `QuoteProvider` (structural Protocol). It SHALL honor a
     per-symbol response map (`{symbol: Quote | None}`) and return
     `None` for unmapped symbols. Per-symbol isolation in
     `fetch_many` SHALL match the `YFinanceProvider` contract (one
     bad symbol does not abort the batch).
  3. **Package layout.** The provider surface SHALL live under
     `src/omaha/quotes/provider/` (a package, not a module). Public
     re-exports at `omaha.quotes.provider.__init__` SHALL preserve
     the existing `Quote`, `QuoteProvider`, `YFinanceProvider`,
     `map_symbol` names so consumers migrate via a single import
     path change (no symbol rename).

## Impact

- **Code touched:**
  - `src/omaha/quotes/provider.py` (deleted, replaced by package)
  - `src/omaha/quotes/provider/__init__.py` (new, re-exports + selector)
  - `src/omaha/quotes/provider/protocol.py` (new, `Quote` + Protocol)
  - `src/omaha/quotes/provider/mapper.py` (new, `map_symbol` + regex constants)
  - `src/omaha/quotes/provider/yfinance.py` (new, moved from `provider.py`)
  - `src/omaha/quotes/provider/stub.py` (new, `StubProvider`)
  - `src/omaha/config.py` (add `QUOTE_PROVIDER: str = "yfinance"` + validator)
  - `src/omaha/main.py` (`_start_quote_service` imports `get_quote_provider` instead of `YFinanceProvider`)
- **Re-exports protect consumers:** `omaha.quotes.cache` and
  `omaha.quotes.service` keep their existing imports
  (`from omaha.quotes.provider import Quote, QuoteProvider`) because
  the package's `__init__.py` re-exports those names. Same for the
  rebalance layer (`rebalance/market_prices.py`,
  `rebalance/quotes_adapter.py`) — they don't import `YFinanceProvider`
  at all, so no change.
- **Tests touched:**
  - `tests/test_yfinance_provider.py` — single import-path tweak
    (`from omaha.quotes.provider import YFinanceProvider, map_symbol`
    still works via the re-export).
  - `tests/test_quote_service.py` — no change (uses local `_FakeProvider`,
    not the new package stub; both satisfy the Protocol structurally).
  - `tests/test_market_prices_adapter.py` — no change.
  - `tests/test_quote_provider_selector.py` (new).
  - `tests/test_quote_provider_stub.py` (new).
  - `tests/conftest.py` (`_UNIT_FILES` extended).
- **Specs touched:**
  - `openspec/specs/quote-provider/spec.md` — delta with 3 ADDED requirements.
  - `openspec/specs/quote-provider-factory/spec.md` — new capability (small,
    ~3 requirements).
- **Docs touched:** `DESIGN.md` §Component inventory gets a one-paragraph
  note that `QuoteProvider` is now a selectable package; `README.md`
  mentions `OMAHA_QUOTE_PROVIDER` env var (doc-only if D01 lands first).
- **Risk surface:** Low. The runtime path is byte-equivalent
  (`YFinanceProvider()` is what `get_quote_provider()` returns by
  default). The selector adds one indirection at startup only —
  the refresh loop and rebalance lookup never see the indirection.
  `StubProvider` is opt-in.
- **Critical-area flag:** the rebalance solver + cotação yfinance
  pair is the cap-1 critical area per the roadmap. R03 only adds
  one new module (`stub.py`) and one factory; the yfinance path is
  unchanged. Cap-1 holds during the `Applying` window because there
  is no concurrent critical-area work in `Spec Proposed`.