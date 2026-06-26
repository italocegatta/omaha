"""T01: PATCH /api/classes/{id} for inline class target_pct edits.

The dashboard's Alpine component clicks the % cell, turns it into an
input, and on blur sends a PATCH with ``{"target_pct": "<new>"}``.
Only the ``target_pct`` field is accepted — name changes and other
mutations go through the snapshot ``POST /classes`` editor.

**Allocation is informational, never blocking.** The PATCH route
accepts any target_pct value, even when the per-profile sum drifts
above or below 100. The user adjusts incrementally; the per-class
"Alvo X%" badge surfaces the delta in real time but never aborts
the request.

Three tests:
  1. ``test_patch_class_updates_target_pct`` — 3 classes at
     33.33/33.33/33.34 (sum = 100.00). PATCH the first from 33.33 to
     33.34 (new sum = 100.01, within 0.01 tolerance). Expect 200,
     response ``{"target_pct": "33.34"}``, DB row updated.
  2. ``test_patch_class_allows_any_target_pct`` — 3 classes at
     30/30/40 (sum = 100). PATCH the first to 60 → new sum = 130.
     Expect 200 (NOT 422) because allocation is informational, not
     blocking. The ``Sobra 30%`` delta shows in the UI badge but
     the row commits.
  3. ``test_patch_class_cross_profile_404`` — log in as profile A;
     PATCH a class belonging to profile B; expect 404.
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


_PROFILE_OWNERS = {1: "Italo", 2: "Ana"}


def _login_and_select(client: TestClient, profile_id: int = 1) -> None:
    """Log in with the seed credentials and bind ``active_profile_id``.

    direct-landing-with-header-profile-switcher: ``POST /login``
    auto-binds the logged-in user's own first profile. Default is
    Italo + profile 1; the explicit ``/profiles/{id}/select`` step
    only runs for cross-profile viewing.
    """
    username = _PROFILE_OWNERS.get(profile_id, "Italo")
    client.post(
        "/login",
        data={"username": username, "password": "test-password"},
        follow_redirects=False,
    )
    if _PROFILE_OWNERS.get(profile_id) != username:
        client.post(f"/profiles/{profile_id}/select", follow_redirects=False)


def _seed_classes(profile_id: int, rows: list[tuple[str, str]]) -> list[int]:
    """Insert ``(name, target_pct)`` rows via SQLAlchemy, return their IDs.

    Returns the list of inserted IDs in ``display_order`` order so
    the test can reference them for PATCH calls.
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


def test_patch_class_updates_target_pct(client: TestClient) -> None:
    """PATCH a class's target_pct to a valid value; expect 200 and DB update.

    Uses 33.33/33.33/33.34 (sum = 100.00). Patching the first from
    33.33 to 33.34 produces a new sum of 33.34+33.33+33.34 = 100.01,
    which is within the 0.01 tolerance and validates as OK.
    """
    _login_and_select(client, profile_id=1)
    ids = _seed_classes(
        profile_id=1,
        rows=[
            ("Renda Fixa", "33.33"),
            ("Acoes", "33.33"),
            ("Reserva", "33.34"),
        ],
    )

    # PATCH the first class: 33.33 → 33.34
    class_id = ids[0]
    response = client.patch(
        f"/api/classes/{class_id}",
        json={"target_pct": "33.34"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == class_id
    assert data["target_pct"] == "33.34"

    # DB row updated
    updated_pct = _get_class_target_pct(class_id)
    assert updated_pct is not None
    assert float(updated_pct) == 33.34


def test_patch_class_allows_any_target_pct(client: TestClient) -> None:
    """PATCH to any value; expect 200 even when the sum exceeds 100.

    Allocation is NEVER blocked by sum-to-100 — the user adjusts
    incrementally. The class must be updated even when the new sum
    goes over or under 100.

    Initial: 30/30/40 (sum = 100). PATCH first to 60 → new sum =
    60+30+40 = 130. Expect 200, DB updated to 60.
    """
    _login_and_select(client, profile_id=1)
    ids = _seed_classes(
        profile_id=1,
        rows=[
            ("Renda Fixa", "30"),
            ("Acoes", "30"),
            ("Reserva", "40"),
        ],
    )

    # PATCH the first class to 60 → sum becomes 130 (over 100)
    class_id = ids[0]
    response = client.patch(
        f"/api/classes/{class_id}",
        json={"target_pct": "60"},
    )

    # Should succeed — allocation is informational, not blocking
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == class_id
    assert data["target_pct"] == "60"

    # DB row updated
    updated_pct = _get_class_target_pct(class_id)
    assert updated_pct is not None
    assert float(updated_pct) == 60.0


def test_patch_class_cross_profile_404(client: TestClient) -> None:
    """PATCH a class belonging to another profile; expect 404.

    Profile 1 has classes at 30/30/40. Log in as profile 1, then
    attempt to PATCH a class that belongs to profile 2.
    """
    # Seed profile 1 with classes
    _login_and_select(client, profile_id=1)
    _seed_classes(
        profile_id=1,
        rows=[
            ("Renda Fixa", "30"),
            ("Acoes", "30"),
            ("Reserva", "40"),
        ],
    )

    # Seed profile 2 with its own class (using a fresh session)
    ids_p2 = _seed_classes(
        profile_id=2,
        rows=[
            ("Profile2 Class", "100"),
        ],
    )

    # Still logged in as profile 1, try to PATCH profile 2's class
    class_id = ids_p2[0]
    response = client.patch(
        f"/api/classes/{class_id}",
        json={"target_pct": "50"},
    )

    assert response.status_code == 404
