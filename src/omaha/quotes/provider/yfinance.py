"""yfinance-backed :class:`QuoteProvider` implementation.

:class:`YFinanceProvider` is the production quote source for the
runtime — it wraps ``yfinance.Ticker`` with ``asyncio.to_thread`` so
the synchronous HTTP calls do not block the FastAPI event loop, and
isolates per-symbol exceptions inside :meth:`fetch_many` so one bad
symbol never poisons the batch.

Behavior lives here byte-for-byte as it did in the previous
single-file ``provider.py`` module. Packaging move only — no
refator. The ``from omaha.quotes.provider.mapper import map_symbol``
+ ``from omaha.quotes.provider.protocol import Quote`` imports keep
this module sibling-only inside the package to avoid circular
imports (R-R03.c).
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from decimal import Decimal

import yfinance as yf

from omaha.quotes.provider.mapper import map_symbol
from omaha.quotes.provider.protocol import Quote


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
        """Translate ``fast_info`` to a :class:`Quote` or ``None`.

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


__all__ = ["YFinanceProvider"]
