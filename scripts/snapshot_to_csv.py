"""Snapshot the live DB state to ``data/seed/{profile}_*.csv``.

The dev DB carries the canonical wallet state via ``AssetClass``,
``Asset``, and ``Position`` rows. The CSV triplet under ``data/seed/``
is the controlled boundary between the DB and hand-edits — when the
schema evolves, when the user tweaks a price via the UI, or when the
user adds a position via the import flow, the DB drifts ahead of the
CSV. Without a path back, the next ``task db-reset`` overwrites the
drift with the stale CSV and the operator loses the work.

This script is the missing **DB → CSV** direction. It is the
symmetric counterpart to ``scripts.seed_from_csv.py``: the latter
reads CSVs and writes DB; this script reads DB and writes CSVs.
``task db-snapshot && task db-reset`` is the deterministic
round-trip.

Why
---

The CSVs in ``data/seed/`` are hand-edited and back-propagated to the
DB via ``task db-reset`` per the AGENTS.md "Seed data" rule. Every
new column on ``Position`` (``total_invested``, ``total_current``,
``broker_ticker``), on ``Asset`` (``buy_enabled``, ``sell_enabled``,
``currency_code``), and on ``AssetClass`` (``quote_kind``) had to be
back-propagated by hand. When the dev DB drifts ahead — the user
fiddles a price in the UI or imports a fresh broker CSV — there was
no path to "freeze" the live state back into the CSV.

What
----

* Iterate every canonical profile in ``PROFILES`` (``italo``, ``ana``)
  in order. Fail fast (exit 1) if the DB contains any profile outside
  the canonical set — usually a stray test profile left behind.
* For each profile, write three CSVs into ``data/seed/``:
  * ``{profile}_classes.csv`` — header
    ``name,target_pct,display_order,quote_kind``
  * ``{profile}_assets.csv`` — header
    ``class_name,name,target_pct,display_order,buy_enabled,
    sell_enabled,currency_code``
  * ``{profile}_positions.csv`` — header
    ``asset_name,broker_ticker,qty,avg_price,current_price``
* Atomic write (``.tmp`` + ``os.replace``) so a crash mid-export
  cannot leave the CSV half-written. Idempotent: re-running overwrites
  with identical content.
* ``broker_ticker`` is taken verbatim from ``Position.broker_ticker``.
  When ``broker_ticker == asset_name`` (the historical 1:1 mapping),
  the row reads the same value in both columns; when they diverge
  (e.g. user labels an asset "Petrobras PN" while the broker reports
  it as ``PETR4``), both columns are preserved.

Usage
-----

::

    uv run python -m scripts.snapshot_to_csv
    # expected:
    #   italo: 6 classes, 48 assets, 47 positions -> 3 files written
    #   ana:   6 classes, ~40 assets, ~43 positions -> 3 files written
    #   snapshot OK: 6 files written

The canonical entry point is ``task db-snapshot`` (see
``pyproject.toml``).
"""

from __future__ import annotations

import csv
import os
import sys
from collections.abc import Iterable
from decimal import Decimal
from pathlib import Path

from sqlalchemy.orm import Session

from omaha.db import SessionLocal
from omaha.models import Profile
from scripts.seed_from_csv import abort

REPO_ROOT = Path(__file__).resolve().parent.parent
SEED_DIR = REPO_ROOT / "data" / "seed"

PROFILES = ("italo", "ana")

CLASS_HEADER = ("name", "target_pct", "display_order", "quote_kind")
ASSET_HEADER = (
    "class_name",
    "name",
    "target_pct",
    "display_order",
    "buy_enabled",
    "sell_enabled",
    "currency_code",
)
POSITION_HEADER = (
    "asset_name",
    "broker_ticker",
    "qty",
    "avg_price",
    "current_price",
    "total_invested",
    "total_current",
)


def _format_decimal(value: Decimal, places: int) -> str:
    """Render ``value`` as ``str`` with ``places`` decimals.

    Mirrors the precision ``seed_from_csv.py`` expects on parse:
    ``target_pct`` uses 2 places; qty/avg_price/current_price use
    8 places (matches the DB column ``Numeric(18, 8)``).
    """
    return str(value.quantize(Decimal(10) ** -places))


def _format_bool(value: bool) -> str:
    """Render a bool as the lowercase ``true``/``false`` the
    ``seed_from_csv._bool`` permissive parser accepts."""
    return "true" if value else "false"


def _atomic_write_csv(
    path: Path, header: tuple[str, ...], rows: Iterable[tuple[object, ...]]
) -> None:
    """Write ``rows`` to ``path`` atomically.

    Writes to ``path.with_suffix(path.suffix + ".tmp")`` first, then
    ``os.replace`` swaps it into place. A crash mid-write leaves the
    original file untouched; the ``.tmp`` is cleaned up on the next
    run (success or failure). Matches the existing CSVs in
    ``data/seed/`` (``lineterminator="\\n"``).
    """
    tmp = path.with_suffix(path.suffix + ".tmp")
    try:
        with tmp.open("w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f, lineterminator="\n")
            writer.writerow(header)
            for row in rows:
                writer.writerow(row)
        os.replace(tmp, path)
    finally:
        if tmp.exists():
            tmp.unlink()


def snapshot_classes(profile: Profile, profile_name: str) -> int:
    """Write ``data/seed/{profile_name}_classes.csv``. Returns the row count.

    ``profile_name`` is the canonical lowercase name (``italo`` / ``ana``)
    so the filename matches the existing CSVs the seed script reads;
    ``profile.name`` is the capitalized display name (``Italo`` /
    ``Ana``).
    """
    path = SEED_DIR / f"{profile_name}_classes.csv"
    classes = sorted(profile.asset_classes, key=lambda c: c.display_order)
    rows = (
        (
            c.name,
            _format_decimal(c.target_pct, 2),
            c.display_order,
            c.quote_kind,
        )
        for c in classes
    )
    _atomic_write_csv(path, CLASS_HEADER, rows)
    return len(classes)


def snapshot_assets(profile: Profile, profile_name: str) -> int:
    """Write ``data/seed/{profile_name}_assets.csv``. Returns the row count."""
    path = SEED_DIR / f"{profile_name}_assets.csv"

    def _iter() -> Iterable[tuple[object, ...]]:
        for klass in sorted(profile.asset_classes, key=lambda c: c.display_order):
            for asset in sorted(klass.assets, key=lambda a: a.display_order):
                yield (
                    klass.name,
                    asset.name,
                    _format_decimal(asset.target_pct, 2),
                    asset.display_order,
                    _format_bool(asset.buy_enabled),
                    _format_bool(asset.sell_enabled),
                    asset.currency_code.upper(),
                )

    _atomic_write_csv(path, ASSET_HEADER, _iter())
    return sum(len(k.assets) for k in profile.asset_classes)


def snapshot_positions(profile: Profile, profile_name: str) -> int:
    """Write ``data/seed/{profile_name}_positions.csv``. Returns the row count."""
    path = SEED_DIR / f"{profile_name}_positions.csv"

    def _iter() -> Iterable[tuple[object, ...]]:
        for klass in sorted(profile.asset_classes, key=lambda c: c.display_order):
            for asset in sorted(klass.assets, key=lambda a: a.display_order):
                for pos in sorted(asset.positions, key=lambda p: p.broker_ticker):
                    # broker-csv-import-totals: totals are
                    # broker-published values, NOT recomputed from
                    # ``qty * price``. Empty cell ↔ ``None``
                    # (contributes 0 to the dashboard aggregate).
                    yield (
                        asset.name,
                        pos.broker_ticker,
                        _format_decimal(pos.qty, 8),
                        _format_decimal(pos.avg_price, 8),
                        _format_decimal(pos.current_price, 8),
                        ""
                        if pos.total_invested is None
                        else _format_decimal(pos.total_invested, 4),
                        "" if pos.total_current is None else _format_decimal(pos.total_current, 4),
                    )

    _atomic_write_csv(path, POSITION_HEADER, _iter())
    return sum(len(a.positions) for k in profile.asset_classes for a in k.assets)


def snapshot_profile(session: Session, profile_name: str) -> tuple[int, int, int]:
    """Snapshot one profile's three CSVs. Returns ``(C, A, P)`` counts."""
    profile = session.query(Profile).filter(Profile.name == profile_name.capitalize()).one_or_none()
    if profile is None:
        abort(f'snapshot FAIL: profile "{profile_name}" missing from DB')
    return (
        snapshot_classes(profile, profile_name),
        snapshot_assets(profile, profile_name),
        snapshot_positions(profile, profile_name),
    )


def main(argv: list[str] | None = None) -> int:
    """Discover profiles, validate against the canonical set, snapshot each.

    Returns 0 on success, 1 on any failure (unknown / missing profile,
    unwritable output dir, etc.). A failure aborts BEFORE any CSV is
    written so the existing CSVs are not touched.
    """
    session = SessionLocal()
    try:
        profiles = session.query(Profile).order_by(Profile.user_id, Profile.display_order).all()
        names = [p.name for p in profiles]
        unknown = [n for n in names if n.lower() not in PROFILES]
        if unknown:
            abort(
                f"snapshot FAIL: profile {unknown!r} not in canonical set {{{', '.join(PROFILES)}}}"
            )
        present = {n.lower() for n in names}
        missing = [p for p in PROFILES if p not in present]
        if missing:
            abort(f"snapshot FAIL: profile {missing!r} missing from DB")

        totals = (0, 0, 0)
        for profile_name in PROFILES:
            c, a, p = snapshot_profile(session, profile_name)
            totals = (totals[0] + c, totals[1] + a, totals[2] + p)
            print(f"{profile_name}: {c} classes, {a} assets, {p} positions -> 3 files written")
        print(
            f"snapshot OK: {totals[0] + totals[1] + totals[2]} rows across "
            f"{len(PROFILES) * 3} files written"
        )
    finally:
        session.close()
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
