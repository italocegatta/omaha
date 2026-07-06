"""In-memory :class:`QuoteProvider` stub for tests + offline scenarios.

:class:`StubProvider` fulfils the :class:`QuoteProvider` Protocol
structurally (no inheritance — the runtime ``Protocol`` checks
``fetch`` + ``fetch_many`` shape, not ``isinstance``). Use it when
production code wants a deterministic provider without monkeypatching
or hitting the network — e.g. ``QuoteService`` integration tests
can pre-stage a response map and exercise the refresh loop offline.

Configuration
-------------
The stub is configured by instance attributes, not via ``Settings``,
because the data is fixture-local and lives next to the test that
uses it:

* ``responses`` — per-symbol response map. Symbols present return
  the mapped value (``Quote`` or ``None``); symbols absent fall
  through to ``default``.
* ``default`` — value returned for unmapped symbols (``None`` when
  not provided, matching the :class:`YFinanceProvider` contract).
"""

from __future__ import annotations

from omaha.quotes.provider.protocol import Quote


class StubProvider:
    """Deterministic, network-free :class:`QuoteProvider` for tests.

    Parameters
    ----------
    responses
        ``{symbol: Quote | None}`` map. Lookups are exact-match; any
        symbol absent from the map falls through to ``default``.
    default
        Value returned for unmapped symbols. Defaults to ``None``
        which matches the "unknown symbol returns ``None``" contract
        of :class:`YFinanceProvider`.
    """

    def __init__(
        self,
        responses: dict[str, Quote | None] | None = None,
        default: Quote | None = None,
    ) -> None:
        self._responses = dict(responses or {})
        self._default = default

    async def fetch(self, symbol: str) -> Quote | None:
        """Return the mapped ``Quote`` for ``symbol``, or ``default``."""
        return self._responses.get(symbol, self._default)

    async def fetch_many(self, symbols: list[str]) -> list[Quote | None]:
        """Call :meth:`fetch` once per symbol and return input-order results.

        A per-symbol ``None`` never aborts the batch — the per-symbol
        contract mirrors :meth:`YFinanceProvider.fetch_many`.
        """
        return [await self.fetch(symbol) for symbol in symbols]


__all__ = ["StubProvider"]
