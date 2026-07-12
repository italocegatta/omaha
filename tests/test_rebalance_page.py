"""Integration tests for the /rebalance page (``rebalance-page`` change).

Covers the spec scenarios from
``openspec/changes/rebalance-page/specs/rebalance-page/spec.md`` and
``openspec/changes/rebalance-page/specs/rebalance-route/spec.md``
(contract-extension scenarios). Exercises the GET + POST handlers
in :mod:`omaha.routes.pages` against the in-process FastAPI app +
session-scoped SQLite DB.

Marker convention
-----------------
The file lives under ``tests/`` and hits the DB + TestClient, so
its prefix must be registered in ``tests/conftest.py::_INTEGRATION_PREFIXES``
(per AGENTS.md "Test marker rule"). The prefix entry was added in
the same change.
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from omaha.models import Asset, AssetClass, QuoteKind

TEST_PASSWORD = "test-password"
_PROFILE_OWNERS = {1: "Italo", 2: "Ana"}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _wipe_tables(_omaha_test_env: dict[str, str]) -> None:
    """Wipe classes / assets / positions before each test (via fresh engine)."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    engine = create_engine(_omaha_test_env["db_url"], future=True)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    db = SessionLocal()
    try:
        # Order matters: positions → assets → classes (FK chain).
        from omaha.models import Position

        db.query(Position).delete()
        db.query(Asset).delete()
        db.query(AssetClass).delete()
        db.commit()
    finally:
        db.close()
        engine.dispose()
    yield


def _login_and_select(client: TestClient, profile_id: int = 1) -> None:
    """Log in with seed credentials and bind active_profile_id."""
    client.post(
        "/login",
        data={"username": _PROFILE_OWNERS[profile_id], "password": TEST_PASSWORD},
        follow_redirects=False,
    )


def _seed_class(
    profile_id: int,
    name: str,
    target_pct: str,
    assets: list[tuple[str, str]],
    _omaha_test_env: dict[str, str] | None = None,
) -> int:
    """Create a class + its assets, return the class id."""
    assert _omaha_test_env is not None
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    engine = create_engine(_omaha_test_env["db_url"], future=True)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    db = SessionLocal()
    try:
        klass = AssetClass(
            profile_id=profile_id,
            name=name,
            target_pct=Decimal(target_pct),
            display_order=0,
            quote_kind=QuoteKind.NONE.value,
        )
        db.add(klass)
        db.flush()
        for index, (asset_name, asset_pct) in enumerate(assets):
            db.add(
                Asset(
                    asset_class_id=klass.id,
                    name=asset_name,
                    target_pct=Decimal(asset_pct),
                    display_order=index,
                )
            )
        db.commit()
        return klass.id
    finally:
        db.close()
        engine.dispose()


# ---------------------------------------------------------------------------
# §"GET /rebalance renders the rebalance plan page"
# ---------------------------------------------------------------------------


def test_unauthenticated_get_rebalance_bounces_to_login(client: TestClient) -> None:
    """``GET /rebalanceamento`` without a session returns 303 to /login."""
    response = client.get("/rebalanceamento", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_get_legacy_rebalance_returns_404(client: TestClient) -> None:
    """``GET /rebalance`` returns HTTP 404 after F02 (no alias, D1).

    The owner decided that the legacy ``/rebalance`` URL would not
    be aliased to ``/rebalanceamento`` — the breakage is exposed
    on purpose so a regression would surface immediately.
    """
    response = client.get("/rebalance", follow_redirects=False)
    assert response.status_code == 404


def test_get_legacy_dashboard_returns_404(client: TestClient) -> None:
    """``GET /dashboard`` returns HTTP 404 after F02 (no alias, D1)."""
    response = client.get("/dashboard", follow_redirects=False)
    assert response.status_code == 404


def test_get_rebalanceamento_empty_profile_renders_empty_state(client: TestClient) -> None:
    """An authenticated user with zero classes sees the empty-state card."""
    _login_and_select(client, profile_id=1)

    response = client.get("/rebalanceamento")

    assert response.status_code == 200
    body = response.text
    assert 'data-testid="rebalance-empty-state"' in body
    assert "Nenhuma classe cadastrada" in body
    # In-body form is present but inert — input + button carry disabled.
    assert 'data-testid="rebalance-form"' in body
    assert 'data-testid="rebalance-contribution-input"' in body
    assert "disabled" in body  # at least one disabled element


def test_get_rebalanceamento_populated_profile_renders_zero_plan(
    client: TestClient, _omaha_test_env: dict[str, str]
) -> None:
    """A profile with classes and no prior aporte shows the zero plan."""
    _seed_two_classes(_omaha_test_env)
    _login_and_select(client, profile_id=1)

    response = client.get("/rebalanceamento")

    assert response.status_code == 200
    body = response.text
    assert 'data-testid="rebalance-plan"' in body
    assert 'data-testid="rebalance-empty-state"' not in body
    assert '"contribution": 0.0' in body or '"contribution":0.0' in body
    assert 'name="min_deviation_value"' in body
    assert 'name="min_deviation_pct"' in body
    assert 'value="1000.0"' in body or 'value="1000"' in body
    assert 'value="1.0"' in body or 'value="1"' in body
    # In-body form is present and not inert (profile has classes).
    assert 'data-testid="rebalance-form"' in body


def test_get_rentabilidade_renders_stub(client: TestClient) -> None:
    """``GET /rentabilidade`` renders the F02 stub (D6)."""
    _login_and_select(client, profile_id=1)

    response = client.get("/rentabilidade")

    assert response.status_code == 200
    body = response.text
    assert 'data-testid="rentabilidade-stub"' in body
    assert "Em construção" in body


def test_get_proventos_renders_stub(client: TestClient) -> None:
    """``GET /proventos`` renders the F02 stub (D6)."""
    _login_and_select(client, profile_id=1)

    response = client.get("/proventos")

    assert response.status_code == 200
    body = response.text
    assert 'data-testid="proventos-stub"' in body
    assert "Em construção" in body


def test_get_patrimonio_renders_dashboard(
    client: TestClient, _omaha_test_env: dict[str, str]
) -> None:
    """``GET /patrimonio`` is the F02 canonical dashboard URL (D1)."""
    _seed_two_classes(_omaha_test_env)
    _login_and_select(client, profile_id=1)

    response = client.get("/patrimonio")

    assert response.status_code == 200
    body = response.text
    # Patrimonio portfolio header (F02 D3 spec). The wrapper renders
    # when portfolio.current_value > 0; the fixture seeds positions so
    # this is non-zero.
    assert 'data-testid="patrimonio-portfolio-header"' in body
    # Action buttons row at the top of the body.
    assert 'data-testid="patrimonio-actions"' in body
    assert 'data-testid="dashboard-import-btn"' in body
    assert 'data-testid="dashboard-add-asset-open"' in body
    assert 'data-testid="empty-state-create-class"' in body
    # Top nav (F02 D2).
    assert 'data-testid="app-tab-nav"' in body
    assert 'data-testid="app-tab-btn-patrimonio"' in body


# ---------------------------------------------------------------------------
# §"POST /rebalance renders the plan"
# ---------------------------------------------------------------------------


def _seed_two_classes(_omaha_test_env: dict[str, str]) -> None:
    _seed_class(1, "RF", "60", [("Selic", "100")], _omaha_test_env=_omaha_test_env)
    _seed_class(1, "RV", "40", [("PETR4", "100")], _omaha_test_env=_omaha_test_env)
    _seed_positions(_omaha_test_env, {"Selic": 6_000.0, "PETR4": 4_000.0})


def _seed_positions(_omaha_test_env: dict[str, str], by_asset: dict[str, float]) -> None:
    """Add one ``Position`` per asset name with the given current_value.

    Required by Phase 4 (``rebalance-engine``) — the CVXPY solver's
    validator rejects profiles whose ``current_value`` sum is zero.
    Pre-Phase-4 stub returned a frozen fixture that bypassed this
    check.
    """
    import os

    from omaha.db import SessionLocal
    from omaha.models import Position

    db_url = _omaha_test_env["db_url"]
    os.environ["DATABASE_URL"] = db_url

    with SessionLocal() as db:
        for asset_name, current_value in by_asset.items():
            asset = db.query(Asset).filter(Asset.name == asset_name).one()
            pos = Position(
                asset_id=asset.id,
                broker_ticker=asset_name,
                qty=Decimal("1"),
                avg_price=Decimal(str(current_value)),
                current_price=Decimal(str(current_value)),
                total_invested=Decimal(str(current_value)),
                total_current=Decimal(str(current_value)),
            )
            db.add(pos)
        db.commit()


def _mutate_position_current_value(
    _omaha_test_env: dict[str, str], asset_name: str, current_value: float
) -> None:
    """Update one seeded position so the next GET must recompute plan data."""
    import os

    from omaha.db import SessionLocal
    from omaha.models import Position

    db_url = _omaha_test_env["db_url"]
    os.environ["DATABASE_URL"] = db_url

    with SessionLocal() as db:
        position = (
            db.query(Position)
            .join(Asset, Position.asset_id == Asset.id)
            .filter(Asset.name == asset_name)
            .one()
        )
        value = Decimal(str(current_value))
        position.current_price = value
        position.total_current = value
        db.commit()


def test_post_rebalanceamento_valid_contribution_renders_plan(
    client: TestClient, _omaha_test_env: dict[str, str]
) -> None:
    """``POST /rebalanceamento`` with a valid finite aporte renders the plan."""
    _seed_two_classes(_omaha_test_env)
    _login_and_select(client, profile_id=1)

    response = client.post("/rebalanceamento", data={"contribution": "5000.00"})

    assert response.status_code == 200
    body = response.text
    # Plan layout rendered.
    assert 'data-testid="rebalance-plan"' in body
    # Params bar (aporte + thresholds + submit).
    assert 'data-testid="rebalance-params-bar"' in body
    # Asset plan table renders (stub fixture has at least 1 asset_plan row).
    assert 'data-testid="rebalance-asset-table"' in body
    # Class deviation summary renders.
    assert 'data-testid="rebalance-class-summary"' in body
    assert 'data-testid="rebalance-filter-bar"' not in body


def test_post_rebalanceamento_thresholds_round_trip_into_rendered_plan(
    client: TestClient, _omaha_test_env: dict[str, str]
) -> None:
    """Threshold fields submit as real form inputs and re-render current values."""
    _seed_class(1, "RF", "50", [("Selic", "100")], _omaha_test_env=_omaha_test_env)
    _seed_class(1, "RV", "50", [("PETR4", "100")], _omaha_test_env=_omaha_test_env)
    _seed_positions(_omaha_test_env, {"Selic": 201_500.0, "PETR4": 198_500.0})
    _login_and_select(client, profile_id=1)

    response = client.post(
        "/rebalanceamento",
        data={
            "contribution": "0",
            "min_deviation_value": "2500",
            "min_deviation_pct": "2",
        },
    )

    assert response.status_code == 200
    body = response.text
    assert 'name="min_deviation_value"' in body
    assert 'name="min_deviation_pct"' in body
    assert 'value="2500.0"' in body or 'value="2500"' in body
    assert 'value="2.0"' in body or 'value="2"' in body
    assert '"action": "hold"' in body or '"action":"hold"' in body


def test_post_rebalanceamento_negative_threshold_renders_form_error(
    client: TestClient, _omaha_test_env: dict[str, str]
) -> None:
    """Page rejects negative threshold fields without issuing a 4xx."""
    _seed_two_classes(_omaha_test_env)
    _login_and_select(client, profile_id=1)

    response = client.post(
        "/rebalanceamento",
        data={"contribution": "0", "min_deviation_value": "-1"},
    )

    assert response.status_code == 200
    body = response.text
    assert 'data-testid="rebalance-form-error"' in body
    assert "zero ou positivo" in body


def test_post_rebalanceamento_zero_contribution_renders_plan(
    client: TestClient, _omaha_test_env: dict[str, str]
) -> None:
    """``contribution = 0`` renders the plan (zero is valid)."""
    _seed_two_classes(_omaha_test_env)
    _login_and_select(client, profile_id=1)

    response = client.post("/rebalanceamento", data={"contribution": "0"})

    assert response.status_code == 200
    assert 'data-testid="rebalance-plan"' in response.text
    assert 'data-testid="rebalance-params-bar"' in response.text


def test_post_rebalanceamento_negative_contribution_renders_form_error(
    client: TestClient, _omaha_test_env: dict[str, str]
) -> None:
    """``contribution = -1000`` re-renders with the engine's rejection message.

    Per design Decision 2, the Phase 4 CVXPY engine rejects negative
    contributions with ``RebalanceValidationError`` ("O aporte
    informado nao pode ser negativo."). The page maps the error to
    inline ``form_error`` rather than rendering a plan. The page
    client-side gates ``< 0`` for v1 (so users do not normally see
    this), but the server-side defense still surfaces here when the
    gate is bypassed.
    """
    _seed_two_classes(_omaha_test_env)
    _login_and_select(client, profile_id=1)

    response = client.post("/rebalanceamento", data={"contribution": "-1000"})

    assert response.status_code == 200
    body = response.text
    assert 'data-testid="rebalance-form-error"' in body
    assert "negativo" in body
    assert 'data-testid="rebalance-plan"' not in body


def test_post_rebalanceamento_missing_contribution_renders_zero_plan(
    client: TestClient, _omaha_test_env: dict[str, str]
) -> None:
    """Missing ``contribution`` field normalizes to zero and renders plan."""
    _seed_two_classes(_omaha_test_env)
    _login_and_select(client, profile_id=1)

    response = client.post("/rebalanceamento", data={})

    assert response.status_code == 200
    body = response.text
    assert 'data-testid="rebalance-plan"' in body
    assert 'data-testid="rebalance-form-error"' not in body
    assert '"contribution": 0.0' in body or '"contribution":0.0' in body


def test_rebalanceamento_persists_aporte_per_profile_and_recomputes_on_get(
    client: TestClient, _omaha_test_env: dict[str, str]
) -> None:
    """Session keeps aporte per profile while GET recomputes from fresh DB data."""
    _seed_two_classes(_omaha_test_env)
    _seed_class(2, "Exterior", "100", [("IVVB11", "100")], _omaha_test_env=_omaha_test_env)
    _seed_positions(_omaha_test_env, {"IVVB11": 4321.0})
    _login_and_select(client, profile_id=1)

    response = client.post("/rebalanceamento", data={"contribution": "5000"})
    assert response.status_code == 200
    assert '"contribution": 5000.0' in response.text or '"contribution":5000.0' in response.text

    client.post("/profiles/2/select", follow_redirects=False)
    profile_two = client.get("/rebalanceamento")
    assert profile_two.status_code == 200
    assert '"contribution": 0.0' in profile_two.text or '"contribution":0.0' in profile_two.text

    client.post("/profiles/1/select", follow_redirects=False)
    _mutate_position_current_value(_omaha_test_env, "Selic", 1234.56)
    refreshed = client.get("/rebalanceamento")
    assert refreshed.status_code == 200
    assert '"contribution": 5000.0' in refreshed.text or '"contribution":5000.0' in refreshed.text
    assert "1234.56" in refreshed.text


def test_rebalanceamento_logout_clears_persisted_aporte(
    client: TestClient, _omaha_test_env: dict[str, str]
) -> None:
    """Logout clears session-backed aporte memory and next login restarts from zero."""
    _seed_two_classes(_omaha_test_env)
    _login_and_select(client, profile_id=1)

    response = client.post("/rebalanceamento", data={"contribution": "5000"})
    assert response.status_code == 200
    assert '"contribution": 5000.0' in response.text or '"contribution":5000.0' in response.text

    client.post("/logout", follow_redirects=False)
    _login_and_select(client, profile_id=1)
    after_relogin = client.get("/rebalanceamento")
    assert after_relogin.status_code == 200
    assert '"contribution": 0.0' in after_relogin.text or '"contribution":0.0' in after_relogin.text


def test_post_rebalanceamento_invalid_contribution_renders_form_error(
    client: TestClient, _omaha_test_env: dict[str, str]
) -> None:
    """Non-numeric contribution re-renders with the finite-float message."""
    _seed_two_classes(_omaha_test_env)
    _login_and_select(client, profile_id=1)

    response = client.post("/rebalanceamento", data={"contribution": "abc"})

    assert response.status_code == 200
    body = response.text
    assert 'data-testid="rebalance-form-error"' in body
    assert "Valor inválido" in body


def test_post_rebalanceamento_solver_validation_error_renders_inline(
    client: TestClient, _omaha_test_env: dict[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """A solver ``RebalanceValidationError`` is mapped to ``form_error``."""
    from omaha.rebalance import glue
    from omaha.rebalance.models import RebalanceValidationError
    from omaha.routes import pages as pages_routes

    _seed_two_classes(_omaha_test_env)
    _login_and_select(client, profile_id=1)

    def raising_run_rebalance(db, profile, contribution, *, solver=None, **kwargs):  # noqa: ARG001
        raise RebalanceValidationError("Classes devem somar 100%")

    monkeypatch.setattr(pages_routes, "run_rebalance", raising_run_rebalance)
    # Belt-and-suspenders: also patch the glue import path in case
    # the pages module captured a stale reference at import time.
    monkeypatch.setattr(glue, "run_rebalance", raising_run_rebalance)

    response = client.post("/rebalanceamento", data={"contribution": "1000"})

    assert response.status_code == 200
    body = response.text
    assert 'data-testid="rebalance-form-error"' in body
    assert "Classes devem somar 100%" in body


# ---------------------------------------------------------------------------
# §"Asset plan table renders eight POC-parity columns plus a data attribute"
# ---------------------------------------------------------------------------


def test_asset_plan_table_has_eight_poc_parity_columns(
    client: TestClient, _omaha_test_env: dict[str, str]
) -> None:
    """The declarative column model preserves F27's eight-column order."""
    _seed_two_classes(_omaha_test_env)
    _login_and_select(client, profile_id=1)

    response = client.post("/rebalanceamento", data={"contribution": "5000"})
    assert response.status_code == 200
    body = response.text

    columns = [
        ("action", "Ação"),
        ("category_name", "Classe"),
        ("asset_name", "Ativo"),
        ("current_value", "Atual"),
        ("target_value", "Alvo"),
        ("deviation", "Desvio"),
        ("projected_value", "Projetado"),
        ("operation", "Operação"),
    ]
    assert body.count('<template x-for="column in columns" :key="column.key">') == 2
    for key, label in columns:
        assert f"key: '{key}'" in body, f"missing declarative table column: {key}"
        assert f"label: '{label}'" in body, f"missing PT-BR label for {key}"
    column_positions = [body.index(f"key: '{key}'") for key, _ in columns]
    assert column_positions == sorted(column_positions)
    assert "label: 'Compra'," not in body
    assert "label: 'Venda'," not in body
    assert "label: 'Qtd'," not in body
    assert ':data-asset-key="row.asset_key"' in body
    assert "headerFilters:" in body
    assert "headerRangeFilters:" in body
    assert "searchTerm" not in body
    assert "rebalance-filter-search" not in body


def test_asset_plan_operation_cell_includes_trade_quantity(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, _omaha_test_env: dict[str, str]
) -> None:
    """POC-parity Operação cell formats amount and available quantity."""
    from omaha.rebalance.schemas import (
        RebalanceAssetPlanRow,
        RebalanceCategoryPlanRow,
        RebalancePlanMetrics,
        RebalancePlanResponse,
    )
    from omaha.routes import pages as pages_routes

    _seed_two_classes(_omaha_test_env)
    _login_and_select(client, profile_id=1)

    def fake_run_rebalance(db, profile, contribution, **kwargs):  # noqa: ARG001
        return RebalancePlanResponse(
            asset_plan=[
                RebalanceAssetPlanRow(
                    asset_key="brl-buy",
                    asset_name="BRL Buy",
                    category_name="RF",
                    current_value=100.0,
                    target_value=200.0,
                    buy_amount=1000.0,
                    sell_amount=0.0,
                    trade_quantity=50.0,
                    projected_value=1100.0,
                    action="buy",
                ),
                RebalanceAssetPlanRow(
                    asset_key="no-price",
                    asset_name="No Price",
                    category_name="RF",
                    current_value=100.0,
                    target_value=150.0,
                    buy_amount=50.0,
                    sell_amount=0.0,
                    trade_quantity=None,
                    projected_value=150.0,
                    action="buy",
                ),
            ],
            category_plan=[
                RebalanceCategoryPlanRow(
                    category_name="RF",
                    current_value=200.0,
                    projected_value=1250.0,
                    delta=1050.0,
                )
            ],
            metrics=RebalancePlanMetrics(
                contribution=0.0,
                total_buy=1050.0,
                total_sell=0.0,
                residual_cash=0.0,
                current_deviation_pct=0.0,
                projected_deviation_pct=0.0,
            ),
            warnings=[],
            applied_policy="sentinel",
        )

    monkeypatch.setattr(pages_routes, "run_rebalance", fake_run_rebalance)

    response = client.post("/rebalanceamento", data={"contribution": "0"})
    assert response.status_code == 200
    body = response.text

    assert "key: 'operation'" in body
    assert "cellFormat: 'operation'" in body
    assert "formatOperation: function (row)" in body
    assert "this.formatQuantity(row.trade_quantity, row.asset_name)" in body
    assert "formatDeviationCombined: function (row)" in body
    assert "return this.formatBRL(row.deviation_value, 0)" in body
    assert '"trade_quantity": 50.0' in body or '"trade_quantity":50.0' in body
    assert '"trade_quantity": null' in body or '"trade_quantity":null' in body


def test_class_deviation_summary_renders(
    client: TestClient, _omaha_test_env: dict[str, str]
) -> None:
    """The class deviation summary section renders with class cards."""
    _seed_two_classes(_omaha_test_env)
    _login_and_select(client, profile_id=1)

    response = client.post("/rebalanceamento", data={"contribution": "5000"})
    assert response.status_code == 200
    body = response.text

    assert 'data-testid="rebalance-class-summary"' in body


# ---------------------------------------------------------------------------
# §"Stub banner conditional on applied_policy"
# ---------------------------------------------------------------------------


def test_footer_policy_and_stub_banner_not_rendered(
    client: TestClient,
    _omaha_test_env: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Footer policy/stub surfaces were removed from the page.

    Route payload still carries ``applied_policy`` and warnings, but the
    page no longer renders them at the bottom.
    """
    from omaha.rebalance import glue
    from omaha.rebalance.solver_stub import stub_solver

    monkeypatch.setattr(glue, "cvxpy_solver", lambda s, p, q, c: stub_solver(s, p, q, c))

    _seed_two_classes(_omaha_test_env)
    _login_and_select(client, profile_id=1)

    response = client.post("/rebalanceamento", data={"contribution": "5000"})
    assert response.status_code == 200
    body = response.text

    assert 'data-testid="rebalance-applied-policy"' not in body
    assert 'data-testid="rebalance-stub-banner"' not in body


def test_warnings_panel_not_rendered(client: TestClient, _omaha_test_env: dict[str, str]) -> None:
    """Warnings remain in payload but are hidden from page footer."""
    _seed_two_classes(_omaha_test_env)
    _login_and_select(client, profile_id=1)

    response = client.post("/rebalanceamento", data={"contribution": "5000"})
    assert response.status_code == 200
    body = response.text

    assert 'data-testid="rebalance-warnings"' not in body


# ---------------------------------------------------------------------------
# Top nav (F02, D2) — the rebalance tab carries aria-current on /rebalanceamento
# ---------------------------------------------------------------------------


def test_rebalanceamento_tab_is_active_on_page(client: TestClient) -> None:
    """``GET /rebalanceamento`` highlights the Rebalanceamento tab."""
    _login_and_select(client, profile_id=1)

    response = client.get("/rebalanceamento")
    assert response.status_code == 200
    body = response.text

    # Top nav is present.
    assert 'data-testid="app-tab-nav"' in body
    # The Rebalanceamento tab carries aria-current + the active modifier.
    assert 'data-testid="app-tab-btn-rebalanceamento"' in body
    assert 'class="tab-nav__btn tab-nav__btn--active"' in body
    assert 'aria-current="true"' in body


def test_patrimonio_tab_is_active_on_patrimonio(client: TestClient) -> None:
    """``GET /`` and ``GET /patrimonio`` highlight the Patrimônio tab."""
    import re

    _login_and_select(client, profile_id=1)

    for path in ("/", "/patrimonio"):
        response = client.get(path)
        assert response.status_code == 200, response.text
        body = response.text
        assert 'data-testid="app-tab-btn-patrimonio"' in body
        # The activo tab carries both the active modifier class AND
        # aria-current="true" on the matching tag. Verify both on
        # the patrimonio tab specifically (not just that the active
        # class is present somewhere in the body).
        match = re.search(
            r'<a[^>]*data-testid="app-tab-btn-patrimonio"[^>]*>',
            body,
        )
        assert match is not None, f"patrimonio tab <a> not found in body for path {path}"
        tag = match.group(0)
        assert "tab-nav__btn--active" in tag, f"patrimonio tab not active on {path}: {tag!r}"
        assert 'aria-current="true"' in tag, (
            f"patrimonio tab missing aria-current on {path}: {tag!r}"
        )
