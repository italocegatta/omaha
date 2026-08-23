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
        assert len(data["auto_matched"]) == 43, (
            f"Expected 43 auto_matched, got {len(data['auto_matched'])}"
        )

        assert "unmatched" in data
        assert isinstance(data["unmatched"], list)
        assert len(data["unmatched"]) == 5, f"Expected 5 unmatched, got {len(data['unmatched'])}"

        assert "asset_classes" in data
        assert isinstance(data["asset_classes"], list)
        assert len(data["asset_classes"]) == 3

        assert set(data["triage"]) == {"new", "changed", "unchanged", "absent"}
        assert len(data["triage"]["new"]) == 5
        assert len(data["triage"]["changed"]) == 43
        assert data["triage"]["unchanged"] == []
        assert data["triage"]["absent"] == []
        assert len(
            data["triage"]["new"] + data["triage"]["changed"] + data["triage"]["unchanged"]
        ) == len(data["auto_matched"]) + len(data["unmatched"])

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
        assert unmatched_tickers == _UNMATCHED_TICKERS, (
            f"Expected unmatched tickers {_UNMATCHED_TICKERS}, got {unmatched_tickers}"
        )

        # asset-trade-flags: every preview row carries the three
        # per-asset trade-control fields. For auto-matched rows the
        # value mirrors the Asset (server_default = True/True/BRL on
        # the seeded rows); for unmatched rows the value is the
        # project default.
        for row in data["auto_matched"]:
            assert "buy_enabled" in row
            assert "sell_enabled" in row
            assert "currency_code" in row
            assert row["buy_enabled"] is True
            assert row["sell_enabled"] is True
            assert row["currency_code"] == "BRL"
        for row in data["unmatched"]:
            assert "buy_enabled" in row
            assert "sell_enabled" in row
            assert "currency_code" in row
            assert row["buy_enabled"] is True
            assert row["sell_enabled"] is True
            assert row["currency_code"] == "BRL"

        # Verify asset_classes item shape
        ac = data["asset_classes"][0]
        assert "id" in ac
        assert "name" in ac
        assert "color" in ac
        assert isinstance(ac["id"], int)
        assert isinstance(ac["name"], str)
        assert isinstance(ac["color"], str)
        # F08: color is OKLCH (post-F08) — parses via coloraide.
        # Pre-F08 contract was hex `#xxxxxx` / `#xxx`. Accept any
        # CSS color string that coloraide can parse.
        from coloraide import Color as _Color

        _Color(ac["color"])  # raises ValueError if unparseable

        for item in data["asset_classes"]:
            assert "color" in item
            assert isinstance(item["color"], str)
            _Color(item["color"])  # parse-check each

        # Verify all auto_matched have asset_id values
        for item in data["auto_matched"]:
            assert isinstance(item["asset_id"], int), (
                f"Expected int asset_id for {item['broker_ticker']}"
            )

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
            import json

            stored = json.loads(preview.raw_json)
            assert isinstance(stored, dict)
            assert len(stored["rows"]) == 48
            assert len(stored["baseline"]) == 48
            assert stored["baseline"][0]["asset_id"] is not None
        finally:
            db.close()

    def test_preview_triage_is_baseline_sourced_and_deterministic(self, client: TestClient) -> None:
        """Triage stays tied to state captured before later portfolio edits."""
        from decimal import Decimal

        from omaha.db import SessionLocal
        from omaha.models import Asset, AssetClass, Position

        _login_and_select(client)
        db = SessionLocal()
        try:
            asset_class = AssetClass(profile_id=1, name="Ações", target_pct=100, display_order=0)
            db.add(asset_class)
            db.flush()
            assets = {
                name: Asset(asset_class_id=asset_class.id, name=name, display_order=index)
                for index, name in enumerate(("Árvore", "AZUL", "arara"))
            }
            db.add_all(assets.values())
            db.flush()
            for name, ticker, qty in (
                ("Árvore", "ARVE3", "100"),
                ("AZUL", "AZUL3", "75"),
                ("arara", "ARAR3", "10"),
            ):
                db.add(
                    Position(
                        asset_id=assets[name].id,
                        broker_ticker=ticker,
                        qty=Decimal(qty),
                        avg_price=Decimal("20"),
                        current_price=Decimal("25"),
                        total_invested=Decimal(qty) * Decimal("20"),
                        total_current=Decimal(qty) * Decimal("25"),
                    )
                )
            db.commit()
        finally:
            db.close()

        csv_bytes = (
            b"Codigo,Ativo,Quantidade,Preco Medio,Preco Atual,Total investido,Total atual\n"
            b"AZUL3,AZUL,60,20,25,1200,1500\n"
            b"ARAR3,arara,10,20,25,200,250\n"
            b"ARVE3,arvore,100,20,25,2000,2500\n"
            b"NOVO3,Novo,4,10,12,40,48\n"
        )
        response = client.post(
            "/api/import/preview",
            files={"file": ("triage.csv", csv_bytes, "text/csv")},
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert [row["name"] for row in data["triage"]["changed"]] == ["arvore", "AZUL"]
        assert [row["name"] for row in data["triage"]["unchanged"]] == ["arara"]
        assert [row["name"] for row in data["triage"]["new"]] == ["Novo"]
        arve_fields = {
            field["id"]: field for field in data["triage"]["changed"][0]["changed_fields"]
        }
        assert arve_fields["asset.name"]["previous_display"] == "Árvore"
        assert "qty" not in arve_fields

        preview_id = data["preview_id"]
        db = SessionLocal()
        try:
            db.query(Position).filter(Position.broker_ticker == "AZUL3").update(
                {"qty": Decimal("999")}
            )
            db.commit()
        finally:
            db.close()

        refreshed = client.get(f"/api/import/preview/{preview_id}")
        assert refreshed.status_code == 200
        refreshed_data = refreshed.json()
        refreshed_arara = refreshed_data["triage"]["unchanged"]
        assert [row["name"] for row in refreshed_arara] == ["arara"]
        azul = next(
            row for row in refreshed_data["triage"]["changed"] if row["broker_ticker"] == "AZUL3"
        )
        azul_qty = next(field for field in azul["changed_fields"] if field["id"] == "qty")
        assert azul_qty["previous_value"] == "75.00000000"
        assert azul_qty["previous_display"] == "75,0"

    def test_preview_diff_display_formats_previous_money_without_fabricating_zero(
        self, client: TestClient
    ) -> None:
        """Money disclosures use integer Brazilian formatting and preserve prior state."""
        from decimal import Decimal

        from omaha.db import SessionLocal
        from omaha.models import Asset, AssetClass, Position

        _login_and_select(client)
        db = SessionLocal()
        try:
            asset_class = AssetClass(profile_id=1, name="Ações", target_pct=100, display_order=0)
            db.add(asset_class)
            db.flush()
            asset = Asset(asset_class_id=asset_class.id, name="Fundo", display_order=0)
            db.add(asset)
            db.flush()
            db.add(
                Position(
                    asset_id=asset.id,
                    broker_ticker="FUND11",
                    qty=Decimal("10"),
                    avg_price=Decimal("100"),
                    current_price=Decimal("120"),
                    total_invested=Decimal("100000"),
                    total_current=Decimal("116615.5300"),
                )
            )
            db.commit()
        finally:
            db.close()

        response = client.post(
            "/api/import/preview",
            files={
                "file": (
                    "money.csv",
                    b"Codigo,Ativo,Quantidade,Preco Medio,Preco Atual,Total investido,Total atual\n"
                    b"FUND11,Fundo,10,100,120,100000,120000\n",
                    "text/csv",
                )
            },
        )
        assert response.status_code == 200, response.text
        field = next(
            field
            for field in response.json()["triage"]["changed"][0]["changed_fields"]
            if field["id"] == "total_current"
        )
        assert field["previous_value"] == "116615.5300"
        assert field["previous_display"] == "R$ 116.616"

    def test_absent_rows_are_profile_scoped_read_only_and_not_committed(
        self, client: TestClient
    ) -> None:
        """Portfolio-only rows are visible but never enter commit assignments."""
        from decimal import Decimal

        from omaha.db import SessionLocal
        from omaha.models import Asset, AssetClass, Position

        _login_and_select(client)
        db = SessionLocal()
        try:
            active_class = AssetClass(profile_id=1, name="Ativos", target_pct=100, display_order=0)
            foreign_class = AssetClass(profile_id=2, name="Fora", target_pct=100, display_order=0)
            db.add_all([active_class, foreign_class])
            db.flush()
            present = Asset(asset_class_id=active_class.id, name="Presente", display_order=0)
            absent_z = Asset(asset_class_id=active_class.id, name="Zeta", display_order=1)
            absent_a = Asset(asset_class_id=active_class.id, name="Alfa", display_order=2)
            foreign = Asset(asset_class_id=foreign_class.id, name="Fora do perfil", display_order=0)
            db.add_all([present, absent_z, absent_a, foreign])
            db.flush()
            db.add_all(
                [
                    Position(
                        asset_id=absent_z.id,
                        broker_ticker="ZET3",
                        qty=Decimal("7"),
                        avg_price=Decimal("11"),
                        current_price=Decimal("12"),
                        total_invested=Decimal("77"),
                        total_current=Decimal("84"),
                    ),
                    Position(
                        asset_id=absent_a.id,
                        broker_ticker="ALF3",
                        qty=Decimal("3"),
                        avg_price=Decimal("20"),
                        current_price=Decimal("22"),
                        total_invested=Decimal("60"),
                        total_current=Decimal("66"),
                    ),
                    Position(
                        asset_id=foreign.id,
                        broker_ticker="FOR3",
                        qty=Decimal("99"),
                        avg_price=Decimal("1"),
                        current_price=Decimal("1"),
                        total_invested=Decimal("99"),
                        total_current=Decimal("99"),
                    ),
                ]
            )
            db.commit()
            active_class_id = active_class.id
            absent_ids = {absent_a.id, absent_z.id}
        finally:
            db.close()

        response = client.post(
            "/api/import/preview",
            files={
                "file": (
                    "absent.csv",
                    b"Codigo,Ativo,Quantidade,Preco Medio,Preco Atual,Total investido,Total atual\n"
                    b"PRE3,Presente,4,10,12,40,48\n",
                    "text/csv",
                )
            },
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert set(data["triage"]) == {"new", "changed", "unchanged", "absent"}
        assert [row["name"] for row in data["triage"]["absent"]] == ["Alfa", "Zeta"]
        assert {row["asset_id"] for row in data["triage"]["absent"]} == absent_ids
        assert all(row["read_only"] is True for row in data["triage"]["absent"])
        assert all(row["committable"] is False for row in data["triage"]["absent"])
        assert all(row["name"] != "Fora do perfil" for row in data["triage"]["absent"])

        preview_id = data["preview_id"]
        commit = client.post(
            "/api/import/commit",
            json={
                "preview_id": preview_id,
                "assignments": [
                    {
                        "broker_ticker": "PRE3",
                        "class_id": active_class_id,
                        "asset_name": "Presente",
                    }
                ],
            },
        )
        assert commit.status_code == 200, commit.text

        db = SessionLocal()
        try:
            absent_positions = (
                db.query(Position)
                .filter(Position.asset_id.in_(absent_ids))
                .order_by(Position.broker_ticker)
                .all()
            )
            assert [
                (position.broker_ticker, str(position.qty)) for position in absent_positions
            ] == [
                ("ALF3", "3.00000000"),
                ("ZET3", "7.00000000"),
            ]
            assert db.query(Asset).filter(Asset.id.in_(absent_ids)).count() == 2
        finally:
            db.close()

    def test_absent_uses_normalized_name_even_when_ticker_differs(self, client: TestClient) -> None:
        """A batch name match prevents Ausentes regardless of broker ticker."""
        from decimal import Decimal

        from omaha.db import SessionLocal
        from omaha.models import Asset, AssetClass, Position

        _login_and_select(client)
        db = SessionLocal()
        try:
            asset_class = AssetClass(profile_id=1, name="Cripto", target_pct=100, display_order=0)
            db.add(asset_class)
            db.flush()
            eth = Asset(asset_class_id=asset_class.id, name="ETH", display_order=0)
            btc = Asset(asset_class_id=asset_class.id, name="BTC", display_order=1)
            db.add_all([eth, btc])
            db.flush()
            db.add_all(
                [
                    Position(
                        asset_id=eth.id,
                        broker_ticker="ETH-OLD",
                        qty=Decimal("1"),
                        avg_price=Decimal("10"),
                        current_price=Decimal("12"),
                        total_invested=Decimal("10"),
                        total_current=Decimal("12"),
                    ),
                    Position(
                        asset_id=btc.id,
                        broker_ticker="BTC-OLD",
                        qty=Decimal("2"),
                        avg_price=Decimal("20"),
                        current_price=Decimal("22"),
                        total_invested=Decimal("40"),
                        total_current=Decimal("44"),
                    ),
                ]
            )
            db.commit()
        finally:
            db.close()

        response = client.post(
            "/api/import/preview",
            files={
                "file": (
                    "eth.csv",
                    b"Codigo,Ativo,Quantidade,Preco Medio,Preco Atual,Total investido,Total atual\n"
                    b"ETH-NEW,ETH,3,10,12,30,36\n",
                    "text/csv",
                )
            },
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert [row["name"] for row in data["triage"]["absent"]] == ["BTC"]
        assert [row["name"] for row in data["triage"]["changed"]] == ["ETH"]

    def test_legacy_raw_list_preview_remains_reviewable(self, client: TestClient) -> None:
        """Pre-F65 raw-list previews use response-time compatibility fallback."""
        import json

        from omaha.db import SessionLocal
        from omaha.models import ImportPreview

        _login_and_select(client)
        _create_asset_classes(1)
        csv_bytes = b"Codigo,Ativo,Quantidade,Preco Medio,Preco Atual\nNOVO3,Novo,4,10,12\n"
        response = client.post(
            "/api/import/preview",
            files={"file": ("legacy.csv", csv_bytes, "text/csv")},
        )
        assert response.status_code == 200
        preview_id = response.json()["preview_id"]

        db = SessionLocal()
        try:
            preview = db.get(ImportPreview, preview_id)
            assert preview is not None
            stored = json.loads(preview.raw_json)
            preview.raw_json = json.dumps(stored["rows"])
            db.commit()
        finally:
            db.close()

        refreshed = client.get(f"/api/import/preview/{preview_id}")
        assert refreshed.status_code == 200
        assert [row["name"] for row in refreshed.json()["triage"]["new"]] == ["Novo"]

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
            f"MXRF11 should suggest class id {rf_pos_id} (RF Pós), got {mxrf['suggested_class_id']}"
        )

        # XPLG11 has category "Ações" → exact match with class "Ações"
        xplg = unmatched_by_ticker["XPLG11"]
        assert xplg["suggested_category"] == "Ações"
        assert xplg["suggested_class_id"] == acoes_id, (
            f"XPLG11 should suggest class id {acoes_id} (Ações), got {xplg['suggested_class_id']}"
        )

        # The other three unmatched rows have category "(Não configurado)"
        # and no class with that name exists, so suggested_class_id stays None.
        for ticker in ("BPAC11", "HGLG11", "VINO11"):
            row = unmatched_by_ticker[ticker]
            assert row["suggested_category"] == "(Não configurado)"
            assert row["suggested_class_id"] is None, (
                f"{ticker} should have suggested_class_id=None, got {row['suggested_class_id']}"
            )
