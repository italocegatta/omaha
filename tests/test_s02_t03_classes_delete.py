"""T03: DELETE /api/classes/{id} with 409 when class has assets.

The dashboard's Alpine ``x`` button (S02/T06) calls this endpoint to
delete a class. If the class has any assets linked to it, the endpoint
returns 409 with the asset count — the operator must explicitly delete
or move the assets first before removing the class.

Three tests:
  1. ``test_delete_class_with_no_assets_returns_204`` — create a class
     with 0 assets; DELETE; expect 204; class is gone from DB.
  2. ``test_delete_class_with_assets_returns_409`` — create a class
     with 2 assets; DELETE; expect 409; body detail mentions "2 ativo(s)";
     class still in DB.
  3. ``test_delete_class_cross_profile_404`` — log in as profile A;
     DELETE a class in profile B; expect 404.
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# Per-test cleanup
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _clean_asset_classes_and_assets() -> None:
    """Wipe the ``assets`` and ``asset_classes`` tables before each test.

    The session-scoped ``_omaha_test_env`` state persists across
    tests. Delete all rows before each test to ensure a clean slate.
    The ``assets`` table must be cleared first to respect FK
    constraints (``Asset.asset_class_id`` references
    ``asset_classes.id``). Only if the adapter supports deferred
    constraints (SQLite does not).
    """
    from omaha.db import SessionLocal
    from omaha.models import Asset, AssetClass

    db = SessionLocal()
    try:
        db.query(Asset).delete()
        db.query(AssetClass).delete()
        db.commit()
    finally:
        db.close()
    yield


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _login_and_select(client: TestClient, profile_id: int = 1) -> None:
    """Log in with the seed credentials and bind ``active_profile_id``.

    The seed creates profile 1 = Italo (display_order=0) and
    profile 2 = Ana (display_order=1).
    """
    client.post(
        "/login",
        data={"username": "Italo", "password": "test-password"},
        follow_redirects=False,
    )
    client.post(f"/profiles/{profile_id}/select", follow_redirects=False)


def _seed_classes(profile_id: int, rows: list[tuple[str, str]]) -> list[int]:
    """Insert ``(name, target_pct)`` rows via SQLAlchemy, return their IDs.

    Returns the list of inserted IDs in ``display_order`` order so
    the test can reference them for DELETE calls.
    """
    from omaha.db import SessionLocal
    from omaha.models import AssetClass

    db = SessionLocal()
    try:
        ids: list[int] = []
        for idx, (name, pct) in enumerate(rows):
            cls = AssetClass(
                profile_id=profile_id,
                name=name,
                target_pct=Decimal(pct),
                display_order=idx,
            )
            db.add(cls)
            db.flush()
            ids.append(cls.id)
        db.commit()
        return ids
    finally:
        db.close()


def _seed_assets(asset_class_id: int, rows: list[str]) -> list[int]:
    """Insert ``name``-only assets for a class via SQLAlchemy, return their IDs.

    Each asset gets ``target_pct=0`` and an auto-incrementing
    ``display_order``. Returns the list of inserted IDs.
    """
    from omaha.db import SessionLocal
    from omaha.models import Asset

    db = SessionLocal()
    try:
        ids: list[int] = []
        for idx, name in enumerate(rows):
            asset = Asset(
                asset_class_id=asset_class_id,
                name=name,
                target_pct=Decimal("0"),
                display_order=idx,
            )
            db.add(asset)
            db.flush()
            ids.append(asset.id)
        db.commit()
        return ids
    finally:
        db.close()


def _class_exists(class_id: int) -> bool:
    """Return ``True`` if the ``AssetClass`` row still exists."""
    from omaha.db import SessionLocal
    from omaha.models import AssetClass

    db = SessionLocal()
    try:
        return db.get(AssetClass, class_id) is not None
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_delete_class_with_no_assets_returns_204(client: TestClient) -> None:
    """DELETE an empty class; expect 204; class is removed from the DB.

    Create a single class at 100% with 0 assets. DELETE it. Expect
    204 with no body. Verify the class row is gone from the DB.
    """
    _login_and_select(client, profile_id=1)
    ids = _seed_classes(
        profile_id=1,
        rows=[
            ("Renda Fixa", "100"),
        ],
    )

    class_id = ids[0]
    response = client.delete(f"/api/classes/{class_id}")

    assert response.status_code == 204
    # No body on 204
    assert response.text == ""

    # Class is gone from DB
    assert not _class_exists(class_id)


def test_delete_class_with_assets_returns_409(client: TestClient) -> None:
    """DELETE a class that has 2 assets; expect 409; class stays in DB.

    Create a class with 2 assets. DELETE it. Expect 409 with body
    ``{"detail": "Classe tem 2 ativo(s); remova-os antes."}``.
    Verify the class row is still in the DB.
    """
    _login_and_select(client, profile_id=1)
    ids = _seed_classes(
        profile_id=1,
        rows=[
            ("Renda Fixa", "100"),
        ],
    )

    class_id = ids[0]
    _seed_assets(class_id, ["Tesouro Selic 2029", "Tesouro IPCA 2035"])

    response = client.delete(f"/api/classes/{class_id}")

    assert response.status_code == 409
    data = response.json()
    assert data["detail"] == "Classe tem 2 ativo(s); remova-os antes."

    # Class still in DB
    assert _class_exists(class_id)


def test_delete_class_cross_profile_404(client: TestClient) -> None:
    """DELETE a class belonging to another profile; expect 404.

    Profile 1 has a class. Log in as profile 1, then DELETE a class
    belonging to profile 2. Expect 404.
    """
    # Seed profile 1 with a class
    _login_and_select(client, profile_id=1)
    _seed_classes(
        profile_id=1,
        rows=[
            ("Renda Fixa", "100"),
        ],
    )

    # Seed profile 2 with its own class
    ids_p2 = _seed_classes(
        profile_id=2,
        rows=[
            ("Profile2 Class", "100"),
        ],
    )

    # Still logged in as profile 1, try to DELETE profile 2's class
    class_id = ids_p2[0]
    response = client.delete(f"/api/classes/{class_id}")

    assert response.status_code == 404
