"""Wire-format dataclass + Protocol for the quote-provider surface.

This module hosts the two types every concrete provider must
satisfy (:class:`Quote` for the wire shape, :class:`QuoteProvider`
for the async surface). Keeping them in one module — separate from
any concrete implementation — means a new provider (brapi, Finnhub,
a future stub) doesn't need to touch this file just to fulfil the
contract.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Protocol


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


__all__ = ["Quote", "QuoteProvider"]
