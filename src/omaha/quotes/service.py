"""Background refresh loop for the market-quote cache.

:class:`QuoteService` ties together the :class:`~omaha.quotes.cache.QuoteCache`
and the :class:`~omaha.quotes.provider.QuoteProvider`, running a periodic
refresh of quotes for every position under an asset class with
``quote_kind = auto``. It exposes:

* :meth:`refresh_once` — one batch refresh; returns a
  :class:`RefreshReport`. Used by the ``POST /api/quotes/refresh``
  trigger and by :meth:`run_forever` on each tick.
* :meth:`run_forever` — the asyncio loop started by the FastAPI
  ``on_event("startup")`` handler. Sleeps
  :attr:`~omaha.config.Settings.QUOTE_REFRESH_INTERVAL_SECONDS`
  (+0-30s jitter) between refreshes; cancels cleanly on
  ``CancelledError``.

Resilience
----------
The circuit breaker tracks consecutive *full-batch* failures
(``refreshed == 0`` and ``failed > 0``). After
:attr:`~omaha.config.Settings.QUOTE_REFRESH_CIRCUIT_THRESHOLD`
consecutive full-batch failures, the breaker opens and skips the
next refreshes for the configured cool-down. A partial failure
(``refreshed > 0``) does NOT count toward the threshold — Yahoo
being flaky for one symbol is normal, Yahoo being unreachable for
all of them is the outage we want to back off.

Concurrency
-----------
Both the background loop and the manual ``POST /api/quotes/refresh``
trigger go through the same :class:`asyncio.Lock`, so two refreshes
cannot write to the cache concurrently. The lock is held for the
whole batch (so the trigger waits for the background tick, and vice
versa) — the trade-off is that a slow refresh blocks the trigger,
but the alternative (concurrent UPSERTs on the same row + duplicate
HTTP calls to Yahoo) is worse.
"""

from __future__ import annotations

import asyncio
import logging
import random
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import select

from omaha.config import settings
from omaha.db import SessionLocal
from omaha.models import Asset, AssetClass, Position, Quote, QuoteKind
from omaha.quotes.cache import QuoteCache
from omaha.quotes.provider import Quote, QuoteProvider

if TYPE_CHECKING:
    pass


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RefreshReport:
    """Outcome of a single :meth:`QuoteService.refresh_once` call.

    * ``refreshed`` — symbols whose quote was written to the cache.
    * ``failed`` — symbols whose fetch returned ``None`` or raised.
    * ``circuit_open`` — True iff the circuit breaker was open at the
      start of the call, so no work happened.
    * ``symbols_total`` — number of symbols we attempted to refresh
      (``refreshed + failed``). Useful for log lines like
      ``refreshed 5/10``.
    """

    refreshed: int
    failed: int
    circuit_open: bool
    symbols_total: int

    @property
    def full_failure(self) -> bool:
        """True iff every attempted symbol failed and we attempted at least one."""
        return self.symbols_total > 0 and self.refreshed == 0


class QuoteService:
    """Background refresh loop + manual refresh trigger for market quotes.

    Constructor parameters are dependency-injected so tests can swap in a
    fake :class:`QuoteProvider` and a controllable :class:`QuoteCache`
    without monkeypatching module globals.
    """

    def __init__(
        self,
        provider: QuoteProvider,
        cache: QuoteCache | None = None,
        *,
        interval_seconds: int | None = None,
        cooldown_seconds: int | None = None,
        threshold: int | None = None,
    ) -> None:
        self._provider = provider
        self._cache = cache or QuoteCache()
        self._lock = asyncio.Lock()
        self._interval = interval_seconds or settings.QUOTE_REFRESH_INTERVAL_SECONDS
        self._cooldown = cooldown_seconds or settings.QUOTE_REFRESH_CIRCUIT_COOLDOWN_SECONDS
        self._threshold = threshold or settings.QUOTE_REFRESH_CIRCUIT_THRESHOLD

        # Circuit-breaker state.
        self._consecutive_failures = 0
        self._circuit_open_until: datetime | None = None

    @property
    def circuit_open(self) -> bool:
        """True iff the breaker is currently open (skip refreshes)."""
        if self._circuit_open_until is None:
            return False
        return datetime.now(tz=timezone.utc).replace(tzinfo=None) < self._circuit_open_until

    async def refresh_once(self) -> RefreshReport:
        """Run a single refresh batch and return a :class:`RefreshReport`.

        Acquires :attr:`_lock` so the background loop and the manual
        trigger serialize their writes. If the circuit is open, returns
        immediately with ``circuit_open=True`` and does no I/O.
        """
        async with self._lock:
            if self.circuit_open:
                logger.warning("quote refresh skipped: circuit breaker open")
                return RefreshReport(refreshed=0, failed=0, circuit_open=True, symbols_total=0)

            symbols = self._collect_symbols()
            if not symbols:
                logger.info("quote refresh: no symbols under quote_kind=auto")
                return RefreshReport(refreshed=0, failed=0, circuit_open=False, symbols_total=0)

            results = await self._provider.fetch_many(symbols)
            return self._apply_results(symbols, results)

    async def run_forever(self) -> None:
        """Run the refresh loop until cancelled.

        On :class:`asyncio.CancelledError` (raised by FastAPI shutdown
        via ``task.cancel()``), exit cleanly without logging a stack
        trace. Any other exception is logged and the loop continues
        after the next sleep — we never let an exception kill the loop
        silently.
        """
        try:
            while True:
                try:
                    await self.refresh_once()
                except Exception as exc:  # noqa: BLE001 — loop must survive
                    logger.error("quote refresh loop iteration crashed: %s", exc)
                jitter = random.uniform(0, 30)
                await asyncio.sleep(self._interval + jitter)
        except asyncio.CancelledError:
            logger.info("quote refresh loop cancelled; exiting cleanly")
            raise

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _collect_symbols(self) -> list[str]:
        """Query the DB for ``broker_ticker`` of every AUTO-class position.

        Uses a single SQL query joined through ``asset_class`` so a
        future per-asset ``quote_kind`` override can be honored by
        swapping the join filter without restructuring the call sites.
        """
        with SessionLocal() as session:
            stmt = (
                select(Position.broker_ticker)
                .join(Position.asset)
                .join(AssetClass, AssetClass.id == Asset.asset_class_id)
                .where(AssetClass.quote_kind == QuoteKind.AUTO.value)
                .distinct()
            )
            rows = session.execute(stmt).scalars().all()
        return [row for row in rows if row]

    def _apply_results(
        self, symbols: list[str], results: list[Quote | None]
    ) -> RefreshReport:
        """Write successful results to the cache, update breaker state.

        Returns a :class:`RefreshReport`. A partial failure resets
        the failure counter to zero (one bad symbol does not count
        toward the threshold). A full failure (refreshed == 0,
        failed > 0) increments the counter and opens the breaker
        once the threshold is reached.
        """
        refreshed = 0
        failed = 0
        for symbol, quote in zip(symbols, results, strict=True):
            if quote is None:
                failed += 1
                continue
            self._cache.upsert(
                Quote(
                    symbol=quote.symbol,
                    price=quote.price,
                    currency=quote.currency,
                    fetched_at=quote.fetched_at,
                )
            )
            refreshed += 1

        report = RefreshReport(
            refreshed=refreshed,
            failed=failed,
            circuit_open=False,
            symbols_total=refreshed + failed,
        )

        if report.full_failure:
            self._consecutive_failures += 1
            if self._consecutive_failures >= self._threshold:
                now = datetime.now(tz=timezone.utc).replace(tzinfo=None)
                self._circuit_open_until = _add_seconds(now, self._cooldown)
                logger.error(
                    "quote refresh: circuit breaker OPEN for %ss "
                    "(%d consecutive full-batch failures)",
                    self._cooldown,
                    self._consecutive_failures,
                )
        else:
            self._consecutive_failures = 0
            self._circuit_open_until = None

        if failed:
            logger.warning(
                "quote refresh partial: refreshed=%d failed=%d total=%d",
                refreshed,
                failed,
                refreshed + failed,
            )
        else:
            logger.info("quote refresh OK: refreshed=%d", refreshed)

        return report


def _add_seconds(now: datetime, seconds: int) -> datetime:
    """Return ``now + seconds`` as a naive UTC :class:`datetime`."""
    from datetime import timedelta

    return now + timedelta(seconds=seconds)


__all__ = ["QuoteService", "RefreshReport"]