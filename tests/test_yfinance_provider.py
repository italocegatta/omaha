"""Unit tests for :mod:`omaha.quotes.provider`.

Eleven cases covering the yfinance mapping rules and the
:class:`YFinanceProvider` async surface, all with ``yfinance.Ticker``
stubbed via ``unittest.mock`` — no network, no DB. The tests run
under ``-m unit`` because the provider is pure Python (no DB, no
SQLAlchemy session).

Cases:

1-7. ``map_symbol`` rules: BR stocks/FIIs/BDRs (.SA suffix), US
   stocks/ETFs (pass-through), BTC/ETH (→ BTC-USD/ETH-USD),
   FX (=X, pass-through).
8-9. :meth:`YFinanceProvider.fetch` happy path + exception path.
10.   :meth:`YFinanceProvider.fetch_many` isolates per-symbol failures.
11-12. BTC → BTC-USD; BRL=X → BRL=X (round-trip the wire format).

Async is driven via :func:`asyncio.run` so the file does not require
``pytest-asyncio`` as a project dependency — the project sticks to
``pytest-bdd`` + ``pytest-cov`` and the BDD layer wraps Playwright's
async runtime.
"""

from __future__ import annotations

import asyncio
from decimal import Decimal
from unittest.mock import MagicMock, patch

from omaha.quotes.provider import YFinanceProvider, map_symbol

# ---------------------------------------------------------------------------
# Symbol mapper (pure function)
# ---------------------------------------------------------------------------


def test_map_symbol_br_stock_appends_sa() -> None:
    """A 4-5 letter + 1-2 digit BR ticker gets the .SA suffix."""
    assert map_symbol("PETR4") == "PETR4.SA"
    assert map_symbol("PRIO3") == "PRIO3.SA"
    assert map_symbol("VALE3") == "VALE3.SA"


def test_map_symbol_fii_appends_sa() -> None:
    """A 6-char code ending in 11 (FII / ETF / BDR) gets .SA."""
    assert map_symbol("HGLG11") == "HGLG11.SA"
    assert map_symbol("MXRF11") == "MXRF11.SA"


def test_map_symbol_bdr_appends_sa() -> None:
    """IVVB11 is the BDR pattern; .SA maps it correctly."""
    assert map_symbol("IVVB11") == "IVVB11.SA"


def test_map_symbol_us_stock_passes_through() -> None:
    """A plain US ticker is returned as-is."""
    assert map_symbol("AAPL") == "AAPL"
    assert map_symbol("MSFT") == "MSFT"


def test_map_symbol_us_etf_passes_through() -> None:
    """US ETFs (no .SA, no crypto) pass through."""
    assert map_symbol("SMH") == "SMH"


def test_map_symbol_btc_to_btc_usd() -> None:
    """A recognized crypto code maps to <CODE>-USD."""
    assert map_symbol("BTC") == "BTC-USD"
    assert map_symbol("ETH") == "ETH-USD"


def test_map_symbol_fx_passes_through() -> None:
    """Yahoo FX codes (=X suffix) pass through unchanged."""
    assert map_symbol("BRL=X") == "BRL=X"
    assert map_symbol("USDBRL=X") == "USDBRL=X"


# ---------------------------------------------------------------------------
# YFinanceProvider (async, driven by asyncio.run)
# ---------------------------------------------------------------------------


def _fast_info_dict(price: float | None, currency: str | None = "USD") -> dict[str, object]:
    """Build a ``fast_info``-like dict with the requested keys."""
    info: dict[str, object] = {"currency": currency}
    if price is not None:
        info["last_price"] = price
    return info


def test_yfinance_provider_fetch_returns_quote_for_known_symbol() -> None:
    """A symbol with a fast_info['last_price'] returns a Quote."""
    with patch("omaha.quotes.provider.yf.Ticker") as ticker_cls:
        ticker_cls.return_value.fast_info = {"last_price": 38.5, "currency": "BRL"}
        provider = YFinanceProvider()
        result = asyncio.run(provider.fetch("PETR4"))

    assert result is not None
    assert result.symbol == "PETR4.SA"
    assert result.price == Decimal("38.5")
    assert result.currency == "BRL"


def test_yfinance_provider_fetch_handles_missing_price() -> None:
    """A symbol with no ``last_price`` returns None (no raise)."""
    with patch("omaha.quotes.provider.yf.Ticker") as ticker_cls:
        ticker_cls.return_value.fast_info = _fast_info_dict(price=None)
        provider = YFinanceProvider()
        result = asyncio.run(provider.fetch("UNKNOWN_XYZ"))

    assert result is None


def test_yfinance_provider_fetch_handles_yfinance_exception() -> None:
    """An exception inside yfinance is swallowed and returns None."""
    with patch("omaha.quotes.provider.yf.Ticker") as ticker_cls:
        ticker_cls.side_effect = RuntimeError("network down")
        provider = YFinanceProvider()
        result = asyncio.run(provider.fetch("PETR4"))

    assert result is None


def test_yfinance_provider_fetch_many_isolates_failures() -> None:
    """One bad symbol in a batch returns None in its slot; others succeed."""
    call_log: list[str] = []

    def _fake_ticker(symbol: str) -> MagicMock:
        call_log.append(symbol)
        info: dict[str, object] = {"currency": "USD"}
        if symbol == "PETR4.SA":
            info["last_price"] = 38.5
        elif symbol == "BAD":
            raise RuntimeError("boom")
        elif symbol == "AAPL":
            info["last_price"] = 190.0
        return MagicMock(fast_info=info)

    with patch("omaha.quotes.provider.yf.Ticker", side_effect=_fake_ticker):
        provider = YFinanceProvider()
        results = asyncio.run(provider.fetch_many(["PETR4", "BAD", "AAPL"]))

    assert len(results) == 3
    assert results[0] is not None
    assert results[0].symbol == "PETR4.SA"
    assert results[1] is None  # the exception was isolated
    assert results[2] is not None
    assert results[2].symbol == "AAPL"
    assert "PETR4.SA" in call_log
    assert "BAD" in call_log
    assert "AAPL" in call_log


def test_yfinance_provider_btc_maps_to_btc_usd() -> None:
    """BTC is fetched as BTC-USD on Yahoo."""
    with patch("omaha.quotes.provider.yf.Ticker") as ticker_cls:
        ticker_cls.return_value.fast_info = {"last_price": 65000.0, "currency": "USD"}
        provider = YFinanceProvider()
        result = asyncio.run(provider.fetch("BTC"))

    assert result is not None
    assert result.symbol == "BTC-USD"
    assert result.currency == "USD"


def test_yfinance_provider_brl_x_maps_through() -> None:
    """BRL=X is fetched verbatim with currency=BRL."""
    with patch("omaha.quotes.provider.yf.Ticker") as ticker_cls:
        ticker_cls.return_value.fast_info = {"last_price": 5.18, "currency": "BRL"}
        provider = YFinanceProvider()
        result = asyncio.run(provider.fetch("BRL=X"))

    assert result is not None
    assert result.symbol == "BRL=X"
    assert result.currency == "BRL"
