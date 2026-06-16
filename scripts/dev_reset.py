"""One-shot dev DB reset: clean state ready for manual import flow test.

Wipes positions / import_previews / assets / asset_classes for the Italo
profile, recreates 6 classes with target percentages, and leaves classes
empty — user adds assets via the import button.

Run with: ``uv run python -m scripts.dev_reset``
"""

from __future__ import annotations

from sqlalchemy import text

from omaha.db import SessionLocal
from omaha.models import AssetClass, Profile, User

CLASS_SPECS: list[tuple[str, int]] = [
    ("RF Dinâmica", 26),
    ("RF Pós", 16),
    ("Internacional", 21),
    ("FII", 15),
    ("Cripto", 8),
    ("Ações", 14),
]


def reset_for_italo() -> None:
    """Wipe + reseed Italo's profile. Idempotent; safe to re-run."""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == "Italo").one()
        italo = db.query(Profile).filter(Profile.user_id == user.id, Profile.name == "Italo").one()
        profile_id = italo.id

        # Cascade-friendly wipe: positions + import_previews first (they
        # don't cascade from anything we touch), then assets, then classes.
        # SQLite has PRAGMA foreign_keys=OFF by default, so ON DELETE
        # CASCADE is not enforced — wipe explicitly.
        db.execute(
            text(
                "DELETE FROM positions WHERE asset_id IN "
                "(SELECT id FROM assets WHERE asset_class_id IN "
                "(SELECT id FROM asset_classes WHERE profile_id = :pid))"
            ),
            {"pid": profile_id},
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
        db.commit()

        # Reseed: classes only — no assets (user adds via import).
        for display_order, (name, target) in enumerate(CLASS_SPECS):
            db.add(
                AssetClass(
                    profile_id=profile_id,
                    name=name,
                    target_pct=target,
                    display_order=display_order,
                )
            )
        db.commit()

        print(
            f"reset OK — Italo now has {len(CLASS_SPECS)} classes "
            f"({', '.join(f'{n}@{t}%' for n, t in CLASS_SPECS)}), "
            "no assets. User adds via import."
        )
    finally:
        db.close()


if __name__ == "__main__":  # pragma: no cover
    reset_for_italo()
