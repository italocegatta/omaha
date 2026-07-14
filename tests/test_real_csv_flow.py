"""T04: Import-flow audit against canonical seeded positions CSV fixture.

Exercises ``omaha.csv_import`` plus preview/commit endpoints by
uploading ``data/seed/italo_positions.csv`` under broker-style
filename ``posicao_italo.csv``. This file no longer mirrors raw broker
export verbatim; coverage here documents current fixture behavior:

- positive-qty seeded rows auto-match existing assets,
- zero-qty placeholders stay unmatched until assigned,
- the import path ignores seeded ``total_invested`` /
  ``total_current`` columns from this fixture,
- idempotence and profile isolation stay green.
"""

from __future__ import annotations

import csv
from decimal import Decimal
from pathlib import Path
from typing import NamedTuple

import pytest
from fastapi.testclient import TestClient

from scripts.seed_from_csv import load_assets, load_positions

REPO_ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = REPO_ROOT / "data" / "seed" / "italo_positions.csv"

# Tests read from data/seed/*.csv which are mutated by test_seed_from_csv.py
# and test_snapshot_to_csv.py.  Serialize to avoid stale/ corrupt reads.
pytestmark = pytest.mark.xdist_group("serial")


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


def _read_posicao_csv() -> bytes:
    return CSV_PATH.read_bytes()


def _raw_position_rows() -> list[dict[str, str]]:
    with CSV_PATH.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _dashboard_class_for_asset(seed_class_name: str, asset_name: str) -> str:
    if seed_class_name in {"RF Dinâmica", "RF Pós"}:
        if asset_name == "Conta corrente em dólar Avenue":
            return "Renda Variavel"
        return "Renda Fixa"
    if seed_class_name == "FII":
        return "Fundos Imobiliarios"
    return "Renda Variavel"


def _seed_assets() -> list[tuple[str, str]]:
    assets_by_name = {row.name: row.class_name for row in load_assets("italo")}
    return [
        (_dashboard_class_for_asset(assets_by_name[row.asset_name], row.asset_name), row.asset_name)
        for row in load_positions("italo")
        if row.qty > 0
    ]


def _unmatched_tickers() -> set[str]:
    return {row.broker_ticker for row in load_positions("italo") if row.qty == 0}


def _expected_class_by_ticker() -> dict[str, str]:
    assets_by_name = {row.name: row.class_name for row in load_assets("italo")}
    out = {
        row.broker_ticker: _dashboard_class_for_asset(
            assets_by_name[row.asset_name], row.asset_name
        )
        for row in load_positions("italo")
        if row.qty > 0
    }
    out.update(
        {
            "RDB Pós 100% CDI 01/08/2033": "Renda Variavel",
            "RDB Pós 100% CDI 01/06/2035": "Renda Variavel",
            "CDB Pós  CDI+1,3% 05/04/2027 AGIBANK": "Renda Fixa",
            "RDB Pós 120% CDI 15/05/2028 Caixinha Turbo NuCel": "Renda Fixa",
            "RDB Pós 120% CDI 04/06/2027 Caixinha Ultravioleta": "Renda Fixa",
        }
    )
    return out


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


# Assignments for 5 zero-qty rows in current CSV.
_ASSIGNMENTS = [
    {"broker_ticker": "RDB Pós 100% CDI 01/08/2033", "class_name": "Renda Variavel"},
    {"broker_ticker": "RDB Pós 100% CDI 01/06/2035", "class_name": "Renda Variavel"},
    {"broker_ticker": "CDB Pós  CDI+1,3% 05/04/2027 AGIBANK", "class_name": "Renda Fixa"},
    {
        "broker_ticker": "RDB Pós 120% CDI 15/05/2028 Caixinha Turbo NuCel",
        "class_name": "Renda Fixa",
    },
    {
        "broker_ticker": "RDB Pós 120% CDI 04/06/2027 Caixinha Ultravioleta",
        "class_name": "Renda Fixa",
    },
]


# ---------------------------------------------------------------------------
# T1: parse_positions with seeded positions fixture uploaded as CSV
# ---------------------------------------------------------------------------


class TestParseRealCsv:
    """Unit tests for parse_positions with uploaded seeded positions fixture."""

    def test_parse_real_csv_47_positions(self) -> None:
        """parse_positions returns one row per uploaded fixture line."""
        from omaha.csv_import import parse_positions

        text = CSV_PATH.read_text(encoding="utf-8")
        result = parse_positions(text)

        assert len(result) == len(_raw_position_rows()), (
            f"Expected CSV row count, got {len(result)}"
        )

        # Spot-check: "Conta corrente em dólar Avenue" included with qty=1
        conta = [r for r in result if "conta corrente" in r.name.lower()]
        assert len(conta) == 1, (
            "Conta corrente em dólar Avenue should be parsed (not filtered as footer)"
        )
        assert conta[0].qty == Decimal("1"), "Conta corrente qty should be 1"

        # Spot-check: "47 ativos" footer is excluded
        footer = [r for r in result if "47" in r.name]
        assert len(footer) == 0, "Footer row '47 ativos' should be excluded"

        # Spot-check a normal position has positive qty
        smh = [r for r in result if r.name == "SMH"]
        assert len(smh) == 1
        assert smh[0].qty == Decimal("14")
        assert smh[0].avg_price == Decimal("990.92")
        assert smh[0].current_price == Decimal("990.92")

    def test_parse_real_csv_br_thousands_qty(self) -> None:
        """qty cells com '.' milhar (sem ',') parseiam como inteiro,
        não como decimal US. Cobre as 8 posições afetadas em
        ``data/seed/italo_positions.csv``."""
        from omaha.csv_import import parse_positions

        text = CSV_PATH.read_text(encoding="utf-8")
        result = parse_positions(text)

        by_ticker = {r.broker_ticker: r for r in result}
        raw_by_ticker = {row["broker_ticker"]: row for row in _raw_position_rows()}
        expected = ["FIXA11", "CPTS11", "RBVA11", "RBRX11", "GMAT3", "KEPL3", "WIZC3", "VAMO3"]
        for ticker in expected:
            expected_qty = Decimal(raw_by_ticker[ticker]["qty"])
            assert by_ticker[ticker].qty == expected_qty, (
                f"{ticker}: expected qty={expected_qty}, got {by_ticker[ticker].qty}"
            )

    def test_parse_real_csv_seed_fixture_leaves_import_totals_empty(self) -> None:
        """Current import parser ignores seed-fixture totals columns.

        ``data/seed/italo_positions.csv`` carries canonical
        ``total_invested`` / ``total_current`` fields for the seed path,
        but ``omaha.csv_import.parse_positions`` does not read them from
        this uploaded fixture shape. This audit pins current behavior so
        docstrings match reality; footer-parity import work belongs in a
        follow-up slice.
        """
        from omaha.csv_import import parse_positions

        text = CSV_PATH.read_text(encoding="utf-8")
        result = parse_positions(text)
        raw_rows = _raw_position_rows()
        assert len(result) == len(raw_rows)

        assert all(rp.total_invested is None for rp in result)
        assert all(rp.total_current is None for rp in result)


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
    """POST /api/import/preview with uploaded seeded positions fixture."""

    def test_preview_real_csv_suggested_class(self, client: TestClient) -> None:
        """Preview returns auto-matched seeded rows plus zero-qty unmatched rows."""
        _login_and_select(client)
        class_map = _create_asset_classes(1)
        _create_assets(class_map, _seed_assets())

        csv_bytes = _read_posicao_csv()
        resp = client.post(
            "/api/import/preview",
            files={"file": ("posicao_italo.csv", csv_bytes, "text/csv")},
        )

        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()

        assert len(data["auto_matched"]) == len(_seed_assets())
        assert len(data["unmatched"]) == len(_unmatched_tickers())
        assert len(data["asset_classes"]) == 3

        # Every unmatched row has suggested_class_id=None (current algo
        # does not infer seeded placeholder classes from this fixture).
        for um in data["unmatched"]:
            assert um["suggested_class_id"] is None, (
                f"Unexpected suggestion for {um['broker_ticker']}: {um['suggested_class_id']}"
            )

        # Unmatched tickers match expected set
        unmatched_tickers = {u["broker_ticker"] for u in data["unmatched"]}
        assert unmatched_tickers == _unmatched_tickers()


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
        assert data["upserted"] == len(_expected_class_by_ticker())
        assert data["created"] == len(_unmatched_tickers())

        return preview_id

    def test_commit_real_csv_creates_correct_class_association(self, client: TestClient) -> None:
        """Each committed Position points to an Asset whose AssetClass matches expectations."""
        from omaha.db import SessionLocal
        from omaha.models import Asset, AssetClass, Position

        _login_and_select(client)
        class_map = _create_asset_classes(1)
        _create_assets(class_map, _seed_assets())

        self._commit_and_verify(client, class_map)

        db = SessionLocal()
        try:
            positions = db.query(Position).all()
            assert len(positions) == len(_expected_class_by_ticker())

            for pos in positions:
                asset = db.get(Asset, pos.asset_id)
                assert asset is not None, f"No asset for position {pos.broker_ticker}"
                asset_class = db.get(AssetClass, asset.asset_class_id)
                assert asset_class is not None, f"No class for asset {asset.name}"
                expected = _expected_class_by_ticker()[pos.broker_ticker]
                assert asset_class.name == expected, (
                    f"{pos.broker_ticker}: expected class {expected!r}, got {asset_class.name!r}"
                )
        finally:
            db.close()


# ---------------------------------------------------------------------------
# T5: reimport idempotent
# ---------------------------------------------------------------------------


class TestReimportRealCsv:
    """Re-import after commit is idempotent (0 unmatched)."""

    def test_reimport_real_csv_idempotent(self, client: TestClient) -> None:
        """After commit, re-uploading same fixture yields 0 unmatched rows."""
        _login_and_select(client)
        class_map = _create_asset_classes(1)
        _create_assets(class_map, _seed_assets())

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

        # Re-upload — every fixture row now has backing asset
        csv_bytes = _read_posicao_csv()
        re_resp = client.post(
            "/api/import/preview",
            files={"file": ("posicao_italo.csv", csv_bytes, "text/csv")},
        )
        assert re_resp.status_code == 200
        data = re_resp.json()
        assert len(data["auto_matched"]) == len(_expected_class_by_ticker()), (
            f"Expected all rows auto, got {len(data['auto_matched'])}"
        )
        assert len(data["unmatched"]) == 0, f"Expected 0 unmatched, got {len(data['unmatched'])}"

        # No duplicate positions (upsert is idempotent)
        from omaha.db import SessionLocal
        from omaha.models import Position

        db = SessionLocal()
        try:
            count = db.query(Position).count()
            assert count == len(_expected_class_by_ticker()), f"Expected CSV row count, got {count}"
        finally:
            db.close()


# ---------------------------------------------------------------------------
# T6: preview changes after adding remaining assets
# ---------------------------------------------------------------------------


class TestPreviewChangesAfterAddingAssets:
    """Preview re-match reflects new assets."""

    def test_preview_real_csv_changes_after_adding_assets(self, client: TestClient) -> None:
        """Initial preview leaves placeholders unmatched; later preview rematches all rows."""
        _login_and_select(client)
        class_map = _create_asset_classes(1)
        _create_assets(class_map, _seed_assets())

        csv_bytes = _read_posicao_csv()

        # First preview: positive-qty rows auto-match; zero-qty placeholders do not.
        resp1 = client.post(
            "/api/import/preview",
            files={"file": ("posicao_italo.csv", csv_bytes, "text/csv")},
        )
        data1 = resp1.json()
        assert len(data1["auto_matched"]) == len(_seed_assets())
        assert len(data1["unmatched"]) == len(_unmatched_tickers())

        # Create the remaining 5 assets
        remaining = [
            ("Renda Variavel", "RDB Pós 100% CDI 01/08/2033"),
            ("Renda Variavel", "RDB Pós 100% CDI 01/06/2035"),
            ("Renda Fixa", "CDB Pós  CDI+1,3% 05/04/2027 AGIBANK"),
            ("Renda Fixa", "RDB Pós 120% CDI 15/05/2028 Caixinha Turbo NuCel"),
            ("Renda Fixa", "RDB Pós 120% CDI 04/06/2027 Caixinha Ultravioleta"),
        ]
        _create_assets(class_map, remaining)

        # Second preview: all rows auto-matched
        resp2 = client.post(
            "/api/import/preview",
            files={"file": ("posicao_italo.csv", csv_bytes, "text/csv")},
        )
        data2 = resp2.json()
        assert len(data2["auto_matched"]) == len(_expected_class_by_ticker()), (
            f"Expected all rows auto, got {len(data2['auto_matched'])}"
        )
        assert len(data2["unmatched"]) == 0, f"Expected 0 unmatched, got {len(data2['unmatched'])}"


# ---------------------------------------------------------------------------
# T7: cross-profile isolation
# ---------------------------------------------------------------------------


class TestCrossProfileIsolation:
    """Profile isolation for uploaded seeded-position previews."""

    def test_cross_profile_isolation_real_csv(self, client: TestClient) -> None:
        """Profile 2 cannot access a preview created by Profile 1."""
        _login_and_select(client, profile_id=1)
        class_map = _create_asset_classes(1)
        _create_assets(class_map, _seed_assets())

        csv_bytes = _read_posicao_csv()
        resp = client.post(
            "/api/import/preview",
            files={"file": ("posicao_italo.csv", csv_bytes, "text/csv")},
        )
        preview_id = resp.json()["preview_id"]

        # Switch to profile 2
        _login_and_select(client, profile_id=2)

        resp2 = client.get(f"/api/import/preview/{preview_id}")
        assert resp2.status_code == 404, (
            f"Expected 404 for cross-profile access, got {resp2.status_code}"
        )


class TestPortfolioTotalsFromCsv:
    """Current import-fixture totals behavior.

    This fixture is a seed CSV, not raw broker export. Preview/commit do
    not carry its ``total_invested`` / ``total_current`` columns through
    the import path, so dashboard aggregates stay zero after commit.
    Audit keeps test behavior and fixes stale narrative only.
    """

    def test_portfolio_totals_remain_zero_without_import_totals(self, client: TestClient) -> None:
        from omaha.routes.pages import portfolio_aggregates

        _login_and_select(client, profile_id=1)
        class_map = _create_asset_classes(1)
        _create_assets(class_map, _seed_assets())

        # Preview uploaded seeded positions fixture.
        csv_bytes = _read_posicao_csv()
        preview_resp = client.post(
            "/api/import/preview",
            files={"file": ("posicao_italo.csv", csv_bytes, "text/csv")},
        )
        assert preview_resp.status_code == 200, preview_resp.text
        preview_id = preview_resp.json()["preview_id"]

        # Commit with assignments for the 5 unmatched rows.
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
        assert commit_resp.status_code == 200, commit_resp.text
        assert commit_resp.json()["upserted"] == len(_expected_class_by_ticker())

        # Dashboard aggregates via the same helper the route uses.
        # Current import path sees no explicit totals from this fixture,
        # so both portfolio totals remain zero.
        from omaha.db import SessionLocal
        from omaha.models import AssetClass

        with SessionLocal() as db:
            classes = (
                db.query(AssetClass)
                .filter(AssetClass.profile_id == 1)
                .order_by(AssetClass.display_order)
                .all()
            )
            aggregates = portfolio_aggregates(classes)

        portfolio = aggregates["portfolio"]
        assert portfolio["total_invested"] == Decimal("0"), portfolio["total_invested"]
        assert portfolio["current_value"] == Decimal("0"), portfolio["current_value"]
