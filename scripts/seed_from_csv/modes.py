"""The three seed modes: ``reset`` (wipe+reseed), ``upsert``
(create-or-update), ``diff`` (no write).

All three modes share the destructive wipe from
``scripts/dev_reset.py`` and the "print summary" idiom. They differ
only in what they do after the wipe / validation:

* ``reset``  — wipe positions/previews/assets/classes for the
  profile, then insert the full triplet in ``display_order``
  ascending.
* ``upsert`` — no wipe. Create-or-update classes by
  ``(profile_id, name)``, assets by ``(asset_class_id, name)``,
  positions by ``(asset_id, broker_ticker)``. Prints
  ``created`` / ``updated`` / ``unchanged`` per layer.
* ``diff``   — no write. Print ``would-create`` / ``would-update``
  / ``would-orphan`` sections for the three layers.

The broker-published ``total_invested`` / ``total_current`` columns
on the position CSV are inserted verbatim — the seed script never
falls back to ``qty * price`` (see ``broker-csv-import-totals``).
"""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.orm import Session

from omaha.models import Asset, AssetClass, Position
from scripts.seed_from_csv.loaders import (
    AssetRow,
    ClassRow,
    PositionRow,
)
from scripts.seed_from_csv.profiles import get_profile_id


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
