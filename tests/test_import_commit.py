"""T02: POST /api/import/commit — commit a preview to assets + positions.

Tests the commit JSON endpoint that creates Asset rows for unmatched
positions (or reuses existing ones), upserts Position rows, deletes
the preview, and returns {upserted, created}.

Covers: full commit with auto_matched + user-assigned unmatched rows,
partial commit (some unmatched without assignments), expired preview,
missing preview, invalid class_id, preview from wrong profile.
"""

from __future__ import annotations

from datetime import UTC
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
    """Wipe asset_classes, assets, positions, and import_previews before each test."""
    from omaha.db import SessionLocal
    from omaha.models import Asset, AssetClass, ImportPreview, Position

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


def _login_and_select(client: TestClient, profile_id: int = 1, username: str = "Italo") -> None:
    """Log in as ``username`` and select the given profile id.

    Each seed user owns exactly one profile, so cross-profile tests
    pass ``username="Ana"`` to reach profile id 2.
    """
    client.post(
        "/login",
        data={"username": username, "password": "test-password"},
        follow_redirects=False,
    )
    client.post(f"/profiles/{profile_id}/select", follow_redirects=False)


def _create_asset_classes(profile_id: int) -> dict[str, int]:
    """Return {name: id} for 3 default classes."""
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
    """Create assets from (class_name, asset_name) pairs."""
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


def _create_preview(profile_id: int, raw_json: str | None = None) -> int:
    """Create an ImportPreview row and return its id."""
    import json

    from omaha.db import SessionLocal
    from omaha.models import ImportPreview

    if raw_json is None:
        raw_json = json.dumps(
            [
                {
                    "broker_ticker": "TEST4",
                    "name": "TEST4",
                    "qty": "10",
                    "avg_price": "50.00",
                    "current_price": "55.00",
                    "row_index": 1,
                    "suggested_category": None,
                }
            ],
            ensure_ascii=False,
        )

    db = SessionLocal()
    try:
        preview = ImportPreview(
            profile_id=profile_id,
            raw_json=raw_json,
        )
        db.add(preview)
        db.commit()
        db.refresh(preview)
        return preview.id
    finally:
        db.close()


def _create_preview_with_full_csv(profile_id: int) -> int:
    """Create a preview using the sample_broker CSV and return its id."""
    import json

    from omaha.csv_import import parse_positions
    from omaha.db import SessionLocal
    from omaha.models import ImportPreview

    csv_path = FIXTURE_DIR / "sample_broker.csv"
    text = csv_path.read_text(encoding="utf-8")
    raw = parse_positions(text)
    raw_dicts = [
        {
            "broker_ticker": r.broker_ticker,
            "name": r.name,
            "qty": str(r.qty),
            "avg_price": str(r.avg_price),
            "current_price": str(r.current_price),
            "row_index": r.row_index,
            "suggested_category": r.suggested_category,
        }
        for r in raw
    ]

    db = SessionLocal()
    try:
        preview = ImportPreview(
            profile_id=profile_id,
            raw_json=json.dumps(raw_dicts, ensure_ascii=False),
        )
        db.add(preview)
        db.commit()
        db.refresh(preview)
        return preview.id
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


class TestPostImportCommit:
    """POST /api/import/commit tests."""

    def test_commit_auto_matched_only(self, client: TestClient) -> None:
        """Commit a preview where all rows are auto-matched (no unmatched assignments)."""
        _login_and_select(client)
        class_map = _create_asset_classes(1)
        _create_assets(class_map, _AUTO_MATCH_NAMES)

        # Create preview first via the upload endpoint
        csv_bytes = (FIXTURE_DIR / "sample_broker.csv").read_bytes()
        preview_resp = client.post(
            "/api/import/preview",
            files={"file": ("sample_broker.csv", csv_bytes, "text/csv")},
        )
        preview_id = preview_resp.json()["preview_id"]

        resp = client.post(
            "/api/import/commit",
            json={
                "preview_id": preview_id,
                "assignments": [],
            },
        )

        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert "upserted" in data
        assert "created" in data
        # 43 auto-matched rows should be upserted, 0 created (all assets pre-exist)
        assert data["upserted"] == 43
        assert data["created"] == 0

    def test_commit_with_unmatched_assignments(self, client: TestClient) -> None:
        """Commit with assignments for all 5 unmatched rows creates new Assets + positions."""
        _login_and_select(client)
        class_map = _create_asset_classes(1)
        _create_assets(class_map, _AUTO_MATCH_NAMES)

        csv_bytes = (FIXTURE_DIR / "sample_broker.csv").read_bytes()
        preview_resp = client.post(
            "/api/import/preview",
            files={"file": ("sample_broker.csv", csv_bytes, "text/csv")},
        )
        preview_id = preview_resp.json()["preview_id"]

        # Assign each unmatched ticker to a class
        assignments = [
            {
                "broker_ticker": "MXRF11",
                "class_id": class_map["Fundos Imobiliários"],
                "asset_name": "MXRF11",
            },
            {
                "broker_ticker": "BPAC11",
                "class_id": class_map["Renda Variável"],
                "asset_name": "BPAC11",
            },
            {
                "broker_ticker": "HGLG11",
                "class_id": class_map["Fundos Imobiliários"],
                "asset_name": "HGLG11",
            },
            {
                "broker_ticker": "XPLG11",
                "class_id": class_map["Renda Variável"],
                "asset_name": "XPLG11",
            },
            {
                "broker_ticker": "VINO11",
                "class_id": class_map["Fundos Imobiliários"],
                "asset_name": "VINO11",
            },
        ]

        resp = client.post(
            "/api/import/commit",
            json={
                "preview_id": preview_id,
                "assignments": assignments,
            },
        )

        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data["upserted"] == 48  # 43 auto + 5 unmatched
        assert data["created"] == 5

    def test_commit_creates_assets_and_positions(self, client: TestClient) -> None:
        """Verify DB state after commit: Asset and Position rows exist."""
        from omaha.db import SessionLocal
        from omaha.models import Asset, Position

        _login_and_select(client)
        class_map = _create_asset_classes(1)
        _create_assets(class_map, _AUTO_MATCH_NAMES)

        csv_bytes = (FIXTURE_DIR / "sample_broker.csv").read_bytes()
        preview_resp = client.post(
            "/api/import/preview",
            files={"file": ("sample_broker.csv", csv_bytes, "text/csv")},
        )
        preview_id = preview_resp.json()["preview_id"]

        assignments = [
            {
                "broker_ticker": "MXRF11",
                "class_id": class_map["Fundos Imobiliários"],
                "asset_name": "MXRF11",
            },
            {
                "broker_ticker": "BPAC11",
                "class_id": class_map["Renda Variável"],
                "asset_name": "BPAC11",
            },
            {
                "broker_ticker": "HGLG11",
                "class_id": class_map["Fundos Imobiliários"],
                "asset_name": "HGLG11",
            },
            {
                "broker_ticker": "XPLG11",
                "class_id": class_map["Renda Variável"],
                "asset_name": "XPLG11",
            },
            {
                "broker_ticker": "VINO11",
                "class_id": class_map["Fundos Imobiliários"],
                "asset_name": "VINO11",
            },
        ]

        resp = client.post(
            "/api/import/commit",
            json={"preview_id": preview_id, "assignments": assignments},
        )
        assert resp.status_code == 200

        db = SessionLocal()
        try:
            # Check assets count: 43 original + 5 new = 48
            assets = db.query(Asset).all()
            assert len(assets) == 48

            # Check positions count: 48
            positions = db.query(Position).all()
            assert len(positions) == 48

            # Verify the new assets were created
            new_asset_names = {
                a.name
                for a in assets
                if a.name in {"MXRF11", "BPAC11", "HGLG11", "XPLG11", "VINO11"}
            }
            assert len(new_asset_names) == 5
        finally:
            db.close()

    def test_commit_reuses_existing_assets(self, client: TestClient) -> None:
        """Committing with an asset that already exists reuses it (no duplicate)."""
        _login_and_select(client)
        class_map = _create_asset_classes(1)
        # Create assets including the normally-unmatched ones
        all_names = _AUTO_MATCH_NAMES + [
            ("Fundos Imobiliários", "MXRF11"),
            ("Renda Variável", "BPAC11"),
            ("Fundos Imobiliários", "HGLG11"),
            ("Renda Variável", "XPLG11"),
            ("Fundos Imobiliários", "VINO11"),
        ]
        _create_assets(class_map, all_names)

        csv_bytes = (FIXTURE_DIR / "sample_broker.csv").read_bytes()
        preview_resp = client.post(
            "/api/import/preview",
            files={"file": ("sample_broker.csv", csv_bytes, "text/csv")},
        )
        preview_id = preview_resp.json()["preview_id"]

        # All 48 rows are now auto-matched (all assets exist)
        resp = client.post(
            "/api/import/commit",
            json={"preview_id": preview_id, "assignments": []},
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["upserted"] == 48
        assert data["created"] == 0

    def test_commit_expired_preview_returns_400(self, client: TestClient) -> None:
        """Committing an expired preview returns 400."""
        from datetime import datetime, timedelta

        from omaha.db import SessionLocal
        from omaha.models import ImportPreview

        _login_and_select(client)
        class_map = _create_asset_classes(1)
        _create_assets(class_map, _AUTO_MATCH_NAMES[:5])

        # Create a preview and manually set created_at to 2 hours ago
        csv_bytes = (FIXTURE_DIR / "sample_broker.csv").read_bytes()
        preview_resp = client.post(
            "/api/import/preview",
            files={"file": ("sample_broker.csv", csv_bytes, "text/csv")},
        )
        preview_id = preview_resp.json()["preview_id"]

        db = SessionLocal()
        try:
            preview = db.get(ImportPreview, preview_id)
            preview.created_at = datetime.now(tz=UTC).replace(tzinfo=None) - timedelta(hours=2)
            db.commit()
        finally:
            db.close()

        resp = client.post(
            "/api/import/commit",
            json={"preview_id": preview_id, "assignments": []},
        )
        assert resp.status_code == 400
        assert "detail" in resp.json()

    def test_commit_nonexistent_preview_returns_400(self, client: TestClient) -> None:
        """Committing a preview that does not exist returns 400."""
        _login_and_select(client)
        resp = client.post(
            "/api/import/commit",
            json={"preview_id": 99999, "assignments": []},
        )
        assert resp.status_code == 400
        assert "detail" in resp.json()

    def test_commit_invalid_class_id_skips_row(self, client: TestClient) -> None:
        """An unmatched row with a non-existent class_id is silently skipped."""
        from omaha.db import SessionLocal
        from omaha.models import Asset, Position

        _login_and_select(client)
        class_map = _create_asset_classes(1)
        _create_assets(class_map, _AUTO_MATCH_NAMES[:5])

        csv_bytes = (FIXTURE_DIR / "sample_broker.csv").read_bytes()
        preview_resp = client.post(
            "/api/import/preview",
            files={"file": ("sample_broker.csv", csv_bytes, "text/csv")},
        )
        preview_id = preview_resp.json()["preview_id"]

        resp = client.post(
            "/api/import/commit",
            json={
                "preview_id": preview_id,
                "assignments": [
                    {"broker_ticker": "MXRF11", "class_id": 999, "asset_name": "MXRF11"},
                ],
            },
        )
        # Invalid class_id is silently skipped, not an error.
        assert resp.status_code == 200
        data = resp.json()
        # 5 auto-matched rows (no assignment → keep original class)
        assert data["upserted"] == 5
        assert data["created"] == 0

        db = SessionLocal()
        try:
            # No new assets created (MXRF11 was skipped due to invalid class)
            assets = db.query(Asset).all()
            assert len(assets) == 5  # only the pre-created 5
            # MXRF11 position should NOT exist
            mxrf_positions = db.query(Position).filter(Position.broker_ticker == "MXRF11").count()
            assert mxrf_positions == 0
        finally:
            db.close()

    def test_commit_skips_rows_without_class_id(self, client: TestClient) -> None:
        """Rows with empty class_id in assignments are not imported."""
        from omaha.db import SessionLocal
        from omaha.models import Asset, Position

        _login_and_select(client)
        class_map = _create_asset_classes(1)
        # Create only 5 assets so 43 rows are unmatched
        _create_assets(class_map, _AUTO_MATCH_NAMES[:5])

        csv_bytes = (FIXTURE_DIR / "sample_broker.csv").read_bytes()
        preview_resp = client.post(
            "/api/import/preview",
            files={"file": ("sample_broker.csv", csv_bytes, "text/csv")},
        )
        preview_id = preview_resp.json()["preview_id"]

        # Send assignments that include empty class_id for some rows
        assignments = [
            # MXRF11 and BPAC11 have valid class_id → should be imported
            {
                "broker_ticker": "MXRF11",
                "class_id": class_map["Fundos Imobiliários"],
                "asset_name": "MXRF11",
            },
            {
                "broker_ticker": "BPAC11",
                "class_id": class_map["Renda Variável"],
                "asset_name": "BPAC11",
            },
            # HGLG11 has null class_id → skipped
            {"broker_ticker": "HGLG11", "class_id": None, "asset_name": "HGLG11"},
            # XPLG11 has no assignment at all → skipped
        ]

        resp = client.post(
            "/api/import/commit",
            json={"preview_id": preview_id, "assignments": assignments},
        )
        assert resp.status_code == 200
        data = resp.json()
        # 5 auto-matched (no assignment → keep original) + 2 with valid class
        assert data["upserted"] == 7
        assert data["created"] == 2

        db = SessionLocal()
        try:
            # 5 pre-existing + 2 new = 7 assets
            assets = db.query(Asset).all()
            assert len(assets) == 7
            # MXRF11 and BPAC11 have positions; HGLG11 and XPLG11 do not
            for ticker in ("MXRF11", "BPAC11"):
                count = db.query(Position).filter(Position.broker_ticker == ticker).count()
                assert count == 1, f"{ticker} should have 1 position"
            for ticker in ("HGLG11", "XPLG11"):
                count = db.query(Position).filter(Position.broker_ticker == ticker).count()
                assert count == 0, f"{ticker} should NOT have a position"
        finally:
            db.close()

    def test_commit_deletes_preview(self, client: TestClient) -> None:
        """After a successful commit, the preview row is deleted from the DB."""
        from omaha.db import SessionLocal
        from omaha.models import ImportPreview

        _login_and_select(client)
        class_map = _create_asset_classes(1)
        _create_assets(class_map, _AUTO_MATCH_NAMES[:5])

        preview_id = _create_preview_with_full_csv(1)

        resp = client.post(
            "/api/import/commit",
            json={"preview_id": preview_id, "assignments": []},
        )
        assert resp.status_code == 200

        db = SessionLocal()
        try:
            preview = db.get(ImportPreview, preview_id)
            assert preview is None
        finally:
            db.close()

    def test_commit_requires_authentication(self, client: TestClient) -> None:
        """Unauthenticated commit request gets redirected."""
        resp = client.post(
            "/api/import/commit",
            json={"preview_id": 1, "assignments": []},
            follow_redirects=False,
        )
        assert resp.status_code in (303, 307)

    def test_commit_second_profile_cannot_access_preview(self, client: TestClient) -> None:
        """Profile 2 cannot commit a preview belonging to profile 1."""
        _login_and_select(client, profile_id=1)
        class_map = _create_asset_classes(1)
        _create_assets(class_map, _AUTO_MATCH_NAMES[:5])
        preview_id = _create_preview_with_full_csv(1)

        # Switch to profile 2 (Ana). Re-authenticate as Ana since
        # each seed user owns only their namesake profile.
        _login_and_select(client, profile_id=2, username="Ana")

        resp = client.post(
            "/api/import/commit",
            json={"preview_id": preview_id, "assignments": []},
        )
        assert resp.status_code == 400
