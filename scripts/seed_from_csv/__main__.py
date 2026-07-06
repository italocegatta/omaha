"""CLI driver for the CSV-driven seed path.

Makes ``python -m scripts.seed_from_csv`` resolve against this
package's ``__main__`` instead of the pre-refactor single-file
module. The flag surface, exit codes, and output are preserved
verbatim.

Run with::

    uv run python -m scripts.seed_from_csv --profile italo --mode reset
    uv run python -m scripts.seed_from_csv --profile ana --mode diff
    uv run python -m scripts.seed_from_csv --profile italo --mode upsert
"""

from __future__ import annotations

import argparse

from omaha.db import SessionLocal
from scripts.seed_from_csv.loaders import (
    PROFILES,
    load_assets,
    load_classes,
    load_positions,
)
from scripts.seed_from_csv.modes import run_diff, run_reset, run_upsert
from scripts.seed_from_csv.validation import validate

MODES = ("reset", "upsert", "diff")


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
