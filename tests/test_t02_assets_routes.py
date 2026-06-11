"""T02: Asset CRUD routes with server-side validation.

Nine test cases against the S03 per-row asset editor. Each
test uses a per-test :class:`TestClient` (cookie isolation)
but the underlying SQLite file is session-scoped, so the T01
``assets`` table is already present after the bootstrap.

Per-row model (different from S02's snapshot model)
--------------------------------------------------
The S03 asset editor is per-row: each POST adds one asset, each
delete removes one. The form payload is a single ``name`` +
``asset_class_id`` pair, not parallel arrays. The editor does
not pre-populate from the DB — the user always sees the
current set on GET and adds/removes one at a time.

The flow exercised by every test:

1. ``POST /login`` with the seed credentials.
2. ``POST /profiles/{id}/select`` to bind ``active_profile_id``.
3. (where needed) seed one or more ``AssetClass`` rows directly
   via SQLAlchemy so the form has a class to attach to.
4. ``POST /assets`` (single name + class id) or
   ``POST /assets/{id}/delete`` as the action under test.

Helper conventions
------------------
- :func:`_login_and_select` performs the two-step cookie bootstrap.
- :func:`_seed_classes` inserts class rows directly so a test
  can pre-populate the profile before exercising the editor.
- :func:`_count_assets` / :func:`_assets_for_class` /
  :func:`_asset_orders` open a fresh session and read the DB
  directly so a test can assert that a rejected POST did not
  commit (the in-flight session from the test client is bound
  to the request lifecycle and would mask the result).
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
def _clean_assets_and_classes() -> None:
    """Wipe ``assets`` AND ``asset_classes`` before each T02 test.

    Mirrors the S02 ``_clean_asset_classes`` autouse fixture:
    session-scoped DB so a successful POST in one test leaves
    rows on disk that the next test would trip over. We also
    wipe ``asset_classes`` so each test starts from a known
    empty state — the S03 tests seed their own class rows via
    :func:`_seed_classes`, and pre-existing rows from the seed
    or a prior test would trip the unique constraint.

    The S02 fixture only needs to wipe ``asset_classes`` because
    every S02 test seeds its own classes too; S03 needs the
    extra ``assets`` wipe so the per-row test isolation holds.
    Delete (not drop) preserves the 0002 + 0003 schema shape.
    """
    from omaha.db import SessionLocal
    from omaha.models import Asset, AssetClass

    db = SessionLocal()
    try:
        # Wipe children first to respect the FK direction
        # (assets → asset_classes → profiles). The cascade on
        # the asset_classes delete would handle the assets, but
        # we delete both explicitly so a future model with a
        # non-cascaded relationship still has clean state.
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
    profile 2 = Ana Livia (display_order=1). Default is profile 1
    because that's what the T04 happy-path flow uses.
    """
    client.post(
        "/login",
        data={"username": "family", "password": "test-password"},
        follow_redirects=False,
    )
    client.post(f"/profiles/{profile_id}/select", follow_redirects=False)


def _seed_classes(profile_id: int, rows: list[tuple[str, str]]) -> list[int]:
    """Insert ``(name, target_pct)`` class rows directly via SQLAlchemy.

    Returns the inserted class ids in insertion order so a
    caller can pass them to a POST as ``asset_class_id``. The
    asset editor is the consumer, so pre-existing classes are
    the right starting state for most tests.
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


def _post_asset(
    client: TestClient,
    name: str,
    asset_class_id: int,
    *,
    follow_redirects: bool = False,
) -> Any:
    """POST ``/assets`` with a single ``name`` and ``asset_class_id``.

    Mirrors the wire format a real browser produces: a single
    ``name`` text field and a single ``asset_class_id`` select
    value, urlencoded body. The S03 editor is per-row — there
    is no parallel-array form field.
    """
    return client.post(
        "/assets",
        data={"name": name, "asset_class_id": str(asset_class_id)},
        follow_redirects=follow_redirects,
    )


def _count_assets(asset_class_id: int) -> int:
    """Return the number of ``assets`` rows for ``asset_class_id``."""
    from omaha.db import SessionLocal
    from omaha.models import Asset

    db = SessionLocal()
    try:
        return db.query(Asset).filter(Asset.asset_class_id == asset_class_id).count()
    finally:
        db.close()


def _assets_for_class(asset_class_id: int) -> list[str]:
    """Return ``[name, ...]`` for ``asset_class_id`` ordered by display_order."""
    from omaha.db import SessionLocal
    from omaha.models import Asset

    db = SessionLocal()
    try:
        rows = (
            db.query(Asset)
            .filter(Asset.asset_class_id == asset_class_id)
            .order_by(Asset.display_order)
            .all()
        )
        return [r.name for r in rows]
    finally:
        db.close()


def _asset_orders(asset_class_id: int) -> list[int]:
    """Return ``[display_order, ...]`` for ``asset_class_id`` ordered by display_order."""
    from omaha.db import SessionLocal
    from omaha.models import Asset

    db = SessionLocal()
    try:
        rows = (
            db.query(Asset)
            .filter(Asset.asset_class_id == asset_class_id)
            .order_by(Asset.display_order)
            .all()
        )
        return [r.display_order for r in rows]
    finally:
        db.close()


def _asset_id_by_name(asset_class_id: int, name: str) -> int:
    """Return the asset id for the unique (class_id, name) row."""
    from omaha.db import SessionLocal
    from omaha.models import Asset

    db = SessionLocal()
    try:
        return (
            db.query(Asset)
            .filter(Asset.asset_class_id == asset_class_id, Asset.name == name)
            .one()
            .id
        )
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_get_assets_renders_editor_with_classes(client: TestClient) -> None:
    """`GET /assets` renders the editor and lists the profile's classes in the dropdown."""
    _login_and_select(client, profile_id=1)
    [class_id] = _seed_classes(profile_id=1, rows=[("Renda Fixa", "100")])

    response = client.get("/assets", follow_redirects=False)

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert 'data-testid="asset-editor"' in response.text
    # The class dropdown surfaces the class name so the user
    # can see what they're attaching an asset to.
    assert "Renda Fixa" in response.text
    # The dropdown's <option value="..."> must carry the class
    # id so a POST can target it.
    assert f'value="{class_id}"' in response.text


def test_get_assets_empty_classes_shows_empty_state(client: TestClient) -> None:
    """Fresh profile with no classes → empty-state copy + no add form."""
    _login_and_select(client, profile_id=1)
    # No _seed_classes: the profile has zero classes.

    response = client.get("/assets", follow_redirects=False)

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    # Empty-state marker: the editor wrapper still renders (so
    # the testid is present) but the add-asset form is absent.
    assert 'data-testid="asset-editor"' in response.text
    assert 'data-testid="asset-empty-state"' in response.text
    assert "Crie classes antes" in response.text
    assert 'data-testid="asset-editor-save"' not in response.text


def test_post_assets_creates_row(client: TestClient) -> None:
    """Valid POST commits one asset, 303s to /assets, name is on disk."""
    _login_and_select(client, profile_id=1)
    [class_id] = _seed_classes(profile_id=1, rows=[("Renda Fixa", "100")])
    assert _count_assets(class_id) == 0

    response = _post_asset(client, "Tesouro Selic 2029", class_id)

    assert response.status_code == 303
    assert response.headers["location"] == "/assets"
    assert _count_assets(class_id) == 1
    assert _assets_for_class(class_id) == ["Tesouro Selic 2029"]


def test_post_assets_empty_name_rejected(client: TestClient) -> None:
    """Empty name → 200 with "obrigatório" and zero assets committed."""
    _login_and_select(client, profile_id=1)
    [class_id] = _seed_classes(profile_id=1, rows=[("Renda Fixa", "100")])

    response = _post_asset(client, "", class_id)

    assert response.status_code == 200
    assert "obrigatório" in response.text
    assert 'data-testid="asset-editor-error"' in response.text
    assert _count_assets(class_id) == 0


def test_post_assets_name_too_long_rejected(client: TestClient) -> None:
    """A 65-char name surfaces the length cap (64) and commits nothing."""
    _login_and_select(client, profile_id=1)
    [class_id] = _seed_classes(profile_id=1, rows=[("Renda Fixa", "100")])
    long_name = "x" * 65

    response = _post_asset(client, long_name, class_id)

    assert response.status_code == 200
    assert "64" in response.text
    assert 'data-testid="asset-editor-error"' in response.text
    assert _count_assets(class_id) == 0


def test_post_assets_class_from_other_profile_rejected(client: TestClient) -> None:
    """Submitting another profile's class id is rejected as 200 with an error.

    Same S02 defensive pattern: a hand-crafted form submission
    that targets a class the active profile doesn't own must
    not silently add an asset. 200 + error keeps the form
    re-submittable.
    """
    # Seed a class under Ana Livia (profile 2). The test
    # fixture only creates profile 1 + 2 via the seed, and the
    # per-test cleanup wipes assets; classes seeded here are
    # confined to the test DB.
    [other_class_id] = _seed_classes(profile_id=2, rows=[("Renda Fixa Ana", "100")])

    _login_and_select(client, profile_id=1)
    # Italo has zero classes; the cross-profile rejection is
    # the only check firing.
    response = _post_asset(client, "Tesouro Selic", other_class_id)

    assert response.status_code == 200
    assert 'data-testid="asset-editor-error"' in response.text
    assert _count_assets(other_class_id) == 0


def test_post_assets_delete_removes_asset(client: TestClient) -> None:
    """`POST /assets/{id}/delete` removes the asset, 303s to /assets, count drops to 0."""
    _login_and_select(client, profile_id=1)
    [class_id] = _seed_classes(profile_id=1, rows=[("Renda Fixa", "100")])
    _post_asset(client, "Tesouro Selic", class_id)
    assert _count_assets(class_id) == 1

    asset_id = _asset_id_by_name(class_id, "Tesouro Selic")
    response = client.post(f"/assets/{asset_id}/delete", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/assets"
    assert _count_assets(class_id) == 0


def test_post_assets_delete_cross_profile_is_404(client: TestClient) -> None:
    """Deleting another profile's asset is 404 (ownership check walks the FK)."""
    [other_class_id] = _seed_classes(profile_id=2, rows=[("Renda Fixa Ana", "100")])
    # Pre-populate an asset under Ana Livia via a direct DB
    # write (we never log in as Ana to keep the test focused
    # on the cross-profile rejection).
    from omaha.db import SessionLocal
    from omaha.models import Asset

    db = SessionLocal()
    try:
        asset = Asset(
            asset_class_id=other_class_id,
            name="PETR4",
            display_order=0,
        )
        db.add(asset)
        db.commit()
        other_asset_id = asset.id
    finally:
        db.close()

    # Switch to Italo (profile 1) and try to delete Ana's asset.
    _login_and_select(client, profile_id=1)

    response = client.post(f"/assets/{other_asset_id}/delete", follow_redirects=False)

    assert response.status_code == 404
    # The asset must still be on disk — the 404 means the route
    # did not touch the row.
    assert _count_assets(other_class_id) == 1


def test_post_assets_display_order_sequential(client: TestClient) -> None:
    """Three adds to one class produce contiguous display_order 0, 1, 2.

    The editor's stable iteration order
    (``AssetClass.assets`` is ``order_by="Asset.display_order"``)
    depends on this. The route uses ``max(existing) + 1`` so
    deletes that don't reset the counter still leave the next
    add at a contiguous slot.
    """
    _login_and_select(client, profile_id=1)
    [class_id] = _seed_classes(profile_id=1, rows=[("Acoes", "100")])

    _post_asset(client, "PETR4", class_id)
    _post_asset(client, "VALE3", class_id)
    _post_asset(client, "ITSA4", class_id)

    assert _assets_for_class(class_id) == ["PETR4", "VALE3", "ITSA4"]
    assert _asset_orders(class_id) == [0, 1, 2]
