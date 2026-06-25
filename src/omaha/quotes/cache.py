"""DB-backed cache for market quotes.

The :class:`QuoteCache` reads/writes the ``quotes`` table built by the
0014 Alembic migration. Persistence is in the same SQLite/Postgres
database as the rest of the app so a uvicorn reload or container
restart does not clear the cache; freshness is computed at read time
from ``fetched_at`` and :attr:`~omaha.config.Settings.QUOTE_TTL_SECONDS`.

Each method uses a short-lived SQLAlchemy session (the same pattern as
:func:`omaha.seed.seed`) so the cache never holds a stale connection
across a reload — important for the background refresh loop in
:mod:`omaha.quotes.service`, which may run for hours.

Upsert implementation
---------------------
``upsert`` uses the dialect-native ``INSERT ... ON CONFLICT(symbol)
DO UPDATE`` form via SQLAlchemy's ``insert().on_conflict_do_update()``,
which generates the right SQL for both SQLite (>= 3.24) and Postgres.
Doing it at the DB level avoids a SELECT-then-INSERT/UPDATE race when
two writers target the same symbol concurrently — the DB enforces the
single-row semantics atomically.

Freshness
---------
``get`` and ``get_many`` return a :class:`QuoteWithFreshness` carrying
the row plus a ``fresh`` flag derived from
``now() - fetched_at <= QUOTE_TTL_SECONDS``. A ``None`` row also yields
``fresh=False`` (the consumer's contract: ``Quote | None`` is the
"missing" signal; the freshness flag is the "we have data but it's
old" signal).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from omaha.config import settings
from omaha.db import SessionLocal
from omaha.models import Quote


@dataclass(frozen=True)
class QuoteWithFreshness:
    """A :class:`~omaha.models.Quote` row plus a freshness flag.

    ``fresh`` is ``True`` iff ``now - fetched_at <= QUOTE_TTL_SECONDS``.
    A missing row is represented as ``None`` (no QuoteWithFreshness),
    not as a stale flag — the route layer distinguishes "no data" from
    "stale data" via the ``None`` vs ``fresh=False`` split.
    """

    quote: Quote
    fresh: bool


def _is_postgres(session: Session) -> bool:
    """Return True when the bound engine speaks the Postgres dialect."""
    return session.bind.dialect.name == "postgresql"


def _now_utc() -> datetime:
    """Return the current UTC time as a naive :class:`datetime`.

    SQLite stores :class:`DateTime` columns without timezone info, and
    Postgres defaults to timestamptz only when the column type is
    declared ``TIMESTAMP WITH TIME ZONE`` — ours is ``TIMESTAMP`` (the
    SQLAlchemy ``DateTime`` default), so we keep things consistent by
    always writing/reading naive UTC.
    """
    return datetime.now(tz=timezone.utc).replace(tzinfo=None)


class QuoteCache:
    """Read/write the ``quotes`` table.

    Constructed with no arguments; the underlying engine is the
    module-level :data:`omaha.db.SessionLocal`. Methods open their own
    short-lived session via the :func:`_session_scope` helper, so a
    caller can keep one cache instance for the life of the process
    without worrying about session lifecycle.
    """

    def upsert(self, quote: Quote) -> None:
        """Write ``quote`` to the cache, replacing any existing row.

        ``quote.fetched_at`` is overwritten with ``now()`` so the
        freshness check downstream does not depend on the caller
        stamping the timestamp correctly.
        """
        stamped = Quote(
            symbol=quote.symbol,
            price=quote.price,
            currency=quote.currency,
            fetched_at=_now_utc(),
        )
        values = {
            "symbol": stamped.symbol,
            "price": stamped.price,
            "currency": stamped.currency,
            "fetched_at": stamped.fetched_at,
        }
        with _session_scope() as session:
            insert_stmt = (
                pg_insert(Quote) if _is_postgres(session) else sqlite_insert(Quote)
            ).values(**values)
            upsert_stmt = insert_stmt.on_conflict_do_update(
                index_elements=[Quote.symbol],
                set_={
                    "price": values["price"],
                    "currency": values["currency"],
                    "fetched_at": values["fetched_at"],
                },
            )
            session.execute(upsert_stmt)
            session.commit()

    def get(self, symbol: str) -> QuoteWithFreshness | None:
        """Return the cached quote for ``symbol`` plus a freshness flag.

        ``None`` when no row exists for ``symbol`` (no flag — "missing"
        is a different signal than "stale"). The freshness flag is
        computed from :attr:`~omaha.config.Settings.QUOTE_TTL_SECONDS`
        against ``fetched_at`` in UTC.
        """
        with _session_scope() as session:
            row = session.get(Quote, symbol)
        if row is None:
            return None
        return QuoteWithFreshness(quote=row, fresh=self._is_fresh(row.fetched_at))

    def get_many(self, symbols: list[str]) -> dict[str, QuoteWithFreshness]:
        """Return ``{symbol: QuoteWithFreshness}`` for every stored symbol.

        Symbols not present in the cache are silently omitted (no
        ``None`` placeholder). The order of the input list is not
        preserved; callers that need ordering should iterate over the
        original list and index the result dict.
        """
        if not symbols:
            return {}
        with _session_scope() as session:
            stmt = select(Quote).where(Quote.symbol.in_(symbols))
            rows = session.execute(stmt).scalars().all()
        return {row.symbol: QuoteWithFreshness(quote=row, fresh=self._is_fresh(row.fetched_at))
                for row in rows}

    @staticmethod
    def _is_fresh(fetched_at: datetime) -> bool:
        """Return True when ``fetched_at`` is within the configured TTL."""
        age = _now_utc() - fetched_at
        return age <= timedelta(seconds=settings.QUOTE_TTL_SECONDS)


class _session_scope:
    """Tiny context manager that yields a fresh :class:`Session`.

    The cache methods prefer the pattern "open, do work, commit, close"
    to "open once and reuse" so a stale connection (after a uvicorn
    reload that swapped the engine) cannot poison the next call.
    """

    def __enter__(self) -> Session:
        self._session = SessionLocal()
        return self._session

    def __exit__(self, exc_type, exc, tb) -> None:
        try:
            if exc_type is None:
                self._session.commit()
            else:
                self._session.rollback()
        finally:
            self._session.close()


__all__ = ["QuoteCache", "QuoteWithFreshness"]