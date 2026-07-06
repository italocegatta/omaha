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

This package re-exports the public API of the pre-refactor single
file so external consumers (``scripts/snapshot_to_csv.py``,
``scripts/reset_both_profiles.py``, ``tests/test_seed_from_csv.py``,
``tests/scripts/test_reset_both_profiles.py``) continue to import
unchanged. Internal modules import each other directly; ``__init__``
is pure re-export.
"""

from __future__ import annotations

from scripts.seed_from_csv.loaders import (
    ASSET_HEADER,
    CLASS_HEADER,
    POSITION_HEADER,
    PROFILES,
    REPO_ROOT,
    SEED_DIR,
    VALID_CURRENCY_CODES,
    VALID_QUOTE_KINDS,
    AssetRow,
    ClassRow,
    PositionRow,
    abort,
    load_assets,
    load_classes,
    load_positions,
)
from scripts.seed_from_csv.modes import run_diff, run_reset, run_upsert
from scripts.seed_from_csv.profiles import PROFILE_OWNER_TO_NAME, get_profile_id
from scripts.seed_from_csv.validation import validate

__all__ = [
    # module constants
    "PROFILES",
    "PROFILE_OWNER_TO_NAME",
    "REPO_ROOT",
    "SEED_DIR",
    "CLASS_HEADER",
    "ASSET_HEADER",
    "POSITION_HEADER",
    "VALID_QUOTE_KINDS",
    "VALID_CURRENCY_CODES",
    # dataclasses
    "ClassRow",
    "AssetRow",
    "PositionRow",
    # loaders
    "load_classes",
    "load_assets",
    "load_positions",
    # validation
    "validate",
    # profile resolution
    "get_profile_id",
    # modes
    "run_reset",
    "run_upsert",
    "run_diff",
    # driver primitive
    "abort",
]
