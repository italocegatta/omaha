"""T02: DELETE /api/assets/{id} with 204 + 404 cross-profile + cascade.

The dashboard's Alpine ``×`` button (S03/T04) calls this endpoint to
delete an asset. Unlike the S02 class delete (which 409s when the
class has assets), the asset delete has no 409 guard — the
``Position`` FK declares ``ondelete=CASCADE`` and the ORM
relationship declares ``cascade="all, delete-orphan"``, so deleting
an asset always succeeds for the active profile's own assets and the
position rows are removed in the same transaction.

Three tests:
  1. ``test_delete_asset_returns_204_and_removes_from_db`` — DELETE the
     active profile's own asset; expect 204 with empty body; the
     asset row is gone from the DB.
  2. ``test_delete_asset_cross_profile_404`` — log in as profile A;
     DELETE an asset in profile B; expect 404; the asset row
     remains on disk.
  3. ``test_delete_asset_cascades_positions`` — asset has Position
     rows; DELETE returns 204; positions are also gone (the FK
     ``ON DELETE CASCADE`` is the line of defense; the ORM
     ``cascade="all, delete-orphan"`` belt-and-suspenders it).
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# Per-test cleanup
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _clean_positions_assets_and_classes() -> None:
    """Wipe positions, assets, and asset_classes before each test.

    Mirrors the S02 ``_clean_asset_classes_and_assets`` autouse
    fixture: the session-scoped DB persists across tests, so a
    successful POST in one test would otherwise leave rows on disk
    that the next test would trip over. ``positions`` is wiped
    first to respect the FK chain ``positions -> assets ->
    asset_classes -> profiles`` (and to make the cascade
    observation in test 3 trivial — the count starts at 0 before
    we seed). The cascade also works the other way (delete the
    parent asset and the FK drops the children), so the order
    is symmetric.
    """
    from omaha.db import SessionLocal
    from omaha.models import Asset, AssetClass, Position

    db = SessionLocal()
    try:
        db.query(Position).delete()
        db.query(Asset).delete()
        db.query(AssetClass).delete()
        db.commit()
    finally:
        db.close()
    yield


# ---------------------------------------------------------------------------
# Helpers (mirrors test_classes_delete.py)
# ---------------------------------------------------------------------------


def _login_and_select(client: TestClient, profile_id: int = 1) -> None:
    """Log in with the seed credentials and bind ``active_profile_id``."""
    client.post(
        "/login",
        data={"username": "Italo", "password": "test-password"},
        follow_redirects=False,
    )
    client.post(f"/profiles/{profile_id}/select", follow_redirects=False)


def _seed_classes(profile_id: int, rows: list[tuple[str, str]]) -> list[int]:
    """Insert (name, target_pct) class rows directly, return their IDs."""
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


def _seed_assets(asset_class_id: int, names: list[str]) -> list[int]:
    """Insert name-only assets for a class, return their IDs."""
    from omaha.db import SessionLocal
    from omaha.models import Asset

    db = SessionLocal()
    try:
        ids: list[int] = []
        for idx, name in enumerate(names):
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


def _seed_positions(asset_id: int, rows: list[tuple[str, str, str, str]]) -> list[int]:
    """Insert Position rows for ``asset_id``.

    ``rows`` is a list of ``(broker_ticker, qty, avg_price, current_price)``
    tuples. Returns the new position IDs (used by the cascade test
    to make the assertion precise if needed).
    """
    from omaha.db import SessionLocal
    from omaha.models import Position

    db = SessionLocal()
    try:
        ids: list[int] = []
        for ticker, qty, avg, current in rows:
            pos = Position(
                asset_id=asset_id,
                broker_ticker=ticker,
                qty=Decimal(qty),
                avg_price=Decimal(avg),
                current_price=Decimal(current),
            )
            db.add(pos)
            db.flush()
            ids.append(pos.id)
        db.commit()
        return ids
    finally:
        db.close()


def _asset_exists(asset_id: int) -> bool:
    """Return ``True`` iff the ``Asset`` row still exists."""
    from omaha.db import SessionLocal
    from omaha.models import Asset

    db = SessionLocal()
    try:
        return db.get(Asset, asset_id) is not None
    finally:
        db.close()


def _count_positions_for_asset(asset_id: int) -> int:
    """Return the number of ``Position`` rows for ``asset_id``."""
    from omaha.db import SessionLocal
    from omaha.models import Position

    db = SessionLocal()
    try:
        return db.query(Position).filter(Position.asset_id == asset_id).count()
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_delete_asset_returns_204_and_removes_from_db(
    client: TestClient,
) -> None:
    """DELETE on the active profile's own asset returns 204 with empty body.

    Create a class and one asset under it. DELETE the asset.
    Expect 204 with no body. Verify the asset is gone from the DB.
    """
    _login_and_select(client, profile_id=1)
    [class_id] = _seed_classes(profile_id=1, rows=[("Renda Fixa", "100")])
    [asset_id] = _seed_assets(class_id, ["Tesouro Selic 2029"])

    response = client.delete(f"/api/assets/{asset_id}")

    assert response.status_code == 204
    # 204 must have an empty body — the response_model=None decorator
    # keeps FastAPI from trying to serialize anything, and the
    # handler returns ``Response(status_code=204)`` directly.
    assert response.text == ""
    assert not _asset_exists(asset_id)


def test_delete_asset_cross_profile_404(client: TestClient) -> None:
    """DELETE on another profile's asset returns 404; asset remains.

    Seed an asset under profile 2 (Ana, per the seed
    script's profile ordering). Log in as profile 1 (Italo) and
    attempt to DELETE Ana's asset. Expect 404. The asset must
    still be on disk — the 404 means the route never touched
    the row (no 204 + side-effect leak).
    """
    # Seed a class + asset under profile 2.
    [other_class_id] = _seed_classes(profile_id=2, rows=[("Renda Fixa Ana", "100")])
    [other_asset_id] = _seed_assets(other_class_id, ["PETR4"])

    # Log in as profile 1 and try to delete Ana's asset.
    _login_and_select(client, profile_id=1)

    response = client.delete(f"/api/assets/{other_asset_id}")

    assert response.status_code == 404
    # The asset is still on disk — the 404 means the route
    # never touched the row. A 204 here would be a cross-profile
    # data leak.
    assert _asset_exists(other_asset_id)


def test_delete_asset_cascades_positions(client: TestClient) -> None:
    """DELETE on an asset with positions returns 204; positions cascade.

    Create a class + asset + 2 Position rows. DELETE the asset.
    Expect 204. Verify the asset row is gone and the 2 position
    rows are gone (FK ``ON DELETE CASCADE`` on
    ``Position.asset_id``, plus the ORM ``cascade="all,
    delete-orphan"`` on ``Asset.positions``).
    """
    _login_and_select(client, profile_id=1)
    [class_id] = _seed_classes(profile_id=1, rows=[("Renda Fixa", "100")])
    [asset_id] = _seed_assets(class_id, ["Tesouro Selic 2029"])
    _seed_positions(
        asset_id,
        [
            ("TESOURO_SELIC_2029_BB", "1.5", "100.00", "110.00"),
            ("TESOURO_SELIC_2029_XP", "0.5", "100.00", "110.00"),
        ],
    )
    # Pre-condition: 2 positions for the asset. This also
    # confirms the seed worked before we make the cascade
    # observation.
    assert _count_positions_for_asset(asset_id) == 2

    response = client.delete(f"/api/assets/{asset_id}")

    assert response.status_code == 204
    assert not _asset_exists(asset_id)
    # The FK cascade (or the ORM cascade) removed the positions
    # too. The test observes the post-state — it doesn't assert
    # which mechanism ran, just that the final count is 0.
    assert _count_positions_for_asset(asset_id) == 0
