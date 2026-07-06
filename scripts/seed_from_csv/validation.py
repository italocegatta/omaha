"""Cross-reference + sum invariant validation for the CSV-driven seed.

Runs BEFORE any DB write for all three modes (``reset``, ``upsert``,
``diff``). Aborts with exit code 1 on any failure, leaving the DB
untouched.

Three layers of checks:

1. **Cross-references.** Every asset references a class by name; every
   position references an asset by name. Duplicate keys within a
   layer abort with the line number of the second occurrence.
2. **Class sum.** ``sum(target_pct) == 100`` across the class file
   (tolerance 0.01, via ``omaha.validators.validate_target_pct_sum``).
3. **Per-class asset sum.** ``sum(target_pct) == 100`` within each
   ``class_name`` group of the asset file (same tolerance).
"""

from __future__ import annotations

from collections import defaultdict
from decimal import Decimal

import scripts.seed_from_csv
from omaha.validators import validate_target_pct_sum
from scripts.seed_from_csv.loaders import (
    AssetRow,
    ClassRow,
    PositionRow,
    abort,
)


def _seed_dir():
    return scripts.seed_from_csv.SEED_DIR


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
            asset_path = _seed_dir() / f"{profile}_assets.csv"
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
            asset_path = _seed_dir() / f"{profile}_assets.csv"
            pos_path = _seed_dir() / f"{profile}_positions.csv"
            existing = ", ".join(sorted(asset_names)) or "(none)"
            abort(
                f"{pos_path}:{p.line_no} position references "
                f"missing asset {p.asset_name!r}; assets that DO exist: {existing}"
            )
        pair = (p.asset_name, p.broker_ticker)
        if pair in seen_pairs:
            pos_path = _seed_dir() / f"{profile}_positions.csv"
            abort(
                f"{pos_path}:{p.line_no} duplicate (asset_name, broker_ticker) "
                f"= ({p.asset_name!r}, {p.broker_ticker!r}) "
                f"(first seen at line {seen_pairs[pair]})"
            )
        seen_pairs[pair] = p.line_no

    # class sum
    ok, msg = validate_target_pct_sum([c.target_pct for c in classes])
    if not ok:
        abort(f"{_seed_dir() / f'{profile}_classes.csv'}: class sum invalid: {msg}")

    # per-class asset sum
    by_cls: dict[str, list[Decimal]] = defaultdict(list)
    for a in assets:
        by_cls[a.class_name].append(a.target_pct)
    for cls_name in class_names:
        ok, msg = validate_target_pct_sum(by_cls[cls_name])
        if not ok:
            abort(f"{_seed_dir() / f'{profile}_assets.csv'}: class {cls_name!r}: {msg}")
