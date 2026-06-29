"""Market-quote provider abstraction and the yfinance implementation.

The :class:`QuoteProvider` protocol decouples the cache / service /
route layers from the concrete quote source. Today the only
implementation is :class:`YFinanceProvider` (yfinance covers BR + US +
FX + crypto in one library, no API key). A future brapi / Finnhub /
BCB adapter would slot in here without touching the rest of the
codebase.

Why a Protocol, not an ABC
--------------------------
A ``typing.Protocol`` lets :class:`YFinanceProvider` satisfy the
interface implicitly (structural typing). Tests can pass a
``Mock(spec=QuoteProvider)`` or a hand-rolled stub without inheriting
from a base class — important because the unit tests stub
``yfinance.Ticker`` via ``unittest.mock`` and do not want a parallel
class hierarchy to maintain.

Why a dataclass, not the ORM model
----------------------------------
The provider's :class:`Quote` dataclass is the wire format between
provider and cache; the ORM ``Quote`` in :mod:`omaha.models` is the
persisted row. Keeping them separate means the provider can be unit-
tested without spinning up a SQLAlchemy session, and a future brapi
adapter can drop in without touching the cache layer.

Symbol mapping
--------------
Yahoo's tickers differ from omaha's broker tickers in three places:

* Brazilian stocks / FIIs / BDRs / ETFs trade under their own code on
  B3 but Yahoo lists them under ``<code>.SA``. The mapper appends
  ``.SA`` when the symbol matches the B3 pattern (4-5 uppercase
  letters + 1-2 digits, or 6 chars ending in ``11``).
* Crypto codes (``BTC``, ``ETH``) become ``<CODE>-USD``.
* FX stays as-is (``BRL=X``, ``USDBRL=X``).
* US stocks / ETFs (``AAPL``, ``SMH``) pass through verbatim.

The mapper is pure (``map_symbol``), easy to unit-test, and produces
the same output the live yfinance library accepts.
"""

from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Protocol

import yfinance as yf

# ---------------------------------------------------------------------------
# Symbol mapper (pure)
# ---------------------------------------------------------------------------

# B3 ticker pattern: 4-5 uppercase letters + 1-2 digits (e.g. ``PETR4``,
# ``PRIO3``, ``VALE3``) OR 6 chars ending in ``11`` (FIIs / ETFs / BDRs /
# equity-style tickers like ``HGLG11``, ``IVVB11``, ``SMAL11``).
_BR_TICKER_RE = re.compile(r"^[A-Z]{4,5}\d{1,2}$|^[A-Z]{4}11$")

# Crypto codes we map to ``<CODE>-USD`` on Yahoo.
_CRYPTO_CODES = frozenset({"BTC", "ETH", "SOL", "USDC", "USDT", "ADA", "XRP", "DOGE"})


def map_symbol(symbol: str) -> str:
    """Map an omaha broker ticker to the corresponding yfinance ticker.

    BR pattern → append ``.SA``. Crypto code → append ``-USD``. FX
    pattern (``=X`` suffix) and any other symbol → pass through.

    Examples
    --------
    >>> map_symbol("PETR4")
    'PETR4.SA'
    >>> map_symbol("HGLG11")
    'HGLG11.SA'
    >>> map_symbol("AAPL")
    'AAPL'
    >>> map_symbol("BTC")
    'BTC-USD'
    >>> map_symbol("BRL=X")
    'BRL=X'
    """
    upper = symbol.upper().strip()
    if upper in _CRYPTO_CODES:
        return f"{upper}-USD"
    if upper.endswith("=X"):
        return upper
    if _BR_TICKER_RE.match(upper):
        return f"{upper}.SA"
    return upper


# ---------------------------------------------------------------------------
# Wire-format dataclass + Protocol
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Quote:
    """Wire-format quote returned by a :class:`QuoteProvider`.

    The shape mirrors the persisted row in the ``quotes`` table; the
    :class:`~omaha.quotes.service.QuoteService` translates between the
    two when writing to the cache.
    """

    symbol: str
    price: Decimal
    currency: str
    fetched_at: datetime


class QuoteProvider(Protocol):
    """Pluggable interface for fetching a single quote.

    Concrete providers must implement :meth:`fetch` (single symbol)
    and :meth:`fetch_many` (batch with per-symbol failure isolation).
    """

    async def fetch(self, symbol: str) -> Quote | None:
        """Return a :class:`Quote` for ``symbol`` or ``None`` on failure."""
        ...

    async def fetch_many(self, symbols: list[str]) -> list[Quote | None]:
        """Return one slot per input symbol; ``None`` on per-symbol failure."""
        ...


# ---------------------------------------------------------------------------
# yfinance implementation
# ---------------------------------------------------------------------------


class YFinanceProvider:
    """:class:`QuoteProvider` backed by the ``yfinance`` library.

    Each ``fetch`` call wraps ``yf.Ticker(symbol).fast_info`` in
    :func:`asyncio.to_thread` so the synchronous yfinance HTTP calls
    do not block the FastAPI event loop. Per-symbol exceptions in
    :meth:`fetch_many` are isolated — one bad symbol does not poison
    the batch.

    Currency resolution
    -------------------
    ``fast_info["currency"]`` returns the quote's currency on most
    symbols. For BRL=X it returns ``BRL`` (the USD/BRL rate); for
    BTC-USD it returns ``USD``; for US tickers it returns ``USD``.
    The mapper does not need to know — the currency travels with
    the data.

    Time zone
    ---------
    ``fast_info`` prices are spot prices (no time stamp of their own
    that we trust). The provider stamps ``fetched_at`` with naive UTC
    so the cache's TTL math stays consistent across backends.
    """

    def __init__(self) -> None:
        """No state required; constructor exists for symmetry with future providers."""

    async def fetch(self, symbol: str) -> Quote | None:
        """Fetch a single quote via yfinance.

        Returns ``None`` for any failure (network, 404, missing price
        field, exception) so callers can treat the absence uniformly.
        """
        mapped = map_symbol(symbol)
        try:
            fast_info = await asyncio.to_thread(self._get_fast_info, mapped)
        except Exception:
            return None
        return self._quote_from_fast_info(symbol, mapped, fast_info)

    async def fetch_many(self, symbols: list[str]) -> list[Quote | None]:
        """Fetch a batch of quotes, isolating per-symbol failures.

        Each ``fetch`` runs in its own :func:`asyncio.to_thread` so the
        event loop stays responsive and one slow symbol does not block
        the rest. Per-symbol exceptions in any single call do not
        abort the batch — ``asyncio.gather`` with no ``return_exceptions``
        would raise on the first failure, but ``fetch`` swallows
        exceptions and returns ``None``, so the gather completes.
        """
        coros = [self.fetch(symbol) for symbol in symbols]
        return list(await asyncio.gather(*coros))

    @staticmethod
    def _get_fast_info(mapped_symbol: str) -> dict[str, object]:
        """Construct a yfinance ``Ticker`` and return ``fast_info``.

        yfinance returns a custom dict-like object; we materialize the
        two keys we read (``last_price`` and ``currency``) to a plain
        ``dict`` so downstream code (and unit tests using
        ``MagicMock``) can rely on a uniform ``dict.get`` API.
        """
        ticker = yf.Ticker(mapped_symbol)
        fast_info = ticker.fast_info
        return {
            "last_price": fast_info.get("last_price")
            if hasattr(fast_info, "get")
            else fast_info["last_price"],
            "currency": fast_info.get("currency")
            if hasattr(fast_info, "get")
            else fast_info["currency"],
        }

    def _quote_from_fast_info(
        self, raw_symbol: str, mapped_symbol: str, fast_info: dict[str, object]
    ) -> Quote | None:
        """Translate ``fast_info`` to a :class:`Quote` or ``None``.

        Missing ``last_price`` (404, rate limit, network error masked
        as empty payload) → ``None``. ``last_price`` is reported by
        yfinance in the symbol's native currency, which we read from
        ``currency`` (defaults to ``"USD"`` because most Yahoo
        responses default to USD when no explicit currency field is
        present).
        """
        raw_price = fast_info.get("last_price")
        if raw_price is None:
            return None
        try:
            price_decimal = Decimal(str(raw_price))
        except Exception:
            return None
        currency_raw = fast_info.get("currency")
        currency = str(currency_raw) if currency_raw else "USD"
        return Quote(
            symbol=mapped_symbol if mapped_symbol != raw_symbol else raw_symbol,
            price=price_decimal,
            currency=currency,
            fetched_at=datetime.now(tz=UTC).replace(tzinfo=None),
        )


__all__ = ["Quote", "QuoteProvider", "YFinanceProvider", "map_symbol"]
