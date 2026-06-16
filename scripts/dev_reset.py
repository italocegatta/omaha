"""One-shot dev DB reset: clean state ready for manual import flow test.

Wipes positions / import_previews / assets / asset_classes for the Italo
profile, recreates 3 classes with target percentages, and pre-seeds the
43 assets whose names match the 43 matched rows in
``tests/fixtures/sample_broker.csv``. After this runs, uploading that
fixture through ``/import`` will produce 43 auto-matched + 5 unmatched
(MXRF11, BPAC11, HGLG11, XPLG11, VINO11), which is the T04 happy path.

Run with: ``uv run python -m scripts.dev_reset``
"""

from __future__ import annotations

from sqlalchemy import text

from omaha.db import SessionLocal
from omaha.models import Asset, AssetClass, Profile, User

# (asset_name, target_class_label) — derived by diffing the 48 fixture
# names against the 5 unmatched set. The distribution targets the
# dashboard weights used in the T04 e2e test (Renda Fixa 60, Acoes 30,
# FIIs 10). Each tuple MUST match a name in sample_broker.csv col 1.
SEED_ASSETS: list[tuple[str, str]] = [
    # Acoes BR — 17 names from fixture, no IVVB11 mismatch (IVVB11 is a
    # Brazilian ETF that the matcher treats as "Acoes").
    ("PETR4", "Acoes"),
    ("VALE3", "Acoes"),
    ("ITUB4", "Acoes"),
    ("BBDC4", "Acoes"),
    ("ABEV3", "Acoes"),
    ("MGLU3", "Acoes"),
    ("BBAS3", "Acoes"),
    ("WEGE3", "Acoes"),
    ("RENT3", "Acoes"),
    ("LREN3", "Acoes"),
    ("B3SA3", "Acoes"),
    ("SUZB3", "Acoes"),
    ("CSAN3", "Acoes"),
    ("PETR3", "Acoes"),
    ("VBBR3", "Acoes"),
    ("PRIO3", "Acoes"),
    ("IVVB11", "Acoes"),
    # ETFs US — 8 names from fixture.
    ("IVV", "Acoes"),
    ("VOO", "Acoes"),
    ("QQQ", "Acoes"),
    ("SMH", "Acoes"),
    ("SOXX", "Acoes"),
    ("VTI", "Acoes"),
    ("SPY", "Acoes"),
    ("VT", "Acoes"),
    # FIIs — 16 names from fixture.
    ("HASH11", "FIIs"),
    ("BTLG11", "FIIs"),
    ("KNCR11", "FIIs"),
    ("IRDM11", "FIIs"),
    ("XPML11", "FIIs"),
    ("VISC11", "FIIs"),
    ("BRCR11", "FIIs"),
    ("TORD11", "FIIs"),
    ("MALL11", "FIIs"),
    ("DEVA11", "FIIs"),
    ("RBVA11", "FIIs"),
    ("VRTA11", "FIIs"),
    ("BPRP11", "FIIs"),
    ("PVBI11", "FIIs"),
    ("HCTR11", "FIIs"),
    ("XPIN11", "FIIs"),
    # Renda Fixa — 2 names from fixture.
    ("Tesouro Selic 2029", "Renda Fixa"),
    ("Tesouro IPCA+ 2035", "Renda Fixa"),
]

CLASS_SPECS: list[tuple[str, int]] = [
    ("Renda Fixa", 60),
    ("Acoes", 30),
    ("FIIs", 10),
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

        # Reseed: 3 classes, then assets distributed by label.
        new_classes: dict[str, AssetClass] = {}
        for display_order, (name, target) in enumerate(CLASS_SPECS):
            cls = AssetClass(
                profile_id=profile_id,
                name=name,
                target_pct=target,
                display_order=display_order,
            )
            db.add(cls)
            new_classes[name] = cls
        db.flush()

        # Within each class, give assets display_order 0, 1, 2, ... in
        # the order they appear in SEED_ASSETS. The dashboard sorts by
        # display_order, so this gives a stable view.
        per_class_counter: dict[str, int] = {name: 0 for name, _ in CLASS_SPECS}
        for asset_name, class_label in SEED_ASSETS:
            cls = new_classes[class_label]
            db.add(
                Asset(
                    asset_class_id=cls.id,
                    name=asset_name,
                    display_order=per_class_counter[class_label],
                )
            )
            per_class_counter[class_label] += 1
        db.commit()

        n_classes = len(new_classes)
        n_assets = len(SEED_ASSETS)
        print(
            f"reset OK — Italo now has {n_classes} classes "
            f"({', '.join(f'{n}@{t}%' for n, t in CLASS_SPECS)}) "
            f"and {n_assets} assets. 5 unmatched on import: "
            "MXRF11, BPAC11, HGLG11, XPLG11, VINO11"
        )
    finally:
        db.close()


if __name__ == "__main__":  # pragma: no cover
    reset_for_italo()
