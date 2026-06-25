"""Tests for :class:`omaha.quotes.cache.QuoteCache`.

Six integration cases (DB-backed) covering the contract documented in
``openspec/changes/add-market-quote-service/specs/quote-cache/spec.md``:

1. ``test_upsert_writes_single_row`` — a fresh insert produces exactly
   one row with the expected columns and a ``fetched_at`` within the
   last second.
2. ``test_upsert_updates_existing_row`` — a second upsert for the same
   symbol replaces ``price``/``currency``/``fetched_at`` in place; no
   duplicate row.
3. ``test_get_returns_fresh_flag_within_ttl`` — a row stored now reads
   back with ``fresh=True``.
4. ``test_get_returns_stale_flag_after_ttl`` — a row whose ``fetched_at``
   is older than :attr:`~omaha.config.Settings.QUOTE_TTL_SECONDS` reads
   back with ``fresh=False`` (the row stays on disk; only the flag
   flips).
5. ``test_get_returns_none_for_missing_symbol`` — no row → ``None``.
6. ``test_get_many_omits_missing_symbols`` — batch read returns only
   the symbols that have a row.

Uses the session-scoped ``_omaha_test_env`` from ``tests/conftest.py``
for a fresh per-test SQLite DB. The ``quotes`` table is wiped in an
``autouse`` fixture to keep tests independent.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
from sqlalchemy import text

from omaha.config import settings
from omaha.db import SessionLocal
from omaha.models import Quote
from omaha.quotes.cache import QuoteCache


@pytest.fixture(autouse=True)
def _wipe_quotes() -> None:
    """Wipe the ``quotes`` table before each test."""
    with SessionLocal() as db:
        db.execute(text("DELETE FROM quotes"))
        db.commit()
    yield


def _utc_now() -> datetime:
    """Naive UTC ``now`` to compare against the cache's stored timestamps."""
    return datetime.now(tz=timezone.utc).replace(tzinfo=None)


def test_upsert_writes_single_row() -> None:
    """Upserting a new symbol creates exactly one row with current fetched_at."""
    cache = QuoteCache()
    cache.upsert(Quote(symbol="PETR4.SA", price=Decimal("38.50"), currency="BRL"))

    with SessionLocal() as db:
        rows = db.query(Quote).all()
    assert len(rows) == 1
    row = rows[0]
    assert row.symbol == "PETR4.SA"
    assert row.price == Decimal("38.5000")
    assert row.currency == "BRL"
    # fetched_at was stamped by upsert (now-ish, allowing 2s clock skew).
    assert _utc_now() - row.fetched_at <= timedelta(seconds=2)


def test_upsert_updates_existing_row() -> None:
    """A second upsert replaces price/currency/fetched_at in place."""
    cache = QuoteCache()
    cache.upsert(Quote(symbol="PETR4.SA", price=Decimal("38.50"), currency="BRL"))
    cache.upsert(Quote(symbol="PETR4.SA", price=Decimal("39.00"), currency="BRL"))

    with SessionLocal() as db:
        rows = db.query(Quote).filter(Quote.symbol == "PETR4.SA").all()
    assert len(rows) == 1
    assert rows[0].price == Decimal("39.0000")


def test_get_returns_fresh_flag_within_ttl() -> None:
    """A recently stored quote reads back with fresh=True."""
    cache = QuoteCache()
    cache.upsert(Quote(symbol="PETR4.SA", price=Decimal("38.50"), currency="BRL"))

    result = cache.get("PETR4.SA")
    assert result is not None
    assert result.quote.symbol == "PETR4.SA"
    assert result.quote.price == Decimal("38.5000")
    assert result.fresh is True


def test_get_returns_stale_flag_after_ttl() -> None:
    """A quote older than QUOTE_TTL_SECONDS reads back with fresh=False."""
    cache = QuoteCache()
    cache.upsert(Quote(symbol="PETR4.SA", price=Decimal("38.50"), currency="BRL"))

    with SessionLocal() as db:
        row = db.get(Quote, "PETR4.SA")
        row.fetched_at = row.fetched_at - timedelta(seconds=settings.QUOTE_TTL_SECONDS + 10)
        db.commit()

    result = cache.get("PETR4.SA")
    assert result is not None
    assert result.fresh is False


def test_get_returns_none_for_missing_symbol() -> None:
    """A symbol with no row returns None (not a stale flag)."""
    cache = QuoteCache()
    assert cache.get("UNKNOWN.SA") is None


def test_get_many_omits_missing_symbols() -> None:
    """Batch read returns only stored symbols."""
    cache = QuoteCache()
    cache.upsert(Quote(symbol="PETR4.SA", price=Decimal("38.50"), currency="BRL"))
    cache.upsert(Quote(symbol="AAPL", price=Decimal("190.00"), currency="USD"))

    results = cache.get_many(["PETR4.SA", "AAPL", "TSLA"])
    assert set(results.keys()) == {"PETR4.SA", "AAPL"}
    assert results["PETR4.SA"].fresh is True
    assert results["AAPL"].fresh is True


def test_get_many_empty_input_returns_empty_dict() -> None:
    """Empty input list short-circuits to an empty dict (no DB roundtrip)."""
    cache = QuoteCache()
    assert cache.get_many([]) == {}