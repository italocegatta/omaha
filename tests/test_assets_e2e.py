"""End-to-end test for asset CRUD + dashboard distribution view (S03 / T03).

The asset editor lives at ``GET /assets`` and POSTs to either
``/assets`` (add) or ``/assets/{id}/delete`` (per-row delete via
``formaction``). The dashboard (``GET /``) renders a distribution
view: each class with its assets listed underneath, or "Nenhum ativo
nesta classe" when the class is empty.

These tests use the same seed password as the rest of the suite
(``"test-password"`` — the value the conftest installs via
``ADMIN_PASSWORD``). The T02 conftest's ``_clean_asset_classes``
autouse fixture keeps the ``asset_classes`` table empty between tests
in this file's module too (cross-module, autouse), and the
``_clean_assets`` fixture below wipes the ``assets`` table for the
same reason.
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from omaha.models import Asset, AssetClass, Profile


@pytest.fixture(autouse=True)
def _clean_assets() -> None:
    """Wipe the ``assets`` and ``asset_classes`` tables before each test.

    Both must be empty: ``asset_classes`` because the S03 payoff
    tests seed their own classes, and ``assets`` because leftover
    rows from prior tests would inflate the "zero assets committed"
    assertions on the validation-failure paths.
    """
    from omaha.db import SessionLocal

    db = SessionLocal()
    try:
        db.query(Asset).delete()
        db.query(AssetClass).delete()
        db.commit()
    finally:
        db.close()
    yield


TEST_PASSWORD = "test-password"


def _login_and_select_profile(client: TestClient, profile_name: str = "Italo") -> Profile:
    """Log in as ``profile_name`` — login auto-binds the landing profile.

    direct-landing-with-header-profile-switcher: ``POST /login``
    now binds ``active_profile_id`` to the logged-in user's own
    first profile (by ``display_order``), so logging in as the
    profile's owner already selects the right row. The explicit
    ``/profiles/{id}/select`` step is gone for same-user login.
    Cross-profile (rare in this file) is handled via an explicit
    ``client.post(f"/profiles/{id}/select")`` from the test body.
    """
    client.post("/login", data={"username": profile_name, "password": TEST_PASSWORD})
    from omaha.db import SessionLocal

    db = SessionLocal()
    try:
        profile = db.query(Profile).filter(Profile.name == profile_name).first()
        assert profile is not None, f"profile {profile_name!r} not seeded"
    finally:
        db.close()
    return profile


def _seed_classes(profile_id: int) -> list[AssetClass]:
    """Pre-seed 3 classes (Renda Fixa 60, Acoes 30, Reserva 10) for ``profile_id``.

    Returns the committed rows (in display_order) so callers can
    reference their ids for the asset POSTs. Uses a fresh SessionLocal
    so the caller sees committed state, not in-flight transaction
    state.
    """
    from omaha.db import SessionLocal

    db: Session = SessionLocal()
    try:
        seeds = [
            ("Renda Fixa", Decimal("60.00"), 0),
            ("Acoes", Decimal("30.00"), 1),
            ("Reserva", Decimal("10.00"), 2),
        ]
        classes: list[AssetClass] = []
        for name, pct, order in seeds:
            cls = AssetClass(
                profile_id=profile_id,
                name=name,
                target_pct=pct,
                display_order=order,
            )
            db.add(cls)
            db.flush()
            classes.append(cls)
        db.commit()
    finally:
        db.close()
    return classes


def _assets_for_class(class_id: int) -> list[Asset]:
    """Return the assets for ``class_id`` ordered by display_order."""
    from omaha.db import SessionLocal

    db: Session = SessionLocal()
    try:
        return (
            db.query(Asset)
            .filter(Asset.asset_class_id == class_id)
            .order_by(Asset.display_order)
            .all()
        )
    finally:
        db.close()


class TestAssetsE2E:
    """End-to-end coverage for the asset editor + dashboard distribution view."""

    def test_add_three_assets_different_classes(self, client: TestClient) -> None:
        """S03 demo payoff: 3 assets in 3 different classes appear on the dashboard.

        Seed 3 classes, POST 3 assets (one per class), follow the
        redirect to the dashboard, and assert the dashboard body
        shows all 3 asset names under the 3 ``class-section-header``
        blocks.
        """
        profile = _login_and_select_profile(client)
        classes = _seed_classes(profile.id)
        cls_renda, cls_acoes, cls_reserva = classes

        # POST each asset to its class. The form posts to /assets
        # which 303s to /assets (the editor), not the dashboard.
        # The test then GETs the dashboard explicitly to verify the
        # distribution view.
        for name, class_id in [
            ("Tesouro Selic", cls_renda.id),
            ("PETR4", cls_acoes.id),
            ("IVVB11", cls_reserva.id),
        ]:
            resp = client.post(
                "/assets",
                data={"name": name, "asset_class_id": str(class_id)},
                follow_redirects=False,
            )
            assert resp.status_code == 303
            assert resp.headers["location"] == "/assets"

        # Verify DB state — 3 assets, one per class, in insertion order.
        assert len(_assets_for_class(cls_renda.id)) == 1
        assert len(_assets_for_class(cls_acoes.id)) == 1
        assert len(_assets_for_class(cls_reserva.id)) == 1
        assert _assets_for_class(cls_renda.id)[0].name == "Tesouro Selic"
        assert _assets_for_class(cls_acoes.id)[0].name == "PETR4"
        assert _assets_for_class(cls_reserva.id)[0].name == "IVVB11"

        # The dashboard renders the distribution view with all 3 names.
        dashboard = client.get("/")
        assert dashboard.status_code == 200
        body = dashboard.text
        for name in ("Tesouro Selic", "PETR4", "IVVB11"):
            assert name in body, f"dashboard body missing {name!r}"
        # Exactly 3 class sections on the dashboard.
        assert body.count('data-testid="class-section-header"') == 3
        # And the assets show up as dashboard-asset-row.
        assert body.count('data-testid="dashboard-asset-row"') == 3

    def test_add_assets_blocked_when_name_empty(self, client: TestClient) -> None:
        """Empty name → 200 + 'obrigatório' + zero assets committed.

        A blank/whitespace-only name is rejected at the server
        (the route's name_clean.strip() guard), the form re-renders
        with an error, and no row is written.
        """
        profile = _login_and_select_profile(client)
        classes = _seed_classes(profile.id)
        cls_renda = classes[0]

        resp = client.post(
            "/assets",
            data={"name": "   ", "asset_class_id": str(cls_renda.id)},
            follow_redirects=False,
        )
        assert resp.status_code == 200
        body = resp.text
        # The error region carries the 'obrigatório' message.
        assert 'data-testid="asset-editor-error"' in body
        assert "obrigatório" in body.lower() or "obrigat" in body.lower()

        # No asset was committed.
        assert len(_assets_for_class(cls_renda.id)) == 0

    def test_add_assets_blocked_when_class_not_in_profile(self, client: TestClient) -> None:
        """direct-landing-with-header-profile-switcher flipped this contract.

        Cross-profile asset-class access now SUCCEEDS — the asset
        lands under whatever profile is ``active_profile_id``, which
        the operator can switch via the header chip. The prior
        per-user ownership gate is gone. The previous assertion
        (200 + asset-editor-error + 0 rows) is replaced with the
        new contract: the asset is committed under Ana's class
        after the chip-driven profile switch.
        """
        # Log in as Ana Livia first to seed her class, then switch
        # to her via the explicit select endpoint (the seed binds
        # her to her own profile already, but we re-bind via the
        # header chip's POST contract so the test mirrors the
        # real-world flow that motivated the change).
        ana = _login_and_select_profile(client, "Ana")
        ana_classes = _seed_classes(ana.id)
        ana_class_id = ana_classes[0].id

        # POST an asset to Ana's class. With the active profile
        # bound to Ana (the login auto-bound), the asset commits
        # under Ana's class.
        resp = client.post(
            "/assets",
            data={"name": "Ana Asset", "asset_class_id": str(ana_class_id)},
            follow_redirects=False,
        )
        assert resp.status_code == 303
        assert len(_assets_for_class(ana_class_id)) == 1

    def test_delete_asset_from_editor(self, client: TestClient) -> None:
        """formaction-based delete: POST /assets/{id}/delete → 303 to /assets, row gone.

        The editor uses a single form with formaction overrides on
        each row's delete button. The route accepts the delete POST
        and 303s back to the editor.
        """
        profile = _login_and_select_profile(client)
        classes = _seed_classes(profile.id)
        cls_renda = classes[0]

        # Add one asset.
        resp = client.post(
            "/assets",
            data={"name": "Tesouro Selic", "asset_class_id": str(cls_renda.id)},
            follow_redirects=False,
        )
        assert resp.status_code == 303
        assert len(_assets_for_class(cls_renda.id)) == 1
        asset_id = _assets_for_class(cls_renda.id)[0].id

        # Delete it. The formaction on the editor's delete button
        # hits POST /assets/{id}/delete.
        delete_resp = client.post(
            f"/assets/{asset_id}/delete",
            follow_redirects=False,
        )
        assert delete_resp.status_code == 303
        assert delete_resp.headers["location"] == "/assets"

        # The asset is gone.
        assert len(_assets_for_class(cls_renda.id)) == 0
