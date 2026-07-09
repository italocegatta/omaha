"""T01: POST /api/assets for adding a single asset.

The dashboard's Alpine ``+`` component (S03/T03) sends a JSON POST with
``{"name": "...", "asset_class_id": ..., "target_pct": "..."}`` to create a
new asset under the selected class. ``target_pct`` is optional and
defaults to ``0`` (matches the S01 D015 contract: an asset can exist
in a class at 0% while the user is still building the allocation).

**Per-class sum is informational only (D006).** The
``asset-table-view`` change removed the per-class sum gate
from ``POST /api/assets`` and ``PATCH /api/assets/{id}``:
off-100 sums are accepted on both endpoints, and the resulting
deviation is surfaced through the dashboard's class-delta badge
and the sticky allocation alert card. ``test_post_api_asset_per_class_sum_accepted``
asserts the new contract.

Five tests:
  1. ``test_post_api_asset_creates_row_with_zero_target`` — empty class;
     POST a new asset with ``target_pct="0"``; expect 201; response has
     the new asset's id, name, target_pct; DB has 1 row with
     ``display_order=0``.
  2. ``test_post_api_asset_per_class_sum_accepted`` — class already
     has one asset at ``target_pct=100`` (sum = 100); POST a 2nd
     with ``target_pct="50"`` (new sum = 150); expect 201, response
     carries the new id/name/target_pct; DB has 2 rows and the
     per-class sum on disk is 150. The alert UI surfaces the
     deviation; the route no longer blocks.
  3. ``test_post_api_asset_duplicate_name_returns_409`` — POST
     "PETR4" → 201; POST another "PETR4" → 409; DB has 1 row.
  4. ``test_post_api_asset_empty_name_returns_422`` — POST ``{"name":
     "", ...}``; expect 422 with "obrigatório" wording; DB empty.
  5. ``test_post_api_asset_cross_profile_class_returns_422`` — class
     id from another profile; expect 422 with "Selecione uma classe
     válida." wording; DB empty.
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# Per-test cleanup
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _clean_assets_and_classes() -> None:
    """Wipe ``assets`` AND ``asset_classes`` before each test.

    Mirrors the T02 ``_clean_assets_and_classes`` autouse fixture:
    session-scoped DB so a successful POST in one test leaves rows
    on disk that the next test would trip over. We wipe both
    tables so each test starts from a known empty state.
    """
    from omaha.db import SessionLocal
    from omaha.models import Asset, AssetClass

    db = SessionLocal()
    try:
        # Wipe children first to respect the FK direction
        # (assets → asset_classes → profiles).
        db.query(Asset).delete()
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
    auto-binds the logged-in user's own first profile (by
    ``display_order``), so logging in as ``Italo`` already binds
    profile 1. The explicit ``/profiles/{id}/select`` step only
    runs when the requested profile is owned by a different user
    (cross-profile viewing tests).
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
    """Insert ``(name, target_pct)`` class rows directly via SQLAlchemy.

    Returns the inserted class ids in insertion order so a caller
    can pass them to a POST as ``asset_class_id``. The asset
    editor is the consumer, so pre-existing classes are the right
    starting state for most tests.
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


def _seed_asset(
    asset_class_id: int,
    name: str,
    target_pct: str,
    display_order: int = 0,
) -> int:
    """Insert a single asset directly via SQLAlchemy; return its id.

    Used to set up a class that already has assets (test 2 needs a
    class with one asset at ``target_pct=100`` so the next POST
    can push the class sum over 100). Skips the route entirely —
    we want a known starting state, not a chain of POSTs.
    """
    from omaha.db import SessionLocal
    from omaha.models import Asset

    db = SessionLocal()
    try:
        asset = Asset(
            asset_class_id=asset_class_id,
            name=name,
            target_pct=Decimal(target_pct),
            display_order=display_order,
        )
        db.add(asset)
        db.flush()
        db.commit()
        return asset.id
    finally:
        db.close()


def _count_assets(asset_class_id: int) -> int:
    """Return the number of ``assets`` rows for ``asset_class_id``."""
    from omaha.db import SessionLocal
    from omaha.models import Asset

    db = SessionLocal()
    try:
        return db.query(Asset).filter(Asset.asset_class_id == asset_class_id).count()
    finally:
        db.close()


def _get_asset(asset_id: int) -> object | None:
    """Return the ``Asset`` row for ``asset_id`` (or ``None``)."""
    from omaha.db import SessionLocal
    from omaha.models import Asset

    db = SessionLocal()
    try:
        return db.get(Asset, asset_id)
    finally:
        db.close()


def _post_api_asset(
    client: TestClient,
    name: str,
    asset_class_id: int,
    target_pct: str | int | None,
) -> object:
    """POST ``/api/assets`` with a JSON body.

    Mirrors the wire format the S03/T03 Alpine ``+`` button
    produces: a JSON object with ``name``, ``asset_class_id``,
    and ``target_pct``. ``target_pct`` is sent as a string so the
    route can parse it through ``_parse_pct`` (the same forgiving
    parser the form-encoded POST and the S01 PATCH route use).
    """
    return client.post(
        "/api/assets",
        json={"name": name, "asset_class_id": asset_class_id, "target_pct": target_pct},
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_post_api_asset_creates_row_with_zero_target(client: TestClient) -> None:
    """POST a new asset with ``target_pct=0`` to an empty class; expect 201 + DB row.

    Initial: 0 assets in the class. POST a new asset with
    ``target_pct="0"`` → 201, response has the new asset's id/name/target_pct,
    DB has 1 row, ``display_order=0``. The ``target_pct=0`` path skips the
    per-class sum gate (the new value cannot push the class over 100 when
    the new value is 0), which is the whole point of D015 — an asset can
    be added at 0% while the user is still building the allocation.
    """
    _login_and_select(client, profile_id=1)
    [class_id] = _seed_classes(profile_id=1, rows=[("Renda Fixa", "100")])

    # POST a new asset with target_pct=0. Sum stays at 0, so the
    # per-class sum gate is skipped (gate fires only when target_pct > 0).
    response = _post_api_asset(
        client,
        name="Tesouro Selic",
        asset_class_id=class_id,
        target_pct="0",
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Tesouro Selic"
    assert Decimal(data["target_pct"]) == Decimal("0")
    assert isinstance(data["id"], int)

    # DB has 1 row for this class
    assert _count_assets(asset_class_id=class_id) == 1

    # Row is on disk with display_order=0 (empty class → first slot)
    asset = _get_asset(data["id"])
    assert asset is not None
    assert asset.display_order == 0
    assert asset.name == "Tesouro Selic"
    assert asset.target_pct == Decimal("0")


def test_post_api_asset_per_class_sum_accepted(client: TestClient) -> None:
    """POST an asset that pushes the class sum over 100; expect 201 (D006).

    Per the ``asset-table-view`` change (D006), the per-class sum
    gate was removed from ``POST /api/assets``. Initial: 1 asset at
    ``target_pct=100`` (sum = 100). POST a 2nd with ``target_pct=50``
    (new sum = 150). The route accepts the write and returns 201
    with the new asset's id/name/target_pct; DB has 2 rows and the
    on-disk per-class sum is 150. The alert UI surfaces the
    deviation; the route no longer blocks.

    Asserts
    -------
    - 201 with the new asset's id, name, and target_pct.
    - DB has 2 rows for the class (the seeded one + the new one).
    - The on-disk per-class sum is 150 (> 100).
    """
    _login_and_select(client, profile_id=1)
    [class_id] = _seed_classes(profile_id=1, rows=[("Renda Fixa", "100")])
    _seed_asset(
        asset_class_id=class_id,
        name="Tesouro Selic",
        target_pct="100",
        display_order=0,
    )

    # POST a 2nd asset at 50% → class sum becomes 150 → Sobra 50%
    # The route no longer blocks (D006). Expect 201.
    response = _post_api_asset(
        client,
        name="Tesouro IPCA",
        asset_class_id=class_id,
        target_pct="50",
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Tesouro IPCA"
    assert Decimal(data["target_pct"]) == Decimal("50")
    assert isinstance(data["id"], int)

    # DB has 2 rows now (the seeded one + the new one).
    assert _count_assets(asset_class_id=class_id) == 2

    # The on-disk per-class sum is 150 (> 100). The dashboard's
    # class-delta badge + sticky allocation alert card surface
    # this deviation.
    from omaha.db import SessionLocal
    from omaha.models import Asset

    db = SessionLocal()
    try:
        rows = db.query(Asset).filter(Asset.asset_class_id == class_id).all()
        on_disk = sum((a.target_pct for a in rows), Decimal("0"))
    finally:
        db.close()
    assert on_disk == Decimal("150")


def test_post_api_asset_preserves_high_precision_target_pct(client: TestClient) -> None:
    """POST accepts 6-decimal canonical target_pct and persists it unchanged."""
    _login_and_select(client, profile_id=1)
    [class_id] = _seed_classes(profile_id=1, rows=[("Renda Fixa", "100")])

    response = _post_api_asset(
        client,
        name="Tesouro IPCA 2035",
        asset_class_id=class_id,
        target_pct="66.666667",
    )

    assert response.status_code == 201
    data = response.json()
    assert data["target_pct"] == "66.666667"
    asset = _get_asset(data["id"])
    assert asset is not None
    assert asset.target_pct == Decimal("66.666667")


def test_post_api_asset_duplicate_name_returns_409(client: TestClient) -> None:
    """POST two assets with the same name in the same class; expect 201 then 409.

    Initial: 0 assets. POST "PETR4" → 201. POST another "PETR4" → 409
    with "Já existe um ativo" wording. DB has 1 row.
    """
    _login_and_select(client, profile_id=1)
    [class_id] = _seed_classes(profile_id=1, rows=[("Acoes", "100")])

    # First POST — succeeds
    first = _post_api_asset(
        client,
        name="PETR4",
        asset_class_id=class_id,
        target_pct="0",
    )
    assert first.status_code == 201
    assert _count_assets(asset_class_id=class_id) == 1

    # Second POST with the same name → 409
    second = _post_api_asset(
        client,
        name="PETR4",
        asset_class_id=class_id,
        target_pct="0",
    )

    assert second.status_code == 409
    data = second.json()
    assert "Já existe um ativo" in data["detail"]
    assert "PETR4" in data["detail"]

    # DB unchanged — still 1 row
    assert _count_assets(asset_class_id=class_id) == 1


def test_post_api_asset_empty_name_returns_422(client: TestClient) -> None:
    """POST an asset with an empty name; expect 422 with "obrigatório" wording.

    Initial: 0 assets. POST ``{"name": "", ...}`` → 422 with
    "O nome do ativo é obrigatório." (the route strips whitespace
    first, so an all-whitespace name also fails this branch).
    DB has 0 rows.
    """
    _login_and_select(client, profile_id=1)
    [class_id] = _seed_classes(profile_id=1, rows=[("Renda Fixa", "100")])

    # POST with an empty name
    response = _post_api_asset(
        client,
        name="",
        asset_class_id=class_id,
        target_pct="0",
    )

    assert response.status_code == 422
    data = response.json()
    assert "obrigatório" in data["detail"]

    # DB empty — no asset was created
    assert _count_assets(asset_class_id=class_id) == 0


def test_post_api_asset_cross_profile_class_returns_422(client: TestClient) -> None:
    """POST an asset targeting a class from another profile; expect 422.

    Seed a class under profile 2 (Ana). Login as profile 1
    (Italo). POST with ``asset_class_id`` pointing at the other
    profile's class → 422 with "Selecione uma classe válida." (the
    route must not surface a 404 for cross-class — that contract
    is reserved for the DELETE route; cross-class POST is a 422
    so the T03 inline form can render the error in the input
    field). DB has 0 assets in either profile.
    """
    # Seed a class under profile 2 (Ana) — must be done
    # before login because the seed helper bypasses the auth
    # session, so the active profile is irrelevant here.
    [other_class_id] = _seed_classes(profile_id=2, rows=[("Acoes", "100")])

    # Now log in as profile 1 (Italo) and seed a class for it.
    _login_and_select(client, profile_id=1)
    _seed_classes(profile_id=1, rows=[("Renda Fixa", "100")])

    # POST with the OTHER profile's class id
    response = _post_api_asset(
        client,
        name="PETR4",
        asset_class_id=other_class_id,
        target_pct="0",
    )

    assert response.status_code == 422
    data = response.json()
    assert "Selecione uma classe válida." in data["detail"]

    # No asset was created in the cross-profile class (the seed
    # would have to be queried under profile 2's namespace; the
    # _count_assets helper scopes to the class id, so it works
    # regardless of which profile owns the class).
    assert _count_assets(asset_class_id=other_class_id) == 0
