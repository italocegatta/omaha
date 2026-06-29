"""Integration tests for :class:`omaha.quotes.service.QuoteService`.

Five cases covering the refresh-once behavior and the circuit breaker:

1. ``test_refresh_once_returns_zero_when_no_auto_classes`` — no
   AUTO-class positions → no work, empty report.
2. ``test_refresh_once_writes_successful_results_to_cache`` — partial
   success persists successful quotes and reports refreshed/failed.
3. ``test_refresh_once_partial_failure_does_not_trip_circuit`` —
   partial success keeps the circuit closed even across many calls.
4. ``test_refresh_once_full_failure_opens_circuit_after_threshold`` —
   3 consecutive full-batch failures open the breaker.
5. ``test_circuit_closes_after_cooldown`` — after the cooldown, the
   breaker closes and a subsequent successful refresh resets state.

The provider is stubbed via a fake ``QuoteProvider`` class (no
yfinance mocking). The DB is the session-scoped test DB from
``tests/conftest.py``.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal

import pytest
from sqlalchemy import text

from omaha.db import SessionLocal
from omaha.models import Asset, AssetClass, Position, Profile, QuoteKind
from omaha.quotes.cache import QuoteCache
from omaha.quotes.provider import Quote as ProviderQuote
from omaha.quotes.service import QuoteService

# ---------------------------------------------------------------------------
# Fake provider
# ---------------------------------------------------------------------------


@dataclass
class _FakeProvider:
    """In-memory QuoteProvider stub. No network, no yfinance."""

    responses: dict[str, ProviderQuote | None] = field(default_factory=dict)
    fetch_many_calls: list[list[str]] = field(default_factory=list)

    async def fetch(self, symbol: str) -> ProviderQuote | None:
        return self.responses.get(symbol)

    async def fetch_many(self, symbols: list[str]) -> list[ProviderQuote | None]:
        self.fetch_many_calls.append(list(symbols))
        return [self.responses.get(s) for s in symbols]


def _make_provider() -> _FakeProvider:
    return _FakeProvider()


# ---------------------------------------------------------------------------
# Fixture: clean slate for classes/positions, fresh AUTO class with symbols
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _wipe_quotes_and_classes() -> None:
    """Wipe the test DB tables that the service reads/writes."""
    with SessionLocal() as db:
        # CASCADE-children first to keep FK enforcement happy.
        db.execute(text("DELETE FROM quotes"))
        db.execute(text("DELETE FROM positions"))
        db.execute(text("DELETE FROM assets"))
        db.execute(text("DELETE FROM asset_classes"))
        db.commit()
    yield


def _seed_auto_profile(symbols: list[str]) -> int:
    """Create Italo's profile + one AUTO class + one asset + N positions.

    Returns the asset_class_id (for direct introspection if a test
    needs it). All positions reuse a single asset because the
    refresh service only cares about ``broker_ticker``, not which
    asset it belongs to.
    """
    with SessionLocal() as db:
        profile = db.query(Profile).filter(Profile.name == "Italo").one_or_none()
        if profile is None:
            profile = Profile(user_id=1, name="Italo", display_order=0)
            db.add(profile)
            db.flush()

        klass = AssetClass(
            profile_id=profile.id,
            name="Ações",
            target_pct=Decimal("100"),
            display_order=0,
            quote_kind=QuoteKind.AUTO.value,
        )
        db.add(klass)
        db.flush()

        asset = Asset(
            asset_class_id=klass.id,
            name="Placeholder",
            target_pct=Decimal("100"),
            display_order=0,
        )
        db.add(asset)
        db.flush()

        for ticker in symbols:
            db.add(
                Position(
                    asset_id=asset.id,
                    qty=Decimal("1"),
                    avg_price=Decimal("0"),
                    current_price=Decimal("0"),
                    broker_ticker=ticker,
                )
            )
        db.commit()
        return klass.id


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_refresh_once_returns_zero_when_no_auto_classes() -> None:
    """No AUTO-class positions → empty report."""
    provider = _make_provider()
    service = QuoteService(provider=provider, threshold=2, cooldown_seconds=1)

    report = asyncio.run(service.refresh_once())
    assert report.refreshed == 0
    assert report.failed == 0
    assert report.symbols_total == 0
    assert report.circuit_open is False
    assert provider.fetch_many_calls == []


def test_refresh_once_writes_successful_results_to_cache() -> None:
    """Successful fetches are written to the cache; failures are reported."""
    _seed_auto_profile(["PETR4", "VALE3", "AAPL"])
    provider = _make_provider()
    provider.responses["PETR4"] = ProviderQuote(
        symbol="PETR4.SA",
        price=Decimal("38.50"),
        currency="BRL",
        fetched_at=datetime.now(tz=UTC).replace(tzinfo=None),
    )
    provider.responses["AAPL"] = ProviderQuote(
        symbol="AAPL",
        price=Decimal("190.00"),
        currency="USD",
        fetched_at=datetime.now(tz=UTC).replace(tzinfo=None),
    )
    # VALE3 missing → fetch returns None → reported as failed.

    cache = QuoteCache()
    service = QuoteService(provider=provider, cache=cache, threshold=2, cooldown_seconds=1)

    report = asyncio.run(service.refresh_once())
    assert report.refreshed == 2
    assert report.failed == 1
    assert report.symbols_total == 3
    # Cache contains only the successful fetches.
    assert cache.get("PETR4.SA") is not None
    assert cache.get("AAPL") is not None
    assert cache.get("VALE3.SA") is None


def test_refresh_once_partial_failure_does_not_trip_circuit() -> None:
    """Partial success keeps the circuit closed across many iterations."""
    _seed_auto_profile(["PETR4", "AAPL"])
    provider = _make_provider()
    provider.responses["PETR4"] = ProviderQuote(
        symbol="PETR4.SA",
        price=Decimal("38.50"),
        currency="BRL",
        fetched_at=datetime.now(tz=UTC).replace(tzinfo=None),
    )
    # AAPL always fails → every iteration is partial.

    service = QuoteService(provider=provider, threshold=2, cooldown_seconds=1)

    for _ in range(5):
        report = asyncio.run(service.refresh_once())
        assert report.circuit_open is False
        assert report.refreshed == 1
        assert report.failed == 1
    assert service.circuit_open is False


def test_refresh_once_full_failure_opens_circuit_after_threshold() -> None:
    """3 consecutive full-batch failures open the breaker."""
    _seed_auto_profile(["PETR4", "AAPL"])
    provider = _make_provider()
    # No responses → all fetches return None.

    service = QuoteService(provider=provider, threshold=3, cooldown_seconds=60)

    for _ in range(2):
        report = asyncio.run(service.refresh_once())
        assert report.circuit_open is False
        assert report.full_failure is True
    # Third consecutive full failure opens the breaker.
    report = asyncio.run(service.refresh_once())
    assert report.full_failure is True
    assert service.circuit_open is True


def test_circuit_closes_after_cooldown() -> None:
    """After cooldown, the breaker closes and a subsequent success resets state."""
    _seed_auto_profile(["PETR4"])
    provider = _make_provider()
    service = QuoteService(provider=provider, threshold=2, cooldown_seconds=1)

    # 2 consecutive full failures open the breaker (cooldown 1s).
    for _ in range(2):
        asyncio.run(service.refresh_once())
    assert service.circuit_open is True

    # While the breaker is open, refresh_once returns circuit_open=True
    # without making any provider calls.
    before_calls = len(provider.fetch_many_calls)
    report = asyncio.run(service.refresh_once())
    assert report.circuit_open is True
    assert report.refreshed == 0
    assert len(provider.fetch_many_calls) == before_calls  # no I/O while open

    # Wait out the cooldown and confirm the breaker closed.
    asyncio.run(asyncio.sleep(1.5))
    assert service.circuit_open is False

    # Provider now returns a successful quote; refresh succeeds and the
    # failure counter resets to zero.
    provider.responses["PETR4"] = ProviderQuote(
        symbol="PETR4.SA",
        price=Decimal("38.50"),
        currency="BRL",
        fetched_at=datetime.now(tz=UTC).replace(tzinfo=None),
    )
    report = asyncio.run(service.refresh_once())
    assert report.refreshed == 1
    assert report.circuit_open is False
    assert service._consecutive_failures == 0
    assert service._circuit_open_until is None


def test_lock_serializes_concurrent_refreshes() -> None:
    """Two refresh_once calls in flight cannot enter fetch_many concurrently."""
    _seed_auto_profile(["PETR4"])

    # Track how many fetch_many calls overlap in time. With the lock
    # in refresh_once, this should peak at 1; without it, it would
    # peak at 2.
    in_flight = 0
    max_in_flight = 0

    class _SlowProvider(_FakeProvider):
        async def fetch_many(self, symbols):  # type: ignore[override]
            nonlocal in_flight, max_in_flight
            in_flight += 1
            max_in_flight = max(max_in_flight, in_flight)
            try:
                await asyncio.sleep(0.1)
                return await super().fetch_many(symbols)
            finally:
                in_flight -= 1

    provider = _SlowProvider()
    provider.responses["PETR4"] = ProviderQuote(
        symbol="PETR4.SA",
        price=Decimal("38.50"),
        currency="BRL",
        fetched_at=datetime.now(tz=UTC).replace(tzinfo=None),
    )
    service = QuoteService(provider=provider, threshold=3, cooldown_seconds=1)

    async def _two_in_parallel() -> None:
        await asyncio.gather(service.refresh_once(), service.refresh_once())

    asyncio.run(_two_in_parallel())
    assert max_in_flight == 1  # lock held; never overlap
