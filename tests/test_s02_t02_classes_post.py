"""T02: POST /api/classes for adding a single class with per-profile sum validation.

The dashboard's Alpine ``+`` component sends a JSON POST with
``{"name": "...", "target_pct": "..."}`` to create a new class.
``display_order`` is optional and defaults to appending after all
existing rows.

Three tests:
  1. ``test_post_class_creates_row`` — 2 existing classes at 60/30
     (sum = 90); POST a 3rd with name "Bonds", target_pct 10; expect
     201; the response has the new class's id, name, and target_pct;
     DB has 3 rows for the profile; sum is 100.
  2. ``test_post_class_invalid_sum_returns_422`` — 2 existing at 60/30
     (sum = 90); POST a 3rd with target_pct 30 (new sum = 120); expect
     422; body ``{"detail": "Sobra 20%"}``; DB unchanged (2 rows).
  3. ``test_post_class_duplicate_name_returns_409`` — 2 existing, one
     named "Stocks"; POST another "Stocks"; expect 409; DB unchanged
     (2 rows).
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# Per-test cleanup
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _clean_asset_classes() -> None:
    """Wipe the ``asset_classes`` table before each test.

    The session-scoped ``_omaha_test_env`` state persists across
    tests. Delete all rows before each test to ensure a clean slate.
    """
    from omaha.db import SessionLocal
    from omaha.models import AssetClass

    db = SessionLocal()
    try:
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
    profile 2 = Ana Livia (display_order=1).
    """
    client.post(
        "/login",
        data={"username": "family", "password": "test-password"},
        follow_redirects=False,
    )
    client.post(f"/profiles/{profile_id}/select", follow_redirects=False)


def _seed_classes(profile_id: int, rows: list[tuple[str, str]]) -> list[int]:
    """Insert ``(name, target_pct)`` rows via SQLAlchemy, return their IDs.

    Returns the list of inserted IDs in ``display_order`` order so
    the test can reference them for assertions.
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


def _count_classes(profile_id: int) -> int:
    """Return the number of ``AssetClass`` rows for the given profile."""
    from omaha.db import SessionLocal
    from omaha.models import AssetClass

    db = SessionLocal()
    try:
        return db.query(AssetClass).filter(AssetClass.profile_id == profile_id).count()
    finally:
        db.close()


def _get_class_target_pct(class_id: int) -> Decimal | None:
    """Return the ``target_pct`` of a class, or ``None`` if not found."""
    from omaha.db import SessionLocal
    from omaha.models import AssetClass

    db = SessionLocal()
    try:
        cls = db.get(AssetClass, class_id)
        return cls.target_pct if cls is not None else None
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_post_class_creates_row(client: TestClient) -> None:
    """POST a valid new class; expect 201, the new class in the response, and DB updated.

    Initial: 2 classes at 60/30 (sum = 90). POST "Bonds" at 10
    → new sum = 100, valid. Expect 201 with response body containing
    the new class's id, name, and target_pct. DB has 3 rows; sum is 100.
    """
    _login_and_select(client, profile_id=1)
    ids = _seed_classes(
        profile_id=1,
        rows=[
            ("Renda Fixa", "60"),
            ("Acoes", "30"),
        ],
    )

    # POST a 3rd class: "Bonds" at 10 → sum becomes 60+30+10 = 100 ✓
    response = client.post(
        "/api/classes",
        json={"name": "Bonds", "target_pct": "10"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Bonds"
    assert Decimal(data["target_pct"]) == Decimal("10")
    assert isinstance(data["id"], int)

    # DB has 3 rows for profile 1
    assert _count_classes(profile_id=1) == 3

    # Sum is 100
    all_pct = []
    for pid in ids:
        pct = _get_class_target_pct(pid)
        assert pct is not None
        all_pct.append(pct)
    # Plus the new one
    from omaha.db import SessionLocal
    from omaha.models import AssetClass

    db = SessionLocal()
    try:
        new_cls = db.get(AssetClass, data["id"])
        assert new_cls is not None
        all_pct.append(new_cls.target_pct)
    finally:
        db.close()

    assert sum(all_pct, Decimal("0")) == Decimal("100")


def test_post_class_creates_even_with_non_100_sum(client: TestClient) -> None:
    """POST a class that makes the per-profile sum exceed 100; expect 201.

    Allocation is NEVER blocked by sum-to-100 — the user builds
    the portfolio incrementally. The class must be created even
    when the sum goes over or under 100.

    Initial: 2 classes at 60/30 (sum = 90). POST a 3rd at 30
    → new sum = 120 (over 100). Expect 201, DB has 3 rows.
    """
    _login_and_select(client, profile_id=1)
    _seed_classes(
        profile_id=1,
        rows=[
            ("Renda Fixa", "60"),
            ("Acoes", "30"),
        ],
    )

    # POST a 3rd class at 30 → sum becomes 60+30+30 = 120 (over 100)
    response = client.post(
        "/api/classes",
        json={"name": "Bonds", "target_pct": "30"},
    )

    # Should succeed — allocation is informational, not blocking
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Bonds"

    # DB has 3 rows (the class was created)
    assert _count_classes(profile_id=1) == 3


def test_post_first_class_at_60_percent(client: TestClient) -> None:
    """Create the very first class at 60%; expect 201.

    This was the original bug: with 0 existing classes, creating
    a class at any value != 100% was rejected with "Falta X%".
    The fix removed the per-profile sum validation — the first
    class can be at any valid percentage.
    """
    _login_and_select(client, profile_id=1)

    # 0 existing classes. Create first class at 60%.
    response = client.post(
        "/api/classes",
        json={"name": "Renda Fixa", "target_pct": "60"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Renda Fixa"

    # DB has 1 row
    assert _count_classes(profile_id=1) == 1


def test_post_class_duplicate_name_returns_409(client: TestClient) -> None:
    """POST a class whose name already exists in the profile; expect 409.

    Initial: 2 classes, one named "Stocks". POST another "Stocks"
    → 409. DB unchanged (2 rows).
    """
    _login_and_select(client, profile_id=1)
    _seed_classes(
        profile_id=1,
        rows=[
            ("Stocks", "60"),
            ("Bonds", "40"),
        ],
    )

    # POST another "Stocks" → duplicate → 409
    response = client.post(
        "/api/classes",
        json={"name": "Stocks", "target_pct": "10"},
    )

    assert response.status_code == 409
    data = response.json()
    assert "Já existe uma classe com o nome Stocks" in data["detail"]

    # DB unchanged (2 rows)
    assert _count_classes(profile_id=1) == 2
