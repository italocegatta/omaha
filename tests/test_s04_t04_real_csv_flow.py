"""T04: Real CSV flow with posicao_italo.csv (48 positions).

End-to-end tests using the user's real broker extract. Covers parsing,
category suggestion, preview, commit, idempotent re-import, and
cross-profile isolation.

Requires Bug 1 (``-`` → ``0``) and Bug 2 ("conta" removed from footer
labels) to be applied first.
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path
from typing import NamedTuple

import pytest
from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = REPO_ROOT / "tests" / "posicao_italo.csv"


# ---------------------------------------------------------------------------
# Fake for unit-testing suggest_class_id
# ---------------------------------------------------------------------------


class _FakeClass(NamedTuple):
    id: int
    name: str


# ---------------------------------------------------------------------------
# Per-test cleanup
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _clean_data() -> None:
    """Wipe positions, assets, asset_classes, and import_previews before each test."""
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
    client.post(
        "/login",
        data={"username": "Italo", "password": "test-password"},
        follow_redirects=False,
    )
    client.post(f"/profiles/{profile_id}/select", follow_redirects=False)


def _read_posicao_csv() -> bytes:
    return CSV_PATH.read_bytes()


def _create_asset_classes(profile_id: int) -> dict[str, int]:
    """Create 3 asset classes, return {name: id}."""
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


# ---------------------------------------------------------------------------
# 43 asset names from posicao_italo.csv that will auto-match
# ---------------------------------------------------------------------------

_AUTO_MATCH_NAMES: list[tuple[str, str]] = [
    ("Renda Variavel", "SMH"),
    ("Renda Fixa", "Tesouro Selic 2029"),
    ("Renda Variavel", "IVVB11"),
    ("Renda Variavel", "IVV"),
    ("Renda Fixa", "Tesouro IPCA+ 2035"),
    ("Renda Fixa", "Tesouro IPCA+ 2050"),
    ("Renda Variavel", "QQQ"),
    ("Renda Variavel", "PRIO3"),
    ("Renda Fixa", "Tesouro IPCA+ 2045"),
    ("Renda Fixa", "FIXA11"),
    ("Renda Fixa", "CDB Pós  CDI+1,3% 05/04/2027 AGIBANK"),
    ("Fundos Imobiliarios", "LVBI11"),
    ("Fundos Imobiliarios", "VISC11"),
    ("Fundos Imobiliarios", "BRCR11"),
    ("Fundos Imobiliarios", "XPML11"),
    ("Renda Fixa", "AUPO11"),
    ("Renda Variavel", "VT"),
    ("Renda Fixa", "Tesouro Selic 2031"),
    ("Fundos Imobiliarios", "VILG11"),
    ("Renda Variavel", "HTEK11"),
    ("Fundos Imobiliarios", "PVBI11"),
    ("Fundos Imobiliarios", "TRXF11"),
    ("Renda Variavel", "VNQ"),
    ("Fundos Imobiliarios", "CPTI11"),
    ("Fundos Imobiliarios", "CPTS11"),
    ("Renda Fixa", "KDIF11"),
    ("Fundos Imobiliarios", "RBVA11"),
    ("Renda Variavel", "NUCL11"),
    ("Fundos Imobiliarios", "XPCI11"),
    ("Renda Variavel", "IAU"),
    ("Renda Variavel", "BRBI11"),
    ("Fundos Imobiliarios", "RBRX11"),
    ("Fundos Imobiliarios", "PSEC11"),
    ("Renda Variavel", "Conta corrente em dólar Avenue"),
    ("Renda Fixa", "Tesouro Renda+ Aposentadoria Extra 2065"),
    ("Renda Fixa", "JURO11"),
    ("Renda Variavel", "SLCE3"),
    ("Renda Variavel", "TFLO"),
    ("Renda Variavel", "GMAT3"),
    ("Renda Variavel", "KEPL3"),
    ("Renda Variavel", "WIZC3"),
    ("Renda Variavel", "VAMO3"),
    ("Renda Variavel", "BTC"),
]

# 5 tickers from the CSV that are NOT pre-created (will be unmatched)
_UNMATCHED_TICKERS = {
    "RDB Pós 100% CDI 01/08/2033",
    "RDB Pós 100% CDI 01/06/2035",
    "CDB Pós  CDI+1,75% 18/06/2026 BMG",
    "RDB Pós 120% CDI 15/05/2028 Caixinha Turbo NuCel",
    "RDB Pós 120% CDI 15/05/2028 Caixinha Turbo Ultravioleta",
}

# All 48 tickers → expected class name for commit verification
_EXPECTED_CLASS: dict[str, str] = {
    "SMH": "Renda Variavel",
    "Tesouro Selic 2029": "Renda Fixa",
    "IVVB11": "Renda Variavel",
    "IVV": "Renda Variavel",
    "Tesouro IPCA+ 2035": "Renda Fixa",
    "RDB Pós 100% CDI 01/08/2033": "Renda Variavel",
    "RDB Pós 100% CDI 01/06/2035": "Renda Variavel",
    "Tesouro IPCA+ 2050": "Renda Fixa",
    "QQQ": "Renda Variavel",
    "PRIO3": "Renda Variavel",
    "Tesouro IPCA+ 2045": "Renda Fixa",
    "FIXA11": "Renda Fixa",
    "CDB Pós  CDI+1,75% 18/06/2026 BMG": "Renda Fixa",
    "RDB Pós 120% CDI 15/05/2028 Caixinha Turbo NuCel": "Renda Fixa",
    "RDB Pós 120% CDI 15/05/2028 Caixinha Turbo Ultravioleta": "Renda Fixa",
    "CDB Pós  CDI+1,3% 05/04/2027 AGIBANK": "Renda Fixa",
    "LVBI11": "Fundos Imobiliarios",
    "VISC11": "Fundos Imobiliarios",
    "BRCR11": "Fundos Imobiliarios",
    "XPML11": "Fundos Imobiliarios",
    "AUPO11": "Renda Fixa",
    "VT": "Renda Variavel",
    "Tesouro Selic 2031": "Renda Fixa",
    "VILG11": "Fundos Imobiliarios",
    "HTEK11": "Renda Variavel",
    "PVBI11": "Fundos Imobiliarios",
    "TRXF11": "Fundos Imobiliarios",
    "VNQ": "Renda Variavel",
    "CPTI11": "Fundos Imobiliarios",
    "CPTS11": "Fundos Imobiliarios",
    "KDIF11": "Renda Fixa",
    "RBVA11": "Fundos Imobiliarios",
    "NUCL11": "Renda Variavel",
    "XPCI11": "Fundos Imobiliarios",
    "IAU": "Renda Variavel",
    "BRBI11": "Renda Variavel",
    "RBRX11": "Fundos Imobiliarios",
    "PSEC11": "Fundos Imobiliarios",
    "Conta corrente em dólar Avenue": "Renda Variavel",
    "Tesouro Renda+ Aposentadoria Extra 2065": "Renda Fixa",
    "JURO11": "Renda Fixa",
    "SLCE3": "Renda Variavel",
    "TFLO": "Renda Variavel",
    "GMAT3": "Renda Variavel",
    "KEPL3": "Renda Variavel",
    "WIZC3": "Renda Variavel",
    "VAMO3": "Renda Variavel",
    "BTC": "Renda Variavel",
}

# Assignments for the 5 unmatched rows
_ASSIGNMENTS = [
    {"broker_ticker": "RDB Pós 100% CDI 01/08/2033", "class_name": "Renda Variavel"},
    {"broker_ticker": "RDB Pós 100% CDI 01/06/2035", "class_name": "Renda Variavel"},
    {"broker_ticker": "CDB Pós  CDI+1,75% 18/06/2026 BMG", "class_name": "Renda Fixa"},
    {
        "broker_ticker": "RDB Pós 120% CDI 15/05/2028 Caixinha Turbo NuCel",
        "class_name": "Renda Fixa",
    },
    {
        "broker_ticker": "RDB Pós 120% CDI 15/05/2028 Caixinha Turbo Ultravioleta",
        "class_name": "Renda Fixa",
    },
]


# ---------------------------------------------------------------------------
# T1: parse_positions with real CSV
# ---------------------------------------------------------------------------


class TestParseRealCsv:
    """Unit tests for parse_positions with posicao_italo.csv."""

    def test_parse_real_csv_48_positions(self) -> None:
        """parse_positions returns 48 RawPosition from the real CSV."""
        from omaha.csv_import import parse_positions

        text = CSV_PATH.read_text(encoding="utf-8")
        result = parse_positions(text)

        assert len(result) == 48, f"Expected 48 positions, got {len(result)}"

        # Spot-check: "Conta corrente em dólar Avenue" included with qty=0
        conta = [r for r in result if "conta corrente" in r.name.lower()]
        assert (
            len(conta) == 1
        ), "Conta corrente em dólar Avenue should be parsed (not filtered as footer)"
        assert conta[0].qty == Decimal("0"), "Conta corrente qty should be 0 (was - in CSV)"

        # Spot-check: "48 ativos" footer is excluded
        footer = [r for r in result if "48" in r.name]
        assert len(footer) == 0, "Footer row '48 ativos' should be excluded"

        # Spot-check a normal position has positive qty
        smh = [r for r in result if r.name == "SMH"]
        assert len(smh) == 1
        assert smh[0].qty == Decimal("14")
        assert smh[0].avg_price == Decimal("990.92")
        assert smh[0].current_price == Decimal("3197.42")
        assert smh[0].suggested_category == "Internacional"


# ---------------------------------------------------------------------------
# T2: suggest_class_id with real categories from CSV
# ---------------------------------------------------------------------------


class TestSuggestClassId:
    """suggest_class_id with categories found in posicao_italo.csv."""

    @pytest.mark.parametrize(
        "category,expected_id",
        [
            ("Internacional", 4),
            ("RF Pós", None),
            ("RF Dinâmica", None),
            ("Ações", None),
            ("FII", None),
            ("BR Dividendos", None),
            ("(Não configurado)", None),
            ("Cripto", None),
            (None, None),
        ],
    )
    def test_suggest_class_id_real_categories(
        self, category: str | None, expected_id: int | None
    ) -> None:
        """CSV categories do not match the base 3 classes by exact/substring/word.

        The ``"Internacional"`` case is a positive parametrization: a
        fourth class named ``"Internacional"`` is added (id=4) so the
        exact-match path in :func:`suggest_class_id` returns a concrete
        id. Without this positive case the parametrize block would be
        all-``None`` and the test would still pass if ``suggest_class_id``
        were deleted entirely (false-positive bait).
        """
        from omaha.csv_import import suggest_class_id

        classes = [
            _FakeClass(1, "Renda Fixa"),
            _FakeClass(2, "Renda Variavel"),
            _FakeClass(3, "Fundos Imobiliarios"),
            _FakeClass(4, "Internacional"),
        ]
        assert suggest_class_id(category, classes) == expected_id


# ---------------------------------------------------------------------------
# T3: preview with suggested_class_id
# ---------------------------------------------------------------------------


class TestPreviewRealCsv:
    """POST /api/import/preview with posicao_italo.csv."""

    def test_preview_real_csv_suggested_class(self, client: TestClient) -> None:
        """Preview returns 43 auto + 5 unmatched with suggested_class_id=None."""
        _login_and_select(client)
        class_map = _create_asset_classes(1)
        _create_assets(class_map, _AUTO_MATCH_NAMES)

        csv_bytes = _read_posicao_csv()
        resp = client.post(
            "/api/import/preview",
            files={"file": ("posicao_italo.csv", csv_bytes, "text/csv")},
        )

        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()

        assert len(data["auto_matched"]) == 43
        assert len(data["unmatched"]) == 5
        assert len(data["asset_classes"]) == 3

        # Every unmatched row has suggested_class_id=None (no CSV category
        # matches the class names via exact/substring/word with current algo)
        for um in data["unmatched"]:
            assert (
                um["suggested_class_id"] is None
            ), f"Unexpected suggestion for {um['broker_ticker']}: {um['suggested_class_id']}"
            assert um["suggested_category"] is not None

        # Unmatched tickers match expected set
        unmatched_tickers = {u["broker_ticker"] for u in data["unmatched"]}
        assert unmatched_tickers == _UNMATCHED_TICKERS


# ---------------------------------------------------------------------------
# T4: commit creates correct class associations
# ---------------------------------------------------------------------------


class TestCommitRealCsv:
    """POST /api/import/commit with posicao_italo.csv."""

    def _commit_and_verify(self, client: TestClient, class_map: dict[str, int]) -> int:
        """Helper: upload, assign 5 unmatched, commit, return preview_id."""
        csv_bytes = _read_posicao_csv()
        preview_resp = client.post(
            "/api/import/preview",
            files={"file": ("posicao_italo.csv", csv_bytes, "text/csv")},
        )
        preview_id = preview_resp.json()["preview_id"]

        assignments = [
            {
                "broker_ticker": a["broker_ticker"],
                "class_id": class_map[a["class_name"]],
                "asset_name": a["broker_ticker"],
            }
            for a in _ASSIGNMENTS
        ]

        resp = client.post(
            "/api/import/commit",
            json={"preview_id": preview_id, "assignments": assignments},
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data["upserted"] == 48
        assert data["created"] == 5

        return preview_id

    def test_commit_real_csv_creates_correct_class_association(self, client: TestClient) -> None:
        """Each committed Position points to an Asset whose AssetClass matches expectations."""
        from omaha.db import SessionLocal
        from omaha.models import Asset, AssetClass, Position

        _login_and_select(client)
        class_map = _create_asset_classes(1)
        _create_assets(class_map, _AUTO_MATCH_NAMES)

        self._commit_and_verify(client, class_map)

        db = SessionLocal()
        try:
            positions = db.query(Position).all()
            assert len(positions) == 48

            for pos in positions:
                asset = db.get(Asset, pos.asset_id)
                assert asset is not None, f"No asset for position {pos.broker_ticker}"
                asset_class = db.get(AssetClass, asset.asset_class_id)
                assert asset_class is not None, f"No class for asset {asset.name}"
                expected = _EXPECTED_CLASS[pos.broker_ticker]
                assert (
                    asset_class.name == expected
                ), f"{pos.broker_ticker}: expected class {expected!r}, got {asset_class.name!r}"
        finally:
            db.close()


# ---------------------------------------------------------------------------
# T5: reimport idempotent
# ---------------------------------------------------------------------------


class TestReimportRealCsv:
    """Re-import after commit is idempotent (0 unmatched)."""

    def test_reimport_real_csv_idempotent(self, client: TestClient) -> None:
        """After commit, re-uploading the same CSV yields 48 auto-matched, 0 unmatched."""
        _login_and_select(client)
        class_map = _create_asset_classes(1)
        _create_assets(class_map, _AUTO_MATCH_NAMES)

        # First commit
        csv_bytes = _read_posicao_csv()
        preview_resp = client.post(
            "/api/import/preview",
            files={"file": ("posicao_italo.csv", csv_bytes, "text/csv")},
        )
        preview_id = preview_resp.json()["preview_id"]

        assignments = [
            {
                "broker_ticker": a["broker_ticker"],
                "class_id": class_map[a["class_name"]],
                "asset_name": a["broker_ticker"],
            }
            for a in _ASSIGNMENTS
        ]
        commit_resp = client.post(
            "/api/import/commit",
            json={"preview_id": preview_id, "assignments": assignments},
        )
        assert commit_resp.status_code == 200

        # Re-upload — all 48 assets exist now
        csv_bytes = _read_posicao_csv()
        re_resp = client.post(
            "/api/import/preview",
            files={"file": ("posicao_italo.csv", csv_bytes, "text/csv")},
        )
        assert re_resp.status_code == 200
        data = re_resp.json()
        assert len(data["auto_matched"]) == 48, f"Expected 48 auto, got {len(data['auto_matched'])}"
        assert len(data["unmatched"]) == 0, f"Expected 0 unmatched, got {len(data['unmatched'])}"

        # No duplicate positions (upsert is idempotent)
        from omaha.db import SessionLocal
        from omaha.models import Position

        db = SessionLocal()
        try:
            count = db.query(Position).count()
            assert count == 48, f"Expected 48 positions, got {count}"
        finally:
            db.close()


# ---------------------------------------------------------------------------
# T6: preview changes after adding remaining assets
# ---------------------------------------------------------------------------


class TestPreviewChangesAfterAddingAssets:
    """Preview re-match reflects new assets."""

    def test_preview_real_csv_changes_after_adding_assets(self, client: TestClient) -> None:
        """Initial preview shows 43 auto + 5 unmatched; after creating all 48 assets, new preview shows 48 auto."""
        _login_and_select(client)
        class_map = _create_asset_classes(1)
        _create_assets(class_map, _AUTO_MATCH_NAMES)

        csv_bytes = _read_posicao_csv()

        # First preview: 43 auto, 5 unmatched
        resp1 = client.post(
            "/api/import/preview",
            files={"file": ("posicao_italo.csv", csv_bytes, "text/csv")},
        )
        data1 = resp1.json()
        assert len(data1["auto_matched"]) == 43
        assert len(data1["unmatched"]) == 5

        # Create the remaining 5 assets
        remaining = [
            ("Renda Variavel", "RDB Pós 100% CDI 01/08/2033"),
            ("Renda Variavel", "RDB Pós 100% CDI 01/06/2035"),
            ("Renda Fixa", "CDB Pós  CDI+1,75% 18/06/2026 BMG"),
            ("Renda Fixa", "RDB Pós 120% CDI 15/05/2028 Caixinha Turbo NuCel"),
            ("Renda Fixa", "RDB Pós 120% CDI 15/05/2028 Caixinha Turbo Ultravioleta"),
        ]
        _create_assets(class_map, remaining)

        # Second preview: all 48 auto-matched
        resp2 = client.post(
            "/api/import/preview",
            files={"file": ("posicao_italo.csv", csv_bytes, "text/csv")},
        )
        data2 = resp2.json()
        assert (
            len(data2["auto_matched"]) == 48
        ), f"Expected 48 auto, got {len(data2['auto_matched'])}"
        assert len(data2["unmatched"]) == 0, f"Expected 0 unmatched, got {len(data2['unmatched'])}"


# ---------------------------------------------------------------------------
# T7: cross-profile isolation
# ---------------------------------------------------------------------------


class TestCrossProfileIsolation:
    """Profile isolation for real CSV previews."""

    def test_cross_profile_isolation_real_csv(self, client: TestClient) -> None:
        """Profile 2 cannot access a preview created by Profile 1."""
        _login_and_select(client, profile_id=1)
        class_map = _create_asset_classes(1)
        _create_assets(class_map, _AUTO_MATCH_NAMES)

        csv_bytes = _read_posicao_csv()
        resp = client.post(
            "/api/import/preview",
            files={"file": ("posicao_italo.csv", csv_bytes, "text/csv")},
        )
        preview_id = resp.json()["preview_id"]

        # Switch to profile 2
        _login_and_select(client, profile_id=2)

        resp2 = client.get(f"/api/import/preview/{preview_id}")
        assert (
            resp2.status_code == 404
        ), f"Expected 404 for cross-profile access, got {resp2.status_code}"
