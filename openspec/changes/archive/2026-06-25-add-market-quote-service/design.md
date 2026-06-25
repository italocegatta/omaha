## Context

The omaha app is a single-process FastAPI + SQLAlchemy 2 / Alembic /
SQLite (dev) / Postgres (prod) family portfolio tracker. Current
data model (see `src/omaha/models.py`): `User` → `Profile` →
`AssetClass` → `Asset` → `Position` (broker_ticker + qty + prices).
Existing slices cover S01 (auth), S02 (class editor), S03 (asset
editor), S04 (CSV import), S05 (dashboard). The
`csv-driven-asset-seed` change (in progress) adds the CSV triplet
seed path.

Two facts shape the design:

1. **The CSV importer is the broker price source.** `Position.current_price`
   is what the broker reported in the last import. The dashboard uses
   `qty × current_price` to compute the portfolio's `current_value`.
   The user wants live quotes to *complement* the broker price, not
   replace it (CDB/RDB/Tesouro have no live quote, only the broker
   has the official number).
2. **yfinance is the only free, no-API-key library that covers BR
   (.SA suffix), US, FX (BRL=X), and crypto (BTC-USD) in one
   place.** yfinance is a synchronous scraper of Yahoo's
   semi-public APIs; it can be slow, time out, or 404 on
   individual symbols. brapi.dev has a richer BR API (with Tesouro
   Direto and PTAX FX), but requires a token and has a free-tier
   limit. We start with yfinance alone and put it behind a
   `QuoteProvider` interface so brapi can be added later without
   touching consumers.

The future portfolio optimization feature (out of scope for this
change) needs fresh quotes. The contract is: this change exposes a
trigger (`POST /api/quotes/refresh`) that the optimizer will call
before reading the cache. The cache is the integration point, not
the optimizer's own state.

## Goals / Non-Goals

**Goals:**
- Cache market quotes for AUTO-class positions in a DB table with TTL
- Resilient refresh loop: tolerates Yahoo being down/slow without
  crashing the server, blocking the event loop, or flooding the log
- Pluggable provider behind a `QuoteProvider` interface
- Trigger endpoint for the future optimizer to force-refresh
- Mark assets as `none` / `manual` / `auto` so the user controls
  what gets refreshed; CDB/RDB/Tesouro default to `none` (no fetch)
- Survive uvicorn reload (DB-backed, not in-memory)

**Non-Goals:**
- UI to display quotes (separate change, S05 follow-up)
- Portfolio optimization / rebalancing (separate change)
- brapi / AwesomeAPI / Finnhub integration (interface allows it
  later; no implementation in this change)
- Streaming via yfinance `AsyncWebSocket` (poll is enough for the
  trigger-based model)
- Cache invalidation UI / manual purge (use TTL + admin SQL)
- Multi-process refresh coordination (single uvicorn worker;
  if we ever scale to multiple workers, add a DB advisory lock)

## Decisions

### D1: yfinance as the sole provider, behind an interface

**Choice:** yfinance 1.4+ via a `YFinanceProvider` class that
implements a `QuoteProvider` protocol. No brapi / Finnhub in this
change.

**Rationale:** yfinance covers BR + US + FX + crypto with one
dependency, no API key, and a probe of all 47 tradeable symbols in
`tests/posicao_italo.csv` returned a price for every single one
(35 .SA tickers, 7 US tickers, 1 BTC-USD; one CSV summary row
`"48 ativos"` was filtered as metadata, not a real symbol).
brapi.dev would be a better fit for BR-specific data (it has
Tesouro Direto quotes and official PTAX FX from BCB), but it
needs an API key, has a free-tier limit, and adding it doubles
the dependency surface for marginal gain. Behind a
`QuoteProvider` protocol, brapi becomes a drop-in addition later.

**Alternatives considered:**
- *brapi + yfinance dual-provider:* rejected for v1 because of the
  API-key onboarding and the small set of assets where the
  difference matters (Tesouro Direto). Easy to add behind the
  interface later.
- *yahooquery:* rejected because the last release was May 2025
  (stale) and yfinance 1.4+ is more current with similar coverage.
- *Custom httpx + Yahoo's undocumented v8/quoteSummary endpoint:*
  rejected because scraping Yahoo's HTML/JSON is exactly what
  yfinance already does, and yfinance is maintained by the
  community. No upside.

### D2: DB-backed cache, not in-process dict

**Choice:** Persist quotes in a `quotes` table (SQLAlchemy model,
Alembic migration). The cache is read by the same SQLAlchemy
session as the rest of the app.

**Rationale:** Matches the existing `import_previews` table
pattern (TTL via `created_at` timestamp, row-level read). Survives
`uvicorn --reload` restarts in dev — important because the dev
server reloads on every code change, and a reload that drops the
in-process cache would force Yahoo to be hit on the next refresh
even if the quotes are seconds old. The dashboard / future
optimizer can read the cache via a single SQL query, no Python
state to coordinate.

**Alternatives considered:**
- *In-process `dict[Symbol, Quote]` with TTL:* survives requests
  but dies on reload, and a single-process dict is invisible to
  tests and the BDD layer.
- *Redis:* adds a dependency for a 1-user, 1-process app.
  Overkill.

### D3: `quote_kind` enum on `AssetClass`, default `none`

**Choice:** Add `quote_kind: enum('auto', 'manual', 'none')` to
`AssetClass`, defaulting to `none` for existing rows. The
QuoteService filters on `quote_kind = auto` to build the symbol
list.

**Rationale:** Matches the user's mental model — a class
("Renda Fixa", "Ações BR", "Ações US") is the natural unit of
policy. One toggle flips behavior for all assets under the class.
The `none` default is conservative: existing classes do not start
fetching until the user explicitly opts in via the class editor
or directly in the CSV seed. This avoids surprise network calls
on first deploy.

**Alternatives considered:**
- *Per-asset `quote_kind` with class default:* over-engineered for
  the current data (every asset in a class shares the same kind in
  every case observed). Nullable column with class fallback could
  be added later if the use case appears.
- *Heuristic from class name (`Renda Fixa` → none, `Ações` →
  auto):* rejected for being magic and brittle. Explicit toggle
  is the principle of least surprise.

### D4: Background loop + manual trigger, both writing to the same cache

**Choice:** An `asyncio` task started in `on_event("startup")`
runs a refresh loop at `QUOTE_REFRESH_INTERVAL_SECONDS` (default
900s). A `POST /api/quotes/refresh` endpoint forces an immediate
refresh. Both paths acquire the same `asyncio.Lock` so they
don't write concurrently. The endpoint returns `202 Accepted`
immediately; the caller reads the cache after a short delay (the
future optimizer will do this).

**Rationale:** The user explicitly asked for both: an
auto-refresh that handles Yahoo being intermittent, AND a
trigger that the future optimizer will call. The background loop
keeps quotes warm during normal use; the trigger gives the
optimizer a way to demand fresh data without waiting for the
next loop tick. The lock prevents two concurrent refreshes
from racing on the same row (a `UPSERT` from one path
interleaved with an `UPSERT` from the other is safe at the row
level, but wasted HTTP calls + a confusing log line).

**Alternatives considered:**
- *Trigger only, no loop:* the user has to click "optimize" to
  ever see fresh quotes. Bad for the (future) dashboard view
  that might want to show "as of HH:MM" freshness.
- *Loop only, no trigger:* the future optimizer would have to
  either wait for the next loop tick (up to 15min) or skip
  freshness. Bad.
- *Lock-free with row-level `INSERT ... ON CONFLICT UPDATE`:*
  technically safe at the row level, but two concurrent
  refreshes both hit Yahoo for the same symbols. Wasteful.

### D5: Circuit breaker for Yahoo outage, partial success is success

**Choice:** Track consecutive full-batch failures. After 3, open
a circuit breaker that pauses refreshes for
`QUOTE_REFRESH_CIRCUIT_COOLDOWN_SECONDS` (default 300s). During
the pause, the loop sleeps without hitting Yahoo. A partial
failure (some symbols succeed, some fail) does NOT count toward
the threshold.

**Rationale:** The probe showed Yahoo is intermittent (PSEC11
timed out once but succeeded on retry). A loop that retries
forever on full failure will burn CPU and log noise. A loop
that gives up on partial failure will miss valid quotes. The
circuit-breaker pattern is the standard fix: fail fast, back
off, retry later.

**Alternatives considered:**
- *No circuit breaker, just exponential backoff per attempt:*
  works but ties up the event loop if Yahoo is fully down for
  hours.
- *Retry with `tenacity` library:* adds a dependency for one
  decorator. The hand-rolled `for attempt in range(3):
  try ... except ... await asyncio.sleep(2 ** attempt)` is
  8 lines and equally clear.

### D6: yfinance wrapped in `asyncio.to_thread`, not AsyncWebSocket

**Choice:** Each `yf.Ticker(symbol).fast_info` call runs in
`asyncio.to_thread(...)`. The loop is `asyncio.sleep(interval)`
between batches. No use of `yfinance.AsyncWebSocket`.

**Rationale:** yfinance's `AsyncWebSocket` is a streaming
client — it pushes every tick Yahoo sends, which for a
1-user/family app is wasteful and means the cache never goes
"stale" by design. The poll model fits the trigger model: the
optimizer asks for fresh, the loop asks for fresh on a timer,
and in between the cache is static. `asyncio.to_thread` is the
standard idiom for wrapping sync libraries in async code; it
moves the blocking call to the default thread pool and yields
the event loop.

**Alternatives considered:**
- *Native `aiohttp` calls to Yahoo's v8 endpoint:* would let
  us drop the yfinance dependency, but the URL and payload
  shape are undocumented and can break at any time. yfinance
  is the abstraction layer.
- *Run yfinance in a separate process and IPC:* solves the
  thread-pool saturation problem but adds deployment
  complexity (extra process, extra port) for an app that
  refreshes ~50 symbols every 15min. Not justified.

### D7: HTTP API at `/api/quotes/*`, no UI

**Choice:** Two endpoints:
- `GET /api/quotes/{symbol}` — read one quote (404 if missing)
- `GET /api/quotes?symbols=A,B,C` — read many
- `POST /api/quotes/refresh` — trigger refresh (202)

No Jinja template, no Alpine code, no CSS. Internal API for the
future optimizer and (later) dashboard widgets.

**Rationale:** The user explicitly said "por enquanto não precisa
mostrar na tela do ativo". Adding UI now would lock in a layout
before we know what the dashboard actually needs. The API
contract is small and stable; UI is a separate change that
consumes the same API.

## Risks / Trade-offs

- **Yahoo bans our IP for scraping** → Mitigation: respect
  `QUOTE_REFRESH_INTERVAL_SECONDS` (default 15min, not 5s); add
  jitter (`asyncio.sleep(interval + random.uniform(0, 30))`); a
  circuit breaker prevents hot-looping on failure. The yfinance
  library already rotates through Yahoo's CDN and uses
  `curl_cffi` for TLS fingerprint bypass. If Yahoo hardens, we
  switch to brapi (interface already in place).
- **Background loop survives reload with a stale DB connection**
  → Mitigation: in the loop, use a fresh SQLAlchemy session per
  iteration (the existing app pattern: short-lived sessions via
  the `Session` context manager). A stale connection will raise
  on the next query and the loop will log + sleep.
- **Single uvicorn worker = no concurrent refreshes needed across
  processes** → Mitigation: explicit; if we ever scale to
  multiple workers, add a `SELECT ... FOR UPDATE` on a
  `quote_refresh_lock` row, or use Postgres advisory locks. Not
  needed for v1.
- **The `48 ativos` summary row in the broker CSV would crash the
  provider** if it ever reached yfinance (`.SA` suffix on a
  non-ticker) → Mitigation: the `csv_import` parser is the
  source of `Position.broker_ticker`; if it ever produces a
  non-ticker, the row should be rejected at import time. Out of
  scope for this change, but flagged in the proposal as a
  latent bug.
- **IVVB11 returns BRL, but tracks IVV (USD). For USD-denominated
  rebalance, this is wrong** → Mitigation: the optimizer (future
  change) must decide whether to use the BRL price directly or
  convert via `BRL=X`. The quote cache stores both the price
  and the currency; the consumer interprets. Document in the
  optimizer change.
- **Manual kind has no UI to set a price** → Mitigation: the
  `manual` value exists for a future change. For v1, `manual`
  behaves the same as `none` (use broker price). The enum is
  future-proofed but not yet wired to a UI.
- **`fast_info` can be slow on the first hit (warmup)** → yfinance
  does an initial HTTP request per `Ticker` instance. We reuse
  the `Ticker` object within a batch (one `Ticker` per symbol,
  cached for the duration of the batch) to avoid the warmup
  cost. Cross-batch reuse is possible but adds caching state;
  not justified for the 15min interval.

## Migration Plan

1. **Add `yfinance>=1.4` to `pyproject.toml`** runtime
   dependencies. Run `uv sync`. No new transitive deps that
   conflict (yfinance pulls `requests`, `beautifulsoup4`,
   `peewee`, `curl_cffi` — `requests` is already implicitly
   present via FastAPI, `beautifulsoup4` is in dev only but
   becomes runtime; `curl_cffi` is optional).
2. **Add config**: `QUOTE_TTL_SECONDS` (default 900),
   `QUOTE_REFRESH_INTERVAL_SECONDS` (default 900),
   `QUOTE_REFRESH_CIRCUIT_COOLDOWN_SECONDS` (default 300),
   `QUOTE_REFRESH_CIRCUIT_THRESHOLD` (default 3). All optional
   with sensible defaults.
3. **Alembic migration `0014_add_quote_cache_and_quote_kind.py`**:
   - `CREATE TABLE quotes (symbol TEXT PRIMARY KEY, price NUMERIC(18,4) NOT NULL, currency TEXT NOT NULL, fetched_at TIMESTAMP NOT NULL)`
   - `ALTER TABLE asset_classes ADD COLUMN quote_kind VARCHAR(8) NOT NULL DEFAULT 'none' CHECK (quote_kind IN ('auto', 'manual', 'none'))`
4. **No data backfill** — `quotes` is empty, `asset_classes`
   defaults to `none`. The user opts in classes explicitly.
5. **Add the routes** (`/api/quotes/*`) and wire the
   `on_event("startup")` background task. Smoke test with
   `task serve` and `curl http://<lan-ip>:8000/api/quotes/PETR4.SA`.
6. **Add the test marker rule entries** for the new test
   files (`tests/test_quote_cache.py` → integration,
   `tests/test_yfinance_provider.py` → unit).
7. **Document the trigger** in the OpenSpec change notes so
   the future optimizer change knows to call
   `POST /api/quotes/refresh` before reading the cache.

**Rollback:** drop the `quotes` table and the `quote_kind`
column. Disable the background task via `OMAHA_SKIP_STARTUP=1`
or by removing the `on_event("startup")` registration. No
data loss in the rest of the schema.

## Open Questions

- **Per-asset override?** YAGNI for v1. If a user puts a FII
  under a `Renda Fixa` class (because they think of it as
  fixed income) and wants the FII to be AUTO, they'd need a
  per-asset flag. Defer until someone actually wants this.
- **Multi-currency rebalance:** IVVB11 in BRL + US tickers in
  USD — the optimizer must convert. The cache stores both
  `price` and `currency`; the FX is also cached (BRL=X). The
  conversion logic lives in the (future) optimizer change.
- **Should `manual` show in the UI now?** The enum is in the
  API response. The class editor (S02) currently has no field
  for it. Add a checkbox/dropdown in the editor as part of
  this change's tasks, or defer to a follow-up.
- **Brapi Tesouro Direto:** the user said "Tesouro Direto
  doesn't have a quote" — true for the rebalance use case
  (held-to-maturity), but brapi does have a Tesouro Direto
  endpoint. If we ever add brapi, the user could mark
  specific Tesouro bonds as AUTO. Out of scope for v1.
- **Refresh interval for FX vs equities:** the same TTL for
  both? FX is more stable intra-day, equities move on every
  tick. Single TTL is fine for v1; if the dashboard later
  shows "last updated" freshness, the consumer can
  differentiate by symbol type.
