"""Integration tests for :mod:`omaha.rebalance.market_prices` +
:class:`omaha.rebalance.quotes_adapter.OmahaMarketPriceLookup`.

Three spec sections covered:

1. §"Quote symbol resolution" — :func:`resolve_quote_symbol` rules
   for BRL (``.SA`` suffix), USD (verbatim), idempotency, and empty
   asset names.
2. §"OmahaMarketPriceLookup satisfies the Protocol" — the six
   scenarios the spec calls out (auto BRL fresh/stale, none-class
   fallback, USD with/without BRL=X, asset with no Position).
3. §"QuoteService fetches BRL=X when any USD asset exists" —
   :meth:`QuoteService._collect_symbols` appends ``BRL=X`` iff at
   least one ``Asset.currency_code == "USD"`` exists.

The cache + DB are wiped per-test (autouse) so leftover state from
S03/S04 or rebalance-infra tests does not pollute the lookup. The
QuoteService tests reuse the same fake-provider pattern from
``test_quote_service.py``.
"""

from __future__ import annotations

import importlib
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pandas as pd
import pytest
from sqlalchemy import text

import omaha.db  # noqa: F401 — referenced at call time via importlib.import_module
import omaha.quotes.cache  # noqa: F401 — resolved at call time via importlib
import omaha.rebalance.quotes_adapter  # noqa: F401 — resolved at call time via importlib
from omaha.models import Asset, AssetClass, Position, Profile, QuoteKind
from omaha.quotes.provider import Quote as ProviderQuote
from omaha.rebalance.market_prices import (
    NoopMarketPriceLookup,
    build_empty_quote_frame,
    is_queryable_quote_symbol,
    quote_status_for,
    resolve_quote_symbol,
)


# Late-binding helpers resolve ``omaha.db`` / ``omaha.quotes.cache`` /
# ``omaha.rebalance.quotes_adapter`` through ``sys.modules`` every call.
# The conftest session-scoped fixture swaps the modules out from under
# any reference captured at pytest collection time (the top-level
# ``import omaha.db`` captures the OLD module object — same trap as
# ``from omaha.db import SessionLocal``).
def _session():
    """Return ``omaha.db.SessionLocal`` at call time (true late binding)."""
    return importlib.import_module("omaha.db").SessionLocal


def _quote_cache_cls():
    """Return the ``QuoteCache`` class from the live ``omaha.quotes.cache`` module."""
    return importlib.import_module("omaha.quotes.cache").QuoteCache


def _adapter_cls():
    """Return the ``OmahaMarketPriceLookup`` class from the live rebalance adapter module."""
    return importlib.import_module("omaha.rebalance.quotes_adapter").OmahaMarketPriceLookup


# ---------------------------------------------------------------------------
# Wipe fixture (shared by every test in this module)
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _wipe_all() -> None:
    """Wipe every table that the adapter / QuoteService reads or writes.

    Resolves ``omaha.db`` via :func:`importlib.import_module` so the
    wipe targets the same DB the conftest session-scoped fixture
    configured — the top-level ``from omaha.db import SessionLocal``
    is captured at pytest collection time, BEFORE the conftest
    replaces ``omaha.db.SessionLocal`` with the test-DB-bound factory.
    """
    sl = importlib.import_module("omaha.db").SessionLocal
    with sl() as db:
        db.execute(text("DELETE FROM quotes"))
        db.execute(text("DELETE FROM positions"))
        db.execute(text("DELETE FROM assets"))
        db.execute(text("DELETE FROM asset_classes"))
        db.commit()
    yield


def _now_naive() -> datetime:
    """Return the current time as naive UTC (the cache convention)."""
    return datetime.now(tz=UTC).replace(tzinfo=None)


# ---------------------------------------------------------------------------
# Section 1 — resolve_quote_symbol
# ---------------------------------------------------------------------------


def test_resolve_quote_symbol_brl_appends_sa_suffix() -> None:
    """``PETR4`` + ``BRL`` → ``PETR4.SA``."""
    assert resolve_quote_symbol("PETR4", "BRL") == "PETR4.SA"


def test_resolve_quote_symbol_brl_already_suffixed_is_idempotent() -> None:
    """``PETR4.SA`` + ``BRL`` → ``PETR4.SA`` (no double suffix)."""
    assert resolve_quote_symbol("PETR4.SA", "BRL") == "PETR4.SA"


def test_resolve_quote_symbol_usd_returns_verbatim() -> None:
    """``AAPL`` + ``USD`` → ``AAPL`` (no suffix)."""
    assert resolve_quote_symbol("AAPL", "USD") == "AAPL"


def test_resolve_quote_symbol_empty_asset_name_returns_empty() -> None:
    """Empty ticker → empty symbol (cache lookup skipped)."""
    assert resolve_quote_symbol("", "BRL") == ""
    assert resolve_quote_symbol("   ", "USD") == ""


def test_resolve_quote_symbol_normalizes_case_and_whitespace() -> None:
    """Lower-case input + surrounding whitespace is normalized upper."""
    assert resolve_quote_symbol("petr4", "brl") == "PETR4.SA"
    assert resolve_quote_symbol("  aapl  ", "usd") == "AAPL"


def test_is_queryable_quote_symbol_pattern_check() -> None:
    """Pattern allowlist for symbols safe to send to yfinance."""
    assert is_queryable_quote_symbol("PETR4.SA") is True
    assert is_queryable_quote_symbol("BRL=X") is True
    assert is_queryable_quote_symbol("BRENT-USD") is True
    # Lower-case input is normalized upper-case before the pattern
    # check (yfinance normalizes anyway) so it matches.
    assert is_queryable_quote_symbol("petr4") is True
    assert is_queryable_quote_symbol("") is False
    assert is_queryable_quote_symbol("with space") is False
    # Empty after stripping is rejected.
    assert is_queryable_quote_symbol("   ") is False


def test_build_empty_quote_frame_full_schema_for_empty_input() -> None:
    """Empty input → frame with the 7 expected columns and zero rows."""
    frame = build_empty_quote_frame(
        pd.DataFrame(columns=["asset_key", "asset_name", "currency_code"]), status="unavailable"
    )
    assert frame.empty
    assert list(frame.columns) == [
        "asset_key",
        "quote_symbol",
        "quote_price",
        "quote_currency",
        "quote_timestamp",
        "quote_status",
        "usdbrl_rate",
    ]


def test_noop_market_price_lookup_returns_all_not_requested() -> None:
    """NoopMarketPriceLookup fills every row with ``quote_status = 'not-requested'``."""
    assets = pd.DataFrame(
        {
            "asset_key": ["petr4", "aapl"],
            "asset_name": ["PETR4", "AAPL"],
            "currency_code": ["BRL", "USD"],
        }
    )
    impl = NoopMarketPriceLookup()
    frame = impl.get_quotes(assets)
    assert (frame["quote_status"] == "not-requested").all()


def test_quote_status_for_usd_requires_usdbrl() -> None:
    """USD asset with non-finite BRL=X → ``unavailable`` even if own price is fine."""
    assert (
        quote_status_for(quote_price=190.0, currency_code="USD", usdbrl_rate=float("nan"))
        == "unavailable"
    )
    assert quote_status_for(quote_price=190.0, currency_code="USD", usdbrl_rate=5.0) == "available"
    # BRL asset: stale BRL=X is irrelevant (NaN is the per-row default for BRL).
    assert (
        quote_status_for(quote_price=38.0, currency_code="BRL", usdbrl_rate=float("nan"))
        == "available"
    )
    # Non-finite own price is always unavailable.
    assert (
        quote_status_for(quote_price=float("nan"), currency_code="BRL", usdbrl_rate=5.0)
        == "unavailable"
    )


# ---------------------------------------------------------------------------
# Section 2 — OmahaMarketPriceLookup scenarios
# ---------------------------------------------------------------------------


def _seed_italo_profile() -> int:
    """Return Italo's profile id (created idempotently)."""
    sl = importlib.import_module("omaha.db").SessionLocal
    with sl() as db:
        profile = db.query(Profile).filter(Profile.name == "Italo").one_or_none()
        if profile is None:
            profile = Profile(user_id=1, name="Italo", display_order=0)
            db.add(profile)
            db.commit()
            db.refresh(profile)
        return profile.id


def _seed_class_with_asset(
    profile_id: int,
    class_name: str,
    target_pct: str,
    asset_name: str,
    asset_pct: str,
    quote_kind: str,
    *,
    currency_code: str = "BRL",
    positions: list[tuple[str, str, str]] | None = None,
) -> int:
    """Create class + asset; optionally seed positions. Returns asset id."""
    with _session()() as db:
        klass = AssetClass(
            profile_id=profile_id,
            name=class_name,
            target_pct=Decimal(target_pct),
            display_order=0,
            quote_kind=quote_kind,
        )
        db.add(klass)
        db.flush()
        asset = Asset(
            asset_class_id=klass.id,
            name=asset_name,
            target_pct=Decimal(asset_pct),
            display_order=0,
            currency_code=currency_code,
        )
        db.add(asset)
        db.flush()
        if positions:
            for _ticker, cur_price, broker_ticker in positions:
                db.add(
                    Position(
                        asset_id=asset.id,
                        qty=Decimal("1"),
                        avg_price=Decimal("0"),
                        current_price=Decimal(cur_price),
                        broker_ticker=broker_ticker,
                    )
                )
        db.commit()
        return asset.id


def _seed_quote(symbol: str, price: str, currency: str, fetched_at: datetime | None = None) -> None:
    """Insert a quote row directly so the cache lookup returns it."""
    with _session()() as db:
        db.execute(
            text(
                "INSERT INTO quotes (symbol, price, currency, fetched_at) "
                "VALUES (:symbol, :price, :currency, :fetched_at)"
            ),
            {
                "symbol": symbol,
                "price": price,
                "currency": currency,
                "fetched_at": fetched_at or _now_naive(),
            },
        )
        db.commit()


def _build_lookup():
    """Build a fresh adapter with a real cache + session."""
    return _adapter_cls()(cache=_quote_cache_cls()(), db=_session()())


def test_adapter_auto_brl_with_fresh_cache_returns_available() -> None:
    """Auto BRL asset + fresh ``PETR4.SA`` row → ``available`` + 38.50."""
    profile_id = _seed_italo_profile()
    _seed_class_with_asset(
        profile_id,
        "RV",
        "100",
        "PETR4",
        "100",
        quote_kind=QuoteKind.AUTO.value,
        positions=[("PETR4.SA", "38.50", "PETR4")],
    )
    _seed_quote("PETR4.SA", "38.50", "BRL")

    # Verify the cache sees the row.
    sl = importlib.import_module("omaha.db").SessionLocal
    with sl() as db:
        db.execute(text("SELECT symbol, price, fetched_at FROM quotes")).all()

    lookup = _build_lookup()
    assets = pd.DataFrame(
        {
            "asset_key": ["petr4"],
            "asset_name": ["PETR4"],
            "currency_code": ["BRL"],
        }
    )
    frame = lookup.get_quotes(assets)
    print(f"DEBUG fresh frame: {frame.to_dict()}")

    assert frame.iloc[0]["quote_symbol"] == "PETR4.SA"
    assert frame.iloc[0]["quote_price"] == pytest.approx(38.50)
    assert frame.iloc[0]["quote_currency"] == "BRL"
    assert frame.iloc[0]["quote_status"] == "available"
    assert pd.isna(frame.iloc[0]["usdbrl_rate"])


def test_adapter_auto_brl_with_stale_cache_returns_unavailable() -> None:
    """Cache row older than TTL → ``unavailable`` + NaN price."""
    profile_id = _seed_italo_profile()
    _seed_class_with_asset(
        profile_id,
        "RV",
        "100",
        "PETR4",
        "100",
        quote_kind=QuoteKind.AUTO.value,
        positions=[("PETR4.SA", "38.50", "PETR4")],
    )
    stale = _now_naive() - timedelta(hours=2)
    _seed_quote("PETR4.SA", "38.50", "BRL", fetched_at=stale)

    lookup = _build_lookup()
    assets = pd.DataFrame(
        {
            "asset_key": ["petr4"],
            "asset_name": ["PETR4"],
            "currency_code": ["BRL"],
        }
    )
    frame = lookup.get_quotes(assets)

    assert frame.iloc[0]["quote_symbol"] == "PETR4.SA"
    assert pd.isna(frame.iloc[0]["quote_price"])
    assert frame.iloc[0]["quote_status"] == "unavailable"


def test_adapter_none_class_falls_back_to_position_current_price() -> None:
    """``quote_kind = none`` → broker-published ``current_price`` + ``not-requested``."""
    profile_id = _seed_italo_profile()
    _seed_class_with_asset(
        profile_id,
        "Tesouro",
        "100",
        "Selic",
        "100",
        quote_kind=QuoteKind.NONE.value,
        positions=[("TESOURO_SELIC_2029", "145.32", "TESOURO_SELIC_2029")],
    )

    lookup = _build_lookup()
    assets = pd.DataFrame(
        {
            "asset_key": ["selic"],
            "asset_name": ["Selic"],
            "currency_code": ["BRL"],
        }
    )
    frame = lookup.get_quotes(assets)

    assert frame.iloc[0]["quote_price"] == pytest.approx(145.32)
    assert frame.iloc[0]["quote_currency"] == "BRL"
    assert frame.iloc[0]["quote_status"] == "not-requested"
    # ``quote_symbol`` is the resolved ``.SA`` form (the asset has a
    # Position with a broker_ticker; the symbol is informational even
    # for ``none`` classes so the solver can log "Cotação de HH:MM").
    assert frame.iloc[0]["quote_symbol"] == "SELIC.SA"


def test_adapter_manual_class_uses_position_current_price() -> None:
    """``quote_kind = manual`` shares the ``none`` fallback path."""
    profile_id = _seed_italo_profile()
    _seed_class_with_asset(
        profile_id,
        "CDB",
        "100",
        "Itau",
        "100",
        quote_kind=QuoteKind.MANUAL.value,
        positions=[("CDB_ITAU_2030", "200.00", "CDB_ITAU_2030")],
    )

    lookup = _build_lookup()
    assets = pd.DataFrame(
        {
            "asset_key": ["itau"],
            "asset_name": ["Itau"],
            "currency_code": ["BRL"],
        }
    )
    frame = lookup.get_quotes(assets)

    assert frame.iloc[0]["quote_status"] == "not-requested"
    assert frame.iloc[0]["quote_price"] == pytest.approx(200.00)


def test_adapter_usd_with_fresh_brl_x_populates_usdbrl_rate() -> None:
    """USD asset + fresh ``BRL=X`` → ``usdbrl_rate`` populated + own quote fresh."""
    profile_id = _seed_italo_profile()
    _seed_class_with_asset(
        profile_id,
        "US",
        "100",
        "AAPL",
        "100",
        quote_kind=QuoteKind.AUTO.value,
        currency_code="USD",
        positions=[("AAPL", "190.00", "AAPL")],
    )
    _seed_quote("AAPL", "190.00", "USD")
    _seed_quote("BRL=X", "5.12", "BRL")

    lookup = _build_lookup()
    assets = pd.DataFrame(
        {
            "asset_key": ["aapl"],
            "asset_name": ["AAPL"],
            "currency_code": ["USD"],
        }
    )
    frame = lookup.get_quotes(assets)

    assert frame.iloc[0]["quote_symbol"] == "AAPL"
    assert frame.iloc[0]["quote_price"] == pytest.approx(190.00)
    assert frame.iloc[0]["usdbrl_rate"] == pytest.approx(5.12)
    assert frame.iloc[0]["quote_status"] == "available"


def test_adapter_usd_with_missing_brl_x_is_unavailable() -> None:
    """USD asset + stale/missing ``BRL=X`` → ``unavailable`` regardless of own quote."""
    profile_id = _seed_italo_profile()
    _seed_class_with_asset(
        profile_id,
        "US",
        "100",
        "AAPL",
        "100",
        quote_kind=QuoteKind.AUTO.value,
        currency_code="USD",
        positions=[("AAPL", "190.00", "AAPL")],
    )
    _seed_quote("AAPL", "190.00", "USD")
    # No BRL=X row seeded — adapter should mark the USD asset
    # unavailable even though its own quote is fresh.

    lookup = _build_lookup()
    assets = pd.DataFrame(
        {
            "asset_key": ["aapl"],
            "asset_name": ["AAPL"],
            "currency_code": ["USD"],
        }
    )
    frame = lookup.get_quotes(assets)

    assert frame.iloc[0]["quote_status"] == "unavailable"


def test_adapter_usd_with_stale_brl_x_is_unavailable() -> None:
    """USD asset + stale ``BRL=X`` (older than TTL) → ``unavailable``."""
    profile_id = _seed_italo_profile()
    _seed_class_with_asset(
        profile_id,
        "US",
        "100",
        "AAPL",
        "100",
        quote_kind=QuoteKind.AUTO.value,
        currency_code="USD",
        positions=[("AAPL", "190.00", "AAPL")],
    )
    _seed_quote("AAPL", "190.00", "USD")
    _seed_quote("BRL=X", "5.12", "BRL", fetched_at=_now_naive() - timedelta(hours=2))

    lookup = _build_lookup()
    assets = pd.DataFrame(
        {
            "asset_key": ["aapl"],
            "asset_name": ["AAPL"],
            "currency_code": ["USD"],
        }
    )
    frame = lookup.get_quotes(assets)

    assert frame.iloc[0]["quote_status"] == "unavailable"


def test_adapter_asset_with_no_position_returns_zero_quote() -> None:
    """Asset with zero ``Position`` rows → ``quote_symbol = ""``, ``quote_price = 0.0``,
    ``quote_status = "not-requested"``."""
    profile_id = _seed_italo_profile()
    _seed_class_with_asset(
        profile_id,
        "RV",
        "100",
        "PETR4",
        "100",
        quote_kind=QuoteKind.AUTO.value,
        # no positions
    )

    lookup = _build_lookup()
    assets = pd.DataFrame(
        {
            "asset_key": ["petr4"],
            "asset_name": ["PETR4"],
            "currency_code": ["BRL"],
        }
    )
    frame = lookup.get_quotes(assets)

    assert frame.iloc[0]["quote_symbol"] == ""
    assert frame.iloc[0]["quote_price"] == 0.0
    assert frame.iloc[0]["quote_status"] == "not-requested"


def test_adapter_empty_input_returns_empty_frame() -> None:
    """Empty assets → empty quote frame (full schema)."""
    lookup = _build_lookup()
    frame = lookup.get_quotes(pd.DataFrame(columns=["asset_key", "asset_name", "currency_code"]))
    assert frame.empty
    assert "quote_status" in frame.columns


# ---------------------------------------------------------------------------
# Section 3 — QuoteService BRL=X injection
# ---------------------------------------------------------------------------


@dataclass
class _FakeProvider:
    """In-memory QuoteProvider stub (no yfinance)."""

    responses: dict[str, ProviderQuote | None] = field(default_factory=dict)
    fetch_many_calls: list[list[str]] = field(default_factory=list)

    async def fetch(self, symbol: str) -> ProviderQuote | None:
        return self.responses.get(symbol)

    async def fetch_many(self, symbols: list[str]) -> list[ProviderQuote | None]:
        self.fetch_many_calls.append(list(symbols))
        return [self.responses.get(s) for s in symbols]


def _seed_auto_class_with_usd_asset(*, has_usd_asset: bool) -> None:
    """Create an AUTO class with one BRL asset; optionally add a USD asset."""
    sl = importlib.import_module("omaha.db").SessionLocal

    profile_id = _seed_italo_profile()
    klass = AssetClass(
        profile_id=profile_id,
        name="Ações",
        target_pct=Decimal("100"),
        display_order=0,
        quote_kind=QuoteKind.AUTO.value,
    )
    with sl() as db:
        db.add(klass)
        db.flush()
        # Always: one BRL asset with one AUTO position so _collect_symbols
        # has at least one ticker to pick up.
        brl_asset = Asset(
            asset_class_id=klass.id,
            name="PETR4",
            target_pct=Decimal("50"),
            display_order=0,
            currency_code="BRL",
        )
        db.add(brl_asset)
        db.flush()
        db.add(
            Position(
                asset_id=brl_asset.id,
                qty=Decimal("1"),
                avg_price=Decimal("0"),
                current_price=Decimal("0"),
                broker_ticker="PETR4",
            )
        )
        if has_usd_asset:
            usd_asset = Asset(
                asset_class_id=klass.id,
                name="AAPL",
                target_pct=Decimal("50"),
                display_order=1,
                currency_code="USD",
            )
            db.add(usd_asset)
            db.flush()
            db.add(
                Position(
                    asset_id=usd_asset.id,
                    qty=Decimal("1"),
                    avg_price=Decimal("0"),
                    current_price=Decimal("0"),
                    broker_ticker="AAPL",
                )
            )
        db.commit()


def test_collect_symbols_includes_brl_x_when_usd_asset_present() -> None:
    """At least one USD asset → ``BRL=X`` appears in the refresh list."""
    _seed_auto_class_with_usd_asset(has_usd_asset=True)

    from omaha.quotes.service import QuoteService

    provider = _FakeProvider()
    service = QuoteService(provider=provider)
    symbols = service._collect_symbols()

    assert "BRL=X" in symbols
    # Both tickers must appear (PETR4 + AAPL + BRL=X).
    assert "PETR4" in symbols
    assert "AAPL" in symbols


def test_collect_symbols_unchanged_when_no_usd_asset() -> None:
    """No USD assets → ``BRL=X`` is NOT in the refresh list (no extra HTTP call)."""
    _seed_auto_class_with_usd_asset(has_usd_asset=False)

    from omaha.quotes.service import QuoteService

    provider = _FakeProvider()
    service = QuoteService(provider=provider)
    symbols = service._collect_symbols()

    assert "BRL=X" not in symbols
    assert "PETR4" in symbols


def test_collect_symbols_does_not_duplicate_brl_x_when_already_in_list() -> None:
    """If a broker ticker happens to be ``BRL=X`` itself, don't append a second copy."""
    profile_id = _seed_italo_profile()
    with _session()() as db:
        klass = AssetClass(
            profile_id=profile_id,
            name="FX",
            target_pct=Decimal("100"),
            display_order=0,
            quote_kind=QuoteKind.AUTO.value,
        )
        db.add(klass)
        db.flush()
        asset = Asset(
            asset_class_id=klass.id,
            name="BRL=X",
            target_pct=Decimal("100"),
            display_order=0,
            currency_code="USD",
        )
        db.add(asset)
        db.flush()
        db.add(
            Position(
                asset_id=asset.id,
                qty=Decimal("1"),
                avg_price=Decimal("0"),
                current_price=Decimal("0"),
                broker_ticker="BRL=X",
            )
        )
        db.commit()

    from omaha.quotes.service import QuoteService

    provider = _FakeProvider()
    service = QuoteService(provider=provider)
    symbols = service._collect_symbols()

    assert symbols.count("BRL=X") == 1
