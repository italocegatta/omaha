"""T02: PATCH /api/assets/{id} route — per-row range check (D006).

Three test cases, each backed by the session-scoped ``_omaha_test_env``
from ``tests/conftest.py`` (per-test :class:`TestClient` for cookie
isolation, but a single SQLite file at the session level so the
T01 ``assets`` and ``asset_classes`` tables are already present and
the T01 ``target_pct`` column is in scope).

The route is the only network path that can mutate
``assets.target_pct`` — locking its behavior in three tests means
the Alpine inline editor can call it from the browser and trust
the contract:

* **200** with ``{"id", "target_pct"}`` on a valid edit (including
  off-100 per-class sums — the sum gate was removed by D006).
* **404** for a non-existent or cross-profile asset id.
* **422** for a per-row range/out-of-range violation only.

Per-row model (T02)
-------------------
Unlike S02's snapshot semantics on ``asset_classes`` (delete-all-
then-insert on every save), the asset list is per-row: a PATCH
updates one row's ``target_pct``. The per-class sum check that
used to fire here was removed by ``asset-table-view`` (D006):
every commit is accepted within the per-row 0-100 range and the
resulting deviation is surfaced through the dashboard's
class-delta badge + sticky allocation alert card rather than a 422.

The flow exercised by every test:

1. ``POST /login`` with the seed credentials.
2. ``POST /profiles/{id}/select`` to bind ``active_profile_id``.
3. (where needed) seed class + asset rows directly via SQLAlchemy
   so the PATCH has a class + asset to target.
4. ``PATCH /api/assets/{id}`` with ``{"target_pct": "..."}``.

Helper conventions
------------------
- :func:`_login_and_select` performs the two-step cookie bootstrap.
- :func:`_seed_class_with_assets` inserts one class plus N assets
  with explicit ``target_pct`` values, returning the class id and
  asset ids in insertion order. The PATCH targets the first
  asset's id; the remaining assets' values feed the per-class
  sum.
- :func:`_read_asset_target_pct` opens a fresh session and reads
  the column directly so a test can assert the on-disk state after
  a successful (or rejected) PATCH (the in-flight session from the
  test client is bound to the request lifecycle and would mask
  the result).
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

import pytest
from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# Per-test cleanup
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _clean_assets_and_classes(_omaha_test_env: dict[str, str]) -> None:
    """Wipe ``assets`` AND ``asset_classes`` before each T02 patch test.

    The shared ``_omaha_test_env`` fixture is session-scoped, so a
    successful PATCH in one test leaves a row on disk with the new
    ``target_pct`` value that the next test would trip over. We
    also wipe ``asset_classes`` so each test seeds its own class
    rows from a known empty state — pre-existing rows from the
    seed or a prior test would trip the unique constraint.

    Why a fresh engine instead of ``from omaha.db import SessionLocal``
    -------------------------------------------------------------------
    The T01 model tests (``test_classes_model.py``,
    ``test_positions_model.py``) use ``monkeypatch`` +
    ``del sys.modules`` to swap ``omaha.db`` to a per-test tmp
    DB. If one of those tests ran first and the swap wasn't
    reverted, ``from omaha.db import SessionLocal`` would target
    the wrong (now-deleted) tmp DB and the seed helpers would
    invisibly seed into it.

    We instead bind a fresh SQLAlchemy engine to the
    session-scoped test DB URL (which the conftest's
    ``_omaha_test_env`` returns) and wipe via that. The route's
    captured engine is the same session-scoped engine, so the
    wipe is visible to the HTTP path. This keeps the fixture
    robust to the T01 model tests' ``sys.modules`` shenanigans.
    """
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from omaha.models import Asset, AssetClass

    engine = create_engine(_omaha_test_env["db_url"], future=True)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    db = SessionLocal()
    try:
        db.query(Asset).delete()
        db.query(AssetClass).delete()
        db.commit()
    finally:
        db.close()
        engine.dispose()
    yield


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


_PROFILE_OWNERS = {1: "Italo", 2: "Ana"}


def _login_and_select(client: TestClient, profile_id: int = 1) -> None:
    """Log in with the seed credentials and bind ``active_profile_id``.

    direct-landing-with-header-profile-switcher: ``POST /login``
    now auto-binds the logged-in user's own first profile (by
    ``display_order``), so logging in as ``Italo`` already binds
    profile 1. If the caller asks for a profile owned by a
    different user, the helper explicitly calls
    ``/profiles/{id}/select`` (cross-profile viewing is now allowed
    by the new contract).
    """
    username = _PROFILE_OWNERS.get(profile_id, "Italo")
    client.post(
        "/login",
        data={"username": username, "password": "test-password"},
        follow_redirects=False,
    )
    if _PROFILE_OWNERS.get(profile_id) != username:
        # Cross-profile: the login bound the wrong user's profile.
        client.post(f"/profiles/{profile_id}/select", follow_redirects=False)


def _seed_class_with_assets(
    profile_id: int,
    class_name: str,
    asset_targets: list[str],
    _omaha_test_env: dict[str, str],
) -> tuple[int, list[int]]:
    """Insert one class plus N assets with explicit ``target_pct`` values.

    Returns ``(class_id, [asset_id, ...])`` in insertion order. The
    PATCH route's per-class sum is computed against the class's
    other assets' current values plus the new value, so seeding
    assets with known ``target_pct`` values is the only way to
    assert the validator's behavior deterministically.

    Uses a fresh engine bound to the session-scoped test DB URL
    (not the monkeypatched ``omaha.db``) for the same reason as
    :func:`_clean_assets_and_classes`.
    """
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from omaha.models import Asset, AssetClass

    engine = create_engine(_omaha_test_env["db_url"], future=True)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    db = SessionLocal()
    try:
        cls = AssetClass(
            profile_id=profile_id,
            name=class_name,
            target_pct=Decimal("100"),
            display_order=0,
        )
        db.add(cls)
        db.flush()
        asset_ids: list[int] = []
        for idx, pct in enumerate(asset_targets):
            asset = Asset(
                asset_class_id=cls.id,
                name=f"Asset-{idx}",
                target_pct=Decimal(pct),
                display_order=idx,
            )
            db.add(asset)
            db.flush()
            asset_ids.append(asset.id)
        db.commit()
        return cls.id, asset_ids
    finally:
        db.close()
        engine.dispose()


def _read_asset_target_pct(asset_id: int, _omaha_test_env: dict[str, str]) -> Decimal:
    """Return the on-disk ``target_pct`` of ``asset_id`` via a fresh session.

    Opens a new engine bound to the session-scoped test DB URL
    (not the monkeypatched ``omaha.db``) so the read reflects
    the on-disk DB state, not the in-flight session. The PATCH
    route commits before returning, so a rejected PATCH must
    leave the column untouched on disk.
    """
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from omaha.models import Asset

    engine = create_engine(_omaha_test_env["db_url"], future=True)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    db = SessionLocal()
    try:
        return db.get(Asset, asset_id).target_pct
    finally:
        db.close()
        engine.dispose()


def _patch_asset(
    client: TestClient,
    asset_id: int,
    payload: str | dict[str, object],
) -> Any:
    """PATCH ``/api/assets/{asset_id}`` with a JSON body.

    String payload is normalized to ``{"target_pct": "<value>"}``
    for the legacy class-level editor path. Dict payload lets tests
    exercise the F17 shortcut field directly.
    """
    json_payload = {"target_pct": payload} if isinstance(payload, str) else payload
    return client.patch(
        f"/api/assets/{asset_id}",
        json=json_payload,
        follow_redirects=False,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_patch_asset_updates_target_pct(
    client: TestClient, _omaha_test_env: dict[str, str]
) -> None:
    """Happy path: 200 with ``{"id", "target_pct"}`` and the row is mutated.

    Seeds a class with one asset at 0% (the T01 column default
    for the new target_pct column) and PATCH to 100. The class
    has no other assets, so the per-class sum is 100 — exactly
    the validator's success target. The response carries the
    new value as a string so the editor can display it
    without a Decimal round-trip.
    """
    _login_and_select(client, profile_id=1)
    class_id, asset_ids = _seed_class_with_assets(1, "Renda Fixa", ["0"], _omaha_test_env)
    (asset_id,) = asset_ids
    assert _read_asset_target_pct(asset_id, _omaha_test_env) == Decimal("0")

    response = _patch_asset(client, asset_id, "100")

    assert response.status_code == 200
    body = response.json()
    # asset-trade-flags: the PATCH response now carries the full
    # 4-field state (``target_pct`` + 3 trade-control fields). The
    # caller only patched ``target_pct`` so the trade fields stay
    # at their server defaults (``True / True / 'BRL'``).
    assert body["id"] == asset_id
    assert body["target_pct"] == "100"
    assert body["buy_enabled"] is True
    assert body["sell_enabled"] is True
    assert body["currency_code"] == "BRL"
    assert _read_asset_target_pct(asset_id, _omaha_test_env) == Decimal("100")


def test_patch_asset_off_sum_accepts_and_persists(
    client: TestClient, _omaha_test_env: dict[str, str]
) -> None:
    """A PATCH that pushes the per-class sum over 100 returns 200 and commits the new value.

    Seeds 3 assets at 30/30/30 (sum 90). PATCH one to 50 → per-class
    sum becomes 30 + 30 + 50 = 110 (off 100 by 10). Per the
    ``asset-table-view`` change (D006), the per-class sum gate
    was removed: every commit is accepted within the per-row
    0-100 range, and the resulting deviation is surfaced through
    the dashboard's class-delta badge + sticky allocation alert
    card rather than a 422.

    Asserts
    -------
    - PATCH returns 200 with ``{"id", "target_pct": "50"}``.
    - The on-disk ``target_pct`` is 50 (the new value committed).
    - The other two assets are untouched (still 30 each).
    - The resulting per-class sum on disk is 110 (> 100).
    """
    _login_and_select(client, profile_id=1)
    class_id, asset_ids = _seed_class_with_assets(
        1, "Renda Fixa", ["30", "30", "30"], _omaha_test_env
    )
    target_asset_id = asset_ids[0]
    other_ids = asset_ids[1:]
    assert _read_asset_target_pct(target_asset_id, _omaha_test_env) == Decimal("30")

    response = _patch_asset(client, target_asset_id, "50")

    assert response.status_code == 200
    body = response.json()
    # asset-trade-flags: 4-field response (see sibling test for
    # the rationale); only ``target_pct`` was sent so the trade
    # fields read their defaults.
    assert body["id"] == target_asset_id
    assert body["target_pct"] == "50"
    assert body["buy_enabled"] is True
    assert body["sell_enabled"] is True
    assert body["currency_code"] == "BRL"
    # The new value committed.
    assert _read_asset_target_pct(target_asset_id, _omaha_test_env) == Decimal("50")
    # The other assets are untouched.
    for aid in other_ids:
        assert _read_asset_target_pct(aid, _omaha_test_env) == Decimal("30")
    # Resulting per-class sum is 110 (> 100) — the alert UI surfaces
    # this on the dashboard.
    on_disk = sum(_read_asset_target_pct(aid, _omaha_test_env) for aid in asset_ids)
    assert on_disk == Decimal("110")


def test_patch_asset_active_profile_succeeds(
    client: TestClient, _omaha_test_env: dict[str, str]
) -> None:
    """direct-landing-with-header-profile-switcher flipped this contract.

    A PATCH against an asset that belongs to the active profile
    succeeds with 200. The prior per-user ownership check
    (``asset.asset_class.profile_id != profile.id`` → 404) was
    removed: any logged-in user can view and mutate any profile's
    data, gated only by ``active_profile_id``.

    Here we seed Ana's asset, log in as Ana (the login auto-binds
    Ana's profile), and PATCH Ana's asset — the new contract says
    this returns 200, not 404.
    """
    # Pre-populate an asset under Ana Livia (profile 2) via a
    # fresh engine bound to the session-scoped test DB URL (not
    # the monkeypatched ``omaha.db`` — see the autouse fixture's
    # docstring for why).
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from omaha.models import Asset, AssetClass

    engine = create_engine(_omaha_test_env["db_url"], future=True)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    db = SessionLocal()
    try:
        cls = AssetClass(
            profile_id=2,
            name="Renda Fixa Ana",
            target_pct=Decimal("100"),
            display_order=0,
        )
        db.add(cls)
        db.flush()
        asset = Asset(
            asset_class_id=cls.id,
            name="PETR4",
            target_pct=Decimal("50"),
            display_order=0,
        )
        db.add(asset)
        db.commit()
        ana_asset_id = asset.id
    finally:
        db.close()
        engine.dispose()

    # Log in as Ana — login auto-binds active_profile_id to Ana's
    # profile (the one that owns the asset). PATCH must succeed.
    _login_and_select(client, profile_id=2)

    response = _patch_asset(client, ana_asset_id, "60")

    assert response.status_code == 200
    body = response.json()
    # asset-trade-flags: 4-field response; trade defaults untouched.
    assert body["id"] == ana_asset_id
    assert body["target_pct"] == "60"
    assert body["buy_enabled"] is True
    assert body["sell_enabled"] is True
    assert body["currency_code"] == "BRL"
    assert _read_asset_target_pct(ana_asset_id, _omaha_test_env) == Decimal("60")


def test_patch_asset_target_pct_total_shortcut_persists_high_precision(
    client: TestClient, _omaha_test_env: dict[str, str]
) -> None:
    """Shortcut edit stores canonical 6-decimal target_pct and returns derived total."""
    _login_and_select(client, profile_id=1)
    class_id, asset_ids = _seed_class_with_assets(1, "Renda Fixa", ["0"], _omaha_test_env)
    asset_id = asset_ids[0]

    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from omaha.models import AssetClass

    engine = create_engine(_omaha_test_env["db_url"], future=True)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    db = SessionLocal()
    try:
        klass = db.get(AssetClass, class_id)
        klass.target_pct = Decimal("30")
        db.commit()
    finally:
        db.close()
        engine.dispose()

    response = _patch_asset(client, asset_id, {"target_pct_total": "20"})

    assert response.status_code == 200
    body = response.json()
    assert body["target_pct"] == "66.666667"
    assert body["target_pct_total"] == "20"
    assert _read_asset_target_pct(asset_id, _omaha_test_env) == Decimal("66.666667")


def test_patch_asset_target_pct_total_rejects_class_target_zero(
    client: TestClient, _omaha_test_env: dict[str, str]
) -> None:
    """Non-zero shortcut edit against 0%-target class returns 422 and keeps DB unchanged."""
    _login_and_select(client, profile_id=1)
    class_id, asset_ids = _seed_class_with_assets(1, "Caixa", ["0"], _omaha_test_env)
    asset_id = asset_ids[0]

    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from omaha.models import AssetClass

    engine = create_engine(_omaha_test_env["db_url"], future=True)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    db = SessionLocal()
    try:
        klass = db.get(AssetClass, class_id)
        klass.target_pct = Decimal("0")
        db.commit()
    finally:
        db.close()
        engine.dispose()

    response = _patch_asset(client, asset_id, {"target_pct_total": "10"})

    assert response.status_code == 422
    assert "classe com alvo 0%" in response.json()["detail"]
    assert _read_asset_target_pct(asset_id, _omaha_test_env) == Decimal("0")


def test_patch_asset_rejects_target_pct_and_target_pct_total_together(
    client: TestClient, _omaha_test_env: dict[str, str]
) -> None:
    """Canonical and shortcut targets are mutually exclusive in one PATCH."""
    _login_and_select(client, profile_id=1)
    _class_id, asset_ids = _seed_class_with_assets(1, "Renda Fixa", ["40"], _omaha_test_env)
    asset_id = asset_ids[0]

    response = _patch_asset(
        client,
        asset_id,
        {"target_pct": "50", "target_pct_total": "20"},
    )

    assert response.status_code == 422
    assert "apenas um alvo" in response.json()["detail"]
    assert _read_asset_target_pct(asset_id, _omaha_test_env) == Decimal("40")
