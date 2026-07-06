"""Pure helpers that map an omaha broker ticker to a Yahoo Finance ticker.

Yahoo's tickers differ from omaha's broker tickers in three places:

* Brazilian stocks / FIIs / BDRs / ETFs trade under their own code on
  B3 but Yahoo lists them under ``<code>.SA``. The mapper appends
  ``.SA`` when the symbol matches the B3 pattern (4-5 uppercase
  letters + 1-2 digits, or 6 chars ending in ``11``).
* Crypto codes (``BTC``, ``ETH``) become ``<CODE>-USD``.
* FX stays as-is (``BRL=X``, ``USDBRL=X``).
* US stocks / ETFs (``AAPL``, ``SMH``) pass through verbatim.

The mapper is pure, easy to unit-test, and produces the same output
the live yfinance library accepts.
"""

from __future__ import annotations

import re

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


__all__ = ["map_symbol"]
