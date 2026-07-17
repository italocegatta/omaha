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
    """Build a :class:`Position` with the broker totals pre-populated.

    broker-csv-import-totals: after the change, ``portfolio_aggregates``
    sums ``total_invested`` / ``total_current`` directly (no
    recompute). Existing tests assume the old ``qty * price`` math
    produces the portfolio total; the helper mimics that by setting
    the totals to those values so the new code path yields the same
    outputs.
    """
    return Position(
        id=pos_id,
        asset_id=0,
        qty=qty,
        avg_price=avg,
        current_price=cur,
        broker_ticker=f"X{pos_id}",
        total_invested=qty * avg,
        total_current=qty * cur,
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
    """Log in as ``profile_name`` — login auto-binds the landing profile.

    direct-landing-with-header-profile-switcher: ``POST /login`` now
    binds ``active_profile_id`` to the logged-in user's first profile
    and redirects to ``/``. The explicit ``POST /profiles/{id}/select``
    step is gone. The helper logs in as the user whose profile we
    want to land on (the seed creates one user per account).

    Returns the profile id (needed to seed classes/assets in tests
    that build state via HTTP). For pure-DB tests, callers can
    ignore the return value.

    Asserts the dashboard renders the profile name in the header
    chip (the h1 "Bem-vindo" element is gone).
    """
    client.post(
        "/login",
        data={"username": profile_name, "password": TEST_PASSWORD},
    )
    from omaha.db import SessionLocal

    db = SessionLocal()
    try:
        profile = db.query(Profile).filter(Profile.name == profile_name).first()
        assert profile is not None, f"profile {profile_name!r} not seeded"
        # The dashboard response should carry the profile name in
        # the sidebar wordmark or the chip. The h1 "Bem-vindo" is gone.
        resp = client.get("/")
        assert resp.status_code == 200, resp.text
        # The chip's <select> carries the active profile name with
        # the `selected` attribute (no ✓ glyph — the browser's own
        # selection state is enough).
        assert f'value="{profile.id}" selected>{profile_name}<' in resp.text, (
            f"profile {profile_name!r} chip not selected; got: {resp.text[:500]}"
        )
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
            # broker-csv-import-totals: write the totals so the new
            # dashboard calc (which sums these directly) preserves
            # the old ``qty * price`` test semantics.
            total_invested=Decimal(qty) * Decimal(avg),
            total_current=Decimal(qty) * Decimal(cur),
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
    # The class summary block renders the target_pct — this proves
    # the selectinload of assets + positions didn't blow up
    # (which would have raised ArgumentError pre-fix). The inline
    # pill carries the value via Alpine ``x-text`` so the SSR body
    # carries the test-id marker but not the formatted number.
    assert 'data-testid="class-target-pct-view"' in body, body
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
    assert 'data-testid="class-section-header"' in body, body
    # F14: swatch square removed — class name text carries the color
    assert 'data-testid="class-color-swatch"' not in body, body
    assert 'data-testid="class-section-name"' in body, body
    assert 'data-testid="class-target-pct-view"' in body, body
    assert 'data-testid="class-current-pct"' in body, body
    assert 'data-testid="class-compare-bar"' not in body, body

    # Per-asset row markers
    assert 'data-testid="dashboard-asset-row"' in body, body
    assert 'data-testid="asset-row-name"' in body, body
    assert 'data-testid="asset-position-count"' in body, body
    assert 'data-testid="asset-current-value"' in body, body
    assert 'data-testid="asset-pct"' in body, body
    assert 'data-testid="asset-progress-bar"' not in body, body

    # asset-table-view 4.x/6.x/7.x/9.x/10.x: proper <table>,
    # group header, sortable <th> cells, inline editor for both
    # alvo % classe and alvo % total, sticky alert card, and the
    # dashboard-level add-asset modal trigger.
    assert 'data-testid="asset-table"' in body, body
    assert 'data-testid="asset-table-th-name"' in body, body
    assert 'data-testid="asset-table-sort-name"' in body, body
    assert 'data-testid="asset-group-header"' not in body, body
    assert 'data-testid="asset-target-pct-class"' in body, body
    assert 'data-testid="asset-current-pct-class"' in body, body
    assert 'data-testid="asset-target-pct-total"' in body, body
    assert 'data-testid="asset-current-pct-total"' in body, body
    assert 'data-testid="asset-inline-edit-input"' in body, body
    assert 'data-testid="asset-target-pct-total-edit-input"' in body, body
    # class-delta-badge is only rendered when the per-class sum is off —
    # the seeded fixture puts one class into a deviating state so the pill
    # is present in the body.
    assert 'data-testid="class-delta-badge"' in body, body
    assert 'data-testid="asset-allocation-alert"' in body, body
    assert 'data-testid="asset-allocation-alert-portfolio"' in body, body
    assert 'data-testid="asset-allocation-alert-class"' in body, body
    assert 'data-testid="dashboard-add-asset-open"' in body, body
    assert 'data-testid="add-asset-modal-overlay"' in body, body
    assert 'data-testid="dashboard-add-asset-name"' in body, body
    assert 'data-testid="dashboard-add-asset-target-pct"' in body, body
    assert 'data-testid="dashboard-add-asset-submit"' in body, body
    # Alpine x-data wrapper on each class section.
    assert "x-data='classSection(" in body, body
    # The new template never renders the visible "N posicao(oes)"
    # line — D015 task scope.
    assert "posicao(oes)" not in body, body

    # Target vs current comparison — both bars present
    assert "compare-bar-target-fill" not in body, body
    assert "compare-bar-current-fill" not in body, body


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
    # F15: the portfolio header stays visible even for an empty profile.
    assert 'data-testid="portfolio-header"' in body, body
    assert "R$ 0,00" in body, body


def test_dashboard_sends_no_store_cache_control(client: TestClient) -> None:
    """The dashboard HTML MUST come back with ``Cache-Control: no-store`` so
    the browser never serves a stale template after we ship a fix (e.g.
    the import-modal class color change — see
    ``investigate-import-class-color``). The middleware is the only
    source of this header; static assets and the login page are
    intentionally exempt.
    """
    _login_and_select(client, profile_name="Italo")

    dashboard = client.get("/")
    assert dashboard.status_code == 200, dashboard.text
    assert dashboard.headers.get("cache-control") == "no-store", (
        f"expected Cache-Control: no-store on dashboard, got "
        f"{dashboard.headers.get('cache-control')!r}"
    )

    # Static assets are served by Starlette's StaticFiles — the
    # middleware must NOT inject no-store on them (production nginx
    # is responsible for the long-lived cache header).
    css = client.get("/static/app.css")
    assert css.status_code == 200, css.text
    assert css.headers.get("cache-control") != "no-store", (
        f"middleware unexpectedly injected no-store on /static/app.css: "
        f"{css.headers.get('cache-control')!r}"
    )

    # JSON API responses are exempt (REST caching semantics).
    api = client.get("/api/classes")
    # 401 / 405 / 200 are all fine for this assertion — what matters
    # is the header is not no-store.
    assert api.headers.get("cache-control") != "no-store", (
        f"middleware unexpectedly injected no-store on /api/classes: "
        f"{api.headers.get('cache-control')!r}"
    )

    # /login is on the explicit skip list (no authenticated data to
    # protect; let the browser use its default heuristic). When the
    # caller is already authenticated the route redirects to /, so
    # we need an UNAUTHENTICATED client to actually exercise the
    # /login code path. Use a fresh client from a new context manager
    # — the per-test ``client`` fixture was already logged in by
    # ``_login_and_select`` above.
    from fastapi.testclient import TestClient as _TestClient

    from omaha.main import app as _app

    with _TestClient(_app) as anon_client:
        login_page = anon_client.get("/login", follow_redirects=False)
    assert login_page.status_code == 200, login_page.text
    assert login_page.headers.get("cache-control") != "no-store", (
        f"middleware unexpectedly injected no-store on /login: "
        f"{login_page.headers.get('cache-control')!r}"
    )


# ---------------------------------------------------------------------------
# class-section-consolidated-totals — header stats + colgroup
# ---------------------------------------------------------------------------


import json as _json  # noqa: E402  — local import keeps the upstream module-order stable
import re as _re  # noqa: E402


def _extract_class_section_blocks(body: str) -> list[str]:
    """Return one HTML slice per <article class="class-section"> block.

    The dashboard renders one class section per ``class_aggregates``
    entry; this helper splits the body at the article boundary so
    per-class assertions can target a single block.
    """
    return _re.findall(
        r'<article class="class-section"[^>]*>.*?(?=<article class="class-section"|</section>)',
        body,
        flags=_re.DOTALL,
    )


def test_class_section_renders_consolidated_value(client: TestClient) -> None:
    """class-section-consolidated-totals 4.1: the new ``.hdr-valor``
    cell carries the consolidated ``current_value`` formatter.

    The cell uses Alpine ``x-text`` to render the BRL string at
    hydration time, so the server-rendered body carries the
    expression, not the formatted value. The assertion verifies the
    ``x-text`` expression matches the compact BRL formatter contract
    (BRL with zero fraction digits, em-dash sentinel for empty
    classes). Real hydration is exercised by the e2e suite.
    """
    profile_id = _login_and_select(client, profile_name="Italo")
    # qty 85.5 * price 110 = 9405; formatBRLCompact → "R$ 9.405".
    _seed_class_with_position(
        profile_id=profile_id,
        class_name="Renda Fixa",
        target_pct="60.00",
        asset_name="TESOURO",
        qty="85.5",
        avg="100",
        cur="110",
        broker_ticker="TESOURO_2029",
    )

    r = client.get("/")
    assert r.status_code == 200, r.text
    body = r.text

    assert 'data-testid="class-total-value"' in body, body

    blocks = _extract_class_section_blocks(body)
    assert blocks, "no class-section article found in body"
    block = blocks[0]
    match = _re.search(
        r'<span class="hdr-valor"[^>]*data-testid="class-total-value"[^>]*x-text="([^"]+)"',
        block,
    )
    assert match is not None, f"class-total-value x-text not found in {block[:500]!r}"
    expr = match.group(1)
    # F15 totals row reuses centralized money formatting.
    assert "formatMoney" in expr, f"expected formatMoney in x-text, got {expr!r}"
    assert "classCurrentValue" in expr, f"expected classCurrentValue in x-text, got {expr!r}"


def test_class_section_renders_em_dash_when_empty(client: TestClient) -> None:
    """class-section-consolidated-totals 4.2: a class with no assets
    falls back to the em-dash sentinel at ``.hdr-valor`` instead of
    ``R$ 0`` (verified via the ``x-text`` expression contract; real
    hydration runs in e2e).
    """
    profile_id = _login_and_select(client, profile_name="Italo")
    from omaha.db import SessionLocal

    db = SessionLocal()
    try:
        db.add(
            AssetClass(
                profile_id=profile_id,
                name="Vazia",
                target_pct=Decimal("10.00"),
                display_order=0,
            )
        )
        db.commit()
    finally:
        db.close()

    r = client.get("/")
    assert r.status_code == 200, r.text
    body = r.text

    blocks = _extract_class_section_blocks(body)
    assert blocks, "no class-section article found in body"
    block = blocks[0]
    match = _re.search(
        r'<span class="hdr-valor"[^>]*data-testid="class-total-value"[^>]*x-text="([^"]+)"',
        block,
    )
    assert match is not None, f"class-total-value x-text not found in {block[:500]!r}"
    expr = match.group(1)
    assert expr == "formatMoney(classCurrentValue)", (
        f"empty-class totals row should use centralized formatter, got {expr!r}"
    )


def test_class_section_renders_pct_with_one_decimal_when_empty(client: TestClient) -> None:
    """F15: totals-row portfolio current cell keeps one-decimal pct formatting."""
    profile_id = _login_and_select(client, profile_name="Italo")
    from omaha.db import SessionLocal

    db = SessionLocal()
    try:
        db.add(
            AssetClass(
                profile_id=profile_id,
                name="Vazia",
                target_pct=Decimal("10.00"),
                display_order=0,
            )
        )
        db.commit()
    finally:
        db.close()

    r = client.get("/")
    assert r.status_code == 200, r.text
    body = r.text

    blocks = _extract_class_section_blocks(body)
    assert blocks, "no class-section article found in body"
    block = blocks[0]
    match = _re.search(
        r'<span class="pct-current-pill"[^>]*data-testid="class-current-pct"[^>]*x-text="([^"]+)"',
        block,
    )
    assert match is not None, f"class-current-pct x-text not found in {block[:500]!r}"
    expr = match.group(1)
    expected = "formatPctRounded(classCurrentPct)"
    assert expr == expected, f"unexpected class-current-pct x-text: {expr!r}"


def test_class_section_delete_btn_precedes_stats(client: TestClient) -> None:
    """class-section-consolidated-totals 4.4: the × delete button
    sits BEFORE ``class-total-value`` in DOM order (it's grouped
    with the class identity, not the trailing stats row).
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

    blocks = _extract_class_section_blocks(body)
    assert blocks, "no class-section article found in body"
    block = blocks[0]

    delete_idx = block.find('data-testid="class-delete-btn"')
    total_idx = block.find('data-testid="class-total-value"')
    alvo_idx = block.find('data-testid="class-target-pct-view"')
    atual_idx = block.find('data-testid="class-current-pct"')

    assert delete_idx != -1, "class-delete-btn not found in class block"
    assert total_idx != -1, "class-total-value not found in class block"
    assert alvo_idx != -1, "class-target-pct-view not found in class block"
    assert atual_idx != -1, "class-current-pct not found in class block"

    # The × button lives inside .hdr-leading (cols 1-3); the stats
    # follow in cols 4-8. The DOM order matches the grid order.
    assert delete_idx < total_idx, (
        f"class-delete-btn (idx {delete_idx}) must precede class-total-value (idx {total_idx})"
    )
    assert total_idx < atual_idx, (
        f"class-total-value (idx {total_idx}) must precede class-current-pct (idx {atual_idx})"
    )
    assert atual_idx < alvo_idx, (
        f"class-current-pct (idx {atual_idx}) must precede class-target-pct-view (idx {alvo_idx})"
    )


def test_asset_table_has_colgroup(client: TestClient) -> None:
    """class-section-consolidated-totals 4.5: the asset table
    declares a ``<colgroup>`` with exactly 14 ``<col>`` elements,
    one per column, so the ``table-layout: fixed`` widths are
    authoritative.
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

    # Find every <table class="...asset-table...">...</table> region and
    # check exactly one of them carries a colgroup with 8 cols.
    table_matches = _re.findall(
        r'<table class="[^"]*asset-table[^"]*"[^>]*>(.*?)</table>',
        body,
        flags=_re.DOTALL,
    )
    assert table_matches, 'no <table class="...asset-table..."> found'

    tables_with_colgroup = [t for t in table_matches if "<colgroup>" in t and "</colgroup>" in t]
    assert len(tables_with_colgroup) == 1, (
        f'expected exactly 1 <table class="...asset-table..."> with <colgroup>, '
        f"found {len(tables_with_colgroup)}"
    )

    cols = _re.findall(r"<col\b", tables_with_colgroup[0])
    assert len(cols) == 14, f"expected 14 <col> elements, found {len(cols)}"


def test_class_data_blob_exposes_current_value(client: TestClient) -> None:
    """class-section-consolidated-totals 4.6: the Alpine
    ``classSection(...)`` factory receives the class's
    ``current_value`` as a numeric field (NOT undefined).
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

    # Extract the first ``x-data='classSection({...})'`` blob. The
    # template escapes single-quotes in the JSON via Jinja's |tojson,
    # so a balanced-brace scan inside the attribute value is safe.
    attr_match = _re.search(r"x-data='classSection\((\{.*?\})\)'", body, flags=_re.DOTALL)
    assert attr_match is not None, "classSection x-data blob not found in body"
    payload = attr_match.group(1)
    # tojson may emit double-quoted JSON inside single-quoted attr
    # value. Parse with stdlib json; on failure, dump for triage.
    try:
        parsed = _json.loads(payload)
    except _json.JSONDecodeError as exc:  # pragma: no cover — defensive
        raise AssertionError(
            f"classSection JSON malformed: {exc}; payload={payload[:300]!r}"
        ) from exc
    assert "current_value" in parsed, f"current_value missing from classSection JSON: {parsed!r}"
    assert isinstance(parsed["current_value"], (int, float)), (
        f"current_value must be numeric, got {type(parsed['current_value']).__name__}: "
        f"{parsed['current_value']!r}"
    )
    # 10 shares @ 110 current_price → 1100.00.
    assert parsed["current_value"] == pytest.approx(1100.0, abs=0.01), (
        f"expected current_value ≈ 1100.0, got {parsed['current_value']!r}"
    )
