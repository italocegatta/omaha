## Context

Today the quote-provider surface lives in a single module:
`src/omaha/quotes/provider.py` (239 lines). The file holds four
logically distinct units that all happen to live together:

1. `Quote` wire-format dataclass (lines 101-113).
2. `QuoteProvider` typing.Protocol (lines 116-129).
3. `map_symbol` pure helper + B3/crypto/FX regex constants
   (lines 55-93).
4. `YFinanceProvider` concrete impl (lines 137-236).

The Protocol-based seam is **already in place** — `QuoteService`
takes `provider: QuoteProvider` (verified) and `QuoteCache` never
imports `YFinanceProvider`. Tests already use local `_FakeProvider`
classes that satisfy the Protocol structurally
(`tests/test_quote_service.py:_FakeProvider`,
`tests/test_market_prices_adapter.py`).

The remaining gap is **wiring**. Only one site hardcodes the
concrete provider:

```python
# src/omaha/main.py:97
service = QuoteService(provider=YFinanceProvider())
```

That single line is the seam we want to widen. Today, swapping the
provider (a brapi adapter for a different rate limit, a deterministic
stub for offline work, a fake for a future migration test) requires
editing `main.py`. The slice keeps the existing Protocol but adds a
selector in the same package so consumers — and the single wiring
site — go through it.

Adjacent constraint from PRD §1.2: yfinance is the only
production-ready provider for the symbols we trade (B3 + US + FX +
crypto). No replacement is planned in this slice; the selector is
infrastructure, not migration.

## Goals / Non-Goals

**Goals:**

- Promote `src/omaha/quotes/provider.py` to a `src/omaha/quotes/provider/`
  package; preserve all current public names via `__init__.py`
  re-exports so consumers don't churn.
- Introduce a `get_quote_provider()` selector driven by
  `Settings.QUOTE_PROVIDER` (default `"yfinance"`).
- Introduce a `StubProvider` for tests + offline scenarios that
  satisfies `QuoteProvider` structurally and honors a per-symbol
  response map.
- Codify the seam in a new spec (`quote-provider-factory`) and three
  `ADDED` requirements on `quote-provider`.
- Zero behavior change on the production path (yfinance stays default;
  selector returns the same `YFinanceProvider()` instance the wiring
  builds today).
- Cap-1 critical-area discipline: only one new module (`stub.py`)
  enters the rebalance/cotação critical area, and the yfinance path
  is byte-equivalent.

**Non-Goals:**

- A second concrete provider beyond `StubProvider` (brapi/Finnhub/etc.
  are explicitly out of scope; the selector is the future entry
  point when one lands).
- Renaming `YFinanceProvider`, `Quote`, `map_symbol`, or any other
  public name.
- Touching `QuoteCache`, `QuoteService`, `OmahaMarketPriceLookup`, or
  `rebalance/quotes_adapter.py` — they already couple only to the
  Protocol.
- Touching the rebalance solver or any CVXPY code.
- Migration script or DB change. The provider is a runtime artifact;
  no schema touches the quote cache.
- Documentation polish (covered by D01 at the end of the queue).

## Decisions

### D-R03.1 — Package layout: protocol + mapper + impl + stub

**Decision:** Four files under `src/omaha/quotes/provider/`:

| File | Holds |
|---|---|
| `__init__.py` | Re-exports + `get_quote_provider()` selector |
| `protocol.py` | `Quote` dataclass + `QuoteProvider` Protocol |
| `mapper.py` | `map_symbol` + `_BR_TICKER_RE` + `_CRYPTO_CODES` constants |
| `yfinance.py` | `YFinanceProvider` (verbatim move from `provider.py`) |
| `stub.py` | `StubProvider` (new) |

**Rationale:** The four units evolve at different rates. The Protocol
is a contract — should not change without spec delta. `map_symbol` is
pure, easy to unit-test in isolation, and B3 regex changes are an
upstream concern (B3 listing rules). `YFinanceProvider` is the impl
that yfinance library upgrades will keep touching. `StubProvider` is
test infrastructure. One file forced them to change together.

**Alternative considered:** Single file with section comments. Rejected
because the slice's whole point is "the package is the seam"; a
single file with comments is the pre-slice state.

### D-R03.2 — Selector: env-driven, fail-loud on unknown value

**Decision:**

```python
# src/omaha/config.py
QUOTE_PROVIDER: Literal["yfinance", "stub"] = "yfinance"
```

```python
# src/omaha/quotes/provider/__init__.py
def get_quote_provider() -> QuoteProvider:
    """Return the configured quote provider.

    Raises ValueError on an unknown Settings.QUOTE_PROVIDER value so a
    misconfigured deploy fails loudly at startup, not silently in the
    refresh loop.
    """
    name = settings.QUOTE_PROVIDER
    if name == "yfinance":
        return YFinanceProvider()
    if name == "stub":
        return StubProvider()
    raise ValueError(f"unknown QUOTE_PROVIDER: {name!r}")
```

**Rationale:** Pydantic-settings (`Literal[...]`) gives us env-var
loading and validation for free — `OMAHA_QUOTE_PROVIDER=brapi` raises
at startup with a clear message. The selector is a pure factory: no
module-level singleton, no caching (the startup handler is the only
caller, called once per process).

**Alternative considered:** `lru_cache` on the selector for the
whole process lifetime. Rejected because (a) `main.py` calls it
exactly once at startup, and (b) caching makes tests harder
(setting `QUOTE_PROVIDER=stub` after first call would still get the
yfinance instance). No caching = trivially testable.

### D-R03.3 — StubProvider config: instance attributes, not settings

**Decision:** `StubProvider` is configured by instance attributes, not
via `Settings`:

```python
class StubProvider:
    def __init__(
        self,
        responses: dict[str, Quote | None] | None = None,
        default: Quote | None = None,
    ) -> None:
        self._responses = dict(responses or {})
        self._default = default

    async def fetch(self, symbol: str) -> Quote | None:
        return self._responses.get(symbol, self._default)

    async def fetch_many(self, symbols: list[str]) -> list[Quote | None]:
        return [await self.fetch(s) for s in symbols]
```

**Rationale:** A stub that reads from `Settings` is a stub that needs
a config layer for no benefit — the test fixture already has the
response map in scope. Instance attributes are the simplest possible
API: pass a dict, get the stub. The default `None` makes the
"unmapped → `None`" path the explicit choice (matches the
`YFinanceProvider` contract).

**Alternative considered:** A class-level dict keyed by
`pytest.fixture`. Rejected because the fixture is what holds the dict;
constructing the stub in the fixture and passing the dict is the same
line of code.

### D-R03.4 — Backward-compat shim: re-export, don't alias

**Decision:** `src/omaha/quotes/provider/__init__.py` re-exports the
old public names verbatim:

```python
from omaha.quotes.provider.mapper import map_symbol
from omaha.quotes.provider.protocol import Quote, QuoteProvider
from omaha.quotes.provider.stub import StubProvider
from omaha.quotes.provider.yfinance import YFinanceProvider


def get_quote_provider() -> QuoteProvider: ...
```

**Rationale:** Consumers (`omaha.quotes.cache`,
`omaha.quotes.service`, `tests/test_yfinance_provider.py`) import
`from omaha.quotes.provider import Quote, QuoteProvider,
YFinanceProvider, map_symbol`. Re-exports preserve every one of those
imports without changes. The selector is a **new** import — old
imports keep working until each consumer is touched (the only consumer
touched in this slice is `main.py`).

**Alternative considered:** Move `YFinanceProvider` import out of
`main.py` and rely solely on the selector. **Adopted** as part of
D-R03.2 — `main.py` switches to `get_quote_provider()`; the
re-export is for downstream consumers + the existing test file.

### D-R03.5 — YFinanceProvider: verbatim move, no internal refator

**Decision:** `YFinanceProvider` lands in `yfinance.py` with the
**exact same code** as `provider.py:137-236`. Imports inside the
class update (`from omaha.quotes.provider.mapper import map_symbol`
for the mapper; `from omaha.quotes.provider.protocol import Quote`
for the dataclass). Behavior preserved byte-for-byte.

**Rationale:** This is a packaging refator, not a behavior change.
Touching `YFinanceProvider` in flight would conflate two unrelated
risks. `tests/test_yfinance_provider.py` runs against the moved code
without modification (modulo the import path, which the re-export
hides).

**Alternative considered:** Refactor `YFinanceProvider._quote_from_fast_info`
to drop the `mapped_symbol if mapped_symbol != raw_symbol else raw_symbol`
branch (it's a redundant dedup). Rejected — out of slice scope;
tracked as a future cleanup in the same R-track family.

### D-R03.6 — Critical-area discipline: cap-1 holds

**Decision:** No concurrent slice in `Applying` covers the rebalance
solver or cotação yfinance critical area while R03 is `Applying`.
The roadmap (`openspec/roadmap.md` §Parallelism) names this critical
area explicitly. R03 enters it (one new module: `stub.py`) but the
yfinance path is byte-equivalent.

**Rationale:** The only critical-area risk in R03 is that the package
split breaks the import resolution for `YFinanceProvider.fast_info`
or `_quote_from_fast_info` — both covered by the verbatim move + the
existing `test_yfinance_provider.py` suite (which runs against the
new module path without test changes). The mutation test for the
rebalance engine (T03) is a separate slice and is **not** a critical
risk during R03's `Applying` because R03 doesn't touch solver code.

**Alternative considered:** Skip the slice until T03 lands. Rejected
— T03 is also `Ready`, not in `Applying`; the cap is on parallel
`Applying`, not parallel readiness.

## Risks / Trade-offs

- **R-R03.a — Re-export hygiene.** The `provider/__init__.py` re-exports
  must match every existing public name exactly. Mitigated by
  `tests/test_yfinance_provider.py` + `tests/test_quote_service.py`
  running unchanged (they import from `omaha.quotes.provider` and
  rely on the re-export). If a name is missed, those tests fail at
  collection time.

- **R-R03.b — Selector misconfiguration.** `OMAHA_QUOTE_PROVIDER=brapi`
  in a deploy would raise `ValueError` at startup. Mitigated by the
  pydantic `Literal[...]` type on `Settings.QUOTE_PROVIDER`: a typo
  fails at app boot, not in the refresh loop. The selector adds a
  second `ValueError` for defense in depth (in case someone bypasses
  pydantic settings in a test).

- **R-R03.c — Package circular import risk.** `provider/yfinance.py`
  needs `Quote` and `map_symbol`. Both live in sibling modules.
  Cycles only appear if `yfinance.py` re-imports from `__init__.py`
  — which it doesn't. Mitigated by the explicit `from
  omaha.quotes.provider.protocol import Quote` style (sibling-only
  imports inside the package).

- **R-R03.d — StubProvider drift.** If `YFinanceProvider` grows new
  methods (e.g. `fetch_ohlc`), `StubProvider` would need them too.
  The Protocol is the contract; both impls must satisfy it. The
  contract today is `fetch` + `fetch_many` (the two methods
  `QuoteService` calls); growing the Protocol is a separate slice
  with its own spec delta.

- **T-R03.1 — `YFinanceProvider` is the only impl today, so the
  selector's value is theoretical until a second provider lands.**
  The trade-off is one new module (`stub.py`) + one selector function
  + one settings field for the future benefit of clean provider
  swaps. Worth it because: (a) the selector is ~15 lines of code,
  (b) `StubProvider` immediately pays off for offline testing
  scenarios (T-track slices will use it), (c) the alternative is
  editing `main.py` on every provider swap, which is the exact
  friction the slice removes.

- **T-R03.2 — `get_quote_provider()` adds one function-call indirection
  at startup.** Trivial — the refresh loop never sees the
  indirection (it gets the already-constructed `QuoteProvider`
  instance from `QuoteService.__init__`).
