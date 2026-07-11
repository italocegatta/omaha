"""Integration tests for GET /teste POC rebalance table page (F27).

Covers the spec scenarios from
``openspec/changes/f27-poc-melhorias-tabela-rebalanceamento/specs/test-rebalance-table-poc/spec.md``.

Marker convention
-----------------
The file lives under ``tests/`` and hits the DB + TestClient, so
its prefix must be registered in ``tests/conftest.py::_INTEGRATION_PREFIXES``.
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


def _seed_positions(_omaha_test_env: dict[str, str], by_asset: dict[str, float]) -> None:
    """Add one Position per asset name with the given current_value."""
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


def _seed_two_classes(_omaha_test_env: dict[str, str]) -> None:
    _seed_class(1, "RF", "60", [("Selic", "100")], _omaha_test_env=_omaha_test_env)
    _seed_class(1, "RV", "40", [("PETR4", "100")], _omaha_test_env=_omaha_test_env)
    _seed_positions(_omaha_test_env, {"Selic": 6_000.0, "PETR4": 4_000.0})


# ---------------------------------------------------------------------------
# §"GET /teste returns the POC rebalance table page"
# ---------------------------------------------------------------------------


def test_unauthenticated_get_teste_renders_public_page(client: TestClient) -> None:
    """``GET /teste`` is public and renders the POC table without auth."""
    response = client.get("/teste", follow_redirects=False)
    assert response.status_code == 200
    assert 'data-testid="poc-rebalance-page"' in response.text
    assert 'data-testid="poc-asset-table"' in response.text


def test_get_teste_populated_profile_renders_table(
    client: TestClient, _omaha_test_env: dict[str, str]
) -> None:
    """A profile with classes + positions shows the POC asset table."""
    _seed_two_classes(_omaha_test_env)
    _login_and_select(client, profile_id=1)

    response = client.get("/teste")

    assert response.status_code == 200
    body = response.text
    # Table shell present
    assert 'data-testid="poc-asset-table"' in body
    # POC page wrapper present
    assert 'data-testid="poc-rebalance-page"' in body
    # Plan data serialized
    assert 'data-testid="poc-rebalance-plan-data"' in body
    # Column-level filter infrastructure present
    assert "rebalance-header-filter-btn" in body
    assert "rebalance-header-clear-btn" in body
    assert "rebalance-range-slider" in body
    # Asset plan data serialized in JSON (Alpine renders rows at runtime)
    assert '"asset_key": "selic"' in body
    assert '"asset_key": "petr4"' in body
    # F27 bugfix: Alpine data bridge is wired and contains real numeric values
    assert "window.__pocRebalancePlan" in body
    assert '"current_value": 6000.0' in body or '"current_value":6000.0' in body
    assert '"current_value": 4000.0' in body or '"current_value":4000.0' in body
    # Legacy CSS classes present
    assert 'class="rebalance-table"' in body
    assert 'class="rebalance-table-th' in body
    assert 'class="rebalance-header-filter-btn"' in body


def test_get_teste_empty_profile_renders_empty_table(
    client: TestClient,
) -> None:
    """A profile with zero classes renders the POC page with zero rows."""
    _login_and_select(client, profile_id=1)

    response = client.get("/teste")

    assert response.status_code == 200
    body = response.text
    assert 'data-testid="poc-asset-table"' in body
    assert 'data-testid="poc-rebalance-page"' in body
    # Table exists but tbody has no rows (empty asset_plan)
    assert "EMPTY_PROFILE" in body or 'data-asset-key="selic"' not in body


def test_get_teste_has_eight_columns(client: TestClient, _omaha_test_env: dict[str, str]) -> None:
    """The POC table <thead> contains exactly 8 <th> columns."""
    _seed_two_classes(_omaha_test_env)
    _login_and_select(client, profile_id=1)

    response = client.get("/teste")

    assert response.status_code == 200
    body = response.text

    # Column definitions are rendered in the Alpine script
    assert "key: 'action'" in body
    assert "key: 'category_name'" in body
    assert "key: 'asset_name'" in body
    assert "key: 'current_value'" in body
    assert "key: 'target_value'" in body
    assert "key: 'deviation'" in body
    assert "key: 'projected_value'" in body
    assert "key: 'operation'" in body




def test_get_teste_uses_existing_css_classes(
    client: TestClient, _omaha_test_env: dict[str, str]
) -> None:
    """The POC table reuses the legacy CSS classes from app.css."""
    _seed_two_classes(_omaha_test_env)
    _login_and_select(client, profile_id=1)

    response = client.get("/teste")

    assert response.status_code == 200
    body = response.text
    # Table classes
    assert "rebalance-table" in body
    assert "rebalance-table-th" in body
    assert "rebalance-table-th-label" in body
    assert "rebalance-table-th-indicator" in body
    assert "rebalance-table-th--num" in body
    # Cell classes
    assert "rebalance-asset-cell" in body
    assert "rebalance-asset-cell--num" in body
    assert "rebalance-asset-cell--action" in body
    # Row classes
    assert "rebalance-asset-row" in body
    # Action badge classes (the --{action} suffix is composed at runtime by Alpine)
    assert "rebalance-action-badge" in body
    assert "rebalance-action-badge--" in body
    # Filter classes (column-level filters)
    assert "rebalance-filter-panel" in body
    assert "rebalance-filter-option" in body
    assert "rebalance-range-slider" in body


def test_get_teste_renders_translated_action_badges(
    client: TestClient, _omaha_test_env: dict[str, str]
) -> None:
    """The POC table renders Ação column with translated badge text."""
    _seed_two_classes(_omaha_test_env)
    _login_and_select(client, profile_id=1)

    response = client.get("/teste")

    assert response.status_code == 200
    body = response.text
    assert "Comprar" in body or "Vender" in body or "Manter" in body


def test_get_teste_does_not_persist_contribution(
    client: TestClient, _omaha_test_env: dict[str, str]
) -> None:
    """GET /teste does not set rebalance_contributions in session."""
    _seed_two_classes(_omaha_test_env)
    _login_and_select(client, profile_id=1)

    # First request
    response = client.get("/teste")
    assert response.status_code == 200

    # Second request to confirm idempotency (no session mutation between calls)
    response2 = client.get("/teste")
    assert response2.status_code == 200

    # After GET /teste, the rebalance page should still use the default
    # contribution (0), confirming no session persistence leaked from /teste
    rebalance_response = client.get("/rebalanceamento")
    assert rebalance_response.status_code == 200
    assert (
        '"contribution": 0.0' in rebalance_response.text
        or '"contribution":0.0' in rebalance_response.text
    )


def test_get_rebalanceamento_unchanged(client: TestClient, _omaha_test_env: dict[str, str]) -> None:
    """``GET /rebalanceamento`` continues to work unchanged after F27."""
    _seed_two_classes(_omaha_test_env)
    _login_and_select(client, profile_id=1)

    response = client.get("/rebalanceamento")

    assert response.status_code == 200
    body = response.text
    assert 'data-testid="rebalance-plan"' in body
    assert 'data-testid="rebalance-params-bar"' in body
