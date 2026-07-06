## 1. Package scaffold

- [x] 1.1 Create `src/omaha/quotes/provider/` directory with empty
  `__init__.py`. Keep the existing `src/omaha/quotes/provider.py`
  in place during the migration so imports don't break between
  commits.
- [x] 1.2 Add `omaha.quotes.provider` to the package list (Python
  discovers it automatically — verify with `python -c "import
  omaha.quotes.provider"`).

## 2. Move existing code into the package

- [x] 2.1 Create `src/omaha/quotes/provider/protocol.py` with the
  `Quote` dataclass and `QuoteProvider` Protocol (verbatim from
  `provider.py:101-129`).
- [x] 2.2 Create `src/omaha/quotes/provider/mapper.py` with
  `map_symbol`, `_BR_TICKER_RE`, `_CRYPTO_CODES` (verbatim from
  `provider.py:55-93`).
- [x] 2.3 Create `src/omaha/quotes/provider/yfinance.py` with
  `YFinanceProvider` (verbatim from `provider.py:137-236`). Update
  its imports to `from omaha.quotes.provider.mapper import
  map_symbol` and `from omaha.quotes.provider.protocol import
  Quote`.
- [x] 2.4 Re-export the four public names from
  `src/omaha/quotes/provider/__init__.py`:
  `Quote`, `QuoteProvider`, `YFinanceProvider`, `map_symbol`.
- [x] 2.5 Delete `src/omaha/quotes/provider.py` (the old single file).
- [x] 2.6 Run `python -c "from omaha.quotes.provider import Quote,
  QuoteProvider, YFinanceProvider, map_symbol"` to verify the
  re-exports resolve.

## 3. StubProvider

- [x] 3.1 Create `src/omaha/quotes/provider/stub.py` with
  `StubProvider` (per design D-R03.3: `responses` + `default`
  constructor args, `fetch` + `fetch_many` methods).
- [x] 3.2 Add `StubProvider` to the package's `__init__.py` re-exports.
- [x] 3.3 Write `tests/test_quote_provider_stub.py` covering:
  mapped symbol returns configured Quote; unmapped returns default
  None; unmapped returns configured default; `fetch_many` preserves
  input order; per-symbol None does not abort batch.

## 4. Selector + settings

- [x] 4.1 Add `QUOTE_PROVIDER: Literal["yfinance", "stub"] =
  "yfinance"` to `src/omaha/config.py` `Settings` class. Use
  pydantic-settings `Literal` so env validation happens at startup.
- [x] 4.2 Add `get_quote_provider()` function to
  `src/omaha/quotes/provider/__init__.py` (per design D-R03.2).
  Import `Settings` lazily inside the function to avoid module-level
  settings evaluation (mirrors `QuoteCache._is_postgres` style).
- [x] 4.3 Re-export `get_quote_provider` from
  `src/omaha/quotes/provider/__init__.py`.

## 5. Wire main.py through the selector

- [x] 5.1 In `src/omaha/main.py:_start_quote_service`, replace
  `from omaha.quotes.provider import YFinanceProvider` +
  `QuoteService(provider=YFinanceProvider())` with `from
  omaha.quotes.provider import get_quote_provider` +
  `QuoteService(provider=get_quote_provider())`.
- [x] 5.2 Verify `main.py` no longer references `YFinanceProvider`
  or `StubProvider` by direct import (`rg "YFinanceProvider|StubProvider"
  src/omaha/main.py` returns only the package import — the selector
  call).

## 6. Selector tests

- [x] 6.1 Write `tests/test_quote_provider_selector.py` covering:
  default settings resolve to `YFinanceProvider`; `stub` setting
  resolves to `StubProvider`; unknown value raises `ValueError`
  (via direct attribute bypass — pydantic-settings Literal already
  blocks construction; selector carries defense-in-depth); the
  selector does not cache (two calls return two distinct instances).
- [x] 6.2 Extend `tests/conftest.py::_UNIT_FILES` with
  `test_quote_provider_selector.py` and `test_quote_provider_stub.py`.

## 7. Update existing test imports

- [x] 7.1 `tests/test_yfinance_provider.py`: patch target updated
  from `omaha.quotes.provider.yf.Ticker` to
  `omaha.quotes.provider.yfinance.yf.Ticker` (6 occurrences). The
  `from omaha.quotes.provider import YFinanceProvider, map_symbol`
  import at the top continues to resolve via the package re-export.
- [x] 7.2 `tests/test_quote_service.py`: no change (uses local
  `_FakeProvider`, not the package's `StubProvider`).
- [x] 7.3 `tests/test_market_prices_adapter.py`: no change.

## 8. Verify

- [x] 8.1 Run `task test-unit` — 271 passed / 2 skipped (+10 from
  pre-slice 261: 4 selector + 6 stub).
- [x] 8.2 Run `task test-integration` — 369 passed / 2 skipped
  (no regression; startup wiring still works).
- [x] 8.3 Run `ruff check` + `ruff format --check` on the new
  package + new tests + touched files — all clean.
- [x] 8.4 Run `openspec validate r03-extract-quote-provider-adapter
  --json` and confirm `valid: true`.
- [x] 8.5 Smoke run: bypass pydantic-validation,
  `Settings(); settings.QUOTE_PROVIDER = "brapi";
  get_quote_provider()` → `ValueError: unknown QUOTE_PROVIDER: 'brapi'`
  (defense-in-depth path).
- [x] 8.6 Smoke run: default → `YFinanceProvider`;
  `Settings(QUOTE_PROVIDER="stub")` → `StubProvider`.
