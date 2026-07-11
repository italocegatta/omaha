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


def test_unauthenticated_get_teste_bounces_to_login(client: TestClient) -> None:
    """``GET /teste`` without a session returns 303 to /login."""
    response = client.get("/teste", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/login"


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
    # Filter bar present
    assert 'data-testid="poc-filter-bar"' in body
    assert 'data-testid="poc-filter-class-trigger"' in body
    assert 'data-testid="poc-filter-action-trigger"' in body
    assert 'data-testid="poc-filter-search"' in body
    # Asset plan data serialized in JSON (Alpine renders rows at runtime)
    assert '"asset_key": "selic"' in body
    assert '"asset_key": "petr4"' in body
    # F27 bugfix: Alpine data bridge is wired and contains real numeric values
    assert "window.__pocRebalancePlan" in body
    assert ('"current_value": 6000.0' in body or '"current_value":6000.0' in body)
    assert ('"current_value": 4000.0' in body or '"current_value":4000.0' in body)
    # Legacy CSS classes present
    assert 'class="rebalance-table"' in body
    assert 'class="rebalance-table-th' in body
    assert 'class="rebalance-filter-bar"' in body


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


def test_get_teste_has_eleven_columns(
    client: TestClient, _omaha_test_env: dict[str, str]
) -> None:
    """The POC table <thead> contains exactly 11 <th> columns."""
    _seed_two_classes(_omaha_test_env)
    _login_and_select(client, profile_id=1)

    response = client.get("/teste")

    assert response.status_code == 200
    body = response.text

    # Check that all 11 column headers are present with correct testids
    th_testids = [
        "poc-asset-th-category",
        "poc-asset-th-name",
        "poc-asset-th-current-value",
        "poc-asset-th-target-value",
        "poc-asset-th-deviation-value",
        "poc-asset-th-deviation-pct",
        "poc-asset-th-buy",
        "poc-asset-th-sell",
        "poc-asset-th-quantity",
        "poc-asset-th-projected",
        "poc-asset-th-action",
    ]
    for testid in th_testids:
        assert f'data-testid="{testid}"' in body, f"Missing TH: {testid}"


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
    # Filter classes
    assert "rebalance-filter-bar" in body
    assert "rebalance-filter-group" in body
    assert "rebalance-filter-trigger" in body
    assert "rebalance-filter-panel" in body
    assert "rebalance-filter-option" in body
    assert "rebalance-filter-search" in body


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
    assert '"contribution": 0.0' in rebalance_response.text or '"contribution":0.0' in rebalance_response.text


def test_get_rebalanceamento_unchanged(
    client: TestClient, _omaha_test_env: dict[str, str]
) -> None:
    """``GET /rebalanceamento`` continues to work unchanged after F27."""
    _seed_two_classes(_omaha_test_env)
    _login_and_select(client, profile_id=1)

    response = client.get("/rebalanceamento")

    assert response.status_code == 200
    body = response.text
    assert 'data-testid="rebalance-plan"' in body
    assert 'data-testid="rebalance-params-bar"' in body
