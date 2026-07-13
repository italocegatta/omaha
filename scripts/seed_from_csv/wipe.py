"""Shared destructive wipe primitives for CSV seed and test harnesses."""

from __future__ import annotations

from collections.abc import Callable, Mapping

from sqlalchemy import text
from sqlalchemy.orm import Session

Execute = Callable[[str, Mapping[str, int]], object]


def wipe_profile_rows(
    profile_id: int,
    execute: Execute,
    *,
    remove_orphan_positions: bool,
    import_previews_before_assets: bool,
) -> None:
    """Delete profile-owned rows with caller-selected legacy ordering."""
    execute(
        "DELETE FROM positions WHERE asset_id IN "
        "(SELECT id FROM assets WHERE asset_class_id IN "
        "(SELECT id FROM asset_classes WHERE profile_id = :pid))",
        {"pid": profile_id},
    )
    if remove_orphan_positions:
        execute("DELETE FROM positions WHERE asset_id NOT IN (SELECT id FROM assets)", {})
    if import_previews_before_assets:
        execute("DELETE FROM import_previews WHERE profile_id = :pid", {"pid": profile_id})
    execute(
        "DELETE FROM assets WHERE asset_class_id IN "
        "(SELECT id FROM asset_classes WHERE profile_id = :pid)",
        {"pid": profile_id},
    )
    execute("DELETE FROM asset_classes WHERE profile_id = :pid", {"pid": profile_id})
    if not import_previews_before_assets:
        execute("DELETE FROM import_previews WHERE profile_id = :pid", {"pid": profile_id})


def wipe_profile(db: Session, profile_id: int) -> None:
    """Seed-reset wipe preserving orphan cleanup and original SQL ordering."""
    wipe_profile_rows(
        profile_id,
        lambda statement, params: db.execute(text(statement), params),
        remove_orphan_positions=True,
        import_previews_before_assets=True,
    )
