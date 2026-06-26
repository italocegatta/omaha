"""Adapter that satisfies the reference :class:`MarketPriceLookup` Protocol.

:class:`OmahaMarketPriceLookup` is the omaha-specific implementation of
the Protocol defined in :mod:`omaha.rebalance.market_prices`. It
reads cached quotes from :class:`~omaha.quotes.cache.QuoteCache` and
falls back to the broker-published
:attr:`~omaha.models.Position.current_price` for assets whose class
opted out of live fetching (``quote_kind ∈ {"none", "manual"}``).

Compared to the reference's ``YFinanceMarketPriceLookup``:

* No yfinance HTTP call on the request path — the cache is warmed by
  :class:`~omaha.quotes.service.QuoteService` in the background.
  ``BRL=X`` is pre-fetched whenever any USD asset exists (see Decision
  2 in ``openspec/changes/rebalance-infra/design.md``) so the FX rate
  is available without an HTTP call.
* The broker-published ``Position.current_price`` is the source of
  truth for ``none`` / ``manual`` classes — the reference has no
  equivalent fallback (it expects live quotes everywhere).

USD FX dependency
-----------------
USD assets require a fresh ``BRL=X`` row to be quoted. The cache
itself enforces freshness (:attr:`~omaha.config.Settings.QUOTE_TTL_SECONDS`);
the adapter adds a second check via :func:`quote_status_for` so a
stale ``BRL=X`` marks the USD row ``unavailable`` even if the asset's
own quote is fresh (the solver can't convert stale prices to BRL).

Per-asset lookup semantics
--------------------------
The adapter reads ``Position`` rows for each input asset (one query
per asset) to discover ``broker_ticker`` (for the cache key) and
``current_price`` (the ``none`` / ``manual`` fallback). The cache
lookup itself batches all symbols into a single ``QuoteCache.get_many``
call so the per-asset DB query is the only N+1 exposure — Phase 3's
route layer should pre-load ``Asset.positions`` via ``selectinload``
if it wants to eliminate that.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING

import numpy as np
import pandas as pd
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from omaha.models import Asset, Position
from omaha.quotes.cache import QuoteCache
from omaha.rebalance.market_prices import (
    USD_BRL_QUOTE_SYMBOL,
    build_empty_quote_frame,
    quote_price_from_cache,
    quote_status_for,
    resolve_quote_symbol,
)

if TYPE_CHECKING:
    from omaha.rebalance.market_prices import MarketPriceLookup


@dataclass
class OmahaMarketPriceLookup:
    """Quote lookup backed by :class:`QuoteCache` + ``Position.current_price``.

    Per-call state (``_usdbrl_price``, ``_usdbrl_fresh``) is held as
    instance attributes so a single ``get_quotes`` call resolves the
    FX rate once and reuses it for every USD asset in the input. The
    adapter is not thread-safe by design — Phase 3 serializes
    requests through the FastAPI threadpool with a per-request
    instance.

    ``db`` is the SQLAlchemy session used to look up
    ``Position.current_price`` for ``none`` / ``manual`` fallback.
    ``cache`` defaults to a new :class:`QuoteCache` instance but the
    Phase 3 caller can inject a shared one to keep the lock /
    connection warm across requests.
    """

    cache: QuoteCache
    db: Session
    _usdbrl_price: float = field(default=float("nan"), init=False, repr=False)
    _usdbrl_fresh: bool = field(default=False, init=False, repr=False)

    def __post_init__(self) -> None:
        # Resolve ``BRL=X`` once at construction so the per-row loop
        # doesn't repeat the cache lookup. ``NaN`` when missing or
        # stale — both cases mark USD assets ``unavailable`` in the
        # per-row decision below.
        cached = self.cache.get(USD_BRL_QUOTE_SYMBOL)
        if cached is not None and cached.fresh:
            self._usdbrl_price = quote_price_from_cache(float(cached.quote.price))
            self._usdbrl_fresh = bool(np.isfinite(self._usdbrl_price))
        else:
            self._usdbrl_price = float("nan")
            self._usdbrl_fresh = False

    def get_quotes(self, assets: pd.DataFrame) -> pd.DataFrame:
        """Return the seven-column quote frame for ``assets``.

        Empty input → empty frame (full schema, zero rows). Otherwise
        builds the empty frame with ``status="unavailable"`` (the
        per-row decision overwrites it to ``available`` or
        ``not-requested``), then fills one row at a time.
        """
        quote_frame = build_empty_quote_frame(assets, status="unavailable")
        if quote_frame.empty:
            return quote_frame

        asset_keys = assets["asset_key"].tolist()
        asset_meta = self._load_asset_meta(asset_keys)
        symbols = self._collect_symbols(asset_meta)
        cache_rows = self.cache.get_many(symbols) if symbols else {}

        for idx in range(len(quote_frame)):
            asset_key = str(quote_frame.at[idx, "asset_key"])
            meta = asset_meta.get(asset_key)
            quote_frame = self._populate_row(
                quote_frame,
                idx,
                asset_key=asset_key,
                meta=meta,
                cache_rows=cache_rows,
            )
        return quote_frame

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _load_asset_meta(
        self, asset_keys: list[str]
    ) -> dict[str, _AssetMeta]:
        """Resolve per-asset quote strategy from the DB.

        Single query per ``get_quotes`` call: loads ``Asset`` rows
        whose ``asset_key`` (= casefold name) matches the input,
        eagerly loading positions so the ``none`` / ``manual``
        fallback can read the first ``Position.current_price`` by id.
        Assets with zero positions get an empty position list (the
        spec's "Asset with no Position returns zero quote" case).
        """
        if not asset_keys:
            return {}

        stmt = (
            select(Asset)
            .where(func.lower(Asset.name).in_([k.casefold() for k in asset_keys]))
            .order_by(Asset.id)
        )
        from sqlalchemy.orm import selectinload

        stmt = stmt.options(selectinload(Asset.positions))
        rows = self.db.execute(stmt).scalars().all()

        result: dict[str, _AssetMeta] = {}
        for asset in rows:
            key = asset.name.casefold()
            first_pos = min(asset.positions, key=lambda p: p.id, default=None)
            result[key] = _AssetMeta(
                asset_name=asset.name,
                currency_code=asset.currency_code,
                quote_kind=_parent_quote_kind(asset),
                broker_ticker=first_pos.broker_ticker if first_pos is not None else None,
                fallback_price=(
                    float(first_pos.current_price)
                    if first_pos is not None
                    else 0.0
                ),
            )
        return result

    def _collect_symbols(self, asset_meta: dict[str, _AssetMeta]) -> list[str]:
        """Resolve the unique set of cache keys to look up.

        Only ``auto`` assets consult the cache — ``none`` / ``manual``
        assets use ``Position.current_price`` directly and never
        touch yfinance (their ``quote_symbol`` stays in the output
        frame for traceability but no cache lookup is made).
        """
        symbols: set[str] = set()
        for meta in asset_meta.values():
            if meta.quote_kind != "auto":
                continue
            symbol = resolve_quote_symbol(meta.asset_name, meta.currency_code)
            if symbol:
                symbols.add(symbol)
        return sorted(symbols)

    def _populate_row(
        self,
        quote_frame: pd.DataFrame,
        idx: int,
        *,
        asset_key: str,
        meta: _AssetMeta | None,
        cache_rows: dict,
    ) -> pd.DataFrame:
        """Fill the seven columns for one row.

        Three branches:

        * Missing from DB (asset was deleted between builders and the
          lookup) — empty symbol, zero price, ``not-requested``,
          empty currency. Mirrors the no-Position scenario.
        * No ``Position`` rows (``broker_ticker is None``) — empty
          symbol, zero price, ``not-requested``. The asset has no
          cache key to look up; the solver treats ``0.0`` as "no
          price available" (matches spec scenario "Asset with no
          Position returns zero quote").
        * Otherwise — by ``quote_kind``:

          - ``auto`` — consult the cache. Fresh hit → ``available``
            + cache price; stale or missing → ``unavailable`` +
            NaN. USD assets also need a fresh ``BRL=X`` (resolved
            once at construction).
          - ``none`` / ``manual`` — fall back to the first
            position's ``current_price``. ``quote_status =
            "not-requested"``, ``quote_currency = asset.currency_code``.
        """
        if meta is None:
            quote_frame.at[idx, "quote_symbol"] = ""
            quote_frame.at[idx, "quote_price"] = 0.0
            quote_frame.at[idx, "quote_currency"] = ""
            quote_frame.at[idx, "quote_timestamp"] = ""
            quote_frame.at[idx, "quote_status"] = "not-requested"
            quote_frame.at[idx, "usdbrl_rate"] = float("nan")
            return quote_frame

        quote_frame.at[idx, "quote_currency"] = meta.currency_code
        symbol = resolve_quote_symbol(meta.asset_name, meta.currency_code)
        if meta.broker_ticker is None:
            # Asset exists but no Position rows → no broker_ticker to
            # key the cache by. Return the "no data" shape regardless
            # of quote_kind (even an AUTO class with no positions
            # can't quote — there is no ticker to query yfinance for).
            quote_frame.at[idx, "quote_symbol"] = ""
            quote_frame.at[idx, "quote_price"] = 0.0
            quote_frame.at[idx, "quote_timestamp"] = ""
            quote_frame.at[idx, "quote_status"] = "not-requested"
            quote_frame.at[idx, "usdbrl_rate"] = float("nan")
            return quote_frame

        quote_frame.at[idx, "quote_symbol"] = symbol

        is_usd = meta.currency_code.upper() == "USD"
        usdbrl_for_row = self._usdbrl_price if is_usd else float("nan")
        quote_frame.at[idx, "usdbrl_rate"] = usdbrl_for_row

        if meta.quote_kind == "auto":
            cached = cache_rows.get(symbol)
            if cached is not None and cached.fresh:
                price = quote_price_from_cache(float(cached.quote.price))
                quote_frame.at[idx, "quote_price"] = price
                quote_frame.at[idx, "quote_timestamp"] = _format_timestamp(
                    cached.quote.fetched_at
                )
                quote_frame.at[idx, "quote_status"] = quote_status_for(
                    quote_price=price,
                    currency_code=meta.currency_code,
                    usdbrl_rate=usdbrl_for_row,
                )
            else:
                quote_frame.at[idx, "quote_price"] = float("nan")
                quote_frame.at[idx, "quote_timestamp"] = ""
                quote_frame.at[idx, "quote_status"] = "unavailable"
        else:
            # ``none`` / ``manual`` / unknown → broker price fallback.
            # ``0.0`` is preserved (a real zero is meaningful — legacy
            # positions import with ``current_price = 0``); ``None`` is
            # converted to ``0.0`` by the meta loader.
            quote_frame.at[idx, "quote_price"] = float(meta.fallback_price)
            quote_frame.at[idx, "quote_timestamp"] = ""
            quote_frame.at[idx, "quote_status"] = "not-requested"

        return quote_frame


@dataclass(frozen=True)
class _AssetMeta:
    """Per-asset quote strategy resolved from the DB.

    Private to the adapter — exposed only as a return type from
    :meth:`OmahaMarketPriceLookup._load_asset_meta`.
    """

    asset_name: str
    currency_code: str
    quote_kind: str
    broker_ticker: str | None
    fallback_price: float


def _parent_quote_kind(asset: Asset) -> str:
    """Return the ``quote_kind`` inherited from ``asset.asset_class``.

    The adapter needs this on every lookup but doesn't eagerly load
    ``AssetClass`` — fetch the attribute lazily (a single extra query
    per asset). When ``asset_class`` is missing (orphaned asset),
    fall back to ``"none"`` (the safe default — the broker price is
    the source of truth).
    """
    klass = getattr(asset, "asset_class", None)
    return getattr(klass, "quote_kind", "none") or "none"


def _format_timestamp(value: datetime | None) -> str:
    """Format a ``Quote.fetched_at`` datetime as ISO 8601 UTC.

    The reference algorithm reads the timestamp as a string for
    logging + the "Cotação de HH:MM" UI surface in Phase 5. Naive
    UTC datetimes are the omaha convention (see
    :func:`omaha.quotes.cache._now_utc`) — emit them as ``...Z`` so
    the consumer doesn't have to second-guess the timezone.
    """
    if value is None:
        return ""
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc).isoformat()
    return value.astimezone(timezone.utc).isoformat()


def _as_protocol(impl: OmahaMarketPriceLookup) -> "MarketPriceLookup":
    """Satisfy the type checker; the dataclass already implements the Protocol."""
    return impl


# ``_as_protocol`` and the alias keep static analyzers from complaining
# about the structural Protocol mismatch while leaving the public
# class name (``OmahaMarketPriceLookup``) unchanged.
_ = _as_protocol
_ = Decimal  # silence unused-import for callers that re-export


__all__ = ["OmahaMarketPriceLookup"]
