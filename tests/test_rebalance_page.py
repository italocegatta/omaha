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
    """``GET /rebalance`` without a session returns 303 to /login."""
    response = client.get("/rebalance", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_get_rebalance_empty_profile_renders_empty_state(client: TestClient) -> None:
    """An authenticated user with zero classes sees the empty-state card."""
    _login_and_select(client, profile_id=1)

    response = client.get("/rebalance")

    assert response.status_code == 200
    body = response.text
    assert 'data-testid="rebalance-empty-state"' in body
    assert "Nenhuma classe cadastrada" in body
    # Sidebar form is present but inert — input + button carry disabled.
    assert 'data-testid="rebalance-form"' in body
    assert 'data-testid="sidebar-contribution-input"' in body
    assert "disabled" in body  # at least one disabled element


def test_get_rebalance_populated_profile_renders_placeholder(
    client: TestClient, _omaha_test_env: dict[str, str]
) -> None:
    """A profile with classes and no POST shows the placeholder card."""
    _seed_two_classes(_omaha_test_env)
    _login_and_select(client, profile_id=1)

    response = client.get("/rebalance")

    assert response.status_code == 200
    body = response.text
    assert 'data-testid="rebalance-placeholder"' in body
    assert 'data-testid="rebalance-empty-state"' not in body
    # Nav row + sidebar form.
    assert 'data-testid="rebalance-nav"' in body
    assert 'data-testid="rebalance-form"' in body
    # Sidebar form is NOT inert (profile has classes).
    assert 'data-testid="rebalance-form"' in body


# ---------------------------------------------------------------------------
# §"POST /rebalance renders the plan"
# ---------------------------------------------------------------------------


def _seed_two_classes(_omaha_test_env: dict[str, str]) -> None:
    _seed_class(1, "RF", "60", [("Selic", "100")], _omaha_test_env=_omaha_test_env)
    _seed_class(1, "RV", "40", [("PETR4", "100")], _omaha_test_env=_omaha_test_env)


def test_post_rebalance_valid_contribution_renders_plan(
    client: TestClient, _omaha_test_env: dict[str, str]
) -> None:
    """``POST /rebalance`` with a valid finite aporte renders the plan."""
    _seed_two_classes(_omaha_test_env)
    _login_and_select(client, profile_id=1)

    response = client.post("/rebalance", data={"contribution": "5000.00"})

    assert response.status_code == 200
    body = response.text
    # Plan layout rendered.
    assert 'data-testid="rebalance-plan"' in body
    # 6 metric cards (one per ``RebalancePlanMetrics`` key).
    for key in (
        "rebalance-stat-contribution",
        "rebalance-stat-total-buy",
        "rebalance-stat-total-sell",
        "rebalance-stat-residual-cash",
        "rebalance-stat-current-deviation",
        "rebalance-stat-projected-deviation",
    ):
        assert f'data-testid="{key}"' in body, f"missing metric card: {key}"
    # Asset plan table renders (stub fixture has at least 1 asset_plan row).
    assert 'data-testid="rebalance-asset-table"' in body
    # Category summary renders.
    assert 'data-testid="rebalance-category-table"' in body


def test_post_rebalance_zero_contribution_renders_plan(
    client: TestClient, _omaha_test_env: dict[str, str]
) -> None:
    """``contribution = 0`` renders the plan (zero is valid)."""
    _seed_two_classes(_omaha_test_env)
    _login_and_select(client, profile_id=1)

    response = client.post("/rebalance", data={"contribution": "0"})

    assert response.status_code == 200
    assert 'data-testid="rebalance-plan"' in response.text
    assert 'data-testid="rebalance-stat-contribution"' in response.text


def test_post_rebalance_negative_contribution_renders_plan(
    client: TestClient, _omaha_test_env: dict[str, str]
) -> None:
    """``contribution = -1000`` renders the plan (server is permissive).

    The page client-side gates ``< 0`` for v1, but the route is
    permissive in preparation for Phase 4 withdrawal support.
    """
    _seed_two_classes(_omaha_test_env)
    _login_and_select(client, profile_id=1)

    response = client.post("/rebalance", data={"contribution": "-1000"})

    assert response.status_code == 200
    assert 'data-testid="rebalance-plan"' in response.text


def test_post_rebalance_missing_contribution_renders_form_error(
    client: TestClient, _omaha_test_env: dict[str, str]
) -> None:
    """Missing ``contribution`` field re-renders with an inline error."""
    _seed_two_classes(_omaha_test_env)
    _login_and_select(client, profile_id=1)

    response = client.post("/rebalance", data={})

    assert response.status_code == 200
    body = response.text
    assert 'data-testid="rebalance-form-error"' in body
    assert "Informe um valor de aporte" in body


def test_post_rebalance_invalid_contribution_renders_form_error(
    client: TestClient, _omaha_test_env: dict[str, str]
) -> None:
    """Non-numeric contribution re-renders with the finite-float message."""
    _seed_two_classes(_omaha_test_env)
    _login_and_select(client, profile_id=1)

    response = client.post("/rebalance", data={"contribution": "abc"})

    assert response.status_code == 200
    body = response.text
    assert 'data-testid="rebalance-form-error"' in body
    assert "Valor inválido" in body


def test_post_rebalance_solver_validation_error_renders_inline(
    client: TestClient, _omaha_test_env: dict[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """A solver ``RebalanceValidationError`` is mapped to ``form_error``."""
    from omaha.rebalance import glue
    from omaha.rebalance.models import RebalanceValidationError
    from omaha.routes import pages as pages_routes

    _seed_two_classes(_omaha_test_env)
    _login_and_select(client, profile_id=1)

    def raising_run_rebalance(db, profile, contribution, *, solver=None):  # noqa: ARG001
        raise RebalanceValidationError("Classes devem somar 100%")

    monkeypatch.setattr(pages_routes, "run_rebalance", raising_run_rebalance)
    # Belt-and-suspenders: also patch the glue import path in case
    # the pages module captured a stale reference at import time.
    monkeypatch.setattr(glue, "run_rebalance", raising_run_rebalance)

    response = client.post("/rebalance", data={"contribution": "1000"})

    assert response.status_code == 200
    body = response.text
    assert 'data-testid="rebalance-form-error"' in body
    assert "Classes devem somar 100%" in body


# ---------------------------------------------------------------------------
# §"Asset plan table renders eight visible columns plus a data attribute"
# ---------------------------------------------------------------------------


def test_asset_plan_table_has_eight_visible_columns(
    client: TestClient, _omaha_test_env: dict[str, str]
) -> None:
    """The asset plan <thead> has exactly 8 <th> cells."""
    _seed_two_classes(_omaha_test_env)
    _login_and_select(client, profile_id=1)

    response = client.post("/rebalance", data={"contribution": "5000"})
    assert response.status_code == 200
    body = response.text

    # Match the asset plan table block: the first <table> after
    # ``rebalance-asset-table`` test-id marker is the asset plan.
    asset_th_keys = [
        "rebalance-asset-th-name",
        "rebalance-asset-th-category",
        "rebalance-asset-th-current-value",
        "rebalance-asset-th-target-value",
        "rebalance-asset-th-buy",
        "rebalance-asset-th-sell",
        "rebalance-asset-th-projected",
        "rebalance-asset-th-action",
    ]
    for key in asset_th_keys:
        assert f'data-testid="{key}"' in body, f"missing asset table column: {key}"


def test_category_summary_has_four_columns(
    client: TestClient, _omaha_test_env: dict[str, str]
) -> None:
    """The category summary <thead> has exactly 4 <th> cells."""
    _seed_two_classes(_omaha_test_env)
    _login_and_select(client, profile_id=1)

    response = client.post("/rebalance", data={"contribution": "5000"})
    assert response.status_code == 200
    body = response.text

    for key in (
        "rebalance-category-th-name",
        "rebalance-category-th-current",
        "rebalance-category-th-projected",
        "rebalance-category-th-delta",
    ):
        assert f'data-testid="{key}"' in body, f"missing category column: {key}"


# ---------------------------------------------------------------------------
# §"Stub banner conditional on applied_policy"
# ---------------------------------------------------------------------------


def test_stub_banner_visible_under_fixture_stub(
    client: TestClient, _omaha_test_env: dict[str, str]
) -> None:
    """When the stub solver runs, ``applied_policy == "stub-fixture-v1"``
    and the stub banner is rendered."""
    _seed_two_classes(_omaha_test_env)
    _login_and_select(client, profile_id=1)

    response = client.post("/rebalance", data={"contribution": "5000"})
    assert response.status_code == 200
    body = response.text

    assert 'data-testid="rebalance-applied-policy"' in body
    assert "stub-fixture-v1" in body
    assert 'data-testid="rebalance-stub-banner"' in body


def test_warnings_panel_present_when_stub_emits_warning(
    client: TestClient, _omaha_test_env: dict[str, str]
) -> None:
    """The stub fixture carries at least one warning → panel renders."""
    _seed_two_classes(_omaha_test_env)
    _login_and_select(client, profile_id=1)

    response = client.post("/rebalance", data={"contribution": "5000"})
    assert response.status_code == 200
    body = response.text

    assert 'data-testid="rebalance-warnings"' in body


# ---------------------------------------------------------------------------
# §"Sidebar carries the rebalance form on every authenticated page"
# ---------------------------------------------------------------------------


def test_dashboard_sidebar_carries_rebalance_form(client: TestClient) -> None:
    """``GET /`` renders the rebalance form in the sidebar."""
    _login_and_select(client, profile_id=1)

    response = client.get("/")
    assert response.status_code == 200
    body = response.text

    assert 'data-testid="rebalance-form"' in body
    # Form's action attribute is /rebalance, method is post.
    assert 'action="/rebalance"' in body
    assert 'method="post"' in body
    # The 4th nav link exists.
    assert 'data-testid="rebalance-nav-link"' in body


def test_rebalance_page_sidebar_active_state(client: TestClient) -> None:
    """``GET /rebalance`` carries ``aria-current="true"`` on the Rebalancear link."""
    _login_and_select(client, profile_id=1)

    response = client.get("/rebalance")
    assert response.status_code == 200
    body = response.text

    # The nav link is rendered with the active-state class and aria-current.
    assert 'data-testid="rebalance-nav-link"' in body
    assert "sidebar-action--active" in body
    assert 'aria-current="true"' in body
