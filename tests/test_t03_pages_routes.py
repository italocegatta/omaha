"""Route tests for the dashboard pages (S05 T01).

The S05 dashboard pulls ``portfolio_aggregates()`` for the active
profile, so this test exercises:

1. The pure ``portfolio_aggregates()`` helper with hand-built ORM
   objects (no HTTP, no DB) — covers the empty-portfolio, multi-class,
   and per-asset math.
2. A TestClient end-to-end pass: log in, select Italo, seed one
   class + one asset + one position, GET /, and assert the rendered
   dashboard surfaces the portfolio total the helper computed.
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from omaha.models import Asset, AssetClass, Position, Profile
from omaha.routes.pages import portfolio_aggregates

TEST_PASSWORD = "test-password"


@pytest.fixture(autouse=True)
def _clean_dashboard_tables() -> None:
    """Wipe classes/assets/positions before each test in this module.

    The session-scoped ``_omaha_test_env`` keeps the same DB file for
    the whole run, so leftover state from S03/S04 tests would leak in
    otherwise.
    """
    from omaha.db import SessionLocal

    db = SessionLocal()
    try:
        db.query(Position).delete()
        db.query(Asset).delete()
        db.query(AssetClass).delete()
        db.commit()
    finally:
        db.close()
    yield


# ---------------------------------------------------------------------------
# Pure-helper tests (no HTTP)
# ---------------------------------------------------------------------------


def _build_class(
    class_id: int,
    name: str,
    target_pct: Decimal,
    assets: list[Asset],
) -> AssetClass:
    """Construct an in-memory AssetClass for aggregate tests."""
    klass = AssetClass(
        id=class_id,
        profile_id=1,
        name=name,
        target_pct=target_pct,
        display_order=0,
    )
    # Attach assets via the relationship (bypass flush).
    klass.assets = list(assets)
    for asset in assets:
        asset.asset_class = klass
    return klass


def _build_asset(asset_id: int, name: str, positions: list[Position]) -> Asset:
    asset = Asset(id=asset_id, asset_class_id=0, name=name, display_order=0)
    asset.positions = list(positions)
    for pos in positions:
        pos.asset = asset
    return asset


def _build_pos(pos_id: int, qty: Decimal, avg: Decimal, cur: Decimal) -> Position:
    return Position(
        id=pos_id,
        asset_id=0,
        qty=qty,
        avg_price=avg,
        current_price=cur,
        broker_ticker=f"X{pos_id}",
    )


def test_aggregates_empty_profile_returns_zero_portfolio() -> None:
    """No classes → portfolio total 0, gain_pct is None (renders '—')."""
    result = portfolio_aggregates([])

    assert result["portfolio"]["total_invested"] == Decimal("0")
    assert result["portfolio"]["current_value"] == Decimal("0")
    assert result["portfolio"]["gain"] == Decimal("0")
    assert result["portfolio"]["gain_pct"] is None
    assert result["classes"] == []


def test_aggregates_class_with_no_positions() -> None:
    """A class with no assets/positions contributes zero to totals and 0% pct."""
    klass = _build_class(1, "Renda Fixa", Decimal("60.00"), assets=[])

    result = portfolio_aggregates([klass])

    assert result["portfolio"]["total_invested"] == Decimal("0")
    assert result["portfolio"]["current_value"] == Decimal("0")
    assert result["portfolio"]["gain_pct"] is None
    assert result["classes"][0]["invested"] == Decimal("0")
    assert result["classes"][0]["current_value"] == Decimal("0")
    # current_pct must be 0 (not undefined) when the portfolio is empty.
    assert result["classes"][0]["current_pct"] == Decimal("0")


def test_aggregates_sums_invested_current_gain_pct() -> None:
    """Two positions across two assets: math must hold.

    Asset A: 10 shares @ 100 avg, 110 cur  →  invested 1000, current 1100
    Asset B:  4 shares @  50 avg,  60 cur  →  invested  200, current  240
    Portfolio:                                invested 1200, current 1340
    Gain:      140, gain_pct ≈ 11.6667
    """
    asset_a = _build_asset(1, "AAA", [_build_pos(1, Decimal("10"), Decimal("100"), Decimal("110"))])
    asset_b = _build_asset(2, "BBB", [_build_pos(2, Decimal("4"), Decimal("50"), Decimal("60"))])
    klass = _build_class(1, "Acoes", Decimal("100.00"), assets=[asset_a, asset_b])

    result = portfolio_aggregates([klass])

    assert result["portfolio"]["total_invested"] == Decimal("1200")
    assert result["portfolio"]["current_value"] == Decimal("1340")
    assert result["portfolio"]["gain"] == Decimal("140")
    # gain_pct = 140 / 1200 * 100 = 11.6666… (12.5 + 20 = 32.5? no, see math above)
    # 140 / 1200 = 0.11666…; *100 = 11.6666…
    assert result["portfolio"]["gain_pct"] == pytest.approx(
        Decimal("11.6666"), rel=Decimal("0.001")
    )


def test_aggregates_per_asset_pct_is_share_of_class() -> None:
    """Asset pct is the share of the *class's* current_value, not the portfolio."""
    asset_a = _build_asset(1, "AAA", [_build_pos(1, Decimal("10"), Decimal("100"), Decimal("110"))])
    asset_b = _build_asset(2, "BBB", [_build_pos(2, Decimal("4"), Decimal("50"), Decimal("60"))])
    klass = _build_class(1, "Acoes", Decimal("100.00"), assets=[asset_a, asset_b])

    result = portfolio_aggregates([klass])

    assets_by_id = {a["id"]: a for a in result["classes"][0]["assets"]}
    # asset_a: 1100 / 1340 = 82.0895…
    assert assets_by_id[1]["asset_pct"] == pytest.approx(Decimal("82.0895"), rel=Decimal("0.001"))
    # asset_b: 240 / 1340 = 17.9104…
    assert assets_by_id[2]["asset_pct"] == pytest.approx(Decimal("17.9104"), rel=Decimal("0.001"))


def test_aggregates_per_class_current_pct_is_share_of_portfolio() -> None:
    """With two classes, each class's current_pct = its current_value / total."""
    asset_a = _build_asset(1, "AAA", [_build_pos(1, Decimal("10"), Decimal("100"), Decimal("110"))])
    asset_b = _build_asset(2, "BBB", [_build_pos(2, Decimal("4"), Decimal("50"), Decimal("60"))])
    fixed = _build_class(1, "Renda Fixa", Decimal("40.00"), assets=[asset_a])
    equities = _build_class(2, "Acoes", Decimal("60.00"), assets=[asset_b])

    result = portfolio_aggregates([fixed, equities])

    by_id = {c["id"]: c for c in result["classes"]}
    # fixed: 1100 / 1340 = 82.0895…%
    assert by_id[1]["current_pct"] == pytest.approx(Decimal("82.0895"), rel=Decimal("0.001"))
    # equities: 240 / 1340 = 17.9104…%
    assert by_id[2]["current_pct"] == pytest.approx(Decimal("17.9104"), rel=Decimal("0.001"))


def test_aggregates_handles_negative_gain() -> None:
    """When current < invested, gain is negative and gain_pct is negative."""
    asset = _build_asset(1, "AAA", [_build_pos(1, Decimal("10"), Decimal("100"), Decimal("80"))])
    klass = _build_class(1, "Acoes", Decimal("100.00"), assets=[asset])

    result = portfolio_aggregates([klass])

    assert result["portfolio"]["gain"] == Decimal("-200")
    # -200 / 1000 * 100 = -20
    assert result["portfolio"]["gain_pct"] == pytest.approx(Decimal("-20"), rel=Decimal("0.001"))


# ---------------------------------------------------------------------------
# End-to-end test (HTTP + DB)
# ---------------------------------------------------------------------------


def _login_and_select(client: TestClient, profile_name: str = "Italo") -> int:
    """Log in as ``family`` and select the named profile.

    Returns the profile id (needed to seed classes/assets in tests
    that build state via HTTP). For pure-DB tests, callers can
    ignore the return value.
    """
    client.post("/login", data={"username": "family", "password": TEST_PASSWORD})
    from omaha.db import SessionLocal

    db = SessionLocal()
    try:
        profile = db.query(Profile).filter(Profile.name == profile_name).first()
        assert profile is not None, f"profile {profile_name!r} not seeded"
        # The form expects the numeric id and redirects 303 to '/'.
        # TestClient follows the 303 automatically, so we just verify
        # the final response is the dashboard for the picked profile.
        resp = client.post(f"/profiles/{profile.id}/select")
        assert resp.status_code == 200, resp.text
        assert f"Bem-vindo, {profile_name}" in resp.text, resp.text
        return profile.id
    finally:
        db.close()


def _seed_class_with_position(
    profile_id: int,
    class_name: str,
    target_pct: str,
    asset_name: str,
    qty: str,
    avg: str,
    cur: str,
    broker_ticker: str,
) -> None:
    """Direct-DB seed: one class + one asset + one position for a profile."""
    from omaha.db import SessionLocal

    db = SessionLocal()
    try:
        klass = AssetClass(
            profile_id=profile_id,
            name=class_name,
            target_pct=Decimal(target_pct),
            display_order=0,
        )
        db.add(klass)
        db.flush()
        asset = Asset(
            asset_class_id=klass.id,
            name=asset_name,
            display_order=0,
        )
        db.add(asset)
        db.flush()
        pos = Position(
            asset_id=asset.id,
            qty=Decimal(qty),
            avg_price=Decimal(avg),
            current_price=Decimal(cur),
            broker_ticker=broker_ticker,
        )
        db.add(pos)
        db.commit()
    finally:
        db.close()


def test_dashboard_renders_portfolio_totals(client: TestClient) -> None:
    """GET / with one position renders the dashboard with seeded asset + position.

    T01 ships the ``portfolio_aggregates()`` helper and the route
    plumbing that passes the portfolio + per-class aggregates into
    the dashboard template. The visual BRL formatting of the
    portfolio total is a T02/T03 concern (the S05 polish); this test
    only proves the end-to-end pipeline works: login → select profile
    → seed ORM state → GET / → dashboard renders 200 with the seeded
    asset and target percentage visible (so we know the route
    executed the selectinload + aggregate helper without error).
    """
    profile_id = _login_and_select(client, profile_name="Italo")
    _seed_class_with_position(
        profile_id=profile_id,
        class_name="Renda Fixa",
        target_pct="60.00",
        asset_name="TESOURO",
        qty="10",
        avg="100",
        cur="110",
        broker_ticker="TESOURO_2029",
    )

    r = client.get("/")
    assert r.status_code == 200, r.text

    body = r.text
    # The class summary block renders the target_pct as "60.00%" — this
    # proves the selectinload of assets + positions didn't blow up
    # (which would have raised ArgumentError pre-fix).
    assert "60.00%" in body, body
    # The asset row renders the seeded asset name.
    assert "TESOURO" in body, body
    # M002 S01/T03: the "1 posicao(oes)" line is removed in favor
    # of the 4-percentage grid + inline editor. The data-position-count
    # attribute is still on the <li> (asserted below in the layout
    # test), but the visible text is gone — so no string match.
    assert "1 posicao" not in body, body


def test_dashboard_renders_distribution_layout(client: TestClient) -> None:
    """S05/T02: dashboard renders the new distribution layout.

    Verifies the data-testid markers the new template uses for the
    portfolio header, per-class sections, color swatches, target-vs-current
    compare bars, per-asset rows, progress bars, and BRL-formatted totals.
    """
    profile_id = _login_and_select(client, profile_name="Italo")
    _seed_class_with_position(
        profile_id=profile_id,
        class_name="Renda Fixa",
        target_pct="60.00",
        asset_name="TESOURO",
        qty="10",
        avg="100",
        cur="110",
        broker_ticker="TESOURO_2029",
    )

    r = client.get("/")
    assert r.status_code == 200, r.text
    body = r.text

    # Portfolio header (3-stat: invested, current, gain)
    assert 'data-testid="portfolio-header"' in body, body
    assert 'data-testid="portfolio-invested"' in body, body
    assert 'data-testid="portfolio-total"' in body, body
    assert 'data-testid="portfolio-gain"' in body, body
    assert 'data-gain-sign="positive"' in body, body  # 110 > 100 → positive

    # BRL formatting appears somewhere in the dashboard
    assert "R$" in body, body
    # 10 * 110 = 1100.00 → R$ 1.100,00
    assert "R$ 1.100,00" in body, body
    # 10 * 100 = 1000.00 → R$ 1.000,00
    assert "R$ 1.000,00" in body, body
    # 1100 - 1000 = 100 → R$ 100,00
    assert "R$ 100,00" in body, body

    # Per-class section markers
    assert 'data-testid="dashboard-class-section"' in body, body
    assert 'data-testid="class-color-swatch"' in body, body
    assert 'data-testid="class-section-name"' in body, body
    assert 'data-testid="class-target-pct-view"' in body, body
    assert 'data-testid="class-current-pct"' in body, body
    assert 'data-testid="class-compare-bar"' in body, body

    # Per-asset row markers
    assert 'data-testid="dashboard-asset-row"' in body, body
    assert 'data-testid="asset-row-name"' in body, body
    assert 'data-testid="asset-position-count"' in body, body
    assert 'data-testid="asset-current-value"' in body, body
    assert 'data-testid="asset-pct"' in body, body
    assert 'data-testid="asset-progress-bar"' in body, body

    # M002 S01/T03: 4-percentage grid + Alpine inline editor
    # (D012 — 1 storage, 2 views; D015 — visual affordance for
    # the migration gap). Each cell carries its own data-testid;
    # the editor's input is the save affordance.
    assert 'data-testid="asset-pct-grid"' in body, body
    assert 'data-testid="asset-target-pct-class"' in body, body
    assert 'data-testid="asset-current-pct-class"' in body, body
    assert 'data-testid="asset-target-pct-total"' in body, body
    assert 'data-testid="asset-current-pct-total"' in body, body
    assert 'data-testid="asset-inline-edit-input"' in body, body
    assert 'data-testid="class-delta-badge"' in body, body
    # Alpine x-data wrapper on each class section.
    assert "x-data='classSection(" in body, body
    # The new template never renders the visible "N posicao(oes)"
    # line — D015 task scope.
    assert "posicao(oes)" not in body, body

    # Target vs current comparison — both bars present
    assert "compare-bar-target-fill" in body, body
    assert "compare-bar-current-fill" in body, body


def test_dashboard_renders_class_summary_with_no_positions(client: TestClient) -> None:
    """S05/T02: when classes exist but have no positions, the class-summary
    block and per-class sections are still rendered (only the portfolio
    header is hidden). The S03 'class-summary' wrapper is preserved for
    backward compat with the S04 e2e journey selectors.
    """
    profile_id = _login_and_select(client, profile_name="Italo")
    from omaha.db import SessionLocal

    db = SessionLocal()
    try:
        klass = AssetClass(
            profile_id=profile_id,
            name="Renda Fixa",
            target_pct=Decimal("60.00"),
            display_order=0,
        )
        db.add(klass)
        db.commit()
    finally:
        db.close()

    r = client.get("/")
    assert r.status_code == 200, r.text
    body = r.text

    # The S03 'class-summary' wrapper and per-class row are still there.
    assert 'data-testid="class-summary"' in body, body
    assert 'data-testid="class-summary-row"' in body, body
    assert "Renda Fixa" in body, body
    # The portfolio header is hidden when current_value is 0.
    assert 'data-testid="portfolio-header"' not in body, body
