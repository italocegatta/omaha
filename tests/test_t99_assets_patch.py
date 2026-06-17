"""T02: PATCH /api/assets/{id} route — per-class sum validation.

Three test cases, each backed by the session-scoped ``_omaha_test_env``
from ``tests/conftest.py`` (per-test :class:`TestClient` for cookie
isolation, but a single SQLite file at the session level so the
T01 ``assets`` and ``asset_classes`` tables are already present and
the T01 ``target_pct`` column is in scope).

The route is the only network path that can mutate
``assets.target_pct`` — locking its behavior in three tests means
the T03 Alpine inline editor can call it from the browser and trust
the contract:

* **200** with ``{"id", "target_pct"}`` on a valid edit.
* **422** with ``{"detail": "<Sobra/Falta X%>"}`` on a per-class
  sum violation, and the row is NOT mutated on disk.
* **404** for a non-existent or cross-profile asset id.

Per-row model (T02)
-------------------
Unlike S02's snapshot semantics on ``asset_classes`` (delete-all-
then-insert on every save), the asset list is per-row: a PATCH
updates one row's ``target_pct`` and the validator re-checks the
class-level invariant against the class's other assets' current
values plus the new value.

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
  the column directly so a test can assert that a rejected PATCH
  did not commit (the in-flight session from the test client is
  bound to the request lifecycle and would mask the result).
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
    The T01 model tests (``test_t01_classes_model.py``,
    ``test_t01_positions_model.py``) use ``monkeypatch`` +
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


def _login_and_select(client: TestClient, profile_id: int = 1) -> None:
    """Log in with the seed credentials and bind ``active_profile_id``.

    The seed (``src/omaha/seed.py``) creates only ``Italo`` and
    ``Ana`` — there is no ``family`` user. Logging in as
    ``family`` silently fails (the login route returns 200 with
    a form error and no session cookie), so the subsequent
    ``/profiles/{id}/select`` is unauthenticated and the PATCH
    route's ``require_active_profile`` dependency raises 404
    before the handler ever reads the asset. ``Italo`` is the
    profile-1 owner per the seed.
    """
    client.post(
        "/login",
        data={"username": "Italo", "password": "test-password"},
        follow_redirects=False,
    )
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
    target_pct: str,
) -> Any:
    """PATCH ``/api/assets/{asset_id}`` with ``{"target_pct": "<value>"}``.

    The body is a JSON object with a *string* value so the editor
    can post ``"40"`` or ``"40.5"`` without a JSON-number round-
    trip (matches the S02 ``_parse_pct`` style). The route's
    response is also JSON, so we assert on the parsed dict.
    """
    return client.patch(
        f"/api/assets/{asset_id}",
        json={"target_pct": target_pct},
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
    assert body == {"id": asset_id, "target_pct": "100"}
    assert _read_asset_target_pct(asset_id, _omaha_test_env) == Decimal("100")


def test_patch_asset_invalid_sum_returns_422(
    client: TestClient, _omaha_test_env: dict[str, str]
) -> None:
    """A PATCH that would push the per-class sum over 100 returns 422 and commits nothing.

    Seeds 3 assets at 30/30/30 (sum 90). PATCH one to 50 → per-class
    sum becomes 30 + 30 + 50 = 110 (Sobra 10%). The response is a
    JSON ``{"detail": "Sobra 10%"}`` so the T03 Alpine editor can
    paint the input red; the on-disk ``target_pct`` must remain
    30 (the original value) so a failed edit never silently
    advances the column.
    """
    _login_and_select(client, profile_id=1)
    class_id, asset_ids = _seed_class_with_assets(
        1, "Renda Fixa", ["30", "30", "30"], _omaha_test_env
    )
    target_asset_id = asset_ids[0]
    other_ids = asset_ids[1:]
    assert _read_asset_target_pct(target_asset_id, _omaha_test_env) == Decimal("30")

    response = _patch_asset(client, target_asset_id, "50")

    assert response.status_code == 422
    body = response.json()
    assert body == {"detail": "Sobra 10%"}
    # The failed edit must not have committed.
    assert _read_asset_target_pct(target_asset_id, _omaha_test_env) == Decimal("30")
    # The other assets are untouched.
    for aid in other_ids:
        assert _read_asset_target_pct(aid, _omaha_test_env) == Decimal("30")


def test_patch_asset_cross_profile_404(client: TestClient, _omaha_test_env: dict[str, str]) -> None:
    """A PATCH against another profile's asset is 404 (ownership check walks the FK).

    Seeds an asset under Ana Livia (profile 2). Logs in as Italo
    (profile 1) and tries to PATCH the asset. The route's
    ``asset.asset_class.profile_id != profile.id`` check raises
    404 — the response is identical to "asset doesn't exist", so
    a stale URL is indistinguishable from a cross-profile probe.
    """
    # Pre-populate an asset under Ana Livia via a fresh engine
    # bound to the session-scoped test DB URL (not the
    # monkeypatched ``omaha.db`` — see the autouse fixture's
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
        other_asset_id = asset.id
    finally:
        db.close()
        engine.dispose()

    # Switch to Italo (profile 1) and try to PATCH Ana's asset.
    _login_and_select(client, profile_id=1)

    response = _patch_asset(client, other_asset_id, "60")

    assert response.status_code == 404
    # The asset must still be on disk at its original value —
    # the 404 means the route did not touch the row.
    assert _read_asset_target_pct(other_asset_id, _omaha_test_env) == Decimal("50")
