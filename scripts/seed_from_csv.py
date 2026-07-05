"""CSV-driven per-profile seed: wipe / upsert / diff.

The dev DB is seeded for each profile (``italo`` / ``ana``) by reading
a triplet of CSV files from ``data/seed/``:

* ``{profile}_classes.csv`` — class targets (sum = 100).
* ``{profile}_assets.csv`` — per-class asset targets (per-class sum = 100).
* ``{profile}_positions.csv`` — current broker positions.

Three modes:

* ``reset`` — wipe ``positions`` / ``import_previews`` / ``assets`` /
  ``asset_classes`` for the profile, then re-insert classes, assets,
  and positions in ``display_order`` ascending. Positions MUST be
  inserted after their asset exists so the ``asset_id`` FK resolves.
* ``upsert`` — no delete. Create-or-update classes by
  ``(profile_id, name)``, assets by ``(asset_class_id, name)``,
  positions by ``(asset_id, broker_ticker)``. Prints
  ``created`` / ``updated`` / ``unchanged`` per layer.
* ``diff`` — no write. Read the triplet, validate, then print
  ``would-create`` / ``would-update`` / ``would-orphan`` sections.

All three modes enforce the same validation pipeline
(headers / types / ranges / uniqueness / cross-references /
``sum == 100`` invariants). Validation aborts BEFORE any DB write,
regardless of mode.

Run with::

    uv run python -m scripts.seed_from_csv --profile italo --mode reset
    uv run python -m scripts.seed_from_csv --profile ana --mode diff
    uv run python -m scripts.seed_from_csv --profile italo --mode upsert
"""

from __future__ import annotations

import argparse
import csv
import sys
from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.orm import Session

from omaha.db import SessionLocal
from omaha.models import Asset, AssetClass, Position, Profile, QuoteKind, User
from omaha.validators import validate_target_pct_sum

REPO_ROOT = Path(__file__).resolve().parent.parent
SEED_DIR = REPO_ROOT / "data" / "seed"

PROFILES = ("italo", "ana")

# Maps each CLI ``--profile`` value to the ``(user.username,
# Profile.name)`` pair the seed targets. The canonical pair
# (``italo`` → ``Italo`` / ``Italo``) keeps the legacy 1-to-1 shape;
# the F01 fixture pair (``italo_rf2`` → ``Italo`` / ``Italo RF2``)
# was retired in F07 because the F01 multi-profile intra-User
# invariant is dead — the Família sentinel (seed.py) is the only
# cross-User aggregator now. Use ``italo`` and ``ana`` only.
PROFILE_OWNER_TO_NAME: dict[str, tuple[str, str]] = {
    "italo": ("Italo", "Italo"),
    "ana": ("Ana", "Ana"),
}
MODES = ("reset", "upsert", "diff")

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

VALID_QUOTE_KINDS = frozenset({q.value for q in QuoteKind})
VALID_CURRENCY_CODES = frozenset({"BRL", "USD"})


# ---------------------------------------------------------------------------
# CSV row dataclasses
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ClassRow:
    name: str
    target_pct: Decimal
    display_order: int
    quote_kind: str
    line_no: int


@dataclass(frozen=True)
class AssetRow:
    class_name: str
    name: str
    target_pct: Decimal
    display_order: int
    buy_enabled: bool
    sell_enabled: bool
    currency_code: str
    line_no: int


@dataclass(frozen=True)
class PositionRow:
    asset_name: str
    broker_ticker: str
    qty: Decimal
    avg_price: Decimal
    current_price: Decimal
    # broker-csv-import-totals: totals are broker-published values,
    # NEVER recomputed from ``qty * price``. An empty cell in the CSV
    # parses to ``None`` and contributes 0 to the dashboard aggregate
    # (see ``routes/pages.py``); a non-empty cell is taken verbatim
    # and inserted into ``Position.total_invested`` / ``total_current``.
    total_invested: Decimal | None
    total_current: Decimal | None
    line_no: int


# ---------------------------------------------------------------------------
# CSV loaders
# ---------------------------------------------------------------------------


def _read_csv(path: Path, expected_header: tuple[str, ...]) -> list[dict[str, str]]:
    """Read a CSV file and verify its header.

    Returns a list of row dicts keyed by header column. Aborts on:
    - missing file
    - wrong header (in order or missing columns)
    """
    if not path.exists():
        abort(f"missing CSV: {path}")
    with open(path, encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        try:
            header = tuple(next(reader))
        except StopIteration:
            abort(f"empty CSV (no header): {path}")
        if header != expected_header:
            abort(
                f"bad header in {path}\n"
                f"  expected: {','.join(expected_header)}\n"
                f"  got:      {','.join(header)}"
            )
        return [dict(zip(expected_header, row, strict=False)) for row in reader]


def _decimal(raw: str, *, field: str, path: Path, line_no: int) -> Decimal:
    try:
        return Decimal(raw.strip())
    except Exception as exc:  # noqa: BLE001 — argparse-style catch
        abort(f"{path}:{line_no} {field}={raw!r} not a decimal: {exc}")


def _optional_decimal(raw: str, *, field: str, path: Path, line_no: int) -> Decimal | None:
    """Parse a CSV cell that may be empty (``None``) or a decimal.

    Empty / whitespace-only cell → ``None``. Non-empty cell must
    parse as :class:`~decimal.Decimal`; otherwise abort with the
    line number. Used for ``total_invested`` / ``total_current``
    so the broker-published values flow through the round-trip
    without ever being recomputed from ``qty * price``.
    """
    s = raw.strip()
    if not s:
        return None
    try:
        value = Decimal(s)
    except Exception as exc:  # noqa: BLE001 — argparse-style catch
        abort(f"{path}:{line_no} {field}={raw!r} not a decimal: {exc}")
    if value < 0:
        abort(f"{path}:{line_no} {field}={value} < 0")
    return value


def _int(raw: str, *, field: str, path: Path, line_no: int) -> int:
    try:
        return int(Decimal(raw.strip()))
    except Exception as exc:  # noqa: BLE001
        abort(f"{path}:{line_no} {field}={raw!r} not an integer: {exc}")


def _bool(raw: str, *, field: str, path: Path, line_no: int) -> bool:
    """Parse a permissive boolean cell. Accepts ``true/false/1/0/yes/no``."""
    s = raw.strip().lower()
    if s in {"true", "1", "yes", "y", "t"}:
        return True
    if s in {"false", "0", "no", "n", "f", ""}:
        return False
    abort(f"{path}:{line_no} {field}={raw!r} not a boolean (use true/false/1/0)")


def load_classes(profile: str) -> list[ClassRow]:
    path = SEED_DIR / f"{profile}_classes.csv"
    raw_rows = _read_csv(path, CLASS_HEADER)
    out: list[ClassRow] = []
    seen: dict[str, int] = {}
    for idx, raw in enumerate(raw_rows, start=2):  # header is line 1
        name = raw["name"].strip()
        if not name:
            abort(f"{path}:{idx} empty class name")
        if name in seen:
            abort(f"{path}:{idx} duplicate class name {name!r} (first seen at line {seen[name]})")
        seen[name] = idx
        target_pct = _decimal(raw["target_pct"], field="target_pct", path=path, line_no=idx)
        if not (Decimal("0") <= target_pct <= Decimal("100")):
            abort(f"{path}:{idx} target_pct={target_pct} out of [0, 100]")
        display_order = _int(raw["display_order"], field="display_order", path=path, line_no=idx)
        if display_order < 0:
            abort(f"{path}:{idx} display_order={display_order} < 0")
        quote_kind = raw["quote_kind"].strip()
        if quote_kind not in VALID_QUOTE_KINDS:
            abort(f"{path}:{idx} quote_kind={quote_kind!r} not one of {sorted(VALID_QUOTE_KINDS)}")
        out.append(
            ClassRow(
                name=name,
                target_pct=target_pct,
                display_order=display_order,
                quote_kind=quote_kind,
                line_no=idx,
            )
        )
    return out


def load_assets(profile: str) -> list[AssetRow]:
    path = SEED_DIR / f"{profile}_assets.csv"
    raw_rows = _read_csv(path, ASSET_HEADER)
    out: list[AssetRow] = []
    seen: dict[tuple[str, str], int] = {}
    for idx, raw in enumerate(raw_rows, start=2):
        class_name = raw["class_name"].strip()
        name = raw["name"].strip()
        if not class_name:
            abort(f"{path}:{idx} empty class_name")
        if not name:
            abort(f"{path}:{idx} empty asset name")
        key = (class_name, name)
        if key in seen:
            abort(
                f"{path}:{idx} duplicate ({class_name!r}, {name!r}) "
                f"(first seen at line {seen[key]})"
            )
        seen[key] = idx
        target_pct = _decimal(raw["target_pct"], field="target_pct", path=path, line_no=idx)
        if not (Decimal("0") <= target_pct <= Decimal("100")):
            abort(f"{path}:{idx} target_pct={target_pct} out of [0, 100]")
        display_order = _int(raw["display_order"], field="display_order", path=path, line_no=idx)
        if display_order < 0:
            abort(f"{path}:{idx} display_order={display_order} < 0")
        buy_enabled = _bool(raw["buy_enabled"], field="buy_enabled", path=path, line_no=idx)
        sell_enabled = _bool(raw["sell_enabled"], field="sell_enabled", path=path, line_no=idx)
        currency_code = raw["currency_code"].strip().upper()
        if currency_code not in VALID_CURRENCY_CODES:
            abort(
                f"{path}:{idx} currency_code={raw['currency_code']!r} "
                f"not one of {sorted(VALID_CURRENCY_CODES)}"
            )
        out.append(
            AssetRow(
                class_name=class_name,
                name=name,
                target_pct=target_pct,
                display_order=display_order,
                buy_enabled=buy_enabled,
                sell_enabled=sell_enabled,
                currency_code=currency_code,
                line_no=idx,
            )
        )
    return out


def load_positions(profile: str) -> list[PositionRow]:
    path = SEED_DIR / f"{profile}_positions.csv"
    raw_rows = _read_csv(path, POSITION_HEADER)
    out: list[PositionRow] = []
    for idx, raw in enumerate(raw_rows, start=2):
        asset_name = raw["asset_name"].strip()
        if not asset_name:
            abort(f"{path}:{idx} empty asset_name")
        broker_ticker = raw["broker_ticker"].strip()
        if not broker_ticker:
            abort(f"{path}:{idx} empty broker_ticker")
        qty = _decimal(raw["qty"], field="qty", path=path, line_no=idx)
        if qty < 0:
            abort(f"{path}:{idx} qty={qty} < 0")
        avg_price = _decimal(raw["avg_price"], field="avg_price", path=path, line_no=idx)
        if avg_price < 0:
            abort(f"{path}:{idx} avg_price={avg_price} < 0")
        current_price = _decimal(
            raw["current_price"], field="current_price", path=path, line_no=idx
        )
        if current_price < 0:
            abort(f"{path}:{idx} current_price={current_price} < 0")
        # broker-csv-import-totals: totals are broker-published
        # values. Empty cell → ``None`` (contributes 0 to the
        # dashboard aggregate). Non-empty cell is taken verbatim;
        # the parser never falls back to ``qty * price`` — that
        # path is the exact drift source this code eliminates.
        total_invested = _optional_decimal(
            raw["total_invested"], field="total_invested", path=path, line_no=idx
        )
        total_current = _optional_decimal(
            raw["total_current"], field="total_current", path=path, line_no=idx
        )
        out.append(
            PositionRow(
                asset_name=asset_name,
                broker_ticker=broker_ticker,
                qty=qty,
                avg_price=avg_price,
                current_price=current_price,
                total_invested=total_invested,
                total_current=total_current,
                line_no=idx,
            )
        )
    return out


# ---------------------------------------------------------------------------
# Validation pipeline (runs for all modes, before any write)
# ---------------------------------------------------------------------------


def validate(
    profile: str,
    classes: list[ClassRow],
    assets: list[AssetRow],
    positions: list[PositionRow],
) -> None:
    """Cross-reference + sum check. Aborts on any failure."""
    class_names = {c.name for c in classes}

    # assets reference classes
    for a in assets:
        if a.class_name not in class_names:
            SEED_DIR / f"{profile}_classes.csv"
            asset_path = SEED_DIR / f"{profile}_assets.csv"
            existing = ", ".join(sorted(class_names)) or "(none)"
            abort(
                f"{asset_path}:{a.line_no} asset {a.name!r} references "
                f"missing class {a.class_name!r}; classes that DO exist: {existing}"
            )

    # asset names per class
    asset_names = {a.name for a in assets}

    # positions reference assets
    seen_pairs: dict[tuple[str, str], int] = {}
    for p in positions:
        if p.asset_name not in asset_names:
            asset_path = SEED_DIR / f"{profile}_assets.csv"
            pos_path = SEED_DIR / f"{profile}_positions.csv"
            existing = ", ".join(sorted(asset_names)) or "(none)"
            abort(
                f"{pos_path}:{p.line_no} position references "
                f"missing asset {p.asset_name!r}; assets that DO exist: {existing}"
            )
        pair = (p.asset_name, p.broker_ticker)
        if pair in seen_pairs:
            pos_path = SEED_DIR / f"{profile}_positions.csv"
            abort(
                f"{pos_path}:{p.line_no} duplicate (asset_name, broker_ticker) "
                f"= ({p.asset_name!r}, {p.broker_ticker!r}) "
                f"(first seen at line {seen_pairs[pair]})"
            )
        seen_pairs[pair] = p.line_no

    # class sum
    ok, msg = validate_target_pct_sum([c.target_pct for c in classes])
    if not ok:
        abort(f"{SEED_DIR / f'{profile}_classes.csv'}: class sum invalid: {msg}")

    # per-class asset sum
    by_cls: dict[str, list[Decimal]] = defaultdict(list)
    for a in assets:
        by_cls[a.class_name].append(a.target_pct)
    for cls_name in class_names:
        ok, msg = validate_target_pct_sum(by_cls[cls_name])
        if not ok:
            abort(f"{SEED_DIR / f'{profile}_assets.csv'}: class {cls_name!r}: {msg}")


# ---------------------------------------------------------------------------
# Profile resolution
# ---------------------------------------------------------------------------


def get_profile_id(db: Session, profile: str) -> int:
    user_username, profile_name = PROFILE_OWNER_TO_NAME[profile]
    user = db.query(User).filter(User.username == user_username).one()
    prof = db.query(Profile).filter(Profile.user_id == user.id, Profile.name == profile_name).one()
    return prof.id


# ---------------------------------------------------------------------------
# Modes
# ---------------------------------------------------------------------------


def _wipe_profile(db: Session, profile_id: int) -> None:
    """Mirror the destructive wipe from ``scripts/dev_reset.py:39-62``.

    SQLite has ``PRAGMA foreign_keys=OFF`` by default, so we wipe
    explicitly in dependency order. The asset-id snapshot is scoped
    to this profile only — broker tickers like ``"SMH"`` may appear
    in multiple profiles' CSVs, so deleting by ticker would leak
    across profiles.

    We also delete **orphan positions**: positions whose ``asset_id``
    no longer references any asset row. These are leftovers from
    past runs that called ``scripts.clear_assets`` (which deletes
    assets out-of-band, leaving positions orphaned because FK
    enforcement is off). SQLite's ``INTEGER PRIMARY KEY`` ROWID may
    reuse the freed id when the next insert happens, so an orphan
    position with ``asset_id=46`` would collide with a freshly
    inserted position for the same asset name.
    """
    db.execute(
        text(
            "DELETE FROM positions WHERE asset_id IN "
            "(SELECT id FROM assets WHERE asset_class_id IN "
            "(SELECT id FROM asset_classes WHERE profile_id = :pid))"
        ),
        {"pid": profile_id},
    )
    db.execute(
        text("DELETE FROM positions WHERE asset_id NOT IN (SELECT id FROM assets)"),
    )
    db.execute(
        text("DELETE FROM import_previews WHERE profile_id = :pid"),
        {"pid": profile_id},
    )
    db.execute(
        text(
            "DELETE FROM assets WHERE asset_class_id IN "
            "(SELECT id FROM asset_classes WHERE profile_id = :pid)"
        ),
        {"pid": profile_id},
    )
    db.execute(
        text("DELETE FROM asset_classes WHERE profile_id = :pid"),
        {"pid": profile_id},
    )


def run_reset(
    db: Session,
    profile: str,
    classes: list[ClassRow],
    assets: list[AssetRow],
    positions: list[PositionRow],
) -> dict[str, int]:
    profile_id = get_profile_id(db, profile)
    _wipe_profile(db, profile_id)

    classes_sorted = sorted(classes, key=lambda c: c.display_order)
    for c in classes_sorted:
        db.add(
            AssetClass(
                profile_id=profile_id,
                name=c.name,
                target_pct=c.target_pct,
                display_order=c.display_order,
                quote_kind=c.quote_kind,
            )
        )
    db.flush()  # populate class ids before assets reference them

    class_by_name = {
        c.name: db.query(AssetClass)
        .filter(AssetClass.profile_id == profile_id, AssetClass.name == c.name)
        .one()
        for c in classes_sorted
    }

    assets_sorted = sorted(assets, key=lambda a: (a.class_name, a.display_order))
    for a in assets_sorted:
        db.add(
            Asset(
                asset_class_id=class_by_name[a.class_name].id,
                name=a.name,
                target_pct=a.target_pct,
                display_order=a.display_order,
                buy_enabled=a.buy_enabled,
                sell_enabled=a.sell_enabled,
                currency_code=a.currency_code,
            )
        )
    db.flush()  # populate asset ids before positions reference them

    asset_by_name = {
        a.name: db.query(Asset)
        .filter(Asset.asset_class_id == class_by_name[a.class_name].id, Asset.name == a.name)
        .one()
        for a in assets_sorted
    }

    positions_created = 0
    for p in positions:
        # broker-csv-import-totals: totals are broker-published
        # values; the CSV's ``total_invested`` / ``total_current``
        # cells are inserted verbatim. ``None`` is a valid value
        # (legacy seed positions or CSVs without the totals
        # columns): the dashboard renders a 0 contribution in
        # that case (see ``routes/pages.py``). The runtime path
        # never recomputes from ``qty * price`` — that arithmetic
        # is the exact drift source this code eliminates.
        db.add(
            Position(
                asset_id=asset_by_name[p.asset_name].id,
                qty=p.qty,
                avg_price=p.avg_price,
                current_price=p.current_price,
                broker_ticker=p.broker_ticker,
                total_invested=p.total_invested,
                total_current=p.total_current,
            )
        )
        positions_created += 1
    db.commit()

    return {
        "classes": len(classes_sorted),
        "assets": len(assets_sorted),
        "positions": positions_created,
    }


def run_upsert(
    db: Session,
    profile: str,
    classes: list[ClassRow],
    assets: list[AssetRow],
    positions: list[PositionRow],
) -> dict[str, int]:
    profile_id = get_profile_id(db, profile)
    out: dict[str, int] = {
        "classes_created": 0,
        "classes_updated": 0,
        "assets_created": 0,
        "assets_updated": 0,
        "positions_created": 0,
        "positions_updated": 0,
        "positions_unchanged": 0,
    }

    # classes
    existing_classes = {
        c.name: c for c in db.query(AssetClass).filter(AssetClass.profile_id == profile_id).all()
    }
    classes_sorted = sorted(classes, key=lambda c: c.display_order)
    for c in classes_sorted:
        if c.name in existing_classes:
            row = existing_classes[c.name]
            changed = False
            if row.target_pct != c.target_pct:
                row.target_pct = c.target_pct
                changed = True
            if row.display_order != c.display_order:
                row.display_order = c.display_order
                changed = True
            if row.quote_kind != c.quote_kind:
                row.quote_kind = c.quote_kind
                changed = True
            if changed:
                out["classes_updated"] += 1
                print(
                    f"updated: {c.name} -> target_pct={c.target_pct}"
                    f" order={c.display_order} quote_kind={c.quote_kind}"
                )
            else:
                pass  # unchanged (no log to keep summary quiet)
        else:
            db.add(
                AssetClass(
                    profile_id=profile_id,
                    name=c.name,
                    target_pct=c.target_pct,
                    display_order=c.display_order,
                    quote_kind=c.quote_kind,
                )
            )
            out["classes_created"] += 1
            print(f"created: {c.name} target_pct={c.target_pct} quote_kind={c.quote_kind}")
    db.flush()

    # refresh class lookup
    class_by_name = {
        c.name: c for c in db.query(AssetClass).filter(AssetClass.profile_id == profile_id).all()
    }

    # assets
    class_ids = [c.id for c in class_by_name.values()]
    existing_assets = (
        db.query(Asset).filter(Asset.asset_class_id.in_(class_ids)).all() if class_ids else []
    )
    asset_by_key: dict[tuple[int, str], Asset] = {
        (a.asset_class_id, a.name): a for a in existing_assets
    }
    assets_sorted = sorted(assets, key=lambda a: (a.class_name, a.display_order))
    for a in assets_sorted:
        klass = class_by_name[a.class_name]
        key = (klass.id, a.name)
        if key in asset_by_key:
            row = asset_by_key[key]
            changed = False
            if row.target_pct != a.target_pct:
                row.target_pct = a.target_pct
                changed = True
            if row.display_order != a.display_order:
                row.display_order = a.display_order
                changed = True
            if row.buy_enabled != a.buy_enabled:
                row.buy_enabled = a.buy_enabled
                changed = True
            if row.sell_enabled != a.sell_enabled:
                row.sell_enabled = a.sell_enabled
                changed = True
            if row.currency_code != a.currency_code:
                row.currency_code = a.currency_code
                changed = True
            if changed:
                out["assets_updated"] += 1
                print(
                    f"updated: {a.class_name} / {a.name} "
                    f"buy={a.buy_enabled} sell={a.sell_enabled} "
                    f"currency={a.currency_code}"
                )
            else:
                pass
        else:
            db.add(
                Asset(
                    asset_class_id=klass.id,
                    name=a.name,
                    target_pct=a.target_pct,
                    display_order=a.display_order,
                    buy_enabled=a.buy_enabled,
                    sell_enabled=a.sell_enabled,
                    currency_code=a.currency_code,
                )
            )
            out["assets_created"] += 1
            print(
                f"created: {a.class_name} / {a.name} "
                f"buy={a.buy_enabled} sell={a.sell_enabled} "
                f"currency={a.currency_code}"
            )
    db.flush()

    # refresh asset lookup by name (only within profile)
    asset_by_name: dict[str, Asset] = (
        {a.name: a for a in db.query(Asset).filter(Asset.asset_class_id.in_(class_ids)).all()}
        if class_ids
        else {}
    )

    # positions
    asset_ids = [a.id for a in asset_by_name.values()]
    existing_positions = (
        db.query(Position).filter(Position.asset_id.in_(asset_ids)).all() if asset_ids else []
    )
    pos_by_key: dict[tuple[int, str], Position] = {
        (p.asset_id, p.broker_ticker): p for p in existing_positions
    }
    for p in positions:
        asset = asset_by_name[p.asset_name]
        key = (asset.id, p.broker_ticker)
        if key in pos_by_key:
            row = pos_by_key[key]
            changed = False
            if row.qty != p.qty:
                row.qty = p.qty
                changed = True
            if row.avg_price != p.avg_price:
                row.avg_price = p.avg_price
                changed = True
            if row.current_price != p.current_price:
                row.current_price = p.current_price
                changed = True
            # broker-csv-import-totals: the CSV's ``total_invested``
            # / ``total_current`` cells are taken verbatim — never
            # recomputed from ``qty * price``. When the CSV cell is
            # empty (``None``), leave the existing row's value
            # untouched: the CSV does not carry an opinion on this
            # field, so the upsert should not overwrite.
            if p.total_invested is not None and row.total_invested != p.total_invested:
                row.total_invested = p.total_invested
                changed = True
            if p.total_current is not None and row.total_current != p.total_current:
                row.total_current = p.total_current
                changed = True
            if changed:
                out["positions_updated"] += 1
                print(
                    f"updated: asset_name={p.asset_name} broker_ticker={p.broker_ticker} "
                    f"current_price {row.current_price} -> {p.current_price}"
                )
            else:
                out["positions_unchanged"] += 1
        else:
            db.add(
                Position(
                    asset_id=asset.id,
                    qty=p.qty,
                    avg_price=p.avg_price,
                    current_price=p.current_price,
                    broker_ticker=p.broker_ticker,
                    # broker-csv-import-totals: insert verbatim;
                    # never recompute ``qty * price``.
                    total_invested=p.total_invested,
                    total_current=p.total_current,
                )
            )
            out["positions_created"] += 1
            print(f"created: position asset_name={p.asset_name} broker_ticker={p.broker_ticker}")
    db.commit()

    return out


def run_diff(
    db: Session,
    profile: str,
    classes: list[ClassRow],
    assets: list[AssetRow],
    positions: list[PositionRow],
) -> dict[str, int]:
    profile_id = get_profile_id(db, profile)
    out: dict[str, int] = {
        "would_create_classes": 0,
        "would_update_classes": 0,
        "would_orphan_classes": 0,
        "would_create_assets": 0,
        "would_update_assets": 0,
        "would_orphan_assets": 0,
        "would_create_positions": 0,
        "would_update_positions": 0,
        "would_orphan_positions": 0,
    }

    print(f"=== diff for {profile} ===")

    # classes
    existing_classes = {
        c.name: c for c in db.query(AssetClass).filter(AssetClass.profile_id == profile_id).all()
    }
    classes_sorted = sorted(classes, key=lambda c: c.display_order)
    print("\n# classes")
    would_create: list[str] = []
    would_update: list[str] = []
    for c in classes_sorted:
        if c.name not in existing_classes:
            would_create.append(f"  + {c.name} target_pct={c.target_pct}")
            out["would_create_classes"] += 1
        else:
            row = existing_classes[c.name]
            if row.target_pct != c.target_pct or row.display_order != c.display_order:
                would_update.append(f"  ~ {c.name} target_pct {row.target_pct} -> {c.target_pct}")
                out["would_update_classes"] += 1
    for c in existing_classes:
        if c not in {x.name for x in classes_sorted}:
            print(f"  - {c} (orphan)")
            out["would_orphan_classes"] += 1
    if would_create:
        print(f"would-create: {len(would_create)}")
        for line in would_create:
            print(line)
    if would_update:
        print(f"would-update: {len(would_update)}")
        for line in would_update:
            print(line)

    # assets
    class_by_name = {
        c.name: c for c in db.query(AssetClass).filter(AssetClass.profile_id == profile_id).all()
    }
    class_ids = [c.id for c in class_by_name.values()]
    existing_assets = (
        db.query(Asset).filter(Asset.asset_class_id.in_(class_ids)).all() if class_ids else []
    )
    asset_by_class_name: dict[tuple[int, str], Asset] = {
        (a.asset_class_id, a.name): a for a in existing_assets
    }
    assets_sorted = sorted(assets, key=lambda a: (a.class_name, a.display_order))
    print("\n# assets")
    would_create = []
    would_update = []
    for a in assets_sorted:
        klass = class_by_name[a.class_name]
        key = (klass.id, a.name)
        if key not in asset_by_class_name:
            would_create.append(
                f"  + {a.class_name} / {a.name} target_pct={a.target_pct} "
                f"buy={a.buy_enabled} sell={a.sell_enabled} currency={a.currency_code}"
            )
            out["would_create_assets"] += 1
        else:
            row = asset_by_class_name[key]
            fields_changed: list[str] = []
            if row.target_pct != a.target_pct:
                fields_changed.append(f"target_pct {row.target_pct} -> {a.target_pct}")
            if row.display_order != a.display_order:
                fields_changed.append(f"display_order {row.display_order} -> {a.display_order}")
            if row.buy_enabled != a.buy_enabled:
                fields_changed.append(f"buy {row.buy_enabled} -> {a.buy_enabled}")
            if row.sell_enabled != a.sell_enabled:
                fields_changed.append(f"sell {row.sell_enabled} -> {a.sell_enabled}")
            if row.currency_code != a.currency_code:
                fields_changed.append(f"currency {row.currency_code} -> {a.currency_code}")
            if fields_changed:
                would_update.append(f"  ~ {a.class_name} / {a.name} " + ", ".join(fields_changed))
                out["would_update_assets"] += 1
    for _key, row in asset_by_class_name.items():
        klass = class_by_name.get(row.asset_class_id)
        if klass is None:
            continue  # asset belongs to a class that no longer exists; skip
        if not any(a.class_name == klass.name and a.name == row.name for a in assets_sorted):
            print(f"  - {klass.name} / {row.name} (orphan)")
            out["would_orphan_assets"] += 1
    if would_create:
        print(f"would-create: {len(would_create)}")
        for line in would_create:
            print(line)
    if would_update:
        print(f"would-update: {len(would_update)}")
        for line in would_update:
            print(line)

    # positions
    asset_by_name = (
        {a.name: a for a in db.query(Asset).filter(Asset.asset_class_id.in_(class_ids)).all()}
        if class_ids
        else {}
    )
    asset_ids = [a.id for a in asset_by_name.values()]
    existing_positions = (
        db.query(Position).filter(Position.asset_id.in_(asset_ids)).all() if asset_ids else []
    )
    pos_by_key: dict[tuple[int, str], Position] = {
        (p.asset_id, p.broker_ticker): p for p in existing_positions
    }
    print("\n# positions")
    would_create = []
    would_update = []
    for p in positions:
        asset = asset_by_name[p.asset_name]
        key = (asset.id, p.broker_ticker)
        if key not in pos_by_key:
            would_create.append(
                f"  + position asset_name={p.asset_name} broker_ticker={p.broker_ticker}"
            )
            out["would_create_positions"] += 1
        else:
            row = pos_by_key[key]
            if (
                row.qty != p.qty
                or row.avg_price != p.avg_price
                or row.current_price != p.current_price
            ):
                would_update.append(
                    f"  ~ asset_name={p.asset_name} broker_ticker={p.broker_ticker} "
                    f"current_price {row.current_price} -> {p.current_price}"
                )
                out["would_update_positions"] += 1
    for _key, row in pos_by_key.items():
        asset = asset_by_name.get(row.asset_id)
        if asset is None:
            continue
        if not any(
            p.asset_name == asset.name and p.broker_ticker == row.broker_ticker for p in positions
        ):
            print(
                f"  - position asset_name={asset.name} broker_ticker={row.broker_ticker} (orphan)"
            )
            out["would_orphan_positions"] += 1
    if would_create:
        print(f"would-create: {len(would_create)}")
        for line in would_create:
            print(line)
    if would_update:
        print(f"would-update: {len(would_update)}")
        for line in would_update:
            print(line)

    return out


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------


def abort(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    sys.exit(1)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="CSV-driven per-profile seed (wipe/upsert/diff).",
    )
    parser.add_argument(
        "--profile",
        required=True,
        choices=PROFILES,
        help="Which profile to seed (italo | ana).",
    )
    parser.add_argument(
        "--mode",
        required=True,
        choices=MODES,
        help="reset (wipe+reseed) | upsert (create-or-update) | diff (no write).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    classes = load_classes(args.profile)
    assets = load_assets(args.profile)
    positions = load_positions(args.profile)

    # Validation runs BEFORE any write regardless of mode.
    validate(args.profile, classes, assets, positions)

    db = SessionLocal()
    try:
        if args.mode == "reset":
            counts = run_reset(db, args.profile, classes, assets, positions)
            print(
                f"profile={args.profile} mode=reset "
                f"classes={counts['classes']} "
                f"assets={counts['assets']} "
                f"positions={counts['positions']}"
            )
        elif args.mode == "upsert":
            counts = run_upsert(db, args.profile, classes, assets, positions)
            n_classes = counts["classes_created"] + counts["classes_updated"]
            n_assets = counts["assets_created"] + counts["assets_updated"]
            n_positions = (
                counts["positions_created"]
                + counts["positions_updated"]
                + counts["positions_unchanged"]
            )
            n_created = (
                counts["classes_created"] + counts["assets_created"] + counts["positions_created"]
            )
            n_updated = (
                counts["classes_updated"] + counts["assets_updated"] + counts["positions_updated"]
            )
            print(
                f"profile={args.profile} mode=upsert "
                f"classes={n_classes} assets={n_assets} positions={n_positions} "
                f"created={n_created} updated={n_updated} "
                f"unchanged={counts['positions_unchanged']}"
            )
        else:  # diff
            counts = run_diff(db, args.profile, classes, assets, positions)
            n_would_create = (
                counts["would_create_classes"]
                + counts["would_create_assets"]
                + counts["would_create_positions"]
            )
            n_would_update = (
                counts["would_update_classes"]
                + counts["would_update_assets"]
                + counts["would_update_positions"]
            )
            n_would_orphan = (
                counts["would_orphan_classes"]
                + counts["would_orphan_assets"]
                + counts["would_orphan_positions"]
            )
            print(
                f"profile={args.profile} mode=diff "
                f"would_create={n_would_create} "
                f"would_update={n_would_update} "
                f"would_orphan={n_would_orphan}"
            )
    finally:
        db.close()

    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
