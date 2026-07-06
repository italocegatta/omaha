"""Unit tests for :class:`omaha.quotes.provider.StubProvider`.

Six cases covering the response-map contract and the per-symbol
isolation guarantees that mirror :class:`YFinanceProvider.fetch_many`.
The stub is pure in-memory — no DB, no HTTP, no patch fixture.

Cases:

1. Mapped symbol returns the configured ``Quote``.
2. Unmapped symbol returns ``default`` (here ``None`` — no override).
3. Unmapped symbol returns the configured ``default`` override.
4. ``fetch_many`` preserves input order including interleaved misses.
5. Per-symbol ``None`` does not abort the batch.
6. Isolation between stub instances — each holds its own response
   map (catches accidental class-level state leaks).

Async is driven via :func:`asyncio.run` so the file does not need
``pytest-asyncio`` as a project dependency (the project sticks to
``pytest-bdd`` + ``pytest-cov`` for its e2e/BDD layer).
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from decimal import Decimal

from omaha.quotes.provider import Quote, StubProvider


def _quote(symbol: str, price: str = "1.00", currency: str = "USD") -> Quote:
    """Build a :class:`Quote` with the given fields."""
    return Quote(
        symbol=symbol,
        price=Decimal(price),
        currency=currency,
        fetched_at=datetime(2026, 7, 5, tzinfo=UTC).replace(tzinfo=None),
    )


def _await(coro):
    """Run a coroutine to completion."""
    return asyncio.run(coro)


def test_mapped_symbol_returns_configured_quote() -> None:
    """A symbol in the response map returns its mapped ``Quote``."""
    petr = _quote("PETR4.SA", price="38.50", currency="BRL")
    stub = StubProvider(responses={"PETR4.SA": petr})
    assert _await(stub.fetch("PETR4.SA")) == petr


def test_unmapped_symbol_returns_default_none() -> None:
    """Without a ``default`` override, unmapped symbols return ``None``."""
    stub = StubProvider(responses={"AAPL": _quote("AAPL")})
    assert _await(stub.fetch("UNKNOWN")) is None


def test_unmapped_symbol_returns_configured_default() -> None:
    """A ``default`` override is returned for any unmapped symbol."""
    fallback = _quote("FALLBACK", price="0.01")
    stub = StubProvider(default=fallback)
    assert _await(stub.fetch("ANYTHING")) == fallback


def test_fetch_many_preserves_input_order() -> None:
    """``fetch_many`` returns results in input order, not map order."""
    a = _quote("A")
    b = _quote("B")
    stub = StubProvider(responses={"A": a, "B": b})
    # Input order is B → A → MISSING — verify against the input, not the map.
    results = _await(stub.fetch_many(["B", "A", "MISSING"]))
    assert results == [b, a, None]


def test_per_symbol_none_does_not_abort_batch() -> None:
    """One ``None``-mapped symbol does not poison the rest of the batch."""
    a = _quote("A")
    stub = StubProvider(responses={"A": a, "MISSING": None})
    results = _await(stub.fetch_many(["A", "MISSING", "A"]))
    assert results == [a, None, a]


def test_stub_instances_do_not_share_state() -> None:
    """Each stub instance carries its own response map."""
    petr = _quote("PETR4.SA")
    aapl = _quote("AAPL")
    s1 = StubProvider(responses={"PETR4.SA": petr})
    s2 = StubProvider(responses={"AAPL": aapl})
    assert _await(s1.fetch("PETR4.SA")) == petr
    assert _await(s1.fetch("AAPL")) is None
    assert _await(s2.fetch("AAPL")) == aapl
    assert _await(s2.fetch("PETR4.SA")) is None
