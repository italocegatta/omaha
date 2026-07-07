"""T02: GET /api/import/preview/{id} — re-fetch a preview as JSON.

Tests the GET endpoint that lets the modal re-fetch preview data
after a navigation or refresh. Returns the same JSON shape as
POST /api/import/preview. Returns 404 for not-found, expired,
or wrong-profile previews.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURE_DIR = REPO_ROOT / "tests" / "fixtures"

# ---------------------------------------------------------------------------
# Per-test cleanup
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _clean_data() -> None:
    from omaha.db import SessionLocal
    from omaha.models import Asset, AssetClass, ImportPreview, Position
    from tests.conftest import _verify_session_local_is_safe

    # Defense-in-depth (2026-07-07 incident): refuse to wipe if
    # SessionLocal is bound to prod. See tests/conftest.py module-load
    # block for the primary isolation contract.
    _verify_session_local_is_safe()

    db = SessionLocal()
    try:
        db.query(Position).delete()
        db.query(Asset).delete()
        db.query(AssetClass).delete()
        db.query(ImportPreview).delete()
        db.commit()
    finally:
        db.close()
    yield


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


_PROFILE_OWNERS = {1: "Italo", 2: "Ana"}


def _login_and_select(client: TestClient, profile_id: int = 1) -> None:
    """Log in with seed credentials and bind active_profile_id.

    direct-landing-with-header-profile-switcher: ``POST /login``
    auto-binds the logged-in user's own first profile. The
    explicit ``/profiles/{id}/select`` step only runs for
    cross-profile viewing.
    """
    username = _PROFILE_OWNERS.get(profile_id, "Italo")
    client.post(
        "/login",
        data={"username": username, "password": "test-password"},
        follow_redirects=False,
    )
    if _PROFILE_OWNERS.get(profile_id) != username:
        client.post(f"/profiles/{profile_id}/select", follow_redirects=False)


def _create_asset_classes(profile_id: int) -> dict[str, int]:
    from omaha.db import SessionLocal
    from omaha.models import AssetClass

    db = SessionLocal()
    try:
        classes = [
            AssetClass(profile_id=profile_id, name="Renda Fixa", target_pct=50, display_order=0),
            AssetClass(
                profile_id=profile_id, name="Renda Variável", target_pct=30, display_order=1
            ),
            AssetClass(
                profile_id=profile_id, name="Fundos Imobiliários", target_pct=20, display_order=2
            ),
        ]
        db.add_all(classes)
        db.commit()
        for c in classes:
            db.refresh(c)
        return {c.name: c.id for c in classes}
    finally:
        db.close()


def _create_assets(class_map: dict[str, int], names: list[tuple[str, str]]) -> None:
    from omaha.db import SessionLocal
    from omaha.models import Asset

    db = SessionLocal()
    try:
        counts: dict[int, int] = {}
        for class_name, asset_name in names:
            cid = class_map[class_name]
            order = counts.get(cid, 0)
            db.add(Asset(asset_class_id=cid, name=asset_name, display_order=order))
            counts[cid] = order + 1
        db.commit()
    finally:
        db.close()


_AUTO_MATCH_NAMES: list[tuple[str, str]] = [
    ("Renda Variável", "PETR4"),
    ("Renda Variável", "VALE3"),
    ("Renda Variável", "ITUB4"),
    ("Renda Variável", "BBDC4"),
    ("Renda Variável", "ABEV3"),
    ("Renda Variável", "MGLU3"),
    ("Renda Variável", "BBAS3"),
    ("Renda Variável", "WEGE3"),
    ("Renda Variável", "RENT3"),
    ("Renda Variável", "LREN3"),
    ("Renda Variável", "B3SA3"),
    ("Renda Variável", "SUZB3"),
    ("Renda Variável", "CSAN3"),
    ("Renda Variável", "PETR3"),
    ("Renda Variável", "VBBR3"),
    ("Renda Variável", "PRIO3"),
    ("Renda Variável", "IVVB11"),
    ("Renda Variável", "IVV"),
    ("Renda Variável", "VOO"),
    ("Renda Variável", "QQQ"),
    ("Renda Variável", "SMH"),
    ("Renda Variável", "SOXX"),
    ("Renda Variável", "VTI"),
    ("Renda Variável", "SPY"),
    ("Renda Variável", "VT"),
    ("Renda Variável", "HASH11"),
    ("Fundos Imobiliários", "BTLG11"),
    ("Fundos Imobiliários", "KNCR11"),
    ("Fundos Imobiliários", "IRDM11"),
    ("Fundos Imobiliários", "XPML11"),
    ("Fundos Imobiliários", "VISC11"),
    ("Fundos Imobiliários", "BRCR11"),
    ("Fundos Imobiliários", "TORD11"),
    ("Fundos Imobiliários", "MALL11"),
    ("Fundos Imobiliários", "DEVA11"),
    ("Fundos Imobiliários", "RBVA11"),
    ("Fundos Imobiliários", "VRTA11"),
    ("Fundos Imobiliários", "BPRP11"),
    ("Fundos Imobiliários", "PVBI11"),
    ("Fundos Imobiliários", "HCTR11"),
    ("Fundos Imobiliários", "XPIN11"),
    ("Renda Fixa", "Tesouro Selic 2029"),
    ("Renda Fixa", "Tesouro IPCA+ 2035"),
]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestGetImportPreview:
    """GET /api/import/preview/{id} tests."""

    def test_get_preview_returns_correct_shape(self, client: TestClient) -> None:
        """Fetch a preview and verify the response shape matches POST /api/import/preview."""
        _login_and_select(client)
        class_map = _create_asset_classes(1)
        _create_assets(class_map, _AUTO_MATCH_NAMES)

        csv_bytes = (FIXTURE_DIR / "sample_broker.csv").read_bytes()
        post_resp = client.post(
            "/api/import/preview",
            files={"file": ("sample_broker.csv", csv_bytes, "text/csv")},
        )
        preview_id = post_resp.json()["preview_id"]

        resp = client.get(f"/api/import/preview/{preview_id}")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()

        # Same shape as POST /api/import/preview
        assert "preview_id" in data
        assert data["preview_id"] == preview_id
        assert "auto_matched" in data
        assert "unmatched" in data
        assert "asset_classes" in data

        assert len(data["auto_matched"]) == 43
        assert len(data["unmatched"]) == 5
        assert len(data["asset_classes"]) == 3

        # Verify item shapes
        am = data["auto_matched"][0]
        assert "broker_ticker" in am
        assert "name" in am
        assert "qty" in am
        assert "avg_price" in am
        assert "current_price" in am
        assert "asset_id" in am
        assert "asset_class_id" in am
        assert isinstance(am["asset_class_id"], int)

        um = data["unmatched"][0]
        assert "broker_ticker" in um
        assert "name" in um
        assert "qty" in um
        assert "avg_price" in um
        assert "current_price" in um
        assert "suggested_category" in um

        # asset_classes carry color (CSS color string — OKLCH post-F08)
        assert len(data["asset_classes"]) == 3
        from coloraide import Color as _Color

        for ac in data["asset_classes"]:
            assert "color" in ac
            assert isinstance(ac["color"], str)
            _Color(ac["color"])  # parse-check via coloraide

    def test_get_preview_nonexistent_returns_404(self, client: TestClient) -> None:
        """Fetching a non-existent preview returns 404."""
        _login_and_select(client)
        resp = client.get("/api/import/preview/99999")
        assert resp.status_code == 404

    def test_get_preview_expired_returns_404(self, client: TestClient) -> None:
        """Fetching an expired preview returns 404."""
        from omaha.db import SessionLocal
        from omaha.models import ImportPreview

        _login_and_select(client)
        class_map = _create_asset_classes(1)
        _create_assets(class_map, _AUTO_MATCH_NAMES[:5])

        csv_bytes = (FIXTURE_DIR / "sample_broker.csv").read_bytes()
        post_resp = client.post(
            "/api/import/preview",
            files={"file": ("sample_broker.csv", csv_bytes, "text/csv")},
        )
        preview_id = post_resp.json()["preview_id"]

        # Manually expire the preview
        db = SessionLocal()
        try:
            preview = db.get(ImportPreview, preview_id)
            preview.created_at = datetime.now(tz=UTC).replace(tzinfo=None) - timedelta(hours=2)
            db.commit()
        finally:
            db.close()

        resp = client.get(f"/api/import/preview/{preview_id}")
        assert resp.status_code == 404

    def test_get_preview_wrong_profile_returns_404(self, client: TestClient) -> None:
        """Profile 2 cannot fetch a preview belonging to profile 1."""
        _login_and_select(client, profile_id=1)
        class_map = _create_asset_classes(1)
        _create_assets(class_map, _AUTO_MATCH_NAMES[:5])

        csv_bytes = (FIXTURE_DIR / "sample_broker.csv").read_bytes()
        post_resp = client.post(
            "/api/import/preview",
            files={"file": ("sample_broker.csv", csv_bytes, "text/csv")},
        )
        preview_id = post_resp.json()["preview_id"]

        # Switch to profile 2
        _login_and_select(client, profile_id=2)

        resp = client.get(f"/api/import/preview/{preview_id}")
        assert resp.status_code == 404

    def test_get_preview_requires_authentication(self, client: TestClient) -> None:
        """Unauthenticated GET gets redirected."""
        resp = client.get("/api/import/preview/1", follow_redirects=False)
        assert resp.status_code in (303, 307)

    def test_get_preview_reflects_new_assets(self, client: TestClient) -> None:
        """After creating new assets, GET returns updated match counts."""
        _login_and_select(client)
        class_map = _create_asset_classes(1)
        _create_assets(class_map, _AUTO_MATCH_NAMES)

        csv_bytes = (FIXTURE_DIR / "sample_broker.csv").read_bytes()
        post_resp = client.post(
            "/api/import/preview",
            files={"file": ("sample_broker.csv", csv_bytes, "text/csv")},
        )
        preview_id = post_resp.json()["preview_id"]

        # Before adding more assets: 43 auto, 5 unmatched
        resp_before = client.get(f"/api/import/preview/{preview_id}")
        assert len(resp_before.json()["auto_matched"]) == 43
        assert len(resp_before.json()["unmatched"]) == 5

        # Add assets for the unmatched tickers
        _create_assets(
            class_map,
            [
                ("Fundos Imobiliários", "MXRF11"),
                ("Renda Variável", "BPAC11"),
                ("Fundos Imobiliários", "HGLG11"),
                ("Renda Variável", "XPLG11"),
                ("Fundos Imobiliários", "VINO11"),
            ],
        )

        # Now GET should show 48 auto, 0 unmatched
        resp_after = client.get(f"/api/import/preview/{preview_id}")
        assert len(resp_after.json()["auto_matched"]) == 48
        assert len(resp_after.json()["unmatched"]) == 0

    def test_get_preview_no_asset_classes(self, client: TestClient) -> None:
        """Preview with no asset classes returns empty asset_classes list."""
        _login_and_select(client)

        csv_bytes = (FIXTURE_DIR / "sample_broker.csv").read_bytes()
        post_resp = client.post(
            "/api/import/preview",
            files={"file": ("sample_broker.csv", csv_bytes, "text/csv")},
        )
        preview_id = post_resp.json()["preview_id"]

        resp = client.get(f"/api/import/preview/{preview_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["asset_classes"] == []

    def test_get_preview_after_commit_returns_404(self, client: TestClient) -> None:
        """After a commit deletes the preview, GET returns 404."""
        _login_and_select(client)
        class_map = _create_asset_classes(1)
        _create_assets(class_map, _AUTO_MATCH_NAMES[:5])

        csv_bytes = (FIXTURE_DIR / "sample_broker.csv").read_bytes()
        post_resp = client.post(
            "/api/import/preview",
            files={"file": ("sample_broker.csv", csv_bytes, "text/csv")},
        )
        preview_id = post_resp.json()["preview_id"]

        # Commit to delete the preview
        client.post(
            "/api/import/commit",
            json={"preview_id": preview_id, "assignments": []},
        )

        resp = client.get(f"/api/import/preview/{preview_id}")
        assert resp.status_code == 404
