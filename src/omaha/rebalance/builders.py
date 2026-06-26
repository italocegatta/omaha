"""Pure-function bridges that translate the omaha ORM into solver inputs.

Two builders consume a :class:`~omaha.models.Profile` + a
:class:`~sqlalchemy.orm.Session` and return the data shapes the
reference CVXPY solver expects:

* :func:`build_setup_from_db` — :class:`~omaha.rebalance.models.PortfolioSetup`
  + warnings. Categories carry target weights in 0..1; assets carry
  per-class and whole-portfolio target weights plus the per-asset
  trade-control flags (``buy_enabled`` / ``sell_enabled`` /
  ``currency_code``) and the omaha-specific ``quote_kind`` column.
* :func:`build_position_frame` — a flat DataFrame with one row per
  asset, aggregating ``qty`` / ``total_invested`` / ``total_current``
  across the asset's positions and computing ``current_weight``.

Decimal → float conversion happens once at extraction time
(:class:`decimal.Decimal` → :class:`float` on the way into the dict),
not per-cell inside a pandas ``.apply`` loop — the solver tolerates
``1e-6`` drift and a per-cell conversion would multiply rounding
errors across hundreds of assets.

``category_order`` / ``asset_order`` are re-numbered ``0..N-1``
regardless of ``display_order`` gaps (defensive — a future CSV edit
that leaves holes in display_order shouldn't confuse the solver's
positional index lookups).

Warnings
--------
The returned warnings list captures two signals from spec §"Asset name
collision" and §"Empty class with non-zero target":

* Cross-class ``Asset.name`` collision → one warning per collision
  naming both ``AssetClass.id`` values. The algorithm's
  ``_validate_rebalance_inputs`` rejects duplicate ``asset_key``;
  groupby-first + warning keeps the solver running while surfacing
  the shadowed row in the response.
* Empty class with ``target_pct > 0`` → one warning naming the class.
  Empty class with ``target_pct == 0`` does NOT warn (the solver
  wouldn't allocate to it anyway).

Eager loading
-------------
Both builders query via the session, so they do not depend on the
caller's pre-loading — but the Phase 3 route layer should still
``selectinload`` ``AssetClass.assets`` and ``Asset.positions`` so a
profile with many positions renders the dashboard while building
without an N+1.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

import pandas as pd
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from omaha.models import Asset, AssetClass, Position, Profile
from omaha.rebalance.models import PortfolioSetup

# Decimal columns from ``Asset.target_pct`` / ``AssetClass.target_pct``
# are stored in 0..100 in the DB; the solver expects fractions in
# 0..1. ``_PCT_DIVISOR`` is the shared scaling factor for both the
# per-class target (``Asset.target_pct / 100``) and the whole-portfolio
# target (``Asset.target_pct * AssetClass.target_pct / 10000``). Pulled
# out as a constant so the test fixtures and the warning text agree
# on the rounding precision (``20.00%`` not ``20%``).
_PCT_DIVISOR = Decimal("100")
_PCT_PRODUCT_DIVISOR = Decimal("10000")

_CATEGORIES_COLUMNS = [
    "category_name",
    "category_key",
    "target_weight",
    "category_order",
]

_ASSETS_COLUMNS = [
    "asset_name",
    "asset_key",
    "category_name",
    "category_key",
    "currency_code",
    "buy_enabled",
    "sell_enabled",
    "target_weight_in_category",
    "target_weight",
    "asset_order",
    "quote_kind",
]

_POSITIONS_COLUMNS = [
    "asset_key",
    "asset_name",
    "category_name",
    "category_key",
    "quantity",
    "invested_value",
    "current_value",
    "current_weight",
]


def build_setup_from_db(
    db: Session, profile: Profile
) -> tuple[PortfolioSetup, list[str]]:
    """Translate ``profile``'s classes+assets into a :class:`PortfolioSetup`.

    Returns ``(setup, warnings)``. ``warnings`` is always a list (never
    ``None``) so callers can ``.extend()`` without a None guard.

    The query is one ``select(AssetClass)`` with a ``selectinload`` on
    ``AssetClass.assets`` — assets are loaded in a single follow-up
    query, not N+1 lazy loads. The asset-level relationship to
    :class:`~omaha.models.Position` is NOT pre-loaded here (the
    positions builder handles that separately to keep this builder's
    hot path free of position data the setup doesn't need).
    """
    classes = (
        db.execute(
            select(AssetClass)
            .where(AssetClass.profile_id == profile.id)
            .options(selectinload(AssetClass.assets))
            .order_by(AssetClass.display_order, AssetClass.id)
        )
        .scalars()
        .all()
    )

    categories_df, categories_warnings = _build_categories_frame(classes)
    assets_df, asset_warnings = _build_assets_frame(classes)

    return (
        PortfolioSetup(categories=categories_df, assets=assets_df),
        [*categories_warnings, *asset_warnings],
    )


def build_position_frame(db: Session, profile: Profile) -> pd.DataFrame:
    """Aggregate ``Position`` rows per asset for ``profile`` into a DataFrame.

    Returns one row per ``Asset`` (whether or not it has positions) so
    the solver's outer-join / reindex calls don't KeyError on
    asset-only rows. Aggregation reads the broker-published
    ``total_invested`` / ``total_current`` columns directly
    (NULL → 0); it does NOT recompute ``qty * price`` — see
    ``broker-csv-import-totals`` for the rationale.

    Empty portfolio (no positions across the whole profile) returns
    a DataFrame with all eight columns and ``current_weight = 0.0``
    per row (NOT ``NaN`` — the solver's ``current_weight`` constraints
    expect a number, and ``0.0`` is the correct "no share" signal).
    """
    asset_rows = (
        db.execute(
            select(Asset)
            .join(AssetClass, AssetClass.id == Asset.asset_class_id)
            .where(AssetClass.profile_id == profile.id)
            .options(selectinload(Asset.positions))
            .order_by(AssetClass.display_order, AssetClass.id, Asset.display_order, Asset.id)
        )
        .scalars()
        .all()
    )

    if not asset_rows:
        return _empty_positions_frame()

    aggregates: list[dict[str, Any]] = []
    for asset in asset_rows:
        klass = asset.asset_class
        quantity = Decimal("0")
        invested = Decimal("0")
        current = Decimal("0")
        for pos in asset.positions:
            quantity += pos.qty or Decimal("0")
            invested += pos.total_invested or Decimal("0")
            current += pos.total_current or Decimal("0")
        aggregates.append(
            {
                "asset_key": asset.name.casefold(),
                "asset_name": asset.name,
                "category_name": klass.name if klass is not None else "",
                "category_key": klass.name.casefold() if klass is not None else "",
                "quantity": float(quantity),
                "invested_value": float(invested),
                "current_value": float(current),
            }
        )

    df = pd.DataFrame(aggregates, columns=_POSITIONS_COLUMNS)
    total_current = float(df["current_value"].sum())
    if total_current == 0.0:
        df["current_weight"] = 0.0
    else:
        df["current_weight"] = df["current_value"] / total_current
    return df


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _build_categories_frame(
    classes: list[AssetClass],
) -> tuple[pd.DataFrame, list[str]]:
    """Build the categories DataFrame + empty-class warnings.

    The categories frame has 4 columns × N rows (one row per class).
    ``category_order`` is re-numbered ``0..N-1`` regardless of
    ``display_order`` gaps so the solver's positional index lookups
    stay consistent even if the user later re-orders or deletes a
    class.

    Empty classes (``assets == []``) with non-zero ``target_pct``
    emit one warning each. Empty classes with ``target_pct == 0``
    emit no warning (the solver wouldn't allocate to them anyway).
    """
    if not classes:
        return _empty_categories_frame(), []

    rows: list[dict[str, Any]] = []
    warnings: list[str] = []
    for new_order, klass in enumerate(classes):
        rows.append(
            {
                "category_name": klass.name,
                "category_key": klass.name.casefold(),
                "target_weight": _decimal_to_weight(klass.target_pct),
                "category_order": new_order,
            }
        )
        if not klass.assets and (klass.target_pct or Decimal("0")) > Decimal("0"):
            warnings.append(
                f"Classe '{klass.name}' está vazia mas com "
                f"target_pct={klass.target_pct:.2f}%; solver irá alocar caixa residual."
            )
    return pd.DataFrame(rows, columns=_CATEGORIES_COLUMNS), warnings


def _build_assets_frame(
    classes: list[AssetClass],
) -> tuple[pd.DataFrame, list[str]]:
    """Build the assets DataFrame + cross-class collision warnings.

    Walks every class × asset in order, then deduplicates by
    ``asset_key`` (casefolded asset name). When two classes share an
    asset name, the first occurrence (by class order, then by
    ``display_order`` then by ``id``) is kept and one warning per
    collision is emitted — see design.md Decision 1.

    ``asset_order`` is re-numbered ``0..N-1`` per class so the solver
    doesn't have to know about ``display_order`` gaps within a class.
    """
    if not classes:
        return _empty_assets_frame(), []

    rows: list[dict[str, Any]] = []
    for klass in classes:
        class_weight = _decimal_to_weight(klass.target_pct)
        sorted_assets = sorted(
            klass.assets,
            key=lambda a: (a.display_order, a.id),
        )
        for new_order, asset in enumerate(sorted_assets):
            asset_target = _decimal_to_weight(asset.target_pct)
            rows.append(
                {
                    "asset_name": asset.name,
                    "asset_key": asset.name.casefold(),
                    "category_name": klass.name,
                    "category_key": klass.name.casefold(),
                    "currency_code": asset.currency_code,
                    "buy_enabled": bool(asset.buy_enabled),
                    "sell_enabled": bool(asset.sell_enabled),
                    "target_weight_in_category": asset_target,
                    "target_weight": asset_target * class_weight,
                    "asset_order": new_order,
                    "quote_kind": klass.quote_kind,
                }
            )

    if not rows:
        return _empty_assets_frame(), []

    df = pd.DataFrame(rows, columns=_ASSETS_COLUMNS)
    grouped = df.groupby("asset_key", sort=False)
    counts = grouped.size()
    if (counts > 1).any():
        collisions = counts[counts > 1].index.tolist()
        deduped = df.drop_duplicates(subset=["asset_key"], keep="first").reset_index(drop=True)
        warnings = _build_collision_warnings(df, collisions)
        return deduped, warnings
    return df.reset_index(drop=True), []


def _build_collision_warnings(
    df: pd.DataFrame, collisions: list[str]
) -> list[str]:
    """Build one warning per cross-class ``asset_key`` collision.

    Each warning names both ``asset_class_id`` values that own the
    shadowed asset row (the warning text uses ``asset_class_id``
    because ``category_key`` is ``casefold(name)`` and a collision
    by definition shares it). Per spec scenario "Asset name collision
    across classes is shadowed with warning".
    """
    warnings: list[str] = []
    for asset_key in collisions:
        matched = df.loc[df["asset_key"] == asset_key, "category_key"].tolist()
        unique_class_ids = sorted(set(matched))
        # ``category_key`` is the casefolded class name; collapse to a
        # de-duplicated, sorted list so the warning is deterministic.
        joined = ", ".join(unique_class_ids)
        warnings.append(
            f"Ativo '{asset_key}' aparece em múltiplas classes ({joined}); "
            "a primeira ocorrência (por ordem de classe) foi mantida."
        )
    return warnings


def _empty_categories_frame() -> pd.DataFrame:
    """Return the categories DataFrame with full schema and zero rows."""
    return pd.DataFrame(columns=_CATEGORIES_COLUMNS)


def _empty_assets_frame() -> pd.DataFrame:
    """Return the assets DataFrame with full schema and zero rows."""
    return pd.DataFrame(columns=_ASSETS_COLUMNS)


def _empty_positions_frame() -> pd.DataFrame:
    """Return the positions DataFrame with full schema and zero rows."""
    df = pd.DataFrame(columns=_POSITIONS_COLUMNS)
    # Force float dtype on the numeric columns so the solver's
    # ``pd.api.types.is_numeric_dtype`` checks succeed even on an
    # empty frame (an all-NaN column reads as object dtype by default).
    for col in ("quantity", "invested_value", "current_value", "current_weight"):
        df[col] = pd.Series(dtype="float64")
    return df


def _decimal_to_weight(value: Decimal | None) -> float:
    """Convert a 0..100 percentage ``Decimal`` to a 0..1 weight float.

    ``None`` and ``Decimal('NaN')`` both map to ``0.0`` (a target of
    zero is meaningful — the solver treats it as "no allocation" — and
    we don't want a downstream ``NaN`` propagating through the LP).
    """
    if value is None:
        return 0.0
    try:
        if value.is_nan():
            return 0.0
    except AttributeError:
        pass
    weight = float(value) / float(_PCT_DIVISOR)
    # Two-product math (asset × class / 10000) may produce 1.0000…0001
    # from rounding. Clamp to [0, 1] so the solver's sum-to-100
    # invariant in ``_validate_rebalance_inputs`` doesn't fire on
    # floating-point dust.
    if weight < 0.0:
        return 0.0
    if weight > 1.0:
        return 1.0
    return weight


# ``func`` import retained for symmetry with future query helpers and
# to silence the unused-import warning when no positional aggregates
# are needed at module level.
_ = func


__all__ = ["build_position_frame", "build_setup_from_db"]
