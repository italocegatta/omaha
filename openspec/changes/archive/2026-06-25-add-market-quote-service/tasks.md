## 1. Setup

- [x] 1.1 Add `yfinance>=1.4` to `[project].dependencies` in `pyproject.toml`; run `uv sync` to refresh the lock
- [x] 1.2 Add `QUOTE_TTL_SECONDS` (default `900`), `QUOTE_REFRESH_INTERVAL_SECONDS` (default `900`), `QUOTE_REFRESH_CIRCUIT_COOLDOWN_SECONDS` (default `300`), and `QUOTE_REFRESH_CIRCUIT_THRESHOLD` (default `3`) to `omaha.config.Settings`; verify `.env.example` documents the new vars
- [x] 1.3 Confirm `yfinance.Ticker("PETR4.SA").fast_info["last_price"]` works in this environment (smoke test in a `uv run python -c` one-liner)

## 2. Schema

- [x] 2.1 Add `Quote` SQLAlchemy model in `src/omaha/models.py` with columns `symbol` (TEXT PK), `price` (NUMERIC(18,4)), `currency` (TEXT), `fetched_at` (TIMESTAMP)
- [x] 2.2 Add `QuoteKind` enum (`auto`, `manual`, `none`) and `quote_kind` column to `AssetClass` in `src/omaha/models.py` (String(8), NOT NULL, default `none`, CHECK constraint)
- [x] 2.3 Generate Alembic revision `0014_add_quote_cache_and_quote_kind.py` with `alembic revision --autogenerate -m "add quote cache and quote_kind"`; review the generated DDL matches the model
- [x] 2.4 Run `uv run task db-migrate` against the dev DB; confirm both `quotes` table exists and `asset_classes.quote_kind` column is `none` for every existing row
- [x] 2.5 Add `quote_kind` to the `data/seed/{profile}_classes.csv` schema (default `none`); run `uv run task db-seed-from-csv --mode diff` to verify the existing seed file is compatible; add a test fixture for a class with `quote_kind = auto`

## 3. Quote cache

- [x] 3.1 Create `src/omaha/quotes/__init__.py` (empty package marker) and `src/omaha/quotes/cache.py`
- [x] 3.2 Implement `QuoteCache.upsert(quote: Quote)` using a short-lived SQLAlchemy session; uses `INSERT ... ON CONFLICT(symbol) DO UPDATE` (SQLite) / `ON CONFLICT ... DO UPDATE` (Postgres) — verify against both engines
- [x] 3.3 Implement `QuoteCache.get(symbol) -> Quote | None` returning a `Quote` plus a `fresh: bool` flag computed from `QUOTE_TTL_SECONDS` and `fetched_at`
- [x] 3.4 Implement `QuoteCache.get_many(symbols) -> dict[str, QuoteWithFreshness]`
- [x] 3.5 Write `tests/test_quote_cache.py` (integration — add `tests/test_quote_` prefix to `_INTEGRATION_PREFIXES` in `tests/conftest.py`); cover fresh/stale/missing/upsert-race cases

## 4. Quote provider

- [x] 4.1 Create `src/omaha/quotes/provider.py` with the `QuoteProvider` `Protocol` and a `Quote` dataclass (`symbol`, `price: Decimal`, `currency`, `fetched_at`)
- [x] 4.2 Implement `YFinanceProvider` with a `fetch(symbol: str) -> Quote | None` method that detects BR / US / crypto / FX and calls yfinance with the mapped ticker
- [x] 4.3 Implement `YFinanceProvider.fetch_many(symbols) -> list[Quote | None]` that runs each `Ticker.fetch` via `asyncio.to_thread` and isolates per-symbol exceptions; uses a per-batch `yf.Ticker` cache to avoid warmup cost
- [x] 4.4 Write `tests/test_yfinance_provider.py` (unit — uses `unittest.mock` to stub `yfinance.Ticker`); cover BR `.SA` mapping, US pass-through, BTC → BTC-USD, BRL=X, and per-symbol-failure isolation
- [x] 4.5 Add `httpx>=0.27` to dev dependencies only (used by the integration test client; not the runtime provider)

## 5. Refresh service

- [x] 5.1 Create `src/omaha/quotes/service.py` with `QuoteService` class: holds a `QuoteCache`, a `QuoteProvider`, an `asyncio.Lock`, the symbol list, and the circuit-breaker state (consecutive failures + last-failure timestamp)
- [x] 5.2 Implement `QuoteService.refresh_once() -> RefreshReport` that:
  - Acquires the lock
  - Queries the DB for symbols under `quote_kind = auto` classes
  - Calls `provider.fetch_many(symbols)`
  - Writes successful results to the cache
  - Updates circuit-breaker state (partial failure does not increment)
  - Returns a `RefreshReport` (`refreshed: int`, `failed: int`, `circuit_open: bool`)
- [x] 5.3 Implement `QuoteService.run_forever()` as an `async` loop: `refresh_once()` → `await asyncio.sleep(interval + random.uniform(0, 30))` → repeat; on `CancelledError` (shutdown), exit cleanly
- [x] 5.4 Write `tests/test_quote_service.py` (integration): test partial success does not trip the circuit; 3 consecutive full failures open the breaker; the breaker closes after cool-down
- [x] 5.5 Wire `QuoteService.run_forever` into `on_event("startup")` in `src/omaha/main.py`; wire `task.cancel()` into `on_event("shutdown")`; respect `OMAHA_SKIP_STARTUP=1`

## 6. API

- [x] 6.1 Create `src/omaha/routes/quotes.py` with the `router` (prefix `/api/quotes`)
- [x] 6.2 Implement `GET /api/quotes/{symbol}` returning `{symbol, price, currency, fetched_at, fresh}`; 404 if missing
- [x] 6.3 Implement `GET /api/quotes?symbols=A,B,C` returning `{results: [...]}`; 200 with empty list if no symbols match
- [x] 6.4 Implement `POST /api/quotes/refresh`: schedules a `service.refresh_once()` task via `asyncio.create_task`, returns `202 Accepted` with `{status: "scheduled"}`; reuses the service lock so it does not overlap with the background loop
- [x] 6.5 Include the `quotes` router in `app.include_router(...)` in `src/omaha/main.py`
- [x] 6.6 Write `tests/test_quote_routes.py` (integration): test the GET endpoints, the 202 trigger, and that the trigger is non-blocking (request returns < 100ms even when the service is mid-refresh)

## 7. CSV seed integration

- [x] 7.1 Update `data/seed/README.md` to document the new `quote_kind` column on `{profile}_classes.csv`; default `none`
- [x] 7.2 Update `scripts/seed_from_csv.py` to read and validate the `quote_kind` column (must be one of `auto` / `manual` / `none`; reject unknown values)
- [x] 7.3 Add a test fixture `data/seed/fixtures/auto_class.csv` (1 class with `quote_kind = auto`) and assert `uv run task db-seed-from-csv --mode diff` accepts it without warnings

## 8. Verification

- [x] 8.1 `uv run task lint` — ruff format + ruff --fix pass
- [x] 8.2 `uv run task test-unit` — full unit suite green (the new `test_yfinance_provider.py` is unit; `test_quote_cache.py` and `test_quote_service.py` are integration)
- [x] 8.3 `uv run task test-integration` — full integration suite green with the new `tests/test_quote_*` files marked correctly via `_INTEGRATION_PREFIXES`
- [x] 8.4 Manual smoke: `uv run task serve`, then on the LAN client machine:
  - `curl http://<lan-ip>:8000/api/quotes/PETR4.SA` → returns a Quote
  - `curl -X POST http://<lan-ip>:8000/api/quotes/refresh` → 202
  - Watch server log for `refreshed N/M` lines and circuit-breaker activity
- [x] 8.5 Confirm `uv run task db-reset` still works end-to-end (idempotent seed + migration + asset + position + new `quote_kind = none` default)
