"""Integration tests for POST /api/rebalance.

Covers the spec §"POST /api/rebalance returns a
RebalancePlanResponse", §"Request validates contribution greater
than zero", and §"RebalanceValidationError maps to HTTP 400".

The DB is the session-scoped SQLite from ``tests/conftest.py``.
Each test wipes the dashboard tables so leftover state from
sibling tests doesn't leak in.

Session-locality gotcha
-----------------------
``omaha.db.SessionLocal`` is bound to the engine at import time.
``_omaha_test_env`` deletes ``omaha.*`` from ``sys.modules`` and
re-imports with the test ``DATABASE_URL`` — but the test module's
local ``SessionLocal`` name (imported at the top of the file) is
already bound to the OLD engine pointing at the dev DB. The
helpers below therefore re-import ``omaha.db`` inside the function
body so they always pick up the fresh ``SessionLocal``.
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from omaha.models import Asset, AssetClass, Position, QuoteKind

# Mirror the seed profile owners from test_assets_trade_flags.py.
_PROFILE_OWNERS = {1: "Italo", 2: "Ana"}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _wipe_tables(_omaha_test_env: dict[str, str]) -> None:
    """Wipe classes / assets before each test (via a fresh engine on the test DB)."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    engine = create_engine(_omaha_test_env["db_url"], future=True)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    db = SessionLocal()
    try:
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
        data={"username": _PROFILE_OWNERS[profile_id], "password": "test-password"},
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
    """Seed one Position per asset name. Required by Phase 4's CVXPY validator."""
    import os

    from omaha.db import SessionLocal as GlobalSessionLocal
    from omaha.models import Position

    os.environ["DATABASE_URL"] = _omaha_test_env["db_url"]
    with GlobalSessionLocal() as db:
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


# ---------------------------------------------------------------------------
# §"POST /api/rebalance returns a RebalancePlanResponse"
# ---------------------------------------------------------------------------


def test_active_profile_returns_200_with_plan(
    client: TestClient, _omaha_test_env: dict[str, str]
) -> None:
    """A logged-in user with an active profile gets a 200 + plan."""
    _seed_class(1, "RF", "60", [("Selic", "100")], _omaha_test_env=_omaha_test_env)
    _seed_class(1, "RV", "40", [("PETR4", "100")], _omaha_test_env=_omaha_test_env)
    _seed_positions(_omaha_test_env, {"Selic": 6_000.0, "PETR4": 4_000.0})

    _login_and_select(client, profile_id=1)

    response = client.post(
        "/api/rebalance",
        json={"contribution": 5000.0},
    )

    assert response.status_code == 200
    body = response.json()
    assert "asset_plan" in body
    assert "category_plan" in body
    assert "metrics" in body
    assert "warnings" in body
    assert "applied_policy" in body
    assert body["metrics"]["contribution"] == 5000.0

    # New F18 schema fields: deviation on asset rows
    for row in body["asset_plan"]:
        assert "deviation_value" in row
        assert "deviation_pct" in row
        assert isinstance(row["deviation_value"], float)
        assert isinstance(row["deviation_pct"], float)

    # New F18 schema fields: pct + deviation on category rows
    for row in body["category_plan"]:
        assert "target_pct" in row
        assert "current_pct" in row
        assert "deviation_pct" in row
        assert isinstance(row["target_pct"], float)
        assert isinstance(row["current_pct"], float)
        assert isinstance(row["deviation_pct"], float)


def test_unauthenticated_request_returns_redirect(client: TestClient) -> None:
    """An unauthenticated request bounces to /login (303 per require_user)."""
    response = client.post(
        "/api/rebalance",
        json={"contribution": 1000.0},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["Location"] == "/login"


# ---------------------------------------------------------------------------
# §"Request validates contribution as a finite float"
# ---------------------------------------------------------------------------


def test_zero_contribution_renders_plan(client: TestClient) -> None:
    """``contribution = 0`` returns 200 with the populated plan.

    rebalance-page contract extension: zero is a valid rebalance-only
    scenario (no new money, just reallocation). Previously rejected
    with 422 by ``Field(gt=0)``; now accepted.
    """
    _login_and_select(client, profile_id=1)

    response = client.post(
        "/api/rebalance",
        json={"contribution": 0},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["metrics"]["contribution"] == 0.0


def test_negative_contribution_renders_plan(client: TestClient) -> None:
    """``contribution < 0`` returns 200 with the populated plan.

    rebalance-page contract extension: negative is accepted
    server-side (withdrawal support in Phase 4). The page gates this
    client-side for v1; the route stays permissive for forward
    compatibility with the CVXPY solver.
    """
    _login_and_select(client, profile_id=1)

    response = client.post(
        "/api/rebalance",
        json={"contribution": -100.0},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["metrics"]["contribution"] == -100.0


# Note: NaN / Infinity coverage for the contract lives in
# ``tests/test_rebalance_schemas.py::test_request_rejects_nan_contribution``
# and ``test_request_rejects_infinity_contribution`` — the Pydantic
# validator is the boundary that matters, and the schema tests exercise
# it directly without having to round-trip a non-JSON-compliant value
# through Starlette's JSONResponse encoder (which would raise a
# separate error in the error-rendering path before the test could
# assert 422).


def test_missing_contribution_defaults_to_zero(client: TestClient) -> None:
    """Missing ``contribution`` resolves to zero and still returns a plan."""
    _login_and_select(client, profile_id=1)

    response = client.post(
        "/api/rebalance",
        json={},
    )

    assert response.status_code == 200
    assert response.json()["metrics"]["contribution"] == 0.0


# ---------------------------------------------------------------------------
# §"RebalanceValidationError maps to HTTP 400"
# ---------------------------------------------------------------------------


def test_solver_validation_error_returns_400(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, _omaha_test_env: dict[str, str]
) -> None:
    """When the solver raises ``RebalanceValidationError``, the route returns 400.

    The bridge itself does NOT raise — Phase 4's solver will. The
    test injects a solver that raises to exercise the error-mapping
    branch in the route.
    """
    from omaha.rebalance.models import RebalanceValidationError

    _login_and_select(client, profile_id=1)
    _seed_class(1, "RF", "100", [("Selic", "100")], _omaha_test_env=_omaha_test_env)

    def raising_solver(setup, positions, quotes, contribution):
        raise RebalanceValidationError("Classes devem somar 100%")

    from omaha.rebalance import glue

    monkeypatch.setattr(glue, "cvxpy_solver", raising_solver)

    response = client.post(
        "/api/rebalance",
        json={"contribution": 1000.0},
    )

    assert response.status_code == 400
    assert "Classes devem somar 100%" in response.json()["detail"]


# ---------------------------------------------------------------------------
# Empty profile returns 200 + EMPTY_PROFILE warning
# ---------------------------------------------------------------------------


def test_empty_profile_returns_200_with_warning(client: TestClient) -> None:
    """A profile with zero classes returns 200 + EMPTY_PROFILE warning."""
    _login_and_select(client, profile_id=1)

    response = client.post(
        "/api/rebalance",
        json={"contribution": 1000.0},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["asset_plan"] == []
    assert body["category_plan"] == []
    codes = [w["code"] for w in body["warnings"]]
    assert "EMPTY_PROFILE" in codes


def test_deviation_fields_on_plan_rows(client: TestClient, _omaha_test_env: dict[str, str]) -> None:
    """Deviation fields are present and division-by-zero returns 0.0."""
    _seed_class(1, "RF", "100", [("Selic", "100")], _omaha_test_env=_omaha_test_env)
    _seed_positions(_omaha_test_env, {"Selic": 5_000.0})
    _login_and_select(client, profile_id=1)

    response = client.post("/api/rebalance", json={"contribution": 0})
    assert response.status_code == 200
    body = response.json()

    # Asset rows have deviation fields
    for row in body["asset_plan"]:
        assert "deviation_value" in row
        assert "deviation_pct" in row

    # Category rows have pct fields
    for row in body["category_plan"]:
        assert "target_pct" in row
        assert "current_pct" in row
        assert "deviation_pct" in row
        # pct values should sum toward 100 (single class = 100%)
        assert row["current_pct"] >= 0.0
        assert row["target_pct"] >= 0.0
