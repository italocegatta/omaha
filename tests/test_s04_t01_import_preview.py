"""T01: POST /api/import/preview -- parse CSV and return JSON preview.

Tests the new JSON API endpoint that the import modal step 1 calls.
Covers the 48-row fixture (43 auto + 5 unmatched), edge cases (empty,
oversized, malformed CSV, no positions, profile with no assets), and
verifies the response shape matches what the Alpine modal expects.
"""

from __future__ import annotations

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


def _login_and_select(client: TestClient, profile_id: int = 1) -> None:
    """Log in and select profile 1 (Italo)."""
    client.post(
        "/login",
        data={"username": "Italo", "password": "test-password"},
        follow_redirects=False,
    )
    client.post(f"/profiles/{profile_id}/select", follow_redirects=False)


def _create_asset_classes(profile_id: int) -> dict[str, int]:
    """Create 3 default asset classes for the profile, return {name: id}."""
    from omaha.db import SessionLocal
    from omaha.models import AssetClass

    db = SessionLocal()
    try:
        classes = [
            AssetClass(profile_id=profile_id, name="Renda Fixa", target_pct=50, display_order=0),
            AssetClass(
                profile_id=profile_id, name="Renda Variavel", target_pct=30, display_order=1
            ),
            AssetClass(
                profile_id=profile_id, name="Fundos Imobiliarios", target_pct=20, display_order=2
            ),
        ]
        db.add_all(classes)
        db.commit()
        for c in classes:
            db.refresh(c)
        return {c.name: c.id for c in classes}
    finally:
        db.close()


def _create_matching_asset_classes(profile_id: int) -> dict[str, int]:
    """Create asset classes whose names match sample_broker.csv categories.

    Returns ``{name: id}`` for the created classes ("RF Pós", "Ações").
    Used to validate that ``suggest_class_id`` actually returns the
    matching class id (not None) when the profile's class names
    coincide with the "Minha Categoria" column in the CSV.
    """
    from omaha.db import SessionLocal
    from omaha.models import AssetClass

    db = SessionLocal()
    try:
        classes = [
            AssetClass(profile_id=profile_id, name="RF Pós", target_pct=50, display_order=0),
            AssetClass(profile_id=profile_id, name="Ações", target_pct=50, display_order=1),
        ]
        db.add_all(classes)
        db.commit()
        for c in classes:
            db.refresh(c)
        return {c.name: c.id for c in classes}
    finally:
        db.close()


def _create_assets(class_map: dict[str, int], names: list[tuple[str, str]]) -> None:
    """Create assets in the given class.

    ``names`` is a list of ``(class_name, asset_name)`` tuples.
    """
    from omaha.db import SessionLocal
    from omaha.models import Asset

    db = SessionLocal()
    try:
        class_counts: dict[int, int] = {}
        for class_name, asset_name in names:
            class_id = class_map[class_name]
            order = class_counts.get(class_id, 0)
            db.add(
                Asset(
                    asset_class_id=class_id,
                    name=asset_name,
                    display_order=order,
                )
            )
            class_counts[class_id] = order + 1
        db.commit()
    finally:
        db.close()


def _read_fixture(name: str) -> bytes:
    """Read a fixture file as bytes."""
    path = FIXTURE_DIR / name
    return path.read_bytes()


# 43 asset names that will auto-match from the fixture.
# These are the first 43 ticker names in sample_broker.csv.
_AUTO_MATCH_NAMES: list[tuple[str, str]] = [
    ("Renda Variavel", "PETR4"),
    ("Renda Variavel", "VALE3"),
    ("Renda Variavel", "ITUB4"),
    ("Renda Variavel", "BBDC4"),
    ("Renda Variavel", "ABEV3"),
    ("Renda Variavel", "MGLU3"),
    ("Renda Variavel", "BBAS3"),
    ("Renda Variavel", "WEGE3"),
    ("Renda Variavel", "RENT3"),
    ("Renda Variavel", "LREN3"),
    ("Renda Variavel", "B3SA3"),
    ("Renda Variavel", "SUZB3"),
    ("Renda Variavel", "CSAN3"),
    ("Renda Variavel", "PETR3"),
    ("Renda Variavel", "VBBR3"),
    ("Renda Variavel", "PRIO3"),
    ("Renda Variavel", "IVVB11"),
    ("Renda Variavel", "IVV"),
    ("Renda Variavel", "VOO"),
    ("Renda Variavel", "QQQ"),
    ("Renda Variavel", "SMH"),
    ("Renda Variavel", "SOXX"),
    ("Renda Variavel", "VTI"),
    ("Renda Variavel", "SPY"),
    ("Renda Variavel", "VT"),
    ("Renda Variavel", "HASH11"),
    ("Fundos Imobiliarios", "BTLG11"),
    ("Fundos Imobiliarios", "KNCR11"),
    ("Fundos Imobiliarios", "IRDM11"),
    ("Fundos Imobiliarios", "XPML11"),
    ("Fundos Imobiliarios", "VISC11"),
    ("Fundos Imobiliarios", "BRCR11"),
    ("Fundos Imobiliarios", "TORD11"),
    ("Fundos Imobiliarios", "MALL11"),
    ("Fundos Imobiliarios", "DEVA11"),
    ("Fundos Imobiliarios", "RBVA11"),
    ("Fundos Imobiliarios", "VRTA11"),
    ("Fundos Imobiliarios", "BPRP11"),
    ("Fundos Imobiliarios", "PVBI11"),
    ("Fundos Imobiliarios", "HCTR11"),
    ("Fundos Imobiliarios", "XPIN11"),
    ("Renda Fixa", "Tesouro Selic 2029"),
    ("Renda Fixa", "Tesouro IPCA+ 2035"),
]

# 5 fixture rows that will NOT be pre-created (unmatched)
_UNMATCHED_TICKERS = {"MXRF11", "BPAC11", "HGLG11", "XPLG11", "VINO11"}

# Assets that belong to the matching classes ("RF Pós", "Ações").
# Same 43 tickers from _AUTO_MATCH_NAMES — the class they sit in is
# irrelevant for the auto-match step, but the test distributes them
# across the two matching classes so the profile shape looks like a
# real user that named classes after broker categories.
_MATCHING_CLASS_ASSETS: list[tuple[str, str]] = [
    (("Ações", name) if i < 26 else ("RF Pós", name))
    for i, (_, name) in enumerate(_AUTO_MATCH_NAMES)
]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestPostImportPreview:
    """POST /api/import/preview tests."""

    def test_preview_with_fixture_returns_correct_shape(self, client: TestClient) -> None:
        """Upload the 48-row fixture with 43 pre-created assets -> 43 auto + 5 unmatched."""
        _login_and_select(client)
        class_map = _create_asset_classes(1)
        _create_assets(class_map, _AUTO_MATCH_NAMES)

        csv_bytes = _read_fixture("sample_broker.csv")
        resp = client.post(
            "/api/import/preview",
            files={"file": ("sample_broker.csv", csv_bytes, "text/csv")},
        )

        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()

        # Check top-level keys
        assert "preview_id" in data
        assert isinstance(data["preview_id"], int)
        assert data["preview_id"] > 0

        assert "auto_matched" in data
        assert isinstance(data["auto_matched"], list)
        assert (
            len(data["auto_matched"]) == 43
        ), f"Expected 43 auto_matched, got {len(data['auto_matched'])}"

        assert "unmatched" in data
        assert isinstance(data["unmatched"], list)
        assert len(data["unmatched"]) == 5, f"Expected 5 unmatched, got {len(data['unmatched'])}"

        assert "asset_classes" in data
        assert isinstance(data["asset_classes"], list)
        assert len(data["asset_classes"]) == 3

        # Verify auto_matched item shape
        am = data["auto_matched"][0]
        assert "broker_ticker" in am
        assert "name" in am
        assert "qty" in am
        assert "avg_price" in am
        assert "current_price" in am
        assert "asset_id" in am
        assert isinstance(am["asset_id"], int)
        assert "asset_class_id" in am
        assert isinstance(am["asset_class_id"], int)

        # Verify unmatched item shape
        um = data["unmatched"][0]
        assert "broker_ticker" in um
        assert "name" in um
        assert "qty" in um
        assert "avg_price" in um
        assert "current_price" in um
        assert "suggested_category" in um
        assert "suggested_class_id" in um
        # suggested_class_id should be None for these unmatched rows
        # because the test classes (Renda Fixa, Renda Variavel,
        # Fundos Imobiliarios) don't match any CSV category names
        # (Ações, RF Pós, (Não configurado)) via exact/substring/word.
        assert um["suggested_class_id"] is None

        # Verify unmatched tickers are the expected 5
        unmatched_tickers = {u["broker_ticker"] for u in data["unmatched"]}
        assert (
            unmatched_tickers == _UNMATCHED_TICKERS
        ), f"Expected unmatched tickers {_UNMATCHED_TICKERS}, got {unmatched_tickers}"

        # Verify asset_classes item shape
        ac = data["asset_classes"][0]
        assert "id" in ac
        assert "name" in ac
        assert isinstance(ac["id"], int)
        assert isinstance(ac["name"], str)

        # Verify all auto_matched have asset_id values
        for item in data["auto_matched"]:
            assert isinstance(
                item["asset_id"], int
            ), f"Expected int asset_id for {item['broker_ticker']}"

    def test_preview_empty_file_returns_400(self, client: TestClient) -> None:
        """Uploading an empty file returns 400."""
        _login_and_select(client)
        resp = client.post(
            "/api/import/preview",
            files={"file": ("empty.csv", b"", "text/csv")},
        )
        assert resp.status_code == 400
        assert "detail" in resp.json()

    def test_preview_oversized_file_returns_400(self, client: TestClient) -> None:
        """Uploading a file larger than MAX_UPLOAD_BYTES returns 400."""
        _login_and_select(client)
        # 2 MB of zeros
        big_data = b"x" * (2 * 1024 * 1024)
        resp = client.post(
            "/api/import/preview",
            files={"file": ("big.csv", big_data, "text/csv")},
        )
        assert resp.status_code == 400
        assert "detail" in resp.json()

    def test_preview_malformed_csv_returns_400(self, client: TestClient) -> None:
        """Uploading a malformed CSV (non-UTF-8) returns 400."""
        _login_and_select(client)
        # Non-UTF-8 bytes sequence
        resp = client.post(
            "/api/import/preview",
            files={"file": ("bad.csv", b"\xff\xfe\x00\x01", "text/csv")},
        )
        assert resp.status_code == 400
        assert "detail" in resp.json()

    def test_preview_no_positions_returns_400(self, client: TestClient) -> None:
        """A CSV with header but no data rows returns 400."""
        _login_and_select(client)
        header_only = b"Codigo,Ativo,Quantidade,Preco Medio,Preco Atual,Minha Categoria"
        resp = client.post(
            "/api/import/preview",
            files={"file": ("header_only.csv", header_only, "text/csv")},
        )
        assert resp.status_code == 400
        assert "detail" in resp.json()

    def test_preview_empty_csv_returns_400(self, client: TestClient) -> None:
        """A completely empty CSV (no rows at all) returns 400."""
        _login_and_select(client)
        resp = client.post(
            "/api/import/preview",
            files={"file": ("empty.csv", b"", "text/csv")},
        )
        assert resp.status_code == 400

    def test_preview_zero_positions_returns_400(self, client: TestClient) -> None:
        """CSV with banner and header but zero data rows returns 400."""
        _login_and_select(client)
        # Banners + header + total only (no real data rows)
        fake_csv = b"Relatorio\nCodigo,Ativo,Quantidade\nTotal,0,,\n"
        resp = client.post(
            "/api/import/preview",
            files={"file": ("zero.csv", fake_csv, "text/csv")},
        )
        assert resp.status_code == 400
        assert "detail" in resp.json()

    def test_preview_no_assets_returns_all_unmatched(self, client: TestClient) -> None:
        """Profile with no existing assets returns all rows as unmatched."""
        _login_and_select(client)
        _create_asset_classes(1)

        csv_bytes = _read_fixture("sample_broker.csv")
        resp = client.post(
            "/api/import/preview",
            files={"file": ("sample_broker.csv", csv_bytes, "text/csv")},
        )

        assert resp.status_code == 200
        data = resp.json()
        assert len(data["auto_matched"]) == 0
        assert len(data["unmatched"]) == 48
        assert len(data["asset_classes"]) == 3

    def test_preview_requires_authentication(self, client: TestClient) -> None:
        """Unauthenticated request gets redirected."""
        csv_bytes = _read_fixture("sample_broker.csv")
        resp = client.post(
            "/api/import/preview",
            files={"file": ("sample_broker.csv", csv_bytes, "text/csv")},
            follow_redirects=False,
        )
        assert resp.status_code in (303, 307)

    def test_preview_persists_preview(self, client: TestClient) -> None:
        """A successful preview creates an ImportPreview row in the DB."""
        from omaha.db import SessionLocal
        from omaha.models import ImportPreview

        _login_and_select(client)
        class_map = _create_asset_classes(1)
        _create_assets(class_map, _AUTO_MATCH_NAMES)

        csv_bytes = _read_fixture("sample_broker.csv")
        resp = client.post(
            "/api/import/preview",
            files={"file": ("sample_broker.csv", csv_bytes, "text/csv")},
        )

        assert resp.status_code == 200
        preview_id = resp.json()["preview_id"]

        db = SessionLocal()
        try:
            preview = db.get(ImportPreview, preview_id)
            assert preview is not None
            assert preview.profile_id == 1
            assert preview.raw_json is not None
        finally:
            db.close()

    def test_preview_profile_with_no_asset_classes(self, client: TestClient) -> None:
        """Profile with no asset classes returns preview with empty asset_classes list."""
        _login_and_select(client)
        csv_bytes = _read_fixture("sample_broker.csv")
        resp = client.post(
            "/api/import/preview",
            files={"file": ("sample_broker.csv", csv_bytes, "text/csv")},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["asset_classes"] == []

    def test_preview_suggests_class_when_category_matches_class_name(
        self, client: TestClient
    ) -> None:
        """When the profile's class names match CSV categories, ``suggested_class_id`` is filled.

        This covers the happy path that the rest of the suite ignores: the
        default test classes (Renda Fixa / Renda Variavel / Fundos
        Imobiliarios) deliberately do NOT match the broker categories
        in ``sample_broker.csv`` (RF Pós / Ações / (Não configurado)),
        so every other test sees ``suggested_class_id is None`` and
        would still pass if ``suggest_class_id`` were deleted.

        Profile classes here are "RF Pós" and "Ações" — exact names of
        two of the unmatched rows' "Minha Categoria" values — so the
        preview API must return those class ids for MXRF11 and XPLG11,
        and ``None`` for the other three unmatched rows whose
        categories do not match any class.
        """
        _login_and_select(client)
        class_map = _create_matching_asset_classes(1)
        _create_assets(class_map, _MATCHING_CLASS_ASSETS)

        rf_pos_id = class_map["RF Pós"]
        acoes_id = class_map["Ações"]

        csv_bytes = _read_fixture("sample_broker.csv")
        resp = client.post(
            "/api/import/preview",
            files={"file": ("sample_broker.csv", csv_bytes, "text/csv")},
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()

        assert len(data["unmatched"]) == 5, (
            f"Expected 5 unmatched rows, got {len(data['unmatched'])}"
        )

        unmatched_by_ticker = {u["broker_ticker"]: u for u in data["unmatched"]}

        # MXRF11 has category "RF Pós" → exact match with class "RF Pós"
        mxrf = unmatched_by_ticker["MXRF11"]
        assert mxrf["suggested_category"] == "RF Pós"
        assert mxrf["suggested_class_id"] == rf_pos_id, (
            f"MXRF11 should suggest class id {rf_pos_id} (RF Pós), "
            f"got {mxrf['suggested_class_id']}"
        )

        # XPLG11 has category "Ações" → exact match with class "Ações"
        xplg = unmatched_by_ticker["XPLG11"]
        assert xplg["suggested_category"] == "Ações"
        assert xplg["suggested_class_id"] == acoes_id, (
            f"XPLG11 should suggest class id {acoes_id} (Ações), "
            f"got {xplg['suggested_class_id']}"
        )

        # The other three unmatched rows have category "(Não configurado)"
        # and no class with that name exists, so suggested_class_id stays None.
        for ticker in ("BPAC11", "HGLG11", "VINO11"):
            row = unmatched_by_ticker[ticker]
            assert row["suggested_category"] == "(Não configurado)"
            assert row["suggested_class_id"] is None, (
                f"{ticker} should have suggested_class_id=None, "
                f"got {row['suggested_class_id']}"
            )
