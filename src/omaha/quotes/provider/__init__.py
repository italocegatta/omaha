"""Public surface of the quote-provider package.

The package layout splits the four units that previously lived in a
single ``provider.py`` file:

* ``protocol`` — :class:`Quote` dataclass + :class:`QuoteProvider`
  Protocol (the contract every concrete implementation satisfies).
* ``mapper`` — pure :func:`map_symbol` helper + B3 / crypto regex
  constants. Lives next to the contract because B3 listing rules
  evolve independently of any provider implementation.
* ``yfinance`` — :class:`YFinanceProvider`, the production
  yfinance-backed implementation. Byte-for-byte the same code that
  lived in the previous single-file module; the move is packaging
  only.
* ``stub`` — :class:`StubProvider`, an in-memory offline
  implementation for tests + scenarios where the network path is
  undesirable (T-track integration tests, CI without a sandbox).

Consumers keep importing the public names from
``omaha.quotes.provider`` (the package) via the re-exports below
— no consumer-side change is required for the move. The new
``get_quote_provider`` selector is the single sanctioned runtime
entry point: ``main.py`` and any future wiring MUST go through it
instead of importing :class:`YFinanceProvider` or
:class:`StubProvider` directly.
"""

from __future__ import annotations

from omaha.quotes.provider.mapper import map_symbol
from omaha.quotes.provider.protocol import Quote, QuoteProvider
from omaha.quotes.provider.stub import StubProvider
from omaha.quotes.provider.yfinance import YFinanceProvider


def get_quote_provider() -> QuoteProvider:
    """Return the concrete quote provider named by ``Settings.QUOTE_PROVIDER``.

    The selector is the single sanctioned entry point for wiring a
    :class:`QuoteProvider` into :class:`~omaha.quotes.service.QuoteService`.
    Default (``"yfinance"``) resolves to :class:`YFinanceProvider` —
    byte-equivalent to the pre-slice ``QuoteService(provider=YFinanceProvider())``
    line. ``"stub"`` resolves to :class:`StubProvider` for offline
    scenarios.

    Settings are imported lazily to avoid module-time evaluation
    (mirrors :meth:`omaha.quotes.cache.QuoteCache._is_postgres`):
    tests can mutate ``os.environ["OMAHA_QUOTE_PROVIDER"]`` and
    have the next call observe the new value.

    Raises
    ------
    ValueError
        When :attr:`Settings.QUOTE_PROVIDER` holds a value outside
        the allowed set (``"yfinance"`` / ``"stub"``). Pydantic
        settings also reject invalid values at validation time, but
        a defense-in-depth check here keeps a bypassed pydantic
        path (e.g. an explicit attribute set in a test) from
        silently returning ``None``.
    """
    from omaha.config import settings

    name = settings.QUOTE_PROVIDER
    if name == "yfinance":
        return YFinanceProvider()
    if name == "stub":
        return StubProvider()
    raise ValueError(f"unknown QUOTE_PROVIDER: {name!r}")


__all__ = [
    "Quote",
    "QuoteProvider",
    "YFinanceProvider",
    "StubProvider",
    "map_symbol",
    "get_quote_provider",
]
